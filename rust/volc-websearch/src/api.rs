use crate::models::*;
use crate::sign;
use std::time::Duration;

const HOST: &str = "mercury.volcengineapi.com";
const ACTION: &str = "WebSearch";
const VERSION: &str = "2025-01-01";
const INTERNAL_API_URL: &str = "https://open.feedcoopapi.com/search_api/web_search";

fn agent() -> ureq::Agent {
    ureq::AgentBuilder::new()
        .timeout_read(Duration::from_secs(30))
        .timeout_write(Duration::from_secs(15))
        .build()
}

pub fn build_request(
    query: &str,
    search_type: &str,
    count: u32,
    sites: Option<&str>,
    block_hosts: Option<&str>,
    time_range: Option<&str>,
    auth_level: u32,
) -> SearchRequest {
    let filter = if search_type == "web" {
        let has_filter = sites.is_some() || block_hosts.is_some() || auth_level > 0;
        if has_filter {
            Some(SearchFilter {
                sites: sites.map(|s| s.to_string()),
                block_hosts: block_hosts.map(|s| s.to_string()),
                auth_info_level: if auth_level > 0 { Some(auth_level) } else { None },
            })
        } else {
            None
        }
    } else {
        None
    };

    SearchRequest {
        query: query.to_string(),
        search_type: search_type.to_string(),
        count,
        need_summary: if search_type == "web" { Some(true) } else { None },
        filter,
        time_range: time_range.map(|s| s.to_string()),
    }
}

pub fn search_with_api_key(body: &str, api_key: &str) -> Result<SearchResponse, String> {
    let resp = agent()
        .post(INTERNAL_API_URL)
        .set("Content-Type", "application/json")
        .set("Authorization", &format!("Bearer {}", api_key))
        .send_string(body)
        .map_err(|e| format!("Request failed: {}", e))?;

    let text = resp.into_string().map_err(|e| format!("Read body failed: {}", e))?;
    serde_json::from_str(&text).map_err(|e| format!("Parse error: {} body: {}", e, text))
}

pub fn search_with_aksk(body: &str, ak: &str, sk: &str) -> Result<SearchResponse, String> {
    let signed = sign::sign_request(ak, sk, body, ACTION, VERSION, HOST);

    let mut req = agent().post(&signed.url);
    for (k, v) in &signed.headers {
        req = req.set(k, v);
    }
    let resp = req
        .send_string(body)
        .map_err(|e| format!("Request failed: {}", e))?;

    let text = resp.into_string().map_err(|e| format!("Read body failed: {}", e))?;
    serde_json::from_str(&text).map_err(|e| format!("Parse error: {} body: {}", e, text))
}

pub fn format_output(resp: &SearchResponse, search_type: &str) -> String {
    let result = match &resp.result {
        Some(r) => r,
        None => return "No results.".to_string(),
    };

    let mut lines = vec![format!(
        "结果数: {}  耗时: {}ms\n",
        result.result_count.unwrap_or(0),
        result.time_cost.unwrap_or(0)
    )];

    if search_type == "web" {
        if let Some(items) = &result.web_results {
            for item in items {
                let sort_id = item.sort_id.map(|i| i.to_string()).unwrap_or_default();
                let title = item.title.as_deref().unwrap_or("");
                lines.push(format!("[{}] {}", sort_id, title));

                let mut meta = Vec::new();
                if let Some(s) = &item.site_name {
                    if !s.is_empty() {
                        meta.push(s.as_str());
                    }
                }
                if let Some(s) = &item.auth_info_des {
                    if !s.is_empty() {
                        meta.push(s.as_str());
                    }
                }
                if !meta.is_empty() {
                    lines.push(format!("    {}", meta.join(" | ")));
                }

                if let Some(url) = &item.url {
                    lines.push(format!("    {}", url));
                }

                let summary = item
                    .summary
                    .as_deref()
                    .or(item.snippet.as_deref())
                    .unwrap_or("");
                if !summary.is_empty() {
                    let truncated: String = summary.chars().take(300).collect();
                    lines.push(format!("    {}", truncated));
                }
                lines.push(String::new());
            }
        }
    } else if search_type == "image" {
        if let Some(items) = &result.image_results {
            for item in items {
                let sort_id = item.sort_id.map(|i| i.to_string()).unwrap_or_default();
                let title = item.title.as_deref().unwrap_or("");
                lines.push(format!("[{}] {}", sort_id, title));

                if let Some(img) = &item.image {
                    if let Some(url) = &img.url {
                        lines.push(format!("    {}", url));
                    }
                    lines.push(format!(
                        "    {}x{} ({})",
                        img.width.map(|w| w.to_string()).unwrap_or("?".into()),
                        img.height.map(|h| h.to_string()).unwrap_or("?".into()),
                        img.shape.as_deref().unwrap_or("")
                    ));
                }
                lines.push(String::new());
            }
        }
    }

    lines.join("\n")
}
