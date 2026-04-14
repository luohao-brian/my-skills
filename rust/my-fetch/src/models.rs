use crate::config::OutputFormat;
use std::collections::HashMap;
use std::fmt;

#[derive(Clone, Debug)]
pub struct RawFetchResult {
    pub status: u16,
    pub headers: HashMap<String, String>,
    pub body: String,
    pub final_url: String,
    pub body_truncated: bool,
    pub raw_body_length: usize,
}

#[derive(Copy, Clone, Debug, Eq, PartialEq)]
pub enum Extractor {
    Readability,
    HtmlToMarkdown,
    Markdown,
    Json,
    Raw,
    CfMarkdown,
    JinaReader,
    Selector,
}

impl fmt::Display for Extractor {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        let value = match self {
            Self::Readability => "readability",
            Self::HtmlToMarkdown => "html-to-markdown",
            Self::Markdown => "markdown",
            Self::Json => "json",
            Self::Raw => "raw",
            Self::CfMarkdown => "cf-markdown",
            Self::JinaReader => "jina-reader",
            Self::Selector => "selector",
        };
        write!(f, "{}", value)
    }
}

#[derive(Copy, Clone, Debug, Eq, PartialEq)]
pub enum PageType {
    Article,
    ListingPage,
    ChallengePage,
    Homepage,
    LoginWall,
    Unknown,
}

impl fmt::Display for PageType {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        let value = match self {
            Self::Article => "article",
            Self::ListingPage => "listing_page",
            Self::ChallengePage => "challenge_page",
            Self::Homepage => "homepage",
            Self::LoginWall => "login_wall",
            Self::Unknown => "unknown",
        };
        write!(f, "{}", value)
    }
}

#[derive(Copy, Clone, Debug, Eq, PartialEq)]
pub enum ContentQuality {
    Usable,
    LowQuality,
    Empty,
}

impl fmt::Display for ContentQuality {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        let value = match self {
            Self::Usable => "usable",
            Self::LowQuality => "low_quality",
            Self::Empty => "empty",
        };
        write!(f, "{}", value)
    }
}

#[derive(Clone, Debug)]
pub struct WebFetchPayload {
    pub url: String,
    pub final_url: String,
    pub status: u16,
    pub content_type: Option<String>,
    pub extract_mode: OutputFormat,
    pub extractor: Extractor,
    pub title: Option<String>,
    pub text: String,
    pub raw_length: usize,
    pub truncated: bool,
    pub empty: bool,
    pub warning: Option<String>,
}
