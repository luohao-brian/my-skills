use crate::config::{Config, JinaMode};
use crate::models::{Extractor, RawFetchResult};
use reqwest::blocking::{Client, Response};
use reqwest::header::{ACCEPT, ACCEPT_LANGUAGE, AUTHORIZATION, HeaderMap, HeaderValue, USER_AGENT};
use std::collections::HashMap;
use std::io::Read;

const JINA_READER_BASE_URL: &str = "https://r.jina.ai/";

pub struct FetchOutcome {
    pub raw: RawFetchResult,
    pub fallback_chain: Vec<String>,
    pub extractor_hint: Option<Extractor>,
}

pub fn fetch_with_fallback(client: &Client, config: &Config) -> Result<FetchOutcome, String> {
    match config.jina_mode {
        JinaMode::Always => {
            let raw = fetch_via_jina(client, config)?;
            Ok(FetchOutcome {
                raw,
                fallback_chain: vec!["jina_reader".to_string()],
                extractor_hint: Some(Extractor::JinaReader),
            })
        }
        JinaMode::Off => {
            let raw = fetch_direct(client, config)?;
            Ok(FetchOutcome {
                raw,
                fallback_chain: vec!["direct_fetch".to_string()],
                extractor_hint: None,
            })
        }
        JinaMode::Auto => match fetch_direct(client, config) {
            Ok(raw) if should_use_jina_fallback_for_status(raw.status) => {
                let jina_raw = fetch_via_jina(client, config)?;
                Ok(FetchOutcome {
                    raw: jina_raw,
                    fallback_chain: vec!["direct_fetch".to_string(), "jina_reader".to_string()],
                    extractor_hint: Some(Extractor::JinaReader),
                })
            }
            Ok(raw) => Ok(FetchOutcome {
                raw,
                fallback_chain: vec!["direct_fetch".to_string()],
                extractor_hint: None,
            }),
            Err(err) => {
                let jina_raw = fetch_via_jina(client, config)
                    .map_err(|_| err.clone())?;
                Ok(FetchOutcome {
                    raw: jina_raw,
                    fallback_chain: vec!["direct_fetch".to_string(), "jina_reader".to_string()],
                    extractor_hint: Some(Extractor::JinaReader),
                })
            }
        },
    }
}

pub fn fetch_via_jina(client: &Client, config: &Config) -> Result<RawFetchResult, String> {
    let target = format!("{}{}", JINA_READER_BASE_URL, config.url);
    let mut headers = HeaderMap::new();
    headers.insert(
        ACCEPT,
        HeaderValue::from_static("text/markdown, text/plain;q=0.9, */*;q=0.1"),
    );
    headers.insert(USER_AGENT, HeaderValue::from_str(&config.user_agent).map_err(|err| err.to_string())?);
    if let Some(api_key) = config.jina_api_key.as_deref() {
        let value = format!("Bearer {}", api_key);
        headers.insert(
            AUTHORIZATION,
            HeaderValue::from_str(&value).map_err(|err| err.to_string())?,
        );
    }
    send_request(client, &target, headers, config.max_response_bytes).map(|mut raw| {
        raw.headers
            .entry("content-type".to_string())
            .or_insert_with(|| "text/markdown; charset=utf-8".to_string());
        raw.final_url = config.url.clone();
        raw
    })
}

fn fetch_direct(client: &Client, config: &Config) -> Result<RawFetchResult, String> {
    let mut headers = HeaderMap::new();
    headers.insert(
        ACCEPT,
        HeaderValue::from_static("text/markdown, text/html;q=0.9, */*;q=0.1"),
    );
    headers.insert(
        ACCEPT_LANGUAGE,
        HeaderValue::from_static("en-US,en;q=0.9"),
    );
    headers.insert(USER_AGENT, HeaderValue::from_str(&config.user_agent).map_err(|err| err.to_string())?);
    send_request(client, &config.url, headers, config.max_response_bytes)
}

fn send_request(
    client: &Client,
    url: &str,
    headers: HeaderMap,
    max_response_bytes: usize,
) -> Result<RawFetchResult, String> {
    let response = client
        .get(url)
        .headers(headers)
        .send()
        .map_err(normalize_error)?;
    read_response(response, max_response_bytes)
}

fn read_response(response: Response, max_response_bytes: usize) -> Result<RawFetchResult, String> {
    let status = response.status().as_u16();
    let final_url = response.url().to_string();
    let headers = normalize_headers(response.headers());
    let content_type = headers.get("content-type").cloned();

    let mut limited = Vec::new();
    let mut reader = response.take((max_response_bytes + 1) as u64);
    reader
        .read_to_end(&mut limited)
        .map_err(|err| format!("Failed to read response body: {}", err))?;

    let body_truncated = limited.len() > max_response_bytes;
    let raw_body_length = limited.len();
    if body_truncated {
        limited.truncate(max_response_bytes);
    }

    let body = if content_type
        .as_deref()
        .unwrap_or_default()
        .contains("application/octet-stream")
    {
        String::from_utf8_lossy(&limited).into_owned()
    } else {
        String::from_utf8_lossy(&limited).into_owned()
    };

    Ok(RawFetchResult {
        status,
        headers,
        body,
        final_url,
        body_truncated,
        raw_body_length,
    })
}

pub fn should_use_jina_fallback_for_status(status: u16) -> bool {
    status == 403 || status == 429 || status >= 500
}

fn normalize_headers(headers: &HeaderMap) -> HashMap<String, String> {
    let mut normalized = HashMap::new();
    for (name, value) in headers.iter() {
        if let Ok(text) = value.to_str() {
            normalized.insert(name.as_str().to_ascii_lowercase(), text.to_string());
        }
    }
    normalized
}

fn normalize_error(err: reqwest::Error) -> String {
    if err.is_timeout() {
        return "Request timed out".to_string();
    }
    if err.is_connect() {
        return "Host could not be resolved or connection failed".to_string();
    }
    err.to_string()
}

#[cfg(test)]
mod tests {
    use super::should_use_jina_fallback_for_status;

    #[test]
    fn marks_jina_retry_statuses() {
        assert!(should_use_jina_fallback_for_status(403));
        assert!(should_use_jina_fallback_for_status(429));
        assert!(should_use_jina_fallback_for_status(500));
        assert!(!should_use_jina_fallback_for_status(404));
    }
}
