use crate::config::{SttEnv, TtsEnv};
use crate::models::{SttOptions, SttOutput, TtsOptions, TtsOutput};
use base64::engine::general_purpose::STANDARD as BASE64_STANDARD;
use base64::Engine;
use flate2::read::GzDecoder;
use flate2::write::GzEncoder;
use flate2::Compression;
use serde_json::{json, Value};
use std::fs;
use std::io::{BufRead, BufReader, Read, Write};
use std::path::{Path, PathBuf};
use std::thread;
use std::time::{Duration, SystemTime, UNIX_EPOCH};
use tungstenite::client::IntoClientRequest;
use tungstenite::http::HeaderValue;
use tungstenite::{connect, Message};
use uuid::Uuid;

const TTS_URL: &str = "https://openspeech.bytedance.com/api/v3/tts/unidirectional";
const STT_WS_URL: &str = "wss://openspeech.bytedance.com/api/v3/sauc/bigmodel_nostream";

const PROTOCOL_VERSION_V1: u8 = 0b0001;
const CLIENT_FULL_REQUEST: u8 = 0b0001;
const CLIENT_AUDIO_ONLY_REQUEST: u8 = 0b0010;
const SERVER_FULL_RESPONSE: u8 = 0b1001;
const SERVER_ERROR_RESPONSE: u8 = 0b1111;
const FLAG_POS_SEQUENCE: u8 = 0b0001;
const FLAG_NEG_WITH_SEQUENCE: u8 = 0b0011;
const SERIALIZATION_JSON: u8 = 0b0001;
const COMPRESSION_GZIP: u8 = 0b0001;
const TTS_FINISH_CODE: i64 = 20_000_000;

#[derive(Debug)]
struct AsrResponse {
    code: i32,
    is_last_package: bool,
    payload_msg: Option<Value>,
}

pub fn synthesize(env: &TtsEnv, options: &TtsOptions) -> Result<String, String> {
    validate_tts_options(options)?;

    let additions = json!({
        "explicit_language": "zh",
        "disable_markdown_filter": true,
        "enable_timestamp": true,
    })
    .to_string();

    let mut audio_params = json!({
        "format": options.format,
        "sample_rate": options.sample_rate,
        "enable_timestamp": true,
        "speech_rate": options.speech_rate,
        "loudness_rate": options.loudness_rate
    });

    if let Some(emotion) = &options.emotion {
        audio_params["emotion"] = Value::String(emotion.clone());
    }
    if let Some(emotion_scale) = options.emotion_scale {
        audio_params["emotion_scale"] = json!(emotion_scale);
    }

    let payload = json!({
        "user": { "uid": options.uid },
        "req_params": {
            "text": options.text,
            "speaker": options.speaker,
            "audio_params": audio_params,
            "additions": additions
        }
    });

    let response = http_agent()
        .post(TTS_URL)
        .set("X-Api-App-Id", &env.app_id)
        .set("X-Api-Access-Key", &env.access_key)
        .set("X-Api-Resource-Id", &env.resource_id)
        .set("Content-Type", "application/json")
        .set("Connection", "keep-alive")
        .send_string(&payload.to_string())
        .map_err(|err| format_ureq_error("POST", TTS_URL, err))?;

    let log_id = response.header("X-Tt-Logid").map(ToOwned::to_owned);
    let mut reader = BufReader::new(response.into_reader());
    let mut audio_data = Vec::new();
    let mut line = String::new();

    loop {
        line.clear();
        let bytes = reader
            .read_line(&mut line)
            .map_err(|err| format!("Failed to read TTS stream: {}", err))?;
        if bytes == 0 {
            break;
        }

        let trimmed = line.trim();
        if trimmed.is_empty() {
            continue;
        }

        let payload: Value = serde_json::from_str(trimmed)
            .map_err(|err| format!("Failed to parse TTS chunk JSON: {}", err))?;
        let code = payload.get("code").and_then(Value::as_i64).unwrap_or(0);

        if code == 0 {
            if let Some(chunk) = payload.get("data").and_then(Value::as_str) {
                if !chunk.is_empty() {
                    let decoded = BASE64_STANDARD
                        .decode(chunk)
                        .map_err(|err| format!("Failed to decode TTS audio chunk: {}", err))?;
                    audio_data.extend(decoded);
                }
            }
            continue;
        }

        if code == TTS_FINISH_CODE {
            break;
        }

        return Err(format!("TTS API returned error chunk: {}", payload));
    }

    if audio_data.is_empty() {
        return Err("TTS finished without returning audio data.".to_string());
    }

    let output_path = resolve_output_path(options.output.as_deref(), &options.format, "tts")?;
    if let Some(parent) = output_path.parent() {
        fs::create_dir_all(parent)
            .map_err(|err| format!("Failed to create {}: {}", parent.display(), err))?;
    }
    fs::write(&output_path, &audio_data)
        .map_err(|err| format!("Failed to write {}: {}", output_path.display(), err))?;

    let result = TtsOutput {
        kind: "audio",
        local_path: output_path.display().to_string(),
        format: options.format.clone(),
        bytes: audio_data.len(),
        log_id,
        speaker: options.speaker.clone(),
        sample_rate: options.sample_rate,
        emotion: options.emotion.clone(),
        emotion_scale: options.emotion_scale,
        speech_rate: options.speech_rate,
        loudness_rate: options.loudness_rate,
    };

    serde_json::to_string_pretty(&result)
        .map_err(|err| format!("Failed to format TTS output JSON: {}", err))
}

fn validate_tts_options(options: &TtsOptions) -> Result<(), String> {
    if let Some(scale) = options.emotion_scale {
        if !(1..=5).contains(&scale) {
            return Err("--emotion-scale must be between 1 and 5.".to_string());
        }
        if options.emotion.is_none() {
            return Err("--emotion-scale requires --emotion.".to_string());
        }
    }

    if !(-50..=100).contains(&options.speech_rate) {
        return Err("--speech-rate must be between -50 and 100.".to_string());
    }

    if !(-50..=100).contains(&options.loudness_rate) {
        return Err("--loudness-rate must be between -50 and 100.".to_string());
    }

    Ok(())
}

pub fn transcribe(env: &SttEnv, options: &SttOptions) -> Result<String, String> {
    let content = fs::read(&options.file_path)
        .map_err(|err| format!("Failed to read {}: {}", options.file_path, err))?;
    if content.is_empty() {
        return Err("Audio file is empty.".to_string());
    }

    let mut request = STT_WS_URL
        .into_client_request()
        .map_err(|err| format!("Failed to create WebSocket request: {}", err))?;
    let headers = request.headers_mut();
    headers.insert(
        "X-Api-Resource-Id",
        HeaderValue::from_str(&env.resource_id)
            .map_err(|err| format!("Invalid STT resource id header: {}", err))?,
    );
    headers.insert(
        "X-Api-Connect-Id",
        HeaderValue::from_str(&Uuid::new_v4().to_string())
            .map_err(|err| format!("Failed to create connect id: {}", err))?,
    );
    headers.insert(
        "X-Api-Access-Key",
        HeaderValue::from_str(&env.access_key)
            .map_err(|err| format!("Invalid STT access key header: {}", err))?,
    );
    headers.insert(
        "X-Api-App-Key",
        HeaderValue::from_str(&env.app_id)
            .map_err(|err| format!("Invalid STT app id header: {}", err))?,
    );

    let (mut socket, _) =
        connect(request).map_err(|err| format!("Failed to connect STT WebSocket: {}", err))?;

    let mut seq = 1_i32;
    socket
        .send(Message::Binary(build_full_request(seq, options)?))
        .map_err(|err| format!("Failed to send STT full request: {}", err))?;
    seq += 1;

    if let Some(response) = read_binary_response(&mut socket)? {
        if response.code != 0 {
            return Err(format!(
                "STT full request failed with code {}",
                response.code
            ));
        }
    }

    let segment_size = calculate_segment_size(content.len());
    let segments = split_audio(&content, segment_size);
    for (index, segment) in segments.iter().enumerate() {
        let is_last = index + 1 == segments.len();
        let frame = build_audio_request(seq, segment, is_last);
        socket
            .send(Message::Binary(frame))
            .map_err(|err| format!("Failed to send STT audio segment: {}", err))?;
        if !is_last {
            seq += 1;
        }
        thread::sleep(Duration::from_millis(options.seg_duration_ms));
    }

    let mut final_text = String::new();
    let mut final_payload: Option<Value> = None;

    loop {
        let Some(response) = read_binary_response(&mut socket)? else {
            break;
        };
        if response.code != 0 {
            return Err(format!("STT stream failed with code {}", response.code));
        }
        if let Some(payload) = response.payload_msg {
            if let Some(text) = payload
                .get("result")
                .and_then(|value| value.get("text"))
                .and_then(Value::as_str)
            {
                if !text.is_empty() {
                    final_text = text.to_string();
                }
            }
            final_payload = Some(payload);
        }
        if response.is_last_package {
            break;
        }
    }

    if final_text.is_empty() {
        return Err("STT finished without returning final text.".to_string());
    }

    let result = SttOutput {
        kind: "transcript",
        text: final_text,
        file_path: options.file_path.clone(),
        payload: if options.json_output {
            final_payload
        } else {
            None
        },
    };

    serde_json::to_string_pretty(&result)
        .map_err(|err| format!("Failed to format STT output JSON: {}", err))
}

fn http_agent() -> ureq::Agent {
    ureq::AgentBuilder::new()
        .timeout_read(Duration::from_secs(120))
        .timeout_write(Duration::from_secs(30))
        .build()
}

fn format_ureq_error(method: &str, url: &str, err: ureq::Error) -> String {
    match err {
        ureq::Error::Status(code, resp) => {
            let body = resp
                .into_string()
                .unwrap_or_else(|_| "<failed to read error body>".to_string());
            format!("{} {} failed with status {}: {}", method, url, code, body)
        }
        other => format!("{} {} failed: {}", method, url, other),
    }
}

fn resolve_output_path(
    output: Option<&str>,
    extension: &str,
    prefix: &str,
) -> Result<PathBuf, String> {
    if let Some(path) = output {
        let path = PathBuf::from(path);
        if path.is_absolute() {
            return Ok(path);
        }
        let cwd =
            std::env::current_dir().map_err(|err| format!("Failed to get current dir: {}", err))?;
        return Ok(cwd.join(path));
    }

    let cwd =
        std::env::current_dir().map_err(|err| format!("Failed to get current dir: {}", err))?;
    let generated_dir = cwd.join("generated");
    let filename = format!(
        "{}-{}.{}",
        prefix,
        unix_ts(),
        extension.trim_start_matches('.')
    );
    Ok(generated_dir.join(filename))
}

fn unix_ts() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|value| value.as_secs())
        .unwrap_or(0)
}

fn calculate_segment_size(file_size: usize) -> usize {
    let num_segments = std::cmp::max(10, file_size / 6400);
    std::cmp::max(1, file_size / num_segments)
}

fn split_audio(content: &[u8], segment_size: usize) -> Vec<Vec<u8>> {
    content
        .chunks(segment_size.max(1))
        .map(|chunk| chunk.to_vec())
        .collect()
}

fn build_full_request(seq: i32, options: &SttOptions) -> Result<Vec<u8>, String> {
    let payload = json!({
        "user": { "uid": options.uid },
        "audio": {
            "format": options.audio_format,
            "codec": options.codec,
            "rate": options.rate,
            "bits": options.bits,
            "channel": options.channels
        },
        "request": {
            "model_name": "bigmodel",
            "enable_itn": true,
            "enable_punc": true
        }
    });

    let compressed = gzip_compress(payload.to_string().as_bytes())?;
    let mut request = Vec::with_capacity(12 + compressed.len());
    request.extend(build_header(CLIENT_FULL_REQUEST, FLAG_POS_SEQUENCE));
    request.extend(seq.to_be_bytes());
    request.extend((compressed.len() as u32).to_be_bytes());
    request.extend(compressed);
    Ok(request)
}

fn build_audio_request(seq: i32, segment: &[u8], is_last: bool) -> Vec<u8> {
    let mut request = Vec::new();
    let flags = if is_last {
        FLAG_NEG_WITH_SEQUENCE
    } else {
        FLAG_POS_SEQUENCE
    };
    let sequence = if is_last { -seq } else { seq };
    let compressed = gzip_compress(segment).unwrap_or_else(|_| segment.to_vec());
    request.extend(build_header(CLIENT_AUDIO_ONLY_REQUEST, flags));
    request.extend(sequence.to_be_bytes());
    request.extend((compressed.len() as u32).to_be_bytes());
    request.extend(compressed);
    request
}

fn build_header(message_type: u8, flags: u8) -> [u8; 4] {
    [
        (PROTOCOL_VERSION_V1 << 4) | 0x01,
        (message_type << 4) | flags,
        (SERIALIZATION_JSON << 4) | COMPRESSION_GZIP,
        0x00,
    ]
}

fn read_binary_response(
    socket: &mut tungstenite::WebSocket<tungstenite::stream::MaybeTlsStream<std::net::TcpStream>>,
) -> Result<Option<AsrResponse>, String> {
    loop {
        let message = socket
            .read()
            .map_err(|err| format!("Failed to read STT WebSocket message: {}", err))?;
        match message {
            Message::Binary(data) => return parse_asr_response(&data).map(Some),
            Message::Close(_) => return Ok(None),
            Message::Ping(payload) => {
                socket
                    .send(Message::Pong(payload))
                    .map_err(|err| format!("Failed to respond to STT ping: {}", err))?;
            }
            Message::Text(_) | Message::Pong(_) | Message::Frame(_) => {}
        }
    }
}

fn parse_asr_response(msg: &[u8]) -> Result<AsrResponse, String> {
    if msg.len() < 4 {
        return Err("Invalid STT response: too short".to_string());
    }

    let header_words = (msg[0] & 0x0F) as usize;
    let header_size = header_words * 4;
    if msg.len() < header_size {
        return Err("Invalid STT response: header size exceeds message length".to_string());
    }

    let message_type = msg[1] >> 4;
    let flags = msg[1] & 0x0F;
    let mut cursor = header_size;
    let mut is_last_package = false;

    if flags & 0x01 != 0 {
        if msg.len() < cursor + 4 {
            return Err("Invalid STT response: missing sequence".to_string());
        }
        cursor += 4;
    }
    if flags & 0x02 != 0 {
        is_last_package = true;
    }

    let mut code = 0_i32;
    match message_type {
        SERVER_FULL_RESPONSE => {
            if msg.len() < cursor + 4 {
                return Err("Invalid STT response: missing payload size".to_string());
            }
            cursor += 4;
        }
        SERVER_ERROR_RESPONSE => {
            if msg.len() < cursor + 8 {
                return Err("Invalid STT error response: missing code or payload size".to_string());
            }
            code = i32::from_be_bytes(msg[cursor..cursor + 4].try_into().unwrap());
            cursor += 8;
        }
        _ => {}
    }

    let payload = &msg[cursor..];
    let payload_msg = if payload.is_empty() {
        None
    } else {
        Some(parse_json_payload(payload)?)
    };

    Ok(AsrResponse {
        code,
        is_last_package,
        payload_msg,
    })
}

fn parse_json_payload(payload: &[u8]) -> Result<Value, String> {
    match gzip_decompress(payload) {
        Ok(decoded) => serde_json::from_slice(&decoded)
            .map_err(|err| format!("Failed to parse gzip STT payload: {}", err)),
        Err(_) => serde_json::from_slice(payload)
            .map_err(|err| format!("Failed to parse STT payload JSON: {}", err)),
    }
}

fn gzip_compress(input: &[u8]) -> Result<Vec<u8>, String> {
    let mut encoder = GzEncoder::new(Vec::new(), Compression::default());
    encoder
        .write_all(input)
        .map_err(|err| format!("Failed to gzip-compress payload: {}", err))?;
    encoder
        .finish()
        .map_err(|err| format!("Failed to finalize gzip payload: {}", err))
}

fn gzip_decompress(input: &[u8]) -> Result<Vec<u8>, String> {
    let mut decoder = GzDecoder::new(input);
    let mut output = Vec::new();
    decoder
        .read_to_end(&mut output)
        .map_err(|err| format!("Failed to gzip-decompress payload: {}", err))?;
    Ok(output)
}

pub fn infer_audio_format(file_path: &str) -> String {
    match Path::new(file_path)
        .extension()
        .and_then(|ext| ext.to_str())
        .map(|ext| ext.to_ascii_lowercase())
        .as_deref()
    {
        Some("wav") => "wav".to_string(),
        Some("pcm") => "pcm".to_string(),
        Some("mp3") => "mp3".to_string(),
        Some("ogg") | Some("opus") => "ogg".to_string(),
        _ => "ogg".to_string(),
    }
}

pub fn infer_codec(audio_format: &str) -> String {
    match audio_format {
        "wav" | "pcm" => "raw".to_string(),
        "mp3" => "raw".to_string(),
        _ => "opus".to_string(),
    }
}
