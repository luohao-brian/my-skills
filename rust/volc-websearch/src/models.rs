use serde::{Deserialize, Serialize};

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

#[derive(Deserialize, Debug, Serialize)]
pub struct SearchResponse {
    #[serde(rename = "Result")]
    pub result: Option<SearchResult>,
    #[serde(rename = "ResponseMetadata")]
    pub response_metadata: Option<ResponseMetadata>,
}

#[derive(Deserialize, Debug, Serialize)]
pub struct SearchResult {
    #[serde(rename = "WebResults")]
    pub web_results: Option<Vec<VolcWebResult>>,
}

#[derive(Deserialize, Debug, Serialize, Clone)]
pub struct VolcWebResult {
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
    #[serde(rename = "PublishTime")]
    pub publish_time: Option<String>,
    #[serde(rename = "RankScore")]
    pub rank_score: Option<f32>,
}

#[derive(Deserialize, Debug, Serialize)]
pub struct ResponseMetadata {
    #[serde(rename = "Error")]
    pub error: Option<ApiError>,
}

#[derive(Deserialize, Debug, Serialize)]
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

#[derive(Deserialize, Debug, Serialize)]
pub struct TavilyResponse {
    pub results: Option<Vec<TavilyResult>>,
}

#[derive(Deserialize, Debug, Serialize, Clone)]
pub struct TavilyResult {
    pub url: Option<String>,
    pub title: Option<String>,
    pub score: Option<f32>,
    pub published_date: Option<String>,
    pub content: Option<String>,
}

#[derive(Deserialize, Debug, Serialize)]
pub struct BochaResponse {
    pub data: Option<BochaData>,
}

#[derive(Deserialize, Debug, Serialize)]
pub struct BochaData {
    #[serde(rename = "webPages")]
    pub web_pages: Option<BochaWebPages>,
}

#[derive(Deserialize, Debug, Serialize)]
pub struct BochaWebPages {
    pub value: Vec<BochaWebPage>,
}

#[derive(Deserialize, Debug, Serialize, Clone)]
pub struct BochaWebPage {
    pub name: Option<String>,
    pub url: Option<String>,
    pub snippet: Option<String>,
    pub summary: Option<String>,
    #[serde(rename = "siteName")]
    pub site_name: Option<String>,
    #[serde(rename = "datePublished")]
    pub date_published: Option<String>,
}

#[derive(Deserialize, Debug, Serialize)]
pub struct BraveResponse {
    pub web: Option<BraveWebResults>,
}

#[derive(Deserialize, Debug, Serialize)]
pub struct BraveWebResults {
    pub results: Vec<BraveWebResult>,
}

#[derive(Deserialize, Debug, Serialize, Clone)]
pub struct BraveWebResult {
    pub title: Option<String>,
    pub url: Option<String>,
    pub description: Option<String>,
    pub published_at: Option<String>,
    pub snippet: Option<String>,
}

// All models are now used directly, no need for unified wrapper
