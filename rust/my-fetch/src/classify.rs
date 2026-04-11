use crate::models::{ContentQuality, PageType};
use once_cell::sync::Lazy;
use regex::Regex;
use url::Url;

#[derive(Copy, Clone, Debug, Eq, PartialEq)]
pub enum UrlTypeHint {
    Article,
    Listing,
    Homepage,
    Unknown,
}

static LISTING_PATTERNS: Lazy<Vec<Regex>> = Lazy::new(|| {
    vec![
        Regex::new(r"/categor(y|ies)/").unwrap(),
        Regex::new(r"/tags?/").unwrap(),
        Regex::new(r"/topics?/").unwrap(),
        Regex::new(r"/search(\?|/|$)").unwrap(),
        Regex::new(r"/archive/").unwrap(),
        Regex::new(r"/page/\d+").unwrap(),
    ]
});

static CHALLENGE_PATTERNS: Lazy<Vec<Regex>> = Lazy::new(|| {
    vec![
        Regex::new(r"(?i)verify\s+you\s+are\s+human").unwrap(),
        Regex::new(r"(?i)security\s+check(point)?").unwrap(),
        Regex::new(r"(?i)enable\s+javascript").unwrap(),
        Regex::new(r"(?i)captcha").unwrap(),
        Regex::new(r"(?i)cloudflare").unwrap(),
        Regex::new(r"(?i)access\s+denied").unwrap(),
        Regex::new(r"(?i)just\s+a\s+moment").unwrap(),
        Regex::new(r"(?i)checking\s+(your\s+)?browser").unwrap(),
        Regex::new(r"(?i)ray\s+id").unwrap(),
    ]
});

static LOGIN_WALL_PATTERNS: Lazy<Vec<Regex>> = Lazy::new(|| {
    vec![
        Regex::new(r"(?i)sign\s+in\s+to\s+continue").unwrap(),
        Regex::new(r"(?i)subscribe\s+to\s+(continue|read)").unwrap(),
        Regex::new(r"(?i)log\s+in\s+to\s+(continue|read|view)").unwrap(),
        Regex::new(r"(?i)subscriber[- ]only").unwrap(),
        Regex::new(r"(?i)create\s+an?\s+account\s+to").unwrap(),
        Regex::new(r"(?i)paywall").unwrap(),
    ]
});

static NOISE_PATTERNS: Lazy<Vec<Regex>> = Lazy::new(|| {
    vec![
        Regex::new(r"(?i)cookie\s*(policy|consent|notice)").unwrap(),
        Regex::new(r"(?i)privacy\s*policy").unwrap(),
        Regex::new(r"(?i)terms\s*(of|&)\s*(service|use)").unwrap(),
        Regex::new(r"(?i)all\s*rights?\s*reserved").unwrap(),
        Regex::new(r"©\s*\d{4}").unwrap(),
        Regex::new(r"(?i)newsletter").unwrap(),
        Regex::new(r"(?i)subscribe\s+to\s+our").unwrap(),
    ]
});

pub fn classify_url_hint(url: &str) -> UrlTypeHint {
    let parsed = match Url::parse(url) {
        Ok(value) => value,
        Err(_) => return UrlTypeHint::Unknown,
    };
    let path = parsed.path();
    if path == "/" || path.is_empty() {
        return UrlTypeHint::Homepage;
    }
    if LISTING_PATTERNS.iter().any(|pattern| pattern.is_match(path)) {
        return UrlTypeHint::Listing;
    }
    let segments: Vec<&str> = path.split('/').filter(|item| !item.is_empty()).collect();
    if segments.len() >= 3 {
        return UrlTypeHint::Article;
    }
    let last = segments.last().copied().unwrap_or_default();
    if last.contains('-') && last.len() > 15 {
        return UrlTypeHint::Article;
    }
    UrlTypeHint::Unknown
}

pub fn classify_page_type(text: &str, url_hint: UrlTypeHint) -> PageType {
    let trimmed = text.trim();
    if trimmed.len() < 100 {
        return PageType::Unknown;
    }
    if trimmed.len() < 2_000 && matches_any(trimmed, &CHALLENGE_PATTERNS) {
        return PageType::ChallengePage;
    }
    if trimmed.len() < 3_000 && matches_any(trimmed, &LOGIN_WALL_PATTERNS) {
        return PageType::LoginWall;
    }
    if url_hint == UrlTypeHint::Homepage {
        return PageType::Homepage;
    }
    if is_listing_content(trimmed, url_hint) {
        return PageType::ListingPage;
    }
    if has_article_structure(trimmed) {
        return PageType::Article;
    }
    PageType::Unknown
}

pub fn score_content_quality(text: &str, page_type: PageType) -> ContentQuality {
    let trimmed = text.trim();
    if matches!(page_type, PageType::ChallengePage | PageType::LoginWall) {
        return ContentQuality::Empty;
    }
    if trimmed.len() < 50 {
        return ContentQuality::Empty;
    }
    if trimmed.len() < 200 && page_type != PageType::Article {
        return ContentQuality::LowQuality;
    }
    if page_type == PageType::Article {
        let paragraphs: Vec<&str> = trimmed
            .split("\n\n")
            .filter(|item| item.trim().len() > 80)
            .collect();
        if paragraphs.len() >= 2 || trimmed.len() > 500 {
            return ContentQuality::Usable;
        }
        return ContentQuality::LowQuality;
    }
    if matches!(page_type, PageType::ListingPage | PageType::Homepage) {
        return if trimmed.len() > 200 {
            ContentQuality::Usable
        } else {
            ContentQuality::LowQuality
        };
    }
    let noise_hits = NOISE_PATTERNS
        .iter()
        .filter(|pattern| pattern.is_match(trimmed))
        .count();
    if trimmed.len() < 300 && noise_hits > 2 {
        return ContentQuality::LowQuality;
    }
    if trimmed.len() > 500 {
        return ContentQuality::Usable;
    }
    ContentQuality::LowQuality
}

pub fn generate_warning(page_type: PageType, quality: ContentQuality) -> Option<String> {
    if quality == ContentQuality::Empty {
        return match page_type {
            PageType::ChallengePage => Some(
                "This page is a security challenge or CAPTCHA page. No article content available."
                    .to_string(),
            ),
            PageType::LoginWall => Some(
                "This page requires login or subscription. Content is behind a paywall."
                    .to_string(),
            ),
            _ => Some("No meaningful content could be extracted from this page.".to_string()),
        };
    }
    if page_type == PageType::ListingPage {
        return Some(
            "This is a listing page rather than a single article. Consider fetching a specific detail URL."
                .to_string(),
        );
    }
    if page_type == PageType::Homepage {
        return Some(
            "This is a homepage or landing page. Consider fetching a more specific page.".to_string(),
        );
    }
    if quality == ContentQuality::LowQuality {
        return Some(
            "Extracted content quality is low. The page may be dynamically rendered or text-light."
                .to_string(),
        );
    }
    None
}

fn matches_any(text: &str, patterns: &[Regex]) -> bool {
    patterns.iter().any(|pattern| pattern.is_match(text))
}

fn is_listing_content(text: &str, url_hint: UrlTypeHint) -> bool {
    let lines: Vec<&str> = text.lines().map(str::trim).filter(|line| !line.is_empty()).collect();
    if lines.len() < 5 {
        return false;
    }
    let short_lines = lines.iter().filter(|line| line.len() < 120).count();
    let long_paragraphs = lines.iter().filter(|line| line.len() > 200).count();
    let short_ratio = short_lines as f32 / lines.len() as f32;
    (url_hint == UrlTypeHint::Listing && short_ratio > 0.6)
        || (short_ratio > 0.8 && long_paragraphs < 2)
}

fn has_article_structure(text: &str) -> bool {
    text.split("\n\n")
        .filter(|paragraph| paragraph.trim().len() > 100)
        .count()
        >= 2
}

#[cfg(test)]
mod tests {
    use super::{
        classify_page_type, classify_url_hint, generate_warning, score_content_quality,
        ContentQuality, PageType, UrlTypeHint,
    };

    #[test]
    fn detects_listing_url() {
        assert_eq!(
            classify_url_hint("https://example.com/category/ai/"),
            UrlTypeHint::Listing
        );
    }

    #[test]
    fn detects_article_page() {
        let para1 = "A".repeat(140);
        let para2 = "B".repeat(140);
        assert_eq!(
            classify_page_type(&format!("{}\n\n{}", para1, para2), UrlTypeHint::Unknown),
            PageType::Article
        );
        assert_eq!(
            score_content_quality(&format!("{}\n\n{}", para1, para2), PageType::Article),
            ContentQuality::Usable
        );
    }

    #[test]
    fn warns_for_listing_page() {
        let warning = generate_warning(PageType::ListingPage, ContentQuality::Usable).unwrap();
        assert!(warning.contains("listing page"));
    }
}
