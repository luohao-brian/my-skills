use crate::config::Config;
use crate::models::{
    BochaResponse, SearchResponse, TavilyResponse, UnifiedSearchResult, UnifiedSearchSource,
};
use crate::sign;
use std::time::Duration;

const VOLC_HOST: &str = "mercury.volcengineapi.com";
const VOLC_ACTION: &str = "WebSearch";
const VOLC_VERSION: &str = "2025-01-01";
const TAVILY_URL: &str = "https://api.tavily.com/search";
const BOCHA_URL: &str = "https://api.bochaai.com/v1/web-search";

fn agent() -> ureq::Agent {
    ureq::AgentBuilder::new()
        .timeout_read(Duration::from_secs(30))
        .timeout_write(Duration::from_secs(15))
        .build()
}

pub fn fetch_all(config: &Config) -> Result<Vec<UnifiedSearchResult>, String> {
    let candidate_count = std::cmp::max(config.count * 3, 10) as u32;
    let mut handles = Vec::new();

    {
        let config = config.clone();
        handles.push(std::thread::spawn(move || fetch_tavily(&config, candidate_count)));
    }
    {
        let config = config.clone();
        handles.push(std::thread::spawn(move || fetch_bocha(&config, candidate_count)));
    }
    {
        let config = config.clone();
        handles.push(std::thread::spawn(move || fetch_volc(&config, candidate_count)));
    }

    let mut results = Vec::new();
    let mut errors = Vec::new();
    for handle in handles {
        match handle.join() {
            Ok(Ok(items)) => results.extend(items),
            Ok(Err(err)) => errors.push(err),
            Err(_) => errors.push("Provider thread panicked".to_string()),
        }
    }

    if results.is_empty() {
        return Err(format!("All providers failed: {}", errors.join(" | ")));
    }
    Ok(results)
}

fn fetch_tavily(config: &Config, count: u32) -> Result<Vec<UnifiedSearchResult>, String> {
    let topic = if is_news_query(&config.time_range) { "news" } else { "general" };
    let body = ureq::json!({
        "query": config.query,
        "topic": topic,
        "max_results": count,
        "include_answer": false,
        "include_raw_content": false
    });

    let resp: TavilyResponse = agent()
        .post(TAVILY_URL)
        .set("Content-Type", "application/json")
        .set("Authorization", &format!("Bearer {}", config.tavily_api_key))
        .send_json(body)
        .map_err(|e| format!("Tavily request failed: {}", e))?
        .into_json()
        .map_err(|e| format!("Tavily parse failed: {}", e))?;

    Ok(resp
        .results
        .unwrap_or_default()
        .into_iter()
        .enumerate()
        .map(|(idx, item)| UnifiedSearchResult {
            provider: UnifiedSearchSource::Tavily,
            title: item.title.unwrap_or_else(|| item.url.clone().unwrap_or_default()),
            site_name: item
                .url
                .as_deref()
                .and_then(extract_host)
                .unwrap_or_default(),
            url: item.url.unwrap_or_default(),
            summary: item.content.unwrap_or_default(),
            auth_info_des: None,
            published_at: item.published_date,
            provider_score: item.score.unwrap_or(0.0),
            raw_rank: idx + 1,
            fused_score: 0.0,
        })
        .collect())
}

fn fetch_bocha(config: &Config, count: u32) -> Result<Vec<UnifiedSearchResult>, String> {
    let body = ureq::json!({
        "query": config.query,
        "summary": true,
        "count": count
    });

    let resp: BochaResponse = agent()
        .post(BOCHA_URL)
        .set("Content-Type", "application/json")
        .set("Authorization", &format!("Bearer {}", config.bocha_api_key))
        .send_json(body)
        .map_err(|e| format!("Bocha request failed: {}", e))?
        .into_json()
        .map_err(|e| format!("Bocha parse failed: {}", e))?;

    let items = resp
        .data
        .and_then(|data| data.web_pages)
        .map(|pages| pages.value)
        .unwrap_or_default();

    Ok(items
        .into_iter()
        .enumerate()
        .map(|(idx, item)| UnifiedSearchResult {
            provider: UnifiedSearchSource::Bocha,
            title: item.name.unwrap_or_else(|| item.url.clone().unwrap_or_default()),
            site_name: item.site_name.unwrap_or_else(|| {
                item.url
                    .as_deref()
                    .and_then(extract_host)
                    .unwrap_or_default()
            }),
            url: item.url.unwrap_or_default(),
            summary: item.summary.or(item.snippet).unwrap_or_default(),
            auth_info_des: None,
            published_at: item.date_published,
            provider_score: 1.0 / ((idx + 1) as f32),
            raw_rank: idx + 1,
            fused_score: 0.0,
        })
        .collect())
}

fn fetch_volc(config: &Config, count: u32) -> Result<Vec<UnifiedSearchResult>, String> {
    let req = crate::api::build_request(
        &config.query,
        count,
        config.sites.as_ref(),
        config.block_hosts.as_ref(),
        config.time_range.as_deref(),
        config.auth_level,
    );
    let body = serde_json::to_string(&req).map_err(|e| format!("Volc request serialize failed: {}", e))?;
    let signed = sign::sign_request(
        &config.ve_access_key,
        &config.ve_secret_key,
        &body,
        VOLC_ACTION,
        VOLC_VERSION,
        VOLC_HOST,
    );

    let mut req = agent().post(&signed.url);
    for (key, value) in &signed.headers {
        req = req.set(key, value);
    }

    let resp: SearchResponse = req
        .send_string(&body)
        .map_err(|e| format!("Volc request failed: {}", e))?
        .into_json()
        .map_err(|e| format!("Volc parse failed: {}", e))?;

    if let Some(meta) = &resp.response_metadata {
        if let Some(err) = &meta.error {
            return Err(err.to_string());
        }
    }

    Ok(resp
        .result
        .and_then(|result| result.web_results)
        .unwrap_or_default()
        .into_iter()
        .enumerate()
        .map(|(idx, item)| UnifiedSearchResult {
            provider: UnifiedSearchSource::Volc,
            title: item.title.unwrap_or_else(|| item.url.clone().unwrap_or_default()),
            site_name: item.site_name.unwrap_or_else(|| {
                item.url
                    .as_deref()
                    .and_then(extract_host)
                    .unwrap_or_default()
            }),
            url: item.url.unwrap_or_default(),
            summary: item.summary.or(item.snippet).unwrap_or_default(),
            auth_info_des: item.auth_info_des,
            published_at: item.publish_time,
            provider_score: item.rank_score.unwrap_or(1.0 / ((idx + 1) as f32)),
            raw_rank: idx + 1,
            fused_score: 0.0,
        })
        .collect())
}

fn extract_host(value: &str) -> Option<String> {
    url::Url::parse(value)
        .ok()
        .and_then(|url| url.host_str().map(|host| host.to_ascii_lowercase()))
}

fn is_news_query(time_range: &Option<String>) -> bool {
    matches!(time_range.as_deref(), Some("OneDay" | "OneWeek" | "OneMonth"))
}
