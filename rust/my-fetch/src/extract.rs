use crate::classify::{
    classify_page_type, classify_url_hint, generate_warning, score_content_quality,
};
use crate::config::{Config, OutputFormat};
use crate::models::{Extractor, RawFetchResult, WebFetchPayload};
use quick_html2md::html_to_markdown;
use readability::extractor::extract as readability_extract;
use scraper::{Html, Selector};
use serde_json::Value;
use std::borrow::Cow;
use std::io::Cursor;

const READABILITY_MAX_HTML_CHARS: usize = 1_000_000;
const READABILITY_MAX_ESTIMATED_NESTING_DEPTH: usize = 3_000;
const MAIN_SELECTORS: &[&str] = &[
    "article",
    "main",
    "[role=\"main\"]",
    ".content",
    ".post",
    ".entry",
    ".article-body",
];

pub fn process_raw_fetch(
    config: &Config,
    raw: RawFetchResult,
    fallback_chain: Vec<String>,
    extractor_hint: Option<Extractor>,
) -> Result<WebFetchPayload, String> {
    let content_type = normalize_content_type(raw.headers.get("content-type").map(String::as_str));
    let effective_hint = extractor_hint.unwrap_or(Extractor::Raw);

    let extracted = if content_type.as_deref().unwrap_or_default().contains("application/json") {
        extract_json_content(&raw.body)?
    } else if content_type
        .as_deref()
        .unwrap_or_default()
        .contains("text/markdown")
        || (effective_hint == Extractor::JinaReader
            && content_type
                .as_deref()
                .unwrap_or_default()
                .contains("text/plain"))
    {
        extract_markdown_content(&raw.body, config.format, effective_hint)
    } else if content_type
        .as_deref()
        .map(|value| {
            value.contains("text/html")
                || value.contains("application/xhtml")
                || value.is_empty()
        })
        .unwrap_or(true)
    {
        extract_html_content(&raw.body, &raw.final_url, config)?
    } else {
        let text = if config.format == OutputFormat::Text {
            normalize_whitespace(&raw.body)
        } else {
            raw.body.trim().to_string()
        };
        ExtractedContent {
            text,
            title: None,
            extractor: effective_hint,
        }
    };

    let raw_length = extracted.text.chars().count();
    let (text, extracted_truncated) = truncate_chars(&extracted.text, config.max_chars);
    let url_hint = classify_url_hint(&config.url);
    let page_type = classify_page_type(&text, url_hint);
    let mut quality = score_content_quality(&text, page_type);
    if config.selector.is_some() && !text.trim().is_empty() && quality == crate::models::ContentQuality::Empty {
        quality = crate::models::ContentQuality::LowQuality;
    }
    let mut warnings = Vec::new();
    if let Some(warning) = generate_warning(page_type, quality) {
        warnings.push(warning);
    }
    if raw.body_truncated {
        warnings.push(format!(
            "Response body truncated before extraction (original {} chars).",
            raw.raw_body_length
        ));
    }
    if fallback_chain.iter().any(|item| item == "jina_reader") {
        warnings.push("Used Jina Reader fallback.".to_string());
    }

    let empty = text.trim().is_empty();
    Ok(WebFetchPayload {
        url: config.url.clone(),
        final_url: raw.final_url,
        status: raw.status,
        content_type,
        extract_mode: config.format,
        extractor: extracted.extractor,
        title: extracted.title,
        text,
        raw_length,
        truncated: extracted_truncated,
        empty,
        warning: if warnings.is_empty() {
            None
        } else {
            Some(warnings.join("; "))
        },
    })
}

struct ExtractedContent {
    text: String,
    title: Option<String>,
    extractor: Extractor,
}

fn extract_json_content(body: &str) -> Result<ExtractedContent, String> {
    let parsed: Value = serde_json::from_str(body).map_err(|_| "Invalid JSON response body.".to_string())?;
    Ok(ExtractedContent {
        text: serde_json::to_string_pretty(&parsed)
            .map_err(|err| format!("Failed to format JSON: {}", err))?,
        title: None,
        extractor: Extractor::Json,
    })
}

fn extract_markdown_content(
    body: &str,
    format: OutputFormat,
    hint: Extractor,
) -> ExtractedContent {
    let text = match format {
        OutputFormat::Text => markdown_to_text(body),
        OutputFormat::Markdown => body.trim().to_string(),
    };
    let extractor = if hint == Extractor::JinaReader {
        Extractor::JinaReader
    } else if hint == Extractor::CfMarkdown {
        Extractor::CfMarkdown
    } else {
        Extractor::Markdown
    };
    ExtractedContent {
        text,
        title: None,
        extractor,
    }
}

fn extract_html_content(body: &str, final_url: &str, config: &Config) -> Result<ExtractedContent, String> {
    let cleaned = sanitize_html(body);
    let title = extract_title(&cleaned);
    let document = Html::parse_document(&cleaned);

    if let Some(selector_text) = config.selector.as_deref() {
        let selector = Selector::parse(selector_text)
            .map_err(|err| format!("Invalid CSS selector: {}", err))?;
        if let Some(element) = document.select(&selector).next() {
            let html = element.html();
            let plain_text = normalize_whitespace(&element.text().collect::<Vec<_>>().join(" "));
            let text = render_html_fragment(&html, config.format, Some(plain_text));
            if !text.trim().is_empty() {
                return Ok(ExtractedContent {
                    text,
                    title: title.clone(),
                    extractor: Extractor::Selector,
                });
            }
        }
    }

    if cleaned.len() <= READABILITY_MAX_HTML_CHARS
        && !exceeds_estimated_html_nesting_depth(&cleaned, READABILITY_MAX_ESTIMATED_NESTING_DEPTH)
    {
        let mut cursor = Cursor::new(cleaned.as_bytes());
        if let Ok(product) = readability_extract(&mut cursor, &url::Url::parse(final_url).map_err(|_| "Invalid final URL.".to_string())?) {
            let readable_text = match config.format {
                OutputFormat::Markdown => render_html(&product.content, config.format),
                OutputFormat::Text => normalize_whitespace(&product.text),
            };
            if !readable_text.trim().is_empty() {
                return Ok(ExtractedContent {
                    text: readable_text,
                    title: normalize_optional(product.title).or(title.clone()),
                    extractor: Extractor::Readability,
                });
            }
        }
    }

    for selector_text in MAIN_SELECTORS {
        let selector = Selector::parse(selector_text).map_err(|err| format!("Invalid built-in selector: {}", err))?;
        if let Some(element) = document.select(&selector).next() {
            let plain_text = normalize_whitespace(&element.text().collect::<Vec<_>>().join(" "));
            let text = render_html_fragment(&element.html(), config.format, Some(plain_text));
            if !text.trim().is_empty() {
                return Ok(ExtractedContent {
                    text,
                    title: title.clone(),
                    extractor: Extractor::HtmlToMarkdown,
                });
            }
        }
    }

    let body_selector = Selector::parse("body").unwrap();
    let fallback_html = document
        .select(&body_selector)
        .next()
        .map(|element| element.html())
        .unwrap_or_else(|| cleaned.clone());
    let text = render_html_fragment(&fallback_html, config.format, None);
    if !text.trim().is_empty() {
        return Ok(ExtractedContent {
            text,
            title,
            extractor: Extractor::HtmlToMarkdown,
        });
    }

    Ok(ExtractedContent {
        text: normalize_whitespace(&strip_tags(&cleaned)),
        title,
        extractor: Extractor::Raw,
    })
}

fn render_html(html: &str, format: OutputFormat) -> String {
    let markdown = html_to_markdown(html).trim().to_string();
    match format {
        OutputFormat::Markdown => markdown,
        OutputFormat::Text => markdown_to_text(&markdown),
    }
}

fn render_html_fragment(
    html: &str,
    format: OutputFormat,
    plain_text_fallback: Option<String>,
) -> String {
    let mut markdown = html_to_markdown(html).trim().to_string();
    if markdown.is_empty() && !html.to_ascii_lowercase().contains("<body") {
        markdown = html_to_markdown(&format!("<body>{}</body>", html))
            .trim()
            .to_string();
    }

    if markdown.is_empty() {
        return plain_text_fallback
            .filter(|value| !value.is_empty())
            .unwrap_or_else(|| normalize_whitespace(&strip_tags(html)));
    }

    match format {
        OutputFormat::Markdown => markdown,
        OutputFormat::Text => markdown_to_text(&markdown),
    }
}

fn extract_title(html: &str) -> Option<String> {
    let document = Html::parse_document(html);
    let selector = Selector::parse("title").ok()?;
    document
        .select(&selector)
        .next()
        .map(|element| element.text().collect::<Vec<_>>().join(" "))
        .and_then(normalize_optional)
}

fn normalize_content_type(value: Option<&str>) -> Option<String> {
    value
        .map(|item| item.split(';').next().unwrap_or_default().trim().to_ascii_lowercase())
        .filter(|item| !item.is_empty())
}

fn normalize_optional(value: String) -> Option<String> {
    let normalized = normalize_whitespace(&value);
    if normalized.is_empty() {
        None
    } else {
        Some(normalized)
    }
}

fn truncate_chars(value: &str, max_chars: usize) -> (String, bool) {
    let count = value.chars().count();
    if count <= max_chars {
        return (value.to_string(), false);
    }
    (value.chars().take(max_chars).collect(), true)
}

fn markdown_to_text(markdown: &str) -> String {
    normalize_whitespace(
        markdown
            .replace("```", "")
            .replace('`', "")
            .replace("---", "\n")
            .lines()
            .map(strip_markdown_line)
            .collect::<Vec<_>>()
            .join("\n")
            .as_str(),
    )
}

fn strip_markdown_line(line: &str) -> String {
    let mut stripped = line.trim().to_string();
    while stripped.starts_with('#') {
        stripped = stripped[1..].trim_start().to_string();
    }
    if let Some(rest) = stripped.strip_prefix("- ") {
        stripped = rest.to_string();
    }
    if let Some(rest) = stripped.strip_prefix("* ") {
        stripped = rest.to_string();
    }
    if let Some(idx) = stripped.find(". ") {
        if stripped[..idx].chars().all(|ch| ch.is_ascii_digit()) {
            stripped = stripped[(idx + 2)..].to_string();
        }
    }
    stripped = stripped.replace("**", "");
    stripped = stripped.replace('*', "");
    stripped = stripped.replace("[", "");
    stripped = stripped.replace("]", "");
    stripped
}

fn normalize_whitespace(value: &str) -> String {
    value
        .split_whitespace()
        .collect::<Vec<_>>()
        .join(" ")
        .replace(" \n ", "\n")
        .trim()
        .to_string()
}

fn sanitize_html(html: &str) -> String {
    let mut cleaned: Cow<'_, str> = Cow::Borrowed(html);
    for tag in ["script", "style", "noscript", "iframe", "svg"] {
        cleaned = Cow::Owned(remove_tag_block(cleaned.as_ref(), tag));
    }
    cleaned.into_owned()
}

fn remove_tag_block(html: &str, tag: &str) -> String {
    let pattern = format!(r"(?is)<{tag}\b[^>]*>.*?</{tag}>");
    let regex = regex::Regex::new(&pattern).unwrap();
    regex.replace_all(html, " ").into_owned()
}

fn strip_tags(html: &str) -> String {
    let regex = regex::Regex::new(r"(?is)<[^>]+>").unwrap();
    regex.replace_all(html, " ").into_owned()
}

fn exceeds_estimated_html_nesting_depth(html: &str, max_depth: usize) -> bool {
    let mut depth = 0usize;
    let mut chars = html.chars().peekable();
    while let Some(ch) = chars.next() {
        if ch != '<' {
            continue;
        }
        let next = match chars.peek() {
            Some(value) => *value,
            None => break,
        };
        if matches!(next, '!' | '?') {
            continue;
        }
        let mut closing = false;
        if next == '/' {
            closing = true;
            chars.next();
        }
        let mut name = String::new();
        while let Some(value) = chars.peek() {
            if value.is_ascii_alphanumeric() || *value == ':' || *value == '-' {
                name.push(*value);
                chars.next();
            } else {
                break;
            }
        }
        if name.is_empty() {
            continue;
        }
        let lower = name.to_ascii_lowercase();
        if closing {
            depth = depth.saturating_sub(1);
            continue;
        }
        if matches!(
            lower.as_str(),
            "area" | "base" | "br" | "col" | "embed" | "hr" | "img" | "input" | "link"
                | "meta" | "param" | "source" | "track" | "wbr"
        ) {
            continue;
        }
        depth += 1;
        if depth > max_depth {
            return true;
        }
    }
    false
}

#[cfg(test)]
mod tests {
    use super::{extract_html_content, markdown_to_text, process_raw_fetch};
    use crate::config::{Config, JinaMode, OutputFormat};
    use crate::models::{Extractor, RawFetchResult};
    use std::collections::HashMap;

    fn test_config() -> Config {
        Config {
            url: "https://example.com/article".to_string(),
            format: OutputFormat::Markdown,
            selector: None,
            max_chars: 50_000,
            max_response_bytes: 2_000_000,
            max_redirects: 3,
            timeout_seconds: 30,
            user_agent: "test-agent".to_string(),
            http_proxy: None,
            https_proxy: None,
            no_proxy_rules: Vec::new(),
            jina_mode: JinaMode::Auto,
            jina_api_key: None,
        }
    }

    #[test]
    fn converts_markdown_to_text() {
        let text = markdown_to_text("# Title\n\n- item");
        assert!(text.contains("Title"));
        assert!(text.contains("item"));
    }

    #[test]
    fn prefers_selector_when_present() {
        let mut config = test_config();
        config.selector = Some("#main".to_string());
        let extracted = extract_html_content(
            r#"<html><head><title>Demo</title></head><body><div id="main"><p>Target text</p></div><div>Noise</div></body></html>"#,
            &config.url,
            &config,
        )
        .unwrap();
        assert_eq!(extracted.extractor, Extractor::Selector);
        assert!(extracted.text.contains("Target text"));
    }

    #[test]
    fn selector_extracts_simple_heading_fragment() {
        let mut config = test_config();
        config.selector = Some("h1".to_string());
        let extracted = extract_html_content(
            r#"<html><head><title>Demo</title></head><body><h1>Heading only</h1></body></html>"#,
            &config.url,
            &config,
        )
        .unwrap();
        assert_eq!(extracted.extractor, Extractor::Selector);
        assert!(extracted.text.contains("Heading only"));
    }

    #[test]
    fn renders_payload_with_warning() {
        let config = test_config();
        let raw = RawFetchResult {
            status: 200,
            headers: HashMap::from([("content-type".to_string(), "text/html".to_string())]),
            body: "<html><body><article><p>".to_string() + &"A".repeat(220) + "</p><p>" + &"B".repeat(220) + "</p></article></body></html>",
            final_url: config.url.clone(),
            body_truncated: false,
            raw_body_length: 0,
        };
        let payload = process_raw_fetch(&config, raw, vec!["direct_fetch".to_string()], None).unwrap();
        assert_eq!(payload.status, 200);
        assert!(!payload.text.is_empty());
    }
}
