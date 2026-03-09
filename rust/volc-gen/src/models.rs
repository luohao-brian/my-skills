use serde::{Deserialize, Serialize};

// ---- Request models ----

#[derive(Serialize)]
pub struct ImageGenRequest {
    pub model: String,
    pub prompt: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub image: Option<String>,
    pub size: String,
    pub watermark: bool,
}

#[derive(Serialize)]
pub struct VideoGenRequest {
    pub model: String,
    pub content: Vec<ContentItem>,
    pub generate_audio: bool,
    pub ratio: &'static str,
    pub duration: u32,
    pub watermark: bool,
}

#[derive(Serialize)]
#[serde(tag = "type")]
pub enum ContentItem {
    #[serde(rename = "text")]
    Text { text: String },
    #[serde(rename = "image_url")]
    ImageUrl { image_url: ImageUrlRef },
}

#[derive(Serialize)]
pub struct ImageUrlRef {
    pub url: String,
}

// ---- Response models ----

#[derive(Deserialize, Debug)]
pub struct ImageGenResponse {
    pub data: Option<Vec<ImageData>>,
    pub error: Option<ApiError>,
}

#[derive(Deserialize, Debug)]
pub struct ImageData {
    pub url: Option<String>,
}

#[derive(Deserialize, Debug)]
pub struct VideoTaskResponse {
    pub id: Option<String>,
    pub error: Option<ApiError>,
}

#[derive(Deserialize, Debug)]
pub struct TaskStatusResponse {
    pub status: Option<String>,
    pub content: Option<TaskContent>,
    pub result: Option<TaskContent>,
    pub error: Option<ApiError>,
}

#[derive(Deserialize, Debug)]
pub struct TaskContent {
    pub video_url: Option<String>,
}

#[derive(Deserialize, Debug)]
pub struct TaskListResponse {
    pub items: Option<Vec<TaskItem>>,
    pub error: Option<ApiError>,
}

#[derive(Deserialize, Debug)]
pub struct TaskItem {
    pub id: Option<String>,
    pub status: Option<String>,
    pub created_at: Option<i64>,
    pub content: Option<TaskContent>,
    pub result: Option<TaskContent>,
}

#[derive(Deserialize, Debug)]
pub struct ApiError {
    pub code: Option<String>,
    pub message: Option<String>,
}

impl std::fmt::Display for ApiError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(
            f,
            "API Error [{}]: {}",
            self.code.as_deref().unwrap_or("unknown"),
            self.message.as_deref().unwrap_or("unknown error")
        )
    }
}
