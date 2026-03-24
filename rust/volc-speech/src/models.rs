use serde::Serialize;
use serde_json::Value;

#[derive(Debug, Clone)]
pub struct TtsOptions {
    pub text: String,
    pub speaker: String,
    pub format: String,
    pub sample_rate: u32,
    pub emotion: Option<String>,
    pub emotion_scale: Option<u8>,
    pub speech_rate: i32,
    pub loudness_rate: i32,
    pub output: Option<String>,
    pub uid: String,
}

#[derive(Debug, Clone)]
pub struct SttOptions {
    pub file_path: String,
    pub audio_format: String,
    pub codec: String,
    pub rate: u32,
    pub bits: u16,
    pub channels: u16,
    pub seg_duration_ms: u64,
    pub json_output: bool,
    pub uid: String,
}

#[derive(Serialize)]
pub struct TtsOutput {
    #[serde(rename = "type")]
    pub kind: &'static str,
    pub local_path: String,
    pub format: String,
    pub bytes: usize,
    pub log_id: Option<String>,
    pub speaker: String,
    pub sample_rate: u32,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub emotion: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub emotion_scale: Option<u8>,
    pub speech_rate: i32,
    pub loudness_rate: i32,
}

#[derive(Serialize)]
pub struct SttOutput {
    #[serde(rename = "type")]
    pub kind: &'static str,
    pub text: String,
    pub file_path: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub payload: Option<Value>,
}
