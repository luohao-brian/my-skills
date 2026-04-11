use clap::{Parser, ValueEnum};
use std::fmt;

pub const DEFAULT_FETCH_USER_AGENT: &str =
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_7_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36";

#[derive(Copy, Clone, Debug, Default, Eq, PartialEq, ValueEnum)]
pub enum OutputFormat {
    #[default]
    Markdown,
    Text,
}

impl fmt::Display for OutputFormat {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        let value = match self {
            Self::Markdown => "markdown",
            Self::Text => "text",
        };
        write!(f, "{}", value)
    }
}

#[derive(Copy, Clone, Debug, Default, Eq, PartialEq, ValueEnum)]
pub enum JinaMode {
    #[default]
    Auto,
    Off,
    Always,
}

#[derive(Parser, Debug)]
#[command(
    name = "my-fetch",
    about = "Fetch and extract readable content from a URL (HTML -> markdown/text)"
)]
pub struct Cli {
    /// URL to fetch
    pub url: String,

    /// Output format
    #[arg(long = "format", alias = "extract-mode", value_enum, default_value_t = OutputFormat::Markdown)]
    pub format: OutputFormat,

    /// Optional CSS selector to extract a specific element first
    #[arg(long)]
    pub selector: Option<String>,

    /// Maximum extracted characters to return
    #[arg(long, default_value_t = 50_000)]
    pub max_chars: usize,

    /// Maximum raw response bytes to read before extraction
    #[arg(long, default_value_t = 2_000_000)]
    pub max_response_bytes: usize,

    /// Maximum redirects to follow
    #[arg(long, default_value_t = 3)]
    pub max_redirects: usize,

    /// Request timeout in seconds
    #[arg(long, default_value_t = 30)]
    pub timeout_seconds: u64,

    /// Override User-Agent header
    #[arg(long)]
    pub user_agent: Option<String>,

    /// HTTP proxy URL
    #[arg(long)]
    pub http_proxy: Option<String>,

    /// HTTPS proxy URL
    #[arg(long)]
    pub https_proxy: Option<String>,

    /// Comma-separated no_proxy rules
    #[arg(long)]
    pub no_proxy: Option<String>,

    /// Jina fallback mode
    #[arg(long, value_enum, default_value_t = JinaMode::Auto)]
    pub jina: JinaMode,
}

#[derive(Clone, Debug)]
pub struct Config {
    pub url: String,
    pub format: OutputFormat,
    pub selector: Option<String>,
    pub max_chars: usize,
    pub max_response_bytes: usize,
    pub max_redirects: usize,
    pub timeout_seconds: u64,
    pub user_agent: String,
    pub http_proxy: Option<String>,
    pub https_proxy: Option<String>,
    pub no_proxy_rules: Vec<String>,
    pub jina_mode: JinaMode,
    pub jina_api_key: Option<String>,
}

impl Config {
    pub fn from_env_and_cli(cli: Cli) -> Result<Self, String> {
        let url = cli.url.trim().to_string();
        if url.is_empty() {
            return Err("url must not be empty.".to_string());
        }
        let parsed = url::Url::parse(&url).map_err(|_| "Invalid URL: must be http or https".to_string())?;
        if !matches!(parsed.scheme(), "http" | "https") {
            return Err("Invalid URL: must be http or https".to_string());
        }
        if cli.max_chars == 0 {
            return Err("--max-chars must be greater than 0.".to_string());
        }
        if cli.max_response_bytes < 1024 {
            return Err("--max-response-bytes must be at least 1024.".to_string());
        }
        if cli.timeout_seconds == 0 {
            return Err("--timeout-seconds must be greater than 0.".to_string());
        }

        let no_proxy_raw = cli
            .no_proxy
            .or_else(|| read_env(&["WEB_FETCH_NO_PROXY", "WEB_SEARCH_NO_PROXY", "NO_PROXY", "no_proxy"]));

        Ok(Self {
            url,
            format: cli.format,
            selector: cli.selector.map(|value| value.trim().to_string()).filter(|value| !value.is_empty()),
            max_chars: cli.max_chars,
            max_response_bytes: cli.max_response_bytes,
            max_redirects: cli.max_redirects,
            timeout_seconds: cli.timeout_seconds,
            user_agent: cli
                .user_agent
                .map(|value| value.trim().to_string())
                .filter(|value| !value.is_empty())
                .unwrap_or_else(|| DEFAULT_FETCH_USER_AGENT.to_string()),
            http_proxy: cli
                .http_proxy
                .or_else(|| read_env(&["WEB_FETCH_HTTP_PROXY", "WEB_SEARCH_HTTP_PROXY", "HTTP_PROXY", "http_proxy"])),
            https_proxy: cli
                .https_proxy
                .or_else(|| read_env(&["WEB_FETCH_HTTPS_PROXY", "WEB_SEARCH_HTTPS_PROXY", "HTTPS_PROXY", "https_proxy"])),
            no_proxy_rules: split_no_proxy(no_proxy_raw.as_deref()),
            jina_mode: cli.jina,
            jina_api_key: read_env(&["WEB_FETCH_JINA_API_KEY", "JINA_API_KEY"]),
        })
    }
}

fn read_env(keys: &[&str]) -> Option<String> {
    keys.iter()
        .find_map(|key| std::env::var(key).ok())
        .map(|value| value.trim().to_string())
        .filter(|value| !value.is_empty())
}

fn split_no_proxy(value: Option<&str>) -> Vec<String> {
    value
        .unwrap_or_default()
        .split(',')
        .map(|item| item.trim().to_ascii_lowercase())
        .filter(|item| !item.is_empty())
        .collect()
}

#[cfg(test)]
mod tests {
    use super::{split_no_proxy, Cli, Config, JinaMode, OutputFormat};
    use clap::Parser;

    #[test]
    fn parses_extract_mode_alias() {
        let cli = Cli::parse_from([
            "my-fetch",
            "https://example.com",
            "--extract-mode",
            "text",
        ]);
        assert_eq!(cli.format, OutputFormat::Text);
    }

    #[test]
    fn splits_no_proxy_rules() {
        let rules = split_no_proxy(Some("localhost,.example.com, 127.0.0.1 "));
        assert_eq!(rules, vec!["localhost", ".example.com", "127.0.0.1"]);
    }

    #[test]
    fn builds_config_from_cli() {
        let cli = Cli::parse_from([
            "my-fetch",
            "https://example.com/article",
            "--format",
            "markdown",
            "--jina",
            "off",
        ]);
        let config = Config::from_env_and_cli(cli).unwrap();
        assert_eq!(config.url, "https://example.com/article");
        assert_eq!(config.format, OutputFormat::Markdown);
        assert_eq!(config.jina_mode, JinaMode::Off);
    }
}
