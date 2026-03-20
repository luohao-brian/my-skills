use crate::models::*;
use crate::config::Config;
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
    pub raw_data: String,
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

fn fetch_tavily_raw(config: &Config) -> Result<Vec<TavilyResult>, String> {
    let topic = if is_news_query(&config.time_range) { "news" } else { "general" };
    let body = ureq::json!({
        "query": config.query,
        "topic": topic,
        "max_results": config.count,
        "include_answer": false,
        "include_raw_content": true
    });

    let resp: TavilyResponse = agent(config)
        .post(TAVILY_URL)
        .set("Content-Type", "application/json")
        .set("Authorization", &format!("Bearer {}", config.tavily_api_key))
        .send_json(body)
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
    let resp: BraveResponse = agent(config)
        .get(&format!(
            "{}?q={}&count={}&text_decorations=false&spell=false",
            BRAVE_URL,
            urlencoding::encode(&config.query),
            config.count
        ))
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
        .unwrap_or_default())
}

fn is_news_query(time_range: &Option<String>) -> bool {
    matches!(time_range.as_deref(), Some("OneDay" | "OneWeek" | "OneMonth"))
}

fn resolve_engines(config: &Config) -> Result<Vec<&'static str>, String> {
    if config.engine != "auto" {
        return Ok(vec![match config.engine.as_str() {
            "tavily" => "tavily",
            "bocha" => "bocha",
            "brave" => "brave",
            "volc" => "volc",
            _ => return Err("Invalid engine specified".to_string()),
        }]);
    }

    let mut available = Vec::new();
    if !config.bocha_api_key.is_empty() {
        available.push("bocha");
    }
    if !config.tavily_api_key.is_empty() {
        available.push("tavily");
    }
    if !config.brave_api_key.is_empty() {
        available.push("brave");
    }
    if !config.ve_access_key.is_empty() && !config.ve_secret_key.is_empty() {
        available.push("volc");
    }
    if available.is_empty() {
        return Err(
            "No search provider credentials found. Configure at least one of: TAVILY_API_KEY, BOCHA_API_KEY, BRAVE_API_KEY, VE_ACCESS_KEY + VE_SECRET_KEY"
                .to_string(),
        );
    }

    let mut ordered = Vec::new();
    let query_lower = config.query.to_lowercase();
    let has_chinese = config.query.chars().any(|ch| ('\u{4e00}'..='\u{9fff}').contains(&ch));
    let looks_like_docs = query_lower.contains("api")
        || query_lower.contains("sdk")
        || query_lower.contains("doc")
        || query_lower.contains("docs")
        || query_lower.contains("documentation");
    let looks_like_news = is_news_query(&config.time_range)
        || query_lower.contains("news")
        || query_lower.contains("latest")
        || query_lower.contains("最近")
        || query_lower.contains("最新")
        || query_lower.contains("今日")
        || query_lower.contains("今天");

    if has_chinese {
        push_engine_if_available(&mut ordered, &available, "bocha");
    }
    if looks_like_news {
        push_engine_if_available(&mut ordered, &available, "tavily");
    }
    if looks_like_docs {
        push_engine_if_available(&mut ordered, &available, "brave");
    }
    push_engine_if_available(&mut ordered, &available, "tavily");
    push_engine_if_available(&mut ordered, &available, "bocha");
    push_engine_if_available(&mut ordered, &available, "brave");
    push_engine_if_available(&mut ordered, &available, "volc");

    Ok(ordered)
}

fn push_engine_if_available(ordered: &mut Vec<&'static str>, available: &[&'static str], engine: &'static str) {
    if available.contains(&engine) && !ordered.contains(&engine) {
        ordered.push(engine);
    }
}

fn map_tavily_results(items: Vec<TavilyResult>) -> Vec<RawSearchResult> {
    items.into_iter().map(|item| {
        let item_clone = item.clone();
        RawSearchResult {
            engine: "Tavily".to_string(),
            title: item.title.unwrap_or_default(),
            url: item.url.unwrap_or_default(),
            content: item.content.unwrap_or_default(),
            published_date: item.published_date,
            raw_data: serde_json::to_string(&item_clone).unwrap_or_default(),
        }
    }).collect()
}

fn map_bocha_results(items: Vec<BochaWebPage>) -> Vec<RawSearchResult> {
    items.into_iter().map(|item| {
        let item_clone = item.clone();
        RawSearchResult {
            engine: "Bocha".to_string(),
            title: item.name.unwrap_or_default(),
            url: item.url.unwrap_or_default(),
            content: item.summary.or(item.snippet).unwrap_or_default(),
            published_date: item.date_published,
            raw_data: serde_json::to_string(&item_clone).unwrap_or_default(),
        }
    }).collect()
}

fn map_brave_results(items: Vec<BraveWebResult>) -> Vec<RawSearchResult> {
    items.into_iter().map(|item| {
        let item_clone = item.clone();
        RawSearchResult {
            engine: "Brave".to_string(),
            title: item.title.unwrap_or_default(),
            url: item.url.unwrap_or_default(),
            content: item.description.or(item.snippet).unwrap_or_default(),
            published_date: item.published_at,
            raw_data: serde_json::to_string(&item_clone).unwrap_or_default(),
        }
    }).collect()
}

fn map_volc_results(items: Vec<VolcWebResult>) -> Vec<RawSearchResult> {
    items.into_iter().map(|item| {
        let item_clone = item.clone();
        RawSearchResult {
            engine: "Volc".to_string(),
            title: item.title.unwrap_or_default(),
            url: item.url.unwrap_or_default(),
            content: item.summary.or(item.snippet).unwrap_or_default(),
            published_date: item.publish_time,
            raw_data: serde_json::to_string(&item_clone).unwrap_or_default(),
        }
    }).collect()
}
