use serde::{Deserialize, Serialize};

// ---- Request ----

#[derive(Serialize)]
pub struct SearchRequest {
    #[serde(rename = "Query")]
    pub query: String,
    #[serde(rename = "SearchType")]
    pub search_type: String,
    #[serde(rename = "Count")]
    pub count: u32,
    #[serde(rename = "NeedSummary", skip_serializing_if = "Option::is_none")]
    pub need_summary: Option<bool>,
    #[serde(rename = "Filter", skip_serializing_if = "Option::is_none")]
    pub filter: Option<SearchFilter>,
    #[serde(rename = "TimeRange", skip_serializing_if = "Option::is_none")]
    pub time_range: Option<String>,
}

#[derive(Serialize)]
pub struct SearchFilter {
    #[serde(rename = "Sites", skip_serializing_if = "Option::is_none")]
    pub sites: Option<String>,
    #[serde(rename = "BlockHosts", skip_serializing_if = "Option::is_none")]
    pub block_hosts: Option<String>,
    #[serde(rename = "AuthInfoLevel", skip_serializing_if = "Option::is_none")]
    pub auth_info_level: Option<u32>,
}

// ---- Response ----

#[derive(Deserialize, Debug)]
pub struct SearchResponse {
    #[serde(rename = "Result")]
    pub result: Option<SearchResult>,
    #[serde(rename = "ResponseMetadata")]
    pub response_metadata: Option<ResponseMetadata>,
}

#[derive(Deserialize, Debug)]
pub struct SearchResult {
    #[serde(rename = "ResultCount")]
    pub result_count: Option<u32>,
    #[serde(rename = "TimeCost")]
    pub time_cost: Option<u64>,
    #[serde(rename = "WebResults")]
    pub web_results: Option<Vec<WebResult>>,
    #[serde(rename = "ImageResults")]
    pub image_results: Option<Vec<ImageResult>>,
}

#[derive(Deserialize, Debug)]
pub struct WebResult {
    #[serde(rename = "SortId")]
    pub sort_id: Option<u32>,
    #[serde(rename = "Title")]
    pub title: Option<String>,
    #[serde(rename = "SiteName")]
    pub site_name: Option<String>,
    #[serde(rename = "Url")]
    pub url: Option<String>,
    #[serde(rename = "Snippet")]
    pub snippet: Option<String>,
    #[serde(rename = "Summary")]
    pub summary: Option<String>,
    #[serde(rename = "AuthInfoDes")]
    pub auth_info_des: Option<String>,
}

#[derive(Deserialize, Debug)]
pub struct ImageResult {
    #[serde(rename = "SortId")]
    pub sort_id: Option<u32>,
    #[serde(rename = "Title")]
    pub title: Option<String>,
    #[serde(rename = "Image")]
    pub image: Option<ImageInfo>,
}

#[derive(Deserialize, Debug)]
pub struct ImageInfo {
    #[serde(rename = "Url")]
    pub url: Option<String>,
    #[serde(rename = "Width")]
    pub width: Option<u32>,
    #[serde(rename = "Height")]
    pub height: Option<u32>,
    #[serde(rename = "Shape")]
    pub shape: Option<String>,
}

#[derive(Deserialize, Debug)]
pub struct ResponseMetadata {
    #[serde(rename = "Error")]
    pub error: Option<ApiError>,
}

#[derive(Deserialize, Debug)]
pub struct ApiError {
    #[serde(rename = "Code")]
    pub code: Option<String>,
    #[serde(rename = "Message")]
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
