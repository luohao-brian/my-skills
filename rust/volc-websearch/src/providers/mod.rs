use crate::models::*;
use crate::config::{Config, SearchIntent};
use crate::sign;
use serde_json::{Map, Value, json};
use std::time::Duration;
use std::env;
use url::Url;

const VOLC_HOST: &str = "mercury.volcengineapi.com";
const VOLC_ACTION: &str = "WebSearch";
const VOLC_VERSION: &str = "2025-01-01";
const TAVILY_URL: &str = "https://api.tavily.com/search";
const BOCHA_URL: &str = "https://api.bochaai.com/v1/web-search";
const BRAVE_URL: &str = "https://api.search.brave.com/res/v1/web/search";

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

pub fn fetch_selected(config: &Config) -> Result<Vec<RawSearchResult>, String> {
    let engines = resolve_engines(config)?;
    let mut errors = Vec::new();

    for engine in engines {
        let fetched = match engine {
            "tavily" => fetch_tavily_raw(config).map(map_tavily_results),
            "bocha" => fetch_bocha_raw(config).map(map_bocha_results),
            "brave" => fetch_brave_raw(config).map(map_brave_results),
            "volc" => fetch_volc_raw(config).map(map_volc_results),
            _ => Err("Invalid engine specified".to_string()),
        };

        match fetched {
            Ok(mut results) if !results.is_empty() => {
                results.truncate(config.count);
                return Ok(results);
            }
            Ok(_) => errors.push(format!("{} returned no results", engine)),
            Err(err) => errors.push(format!("{}: {}", engine, err)),
        }
    }

    Err(format!("No results found. {}", errors.join(" | ")))
}

pub struct RawSearchResult {
    pub engine: String,
    pub title: String,
    pub url: String,
    pub content: String,
    pub published_date: Option<String>,
}

pub fn format_raw_results(results: &[RawSearchResult]) -> String {
    let mut output = String::new();

    for (i, result) in results.iter().enumerate() {
        output.push_str(&format!(
            "[{}] {}\n    {} | {}\n    {}\n    {}\n\n",
            i + 1,
            result.title,
            result.engine,
            result.url,
            result.published_date.as_deref().unwrap_or(""),
            result.content
        ));
    }

    output
}

pub fn format_summary_results(results: &[RawSearchResult]) -> String {
    let mut output = String::new();
    output.push_str("搜索摘要\n");

    for (index, result) in results.iter().take(5).enumerate() {
        let summary = compact_text(&result.content, 180);
        output.push_str(&format!(
            "{}. {}{}\n",
            index + 1,
            result.title,
            if summary.is_empty() {
                String::new()
            } else {
                format!(": {}", summary)
            }
        ));
    }

    output.push_str("\n来源\n");
    for (index, result) in results.iter().enumerate() {
        output.push_str(&format!(
            "[{}] {} | {}\n",
            index + 1,
            result.title,
            result.url
        ));
    }

    output
}

fn fetch_tavily_raw(config: &Config) -> Result<Vec<TavilyResult>, String> {
    let topic = tavily_topic(config);
    let mut body = Map::new();
    body.insert("query".to_string(), json!(config.query));
    body.insert("topic".to_string(), json!(topic));
    body.insert("max_results".to_string(), json!(config.count));
    body.insert("include_answer".to_string(), json!(false));
    body.insert("include_raw_content".to_string(), json!(false));

    if let Some(freshness) = config.freshness {
        body.insert(
            "time_range".to_string(),
            json!(freshness.as_tavily_time_range()),
        );
    }
    if let Some(date_after) = config.date_after.as_deref() {
        body.insert("start_date".to_string(), json!(date_after));
    }
    if let Some(date_before) = config.date_before.as_deref() {
        body.insert("end_date".to_string(), json!(date_before));
    }
    if let Some(domains) = config.domain_filter.as_ref() {
        body.insert("include_domains".to_string(), json!(domains));
    }
    if let Some(domains) = config.block_hosts.as_ref() {
        body.insert("exclude_domains".to_string(), json!(domains));
    }
    if topic == "general" {
        if let Some(country) = tavily_country_name(config.country.as_deref()) {
            body.insert("country".to_string(), json!(country));
        }
    }

    let resp: TavilyResponse = agent(config)
        .post(TAVILY_URL)
        .set("Content-Type", "application/json")
        .set("Authorization", &format!("Bearer {}", config.tavily_api_key))
        .send_json(Value::Object(body))
        .map_err(|e| format!("Tavily request failed: {}", e))?
        .into_json()
        .map_err(|e| format!("Tavily parse failed: {}", e))?;

    Ok(resp.results.unwrap_or_default())
}

fn fetch_bocha_raw(config: &Config) -> Result<Vec<BochaWebPage>, String> {
    let body = ureq::json!({
        "query": config.query,
        "summary": true,
        "count": config.count
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

    Ok(items)
}

fn fetch_brave_raw(config: &Config) -> Result<Vec<BraveWebResult>, String> {
    let mut url = Url::parse(BRAVE_URL).map_err(|e| format!("Brave URL parse failed: {}", e))?;
    {
        let mut pairs = url.query_pairs_mut();
        pairs.append_pair("q", &config.query);
        pairs.append_pair("count", &config.count.to_string());
        pairs.append_pair("text_decorations", "false");
        pairs.append_pair("spell", "false");

        if let Some(country) = config.country.as_deref() {
            pairs.append_pair("country", &country.to_ascii_lowercase());
        }
        if let Some(language) = config.language.as_deref() {
            pairs.append_pair("search_lang", language);
        }
    }

    let resp: BraveResponse = agent(config)
        .get(url.as_str())
        .set("X-Subscription-Token", &config.brave_api_key)
        .call()
        .map_err(|e| format!("Brave request failed: {}", e))?
        .into_json()
        .map_err(|e| format!("Brave parse failed: {}", e))?;

    let items = resp
        .web
        .map(|web| web.results)
        .unwrap_or_default();

    Ok(items)
}

fn fetch_volc_raw(config: &Config) -> Result<Vec<VolcWebResult>, String> {
    let req = crate::api::build_request(
        &config.query,
        config.count as u32,
        config.domain_filter.as_ref(),
        config.block_hosts.as_ref(),
        config.volc_time_range().as_deref(),
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
        .unwrap_or_default())
}

fn is_news_query(config: &Config) -> bool {
    matches!(config.intent, SearchIntent::News)
        || matches!(config.freshness, Some(crate::config::Freshness::Pd | crate::config::Freshness::Pw | crate::config::Freshness::Pm))
        || config.date_after.is_some()
        || config.date_before.is_some()
}

fn tavily_topic(config: &Config) -> &'static str {
    if matches!(config.intent, SearchIntent::News) || is_news_query(config) {
        "news"
    } else {
        "general"
    }
}

fn resolve_engines(config: &Config) -> Result<Vec<&'static str>, String> {
    Ok(vec![match config.engine.as_str() {
        "tavily" => "tavily",
        "bocha" => "bocha",
        "brave" => "brave",
        "volc" => "volc",
        _ => return Err("Invalid engine specified".to_string()),
    }])
}

fn compact_text(input: &str, limit: usize) -> String {
    let collapsed = input.split_whitespace().collect::<Vec<_>>().join(" ");
    if collapsed.chars().count() <= limit {
        return collapsed;
    }
    let mut shortened = collapsed.chars().take(limit).collect::<String>();
    shortened.push_str("...");
    shortened
}

fn tavily_country_name(country: Option<&str>) -> Option<&'static str> {
    match country? {
        "CN" => Some("china"),
        "US" => Some("united states"),
        "GB" => Some("united kingdom"),
        "UK" => Some("united kingdom"),
        "JP" => Some("japan"),
        "KR" => Some("south korea"),
        "SG" => Some("singapore"),
        "DE" => Some("germany"),
        "FR" => Some("france"),
        "CA" => Some("canada"),
        "AU" => Some("australia"),
        "IN" => Some("india"),
        _ => None,
    }
}

fn map_tavily_results(items: Vec<TavilyResult>) -> Vec<RawSearchResult> {
    items.into_iter().map(|item| {
        RawSearchResult {
            engine: "Tavily".to_string(),
            title: item.title.unwrap_or_default(),
            url: item.url.unwrap_or_default(),
            content: item.content.unwrap_or_default(),
            published_date: item.published_date,
        }
    }).collect()
}

fn map_bocha_results(items: Vec<BochaWebPage>) -> Vec<RawSearchResult> {
    items.into_iter().map(|item| {
        RawSearchResult {
            engine: "Bocha".to_string(),
            title: item.name.unwrap_or_default(),
            url: item.url.unwrap_or_default(),
            content: item.summary.or(item.snippet).unwrap_or_default(),
            published_date: item.date_published,
        }
    }).collect()
}

fn map_brave_results(items: Vec<BraveWebResult>) -> Vec<RawSearchResult> {
    items.into_iter().map(|item| {
        RawSearchResult {
            engine: "Brave".to_string(),
            title: item.title.unwrap_or_default(),
            url: item.url.unwrap_or_default(),
            content: item.description.or(item.snippet).unwrap_or_default(),
            published_date: item.published_at,
        }
    }).collect()
}

fn map_volc_results(items: Vec<VolcWebResult>) -> Vec<RawSearchResult> {
    items.into_iter().map(|item| {
        RawSearchResult {
            engine: "Volc".to_string(),
            title: item.title.unwrap_or_default(),
            url: item.url.unwrap_or_default(),
            content: item.summary.or(item.snippet).unwrap_or_default(),
            published_date: item.publish_time,
        }
    }).collect()
}
