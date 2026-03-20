use crate::models::*;
use base64::engine::general_purpose::STANDARD as BASE64_STANDARD;
use base64::Engine;
use image::codecs::jpeg::JpegEncoder;
use image::codecs::png::PngEncoder;
use image::imageops::FilterType;
use image::ColorType;
use image::DynamicImage;
use image::GenericImageView;
use image::ImageEncoder;
use std::fs;
use std::fs::File;
use std::io;
use std::path::Path;
use std::path::PathBuf;
use std::thread;
use std::time::Duration;
use std::time::{SystemTime, UNIX_EPOCH};

const BASE_URL: &str = "https://ark.cn-beijing.volces.com/api/v3";
const DEFAULT_IMAGE_MODEL: &str = "doubao-seedream-5-0-260128";
const DEFAULT_VIDEO_MODEL: &str = "doubao-seedance-1-5-pro-251215";
const DEFAULT_IMAGE_SIZE: &str = "2848x1600";
const DEFAULT_SIZE_PRESET: &str = "16:9";
const I2I_MAX_EDGE: u32 = 1600;
const I2V_MAX_EDGE: u32 = 1280;
const I2I_MIN_EDGE: u32 = 64;
const I2V_MIN_EDGE: u32 = 300;
const JPEG_QUALITY: u8 = 84;

#[derive(Clone, Copy)]
enum UploadProfile {
    ImageToImage,
    ImageToVideo,
}

impl UploadProfile {
    fn max_edge(self) -> u32 {
        match self {
            UploadProfile::ImageToImage => I2I_MAX_EDGE,
            UploadProfile::ImageToVideo => I2V_MAX_EDGE,
        }
    }

    fn min_edge(self) -> u32 {
        match self {
            UploadProfile::ImageToImage => I2I_MIN_EDGE,
            UploadProfile::ImageToVideo => I2V_MIN_EDGE,
        }
    }
}

fn image_model() -> String {
    std::env::var("VOLC_IMAGE_MODEL_ID").unwrap_or_else(|_| DEFAULT_IMAGE_MODEL.to_string())
}

fn video_model() -> String {
    std::env::var("VOLC_VIDEO_MODEL_ID").unwrap_or_else(|_| DEFAULT_VIDEO_MODEL.to_string())
}

fn agent() -> ureq::Agent {
    ureq::AgentBuilder::new()
        .timeout_read(Duration::from_secs(60))
        .timeout_write(Duration::from_secs(30))
        .build()
}

fn post_json(api_key: &str, path: &str, body: &impl serde::Serialize) -> Result<String, String> {
    let url = format!("{}{}", BASE_URL, path);
    let resp = agent()
        .post(&url)
        .set("Content-Type", "application/json")
        .set("Authorization", &format!("Bearer {}", api_key))
        .send_string(&serde_json::to_string(body).unwrap())
        .map_err(|e| format_ureq_error("POST", &url, e))?;
    resp.into_string().map_err(|e| format!("Read body failed: {}", e))
}

fn get_json(api_key: &str, url: &str) -> Result<String, String> {
    let resp = agent()
        .get(url)
        .set("Authorization", &format!("Bearer {}", api_key))
        .call()
        .map_err(|e| format_ureq_error("GET", url, e))?;
    resp.into_string().map_err(|e| format!("Read body failed: {}", e))
}

fn resolve_generation_size(size: &str) -> Result<String, String> {
    let normalized = size.trim().to_ascii_lowercase();
    let resolved = match normalized.as_str() {
        "" | "2k" => DEFAULT_IMAGE_SIZE,
        "1:1" => "2048x2048",
        "3:4" => "1728x2304",
        "4:3" => "2304x1728",
        DEFAULT_SIZE_PRESET => "2848x1600",
        "9:16" => "1600x2848",
        "3:2" => "2496x1664",
        "2:3" => "1664x2496",
        "21:9" => "3136x1344",
        _ if is_explicit_size(&normalized) => size.trim(),
        _ => {
            return Err(format!(
                "Unsupported size '{}'. Use one of 1:1, 3:4, 4:3, 16:9, 9:16, 3:2, 2:3, 21:9, 2K, or an explicit WIDTHxHEIGHT.",
                size
            ))
        }
    };
    Ok(resolved.to_string())
}

fn is_explicit_size(value: &str) -> bool {
    let Some((w, h)) = value.split_once('x') else {
        return false;
    };
    w.parse::<u32>().is_ok() && h.parse::<u32>().is_ok()
}

fn normalize_image_input(image: &str, profile: UploadProfile) -> Result<String, String> {
    let bytes = read_image_input_bytes(image)?;
    prepare_image_for_upload(&bytes, profile)
}

fn read_image_input_bytes(image: &str) -> Result<Vec<u8>, String> {
    if image.starts_with("http://") || image.starts_with("https://") {
        let resp = agent()
            .get(image)
            .call()
            .map_err(|e| format_ureq_error("GET", image, e))?;
        let mut reader = resp.into_reader();
        let mut buf = Vec::new();
        io::copy(&mut reader, &mut buf).map_err(|e| format!("Failed to read {}: {}", image, e))?;
        return Ok(buf);
    }

    if image.starts_with("data:image/") {
        return decode_data_url(image);
    }

    let path = Path::new(image);
    if !path.exists() {
        return Err(format!(
            "Image input must be an http(s) URL, a data URL, or an existing local file path: {}",
            image
        ));
    }

    fs::read(path).map_err(|e| format!("Failed to read image file {}: {}", image, e))
}

fn decode_data_url(value: &str) -> Result<Vec<u8>, String> {
    let Some((header, payload)) = value.split_once(',') else {
        return Err("Invalid data URL: missing comma separator".to_string());
    };

    if !header.ends_with(";base64") {
        return Err("Invalid data URL: only base64-encoded image data is supported".to_string());
    }

    BASE64_STANDARD
        .decode(payload)
        .map_err(|e| format!("Failed to decode image data URL: {}", e))
}

fn prepare_image_for_upload(bytes: &[u8], profile: UploadProfile) -> Result<String, String> {
    let image = image::load_from_memory(bytes).map_err(|e| format!("Failed to decode image: {}", e))?;
    let image = resize_for_profile(image, profile);
    let has_alpha = image.color().has_alpha();

    let (mime, encoded) = if has_alpha {
        let rgba = image.to_rgba8();
        let (w, h) = rgba.dimensions();
        let mut out = Vec::new();
        PngEncoder::new(&mut out)
            .write_image(rgba.as_raw(), w, h, ColorType::Rgba8.into())
            .map_err(|e| format!("Failed to encode PNG: {}", e))?;
        ("image/png", out)
    } else {
        let rgb = image.to_rgb8();
        let (w, h) = rgb.dimensions();
        let mut out = Vec::new();
        let mut encoder = JpegEncoder::new_with_quality(&mut out, JPEG_QUALITY);
        encoder
            .encode(rgb.as_raw(), w, h, ColorType::Rgb8.into())
            .map_err(|e| format!("Failed to encode JPEG: {}", e))?;
        ("image/jpeg", out)
    };

    Ok(format!("data:{};base64,{}", mime, BASE64_STANDARD.encode(encoded)))
}

fn resize_for_profile(image: DynamicImage, profile: UploadProfile) -> DynamicImage {
    let (width, height) = image.dimensions();
    if width == 0 || height == 0 {
        return image;
    }

    let max_edge = profile.max_edge();
    let min_edge = profile.min_edge();
    let current_max = width.max(height);
    let current_min = width.min(height);

    if current_max > max_edge {
        return image.resize(max_edge, max_edge, FilterType::Lanczos3);
    }

    if current_min < min_edge {
        let scale = min_edge as f32 / current_min as f32;
        let target_w = ((width as f32) * scale).ceil() as u32;
        let target_h = ((height as f32) * scale).ceil() as u32;
        return image.resize_exact(target_w, target_h, FilterType::CatmullRom);
    }

    image
}

fn save_image_and_format_output(image_url: &str) -> Result<String, String> {
    let saved_path = download_to_current_dir(image_url)?;
    Ok(serde_json::to_string_pretty(&serde_json::json!({
        "type": "image",
        "local_path": saved_path.display().to_string(),
        "remote_url": image_url,
    }))
    .unwrap())
}

fn download_to_current_dir(url: &str) -> Result<PathBuf, String> {
    let cwd = std::env::current_dir().map_err(|e| format!("Failed to get current dir: {}", e))?;
    let filename = unique_filename(&cwd, filename_from_url(url));
    let path = cwd.join(filename);

    let resp = agent()
        .get(url)
        .call()
        .map_err(|e| format_ureq_error("GET", url, e))?;

    let mut reader = resp.into_reader();
    let mut file = File::create(&path).map_err(|e| format!("Failed to create {}: {}", path.display(), e))?;
    io::copy(&mut reader, &mut file).map_err(|e| format!("Failed to write {}: {}", path.display(), e))?;
    Ok(path)
}

fn filename_from_url(url: &str) -> String {
    let without_query = url.split('?').next().unwrap_or(url);
    let candidate = without_query.rsplit('/').next().unwrap_or("generated-image");
    let sanitized = sanitize_filename(candidate);
    if sanitized.is_empty() {
        fallback_filename()
    } else {
        sanitized
    }
}

fn sanitize_filename(name: &str) -> String {
    name.chars()
        .map(|c| match c {
            'a'..='z' | 'A'..='Z' | '0'..='9' | '.' | '_' | '-' => c,
            _ => '_',
        })
        .collect()
}

fn unique_filename(dir: &Path, base: String) -> String {
    let path = Path::new(&base);
    let stem = path.file_stem().and_then(|s| s.to_str()).unwrap_or("generated-image");
    let ext = path.extension().and_then(|s| s.to_str());

    let mut candidate = base.clone();
    let mut index = 1;
    while dir.join(&candidate).exists() {
        candidate = match ext {
            Some(ext) => format!("{}-{}.{}", stem, index, ext),
            None => format!("{}-{}", stem, index),
        };
        index += 1;
    }
    candidate
}

fn fallback_filename() -> String {
    let timestamp = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_secs())
        .unwrap_or(0);
    format!("generated-image-{}.bin", timestamp)
}

fn format_ureq_error(method: &str, url: &str, err: ureq::Error) -> String {
    match err {
        ureq::Error::Status(status, resp) => {
            let body = resp
                .into_string()
                .unwrap_or_else(|read_err| format!("<failed to read error body: {}>", read_err));

            let details = match serde_json::from_str::<serde_json::Value>(&body) {
                Ok(value) => {
                    if let Some(error) = value.get("error") {
                        serde_json::to_string(error).unwrap_or(body.clone())
                    } else {
                        body.clone()
                    }
                }
                Err(_) => body.clone(),
            };

            format!(
                "Request failed: {} {} returned status {} with body: {}",
                method, url, status, details
            )
        }
        other => format!("Request failed: {} {}: {}", method, url, other),
    }
}

pub fn text_to_image(api_key: &str, prompt: &str, size: &str) -> Result<String, String> {
    eprintln!("Generating image (Text-to-Image)...");
    let size = resolve_generation_size(size)?;
    let req = ImageGenRequest {
        model: image_model(),
        prompt: prompt.to_string(),
        image: None,
        size,
        watermark: false,
    };
    let body = post_json(api_key, "/images/generations", &req)?;
    let resp: ImageGenResponse = serde_json::from_str(&body).map_err(|e| format!("Parse error: {}", e))?;

    if let Some(err) = resp.error {
        return Err(err.to_string());
    }
    let image_url = resp.data
        .and_then(|d| d.into_iter().next())
        .and_then(|d| d.url)
        .ok_or_else(|| format!("No image URL in response: {}", body))?;
    save_image_and_format_output(&image_url)
}

pub fn image_to_image(api_key: &str, prompt: &str, image_input: &str, size: &str) -> Result<String, String> {
    eprintln!("Generating image (Image-to-Image)...");
    let size = resolve_generation_size(size)?;
    let image_input = normalize_image_input(image_input, UploadProfile::ImageToImage)?;
    let req = ImageGenRequest {
        model: image_model(),
        prompt: prompt.to_string(),
        image: Some(image_input),
        size,
        watermark: false,
    };
    let body = post_json(api_key, "/images/generations", &req)?;
    let resp: ImageGenResponse = serde_json::from_str(&body).map_err(|e| format!("Parse error: {}", e))?;

    if let Some(err) = resp.error {
        return Err(err.to_string());
    }
    let image_url = resp.data
        .and_then(|d| d.into_iter().next())
        .and_then(|d| d.url)
        .ok_or_else(|| format!("No image URL in response: {}", body))?;
    save_image_and_format_output(&image_url)
}

pub fn image_to_video(api_key: &str, text: &str, image_input: &str) -> Result<String, String> {
    eprintln!("Generating video task (Image-to-Video)...");
    let image_input = normalize_image_input(image_input, UploadProfile::ImageToVideo)?;
    let req = VideoGenRequest {
        model: video_model(),
        content: vec![
            ContentItem::Text { text: text.to_string() },
            ContentItem::ImageUrl {
                image_url: ImageUrlRef { url: image_input },
                role: Some("first_frame"),
            },
        ],
        generate_audio: true,
        ratio: "adaptive",
        duration: 10,
        watermark: false,
    };
    let body = post_json(api_key, "/contents/generations/tasks", &req)?;
    let resp: VideoTaskResponse = serde_json::from_str(&body).map_err(|e| format!("Parse error: {}", e))?;

    if let Some(err) = resp.error {
        return Err(err.to_string());
    }
    let task_id = resp.id.ok_or("No task ID in response")?;
    eprintln!("Task Submitted. ID: {}", task_id);
    let video_url = wait_for_task(api_key, &task_id)?;
    Ok(serde_json::to_string_pretty(&serde_json::json!({
        "type": "video",
        "task_id": task_id,
        "status": "succeeded",
        "remote_url": video_url,
    }))
    .unwrap())
}

fn wait_for_task(api_key: &str, task_id: &str) -> Result<String, String> {
    const MAX_RETRIES: u32 = 48;
    const POLL_INTERVAL: Duration = Duration::from_secs(5);

    eprintln!("Waiting for task {} to complete...", task_id);

    for i in 0..MAX_RETRIES {
        let url = format!("{}/contents/generations/tasks/{}", BASE_URL, task_id);
        let body = get_json(api_key, &url)?;
        let resp: TaskStatusResponse =
            serde_json::from_str(&body).map_err(|e| format!("Parse error: {}", e))?;

        if let Some(err) = resp.error {
            return Err(format!("API Error during check: {}", err));
        }

        let status = resp.status.as_deref().unwrap_or("unknown");
        match status.to_lowercase().as_str() {
            "succeeded" => {
                eprintln!("\nTask Succeeded!");
                let video_url = resp
                    .content
                    .and_then(|c| c.video_url)
                    .or_else(|| resp.result.and_then(|r| r.video_url));
                return video_url.ok_or_else(|| {
                    format!("Status is succeeded but no video_url found: {}", body)
                });
            }
            "failed" | "cancelled" => {
                return Err(format!("\nTask {}.\n{}", status, body));
            }
            _ => {
                eprint!("\rStatus: {}... ({}/{})", status, i + 1, MAX_RETRIES);
            }
        }
        thread::sleep(POLL_INTERVAL);
    }
    Err("Timeout waiting for task.".to_string())
}

pub fn query_task(api_key: &str, task_id: &str) -> Result<String, String> {
    let url = format!("{}/contents/generations/tasks/{}", BASE_URL, task_id);
    let body = get_json(api_key, &url)?;

    let check: serde_json::Value = serde_json::from_str(&body).map_err(|e| format!("Parse error: {}", e))?;
    if check.get("error").is_some() {
        return Err(format!("API Error: {}", body));
    }

    let v: serde_json::Value = serde_json::from_str(&body).unwrap();
    Ok(serde_json::to_string_pretty(&v).unwrap())
}

pub fn list_tasks(api_key: &str, page: u32, page_size: u32) -> Result<String, String> {
    let url = format!(
        "{}/contents/generations/tasks?page_num={}&page_size={}",
        BASE_URL, page, page_size
    );
    let body = get_json(api_key, &url)?;
    let resp: TaskListResponse = serde_json::from_str(&body).map_err(|e| format!("Parse error: {}", e))?;

    if let Some(err) = resp.error {
        return Err(err.to_string());
    }

    let items = resp.items.unwrap_or_default();
    let items_json: Vec<serde_json::Value> = items
        .iter()
        .map(|item| {
            serde_json::json!({
                "id": item.id,
                "status": item.status,
                "created_at": item.created_at,
                "created_at_iso": item.created_at.map(chrono_from_timestamp),
                "video_url": item
                    .content
                    .as_ref()
                    .and_then(|c| c.video_url.as_deref())
                    .or_else(|| item.result.as_ref().and_then(|r| r.video_url.as_deref())),
            })
        })
        .collect();

    Ok(serde_json::to_string_pretty(&serde_json::json!({
        "type": "task_list",
        "page": page,
        "page_size": page_size,
        "items": items_json,
    }))
    .unwrap())
}

fn chrono_from_timestamp(ts: i64) -> String {
    let secs_per_day: i64 = 86400;
    let secs_per_hour: i64 = 3600;
    let secs_per_min: i64 = 60;

    let days = ts / secs_per_day;
    let remaining = ts % secs_per_day;
    let hour = remaining / secs_per_hour;
    let min = (remaining % secs_per_hour) / secs_per_min;
    let sec = remaining % secs_per_min;

    let (year, month, day) = days_to_ymd(days);
    format!("{:04}-{:02}-{:02}T{:02}:{:02}:{:02}Z", year, month, day, hour, min, sec)
}

fn days_to_ymd(days_since_epoch: i64) -> (i64, i64, i64) {
    let z = days_since_epoch + 719468;
    let era = if z >= 0 { z } else { z - 146096 } / 146097;
    let doe = z - era * 146097;
    let yoe = (doe - doe / 1460 + doe / 36524 - doe / 146096) / 365;
    let y = yoe + era * 400;
    let doy = doe - (365 * yoe + yoe / 4 - yoe / 100);
    let mp = (5 * doy + 2) / 153;
    let d = doy - (153 * mp + 2) / 5 + 1;
    let m = if mp < 10 { mp + 3 } else { mp - 9 };
    let y = if m <= 2 { y + 1 } else { y };
    (y, m, d)
}
