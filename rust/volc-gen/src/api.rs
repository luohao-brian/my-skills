use crate::models::*;
use std::thread;
use std::time::Duration;

const BASE_URL: &str = "https://ark.cn-beijing.volces.com/api/v3";
const DEFAULT_IMAGE_MODEL: &str = "doubao-seedream-5-0-260128";
const DEFAULT_VIDEO_MODEL: &str = "doubao-seedance-1-5-pro-251215";

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
        .map_err(|e| format!("Request failed: {}", e))?;
    resp.into_string().map_err(|e| format!("Read body failed: {}", e))
}

fn get_json(api_key: &str, url: &str) -> Result<String, String> {
    let resp = agent()
        .get(url)
        .set("Authorization", &format!("Bearer {}", api_key))
        .call()
        .map_err(|e| format!("Request failed: {}", e))?;
    resp.into_string().map_err(|e| format!("Read body failed: {}", e))
}

pub fn text_to_image(api_key: &str, prompt: &str, size: &str) -> Result<String, String> {
    eprintln!("Generating image (Text-to-Image)...");
    let req = ImageGenRequest {
        model: image_model(),
        prompt: prompt.to_string(),
        image: None,
        size: size.to_string(),
        watermark: false,
    };
    let body = post_json(api_key, "/images/generations", &req)?;
    let resp: ImageGenResponse = serde_json::from_str(&body).map_err(|e| format!("Parse error: {}", e))?;

    if let Some(err) = resp.error {
        return Err(err.to_string());
    }
    resp.data
        .and_then(|d| d.into_iter().next())
        .and_then(|d| d.url)
        .ok_or_else(|| format!("No image URL in response: {}", body))
}

pub fn image_to_image(api_key: &str, prompt: &str, image_url: &str, size: &str) -> Result<String, String> {
    eprintln!("Generating image (Image-to-Image)...");
    let req = ImageGenRequest {
        model: image_model(),
        prompt: prompt.to_string(),
        image: Some(image_url.to_string()),
        size: size.to_string(),
        watermark: false,
    };
    let body = post_json(api_key, "/images/generations", &req)?;
    let resp: ImageGenResponse = serde_json::from_str(&body).map_err(|e| format!("Parse error: {}", e))?;

    if let Some(err) = resp.error {
        return Err(err.to_string());
    }
    resp.data
        .and_then(|d| d.into_iter().next())
        .and_then(|d| d.url)
        .ok_or_else(|| format!("No image URL in response: {}", body))
}

pub fn image_to_video(api_key: &str, text: &str, image_url: &str) -> Result<String, String> {
    eprintln!("Generating video task (Image-to-Video)...");
    let req = VideoGenRequest {
        model: video_model(),
        content: vec![
            ContentItem::Text { text: text.to_string() },
            ContentItem::ImageUrl {
                image_url: ImageUrlRef { url: image_url.to_string() },
            },
        ],
        generate_audio: true,
        ratio: "adaptive",
        duration: 12,
        watermark: false,
    };
    let body = post_json(api_key, "/contents/generations/tasks", &req)?;
    let resp: VideoTaskResponse = serde_json::from_str(&body).map_err(|e| format!("Parse error: {}", e))?;

    if let Some(err) = resp.error {
        return Err(err.to_string());
    }
    let task_id = resp.id.ok_or("No task ID in response")?;
    eprintln!("Task Submitted. ID: {}", task_id);
    wait_for_task(api_key, &task_id)
}

fn wait_for_task(api_key: &str, task_id: &str) -> Result<String, String> {
    const MAX_RETRIES: u32 = 48; // 4 minutes (48 * 5s)
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

    // Check for errors
    let check: serde_json::Value = serde_json::from_str(&body).map_err(|e| format!("Parse error: {}", e))?;
    if check.get("error").is_some() {
        return Err(format!("API Error: {}", body));
    }

    // Pretty print
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
    let mut out = format!("Recent Tasks (Page {}, Size {}):\n", page, page_size);
    out.push_str(&format!(
        "{:<28} {:<12} {:<22} {}\n",
        "ID", "STATUS", "CREATED_AT", "VIDEO_URL"
    ));

    for item in &items {
        let id = item.id.as_deref().unwrap_or("-");
        let status = item.status.as_deref().unwrap_or("-");
        let created = item
            .created_at
            .map(|ts| {
                let secs = ts;
                let dt = chrono_from_timestamp(secs);
                dt
            })
            .unwrap_or_else(|| "-".to_string());
        let video = item
            .content
            .as_ref()
            .and_then(|c| c.video_url.as_deref())
            .or_else(|| item.result.as_ref().and_then(|r| r.video_url.as_deref()))
            .unwrap_or("N/A");

        out.push_str(&format!("{:<28} {:<12} {:<22} {}\n", id, status, created, video));
    }

    Ok(out)
}

fn chrono_from_timestamp(ts: i64) -> String {
    // Simple UTC timestamp formatting without chrono dependency
    // Unix timestamp to readable date
    let secs_per_day: i64 = 86400;
    let secs_per_hour: i64 = 3600;
    let secs_per_min: i64 = 60;

    let days = ts / secs_per_day;
    let remaining = ts % secs_per_day;
    let hour = remaining / secs_per_hour;
    let min = (remaining % secs_per_hour) / secs_per_min;
    let sec = remaining % secs_per_min;

    // Days since epoch to Y-M-D (simplified)
    let (year, month, day) = days_to_ymd(days);
    format!("{:04}-{:02}-{:02}T{:02}:{:02}:{:02}Z", year, month, day, hour, min, sec)
}

fn days_to_ymd(days_since_epoch: i64) -> (i64, i64, i64) {
    // Algorithm from https://howardhinnant.github.io/date_algorithms.html
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
