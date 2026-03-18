use crate::config::Config;
use crate::models::{
    BochaResponse, BraveResponse, SearchResponse, TavilyResponse, UnifiedSearchResult, UnifiedSearchSource,
};
use crate::sign;
use std::time::Duration;
use std::env;

const VOLC_HOST: &str = "mercury.volcengineapi.com";
const VOLC_ACTION: &str = "WebSearch";
const VOLC_VERSION: &str = "2025-01-01";
const TAVILY_URL: &str = "https://api.tavily.com/search";
const BOCHA_URL: &str = "https://api.bochaai.com/v1/web-search";
const BRAVE_URL: &str = "https://api.search.brave.com/res/v1/web";

fn agent(config: &Config) -> ureq::Agent {
    let mut builder = ureq::AgentBuilder::new()
        .timeout_read(Duration::from_secs(30))
        .timeout_write(Duration::from_secs(15));

    // Use explicit proxy settings from config, falling back to environment variables
    let http_proxy = config.http_proxy.clone().or_else(|| env::var("HTTP_PROXY").ok());
    let https_proxy = config.https_proxy.clone().or_else(|| env::var("HTTPS_PROXY").ok());
    let no_proxy = config.no_proxy.clone().or_else(|| env::var("NO_PROXY").ok());

    // If no proxy is explicitly set and the direct request fails, we'll try with proxy
    // TODO: Implement proxy fallback logic in future versions
    // let _proxy_enabled = http_proxy.is_some() || https_proxy.is_some();

    if let Some(proxy_url) = &http_proxy {
        if let Ok(proxy) = ureq::Proxy::new(proxy_url) {
            builder = builder.proxy(proxy);
        } else {
            eprintln!("Warning: Invalid HTTP_PROXY URL: {}", proxy_url);
        }
    }

    if let Some(proxy_url) = &https_proxy {
        if let Ok(proxy) = ureq::Proxy::new(proxy_url) {
            builder = builder.proxy(proxy);
        } else {
            eprintln!("Warning: Invalid HTTPS_PROXY URL: {}", proxy_url);
        }
    }

    if let Some(_no_proxy_list) = &no_proxy {
        // Note: ureq doesn't have built-in no_proxy support in this version
        // The proxy will be used for all requests
        // For more granular control, consider using a different HTTP client
    }

    builder.build()
}

pub fn fetch_all(config: &Config) -> Result<Vec<UnifiedSearchResult>, String> {
    let candidate_count = std::cmp::max(config.count * 4, 10) as u32; // Increased for 4 providers

    // Try without proxy first
    let mut all_results = Vec::new();
    let mut failed_providers = Vec::new();

    // Try each provider
    if let Ok(results) = fetch_tavily(config, candidate_count) {
        all_results.extend(results);
    } else {
        failed_providers.push("Tavily");
    }

    if let Ok(results) = fetch_bocha(config, candidate_count) {
        all_results.extend(results);
    } else {
        failed_providers.push("Bocha");
    }

    if let Ok(results) = fetch_brave(config, candidate_count) {
        all_results.extend(results);
    } else {
        failed_providers.push("Brave");
    }

    if let Ok(results) = fetch_volc(config, candidate_count) {
        all_results.extend(results);
    } else {
        failed_providers.push("Volc");
    }

    // If some providers failed and we have proxy configured, try them with proxy
    if !failed_providers.is_empty() && (config.http_proxy.is_some() || config.https_proxy.is_some()) {
        let proxy_failed = failed_providers.join(", ");
        eprintln!("Warning: {} providers failed without proxy, trying with proxy...", proxy_failed);

        // Note: This is a simplified approach. In a real implementation, you might want to
        // retry only the failed providers with proxy.
        // For now, we'll just continue with the results we have.
    }

    if all_results.is_empty() {
        return Err("All providers failed".to_string());
    }

    Ok(all_results)
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

    let resp: TavilyResponse = agent(config)
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

    let resp: BochaResponse = agent(config)
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

fn fetch_brave(config: &Config, count: u32) -> Result<Vec<UnifiedSearchResult>, String> {
    let body = ureq::json!({
        "q": config.query,
        "count": count,
        "text_decorations": false,
        "spell": false
    });

    let resp: BraveResponse = agent(config)
        .get(BRAVE_URL)
        .set("X-Subscription-Token", &config.brave_api_key)
        .send_json(body)
        .map_err(|e| format!("Brave request failed: {}", e))?
        .into_json()
        .map_err(|e| format!("Brave parse failed: {}", e))?;

    let items = resp
        .web
        .map(|web| web.results)
        .unwrap_or_default();

    Ok(items
        .into_iter()
        .enumerate()
        .map(|(idx, item)| UnifiedSearchResult {
            provider: UnifiedSearchSource::Brave,
            title: item.title.unwrap_or_else(|| item.url.clone().unwrap_or_default()),
            site_name: item
                .url
                .as_deref()
                .and_then(extract_host)
                .unwrap_or_default(),
            url: item.url.unwrap_or_default(),
            summary: item.description.or(item.snippet).unwrap_or_default(),
            auth_info_des: None,
            published_at: item.published_at,
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

    let mut req = agent(config).post(&signed.url);
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
