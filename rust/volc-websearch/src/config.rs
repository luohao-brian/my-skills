use clap::{Parser, ValueEnum};

pub const TIME_RANGE_SHORTCUTS: &[&str] = &["OneDay", "OneWeek", "OneMonth", "OneYear"];

#[derive(Copy, Clone, Debug, Eq, PartialEq, ValueEnum)]
pub enum Freshness {
    Pd,
    Pw,
    Pm,
    Py,
}

impl Freshness {
    pub fn as_volc_time_range(self) -> &'static str {
        match self {
            Self::Pd => "OneDay",
            Self::Pw => "OneWeek",
            Self::Pm => "OneMonth",
            Self::Py => "OneYear",
        }
    }

    pub fn as_tavily_time_range(self) -> &'static str {
        match self {
            Self::Pd => "day",
            Self::Pw => "week",
            Self::Pm => "month",
            Self::Py => "year",
        }
    }
}

#[derive(Copy, Clone, Debug, Default, Eq, PartialEq, ValueEnum)]
pub enum SearchIntent {
    #[default]
    Discover,
    News,
    Fact,
    #[value(name = "source_finding")]
    SourceFinding,
}

#[derive(Copy, Clone, Debug, Default, Eq, PartialEq, ValueEnum)]
pub enum ResultType {
    #[default]
    List,
    Summary,
}

#[derive(Parser, Debug)]
#[command(
    name = "volc-websearch",
    about = "Fused web search across Tavily, Bocha, Brave, and Volc Search"
)]
pub struct Cli {
    /// Search query
    pub query: String,

    /// Legacy search type flag, only web is supported
    #[arg(short = 't', long = "type", default_value = "web", hide = true)]
    pub search_type: String,

    /// Search engine to use: auto, tavily, bocha, brave, volc
    #[arg(long, default_value = "auto")]
    pub engine: String,

    /// Number of results to return
    #[arg(short = 'c', long, default_value_t = 15)]
    pub count: u32,

    /// Shortcut freshness window: pd (day), pw (week), pm (month), py (year)
    #[arg(long, value_enum)]
    pub freshness: Option<Freshness>,

    /// Inclusive start date in YYYY-MM-DD format
    #[arg(long)]
    pub date_after: Option<String>,

    /// Inclusive end date in YYYY-MM-DD format
    #[arg(long)]
    pub date_before: Option<String>,

    /// Country hint such as CN or US
    #[arg(long)]
    pub country: Option<String>,

    /// Language hint such as zh or en
    #[arg(long)]
    pub language: Option<String>,

    /// Domain allowlist, comma-separated or repeated
    #[arg(long = "domain-filter", value_delimiter = ',')]
    pub domain_filter: Vec<String>,

    /// Search intent hint for provider selection
    #[arg(long, value_enum, default_value_t = SearchIntent::Discover)]
    pub intent: SearchIntent,

    /// Output shape
    #[arg(long, value_enum, default_value_t = ResultType::List)]
    pub result_type: ResultType,

    /// Legacy time range: OneDay/OneWeek/OneMonth/OneYear/YYYY-MM-DD..YYYY-MM-DD
    #[arg(long, hide = true, conflicts_with_all = ["freshness", "date_after", "date_before"])]
    pub time_range: Option<String>,

    /// Legacy domain filter, pipe-separated
    #[arg(long, hide = true, conflicts_with = "domain_filter")]
    pub sites: Option<String>,

    /// Exclude sites, pipe-separated
    #[arg(long, hide = true)]
    pub block_hosts: Option<String>,

    /// Prioritize authoritative sources (0 or 1)
    #[arg(long, default_value_t = 0, hide = true)]
    pub auth_level: u32,

    /// HTTP proxy URL (overrides HTTP_PROXY env var)
    #[arg(long)]
    pub http_proxy: Option<String>,

    /// HTTPS proxy URL (overrides HTTPS_PROXY env var)
    #[arg(long)]
    pub https_proxy: Option<String>,

    /// No proxy hosts (overrides NO_PROXY env var)
    #[arg(long)]
    pub no_proxy: Option<String>,
}

#[derive(Clone, Debug)]
pub struct Config {
    pub query: String,
    pub count: usize,
    pub freshness: Option<Freshness>,
    pub date_after: Option<String>,
    pub date_before: Option<String>,
    pub country: Option<String>,
    pub language: Option<String>,
    pub domain_filter: Option<Vec<String>>,
    pub block_hosts: Option<Vec<String>>,
    pub auth_level: u32,
    pub intent: SearchIntent,
    pub result_type: ResultType,
    pub engine: String,
    pub tavily_api_key: String,
    pub bocha_api_key: String,
    pub brave_api_key: String,
    pub ve_access_key: String,
    pub ve_secret_key: String,
    pub http_proxy: Option<String>,
    pub https_proxy: Option<String>,
    pub no_proxy: Option<String>,
}

impl Config {
    pub fn from_env_and_cli(cli: Cli) -> Result<Self, String> {
        if cli.search_type != "web" {
            return Err("Only --type web is supported in fused search mode.".to_string());
        }
        if cli.count == 0 || cli.count > 50 {
            return Err("--count must be between 1 and 50.".to_string());
        }

        // Validate engine
        let valid_engines = ["auto", "tavily", "bocha", "brave", "volc"];
        if !valid_engines.contains(&cli.engine.as_str()) {
            return Err("--engine must be one of: auto, tavily, bocha, brave, volc".to_string());
        }

        let query = cli.query.trim().to_string();
        if query.is_empty() {
            return Err("query must not be empty.".to_string());
        }

        if cli.freshness.is_some() && (cli.date_after.is_some() || cli.date_before.is_some()) {
            return Err(
                "--freshness cannot be combined with --date-after/--date-before.".to_string(),
            );
        }

        let mut freshness = cli.freshness;
        let mut date_after = cli.date_after;
        let mut date_before = cli.date_before;

        if let Some(ref tr) = cli.time_range {
            let (legacy_freshness, legacy_after, legacy_before) = parse_legacy_time_range(tr)?;
            freshness = legacy_freshness;
            date_after = legacy_after;
            date_before = legacy_before;
        }

        if let Some(ref after) = date_after {
            validate_date(after)?;
        }
        if let Some(ref before) = date_before {
            validate_date(before)?;
        }
        if let (Some(after), Some(before)) = (date_after.as_deref(), date_before.as_deref()) {
            if after > before {
                return Err("--date-after must not be later than --date-before.".to_string());
            }
        }

        let country = normalize_country(cli.country)?;
        let language = normalize_language(cli.language)?;

        let mut domain_filter = if cli.domain_filter.is_empty() {
            None
        } else {
            Some(normalize_domains(cli.domain_filter))
        };
        if domain_filter.is_none() {
            domain_filter = split_domains(cli.sites);
        }

        let engine = cli.engine.clone();
        let auth_level = if cli.auth_level > 0 {
            cli.auth_level
        } else if matches!(cli.intent, SearchIntent::Fact | SearchIntent::SourceFinding) {
            1
        } else {
            0
        };

        Ok(Self {
            query,
            count: cli.count as usize,
            freshness,
            date_after,
            date_before,
            country,
            language,
            domain_filter,
            block_hosts: split_domains(cli.block_hosts),
            auth_level,
            intent: cli.intent,
            result_type: cli.result_type,
            engine: engine.clone(),
            tavily_api_key: if engine == "tavily" {
                required_env("TAVILY_API_KEY")?
            } else {
                optional_env("TAVILY_API_KEY")
            },
            bocha_api_key: if engine == "bocha" {
                required_env("BOCHA_API_KEY")?
            } else {
                optional_env("BOCHA_API_KEY")
            },
            brave_api_key: if engine == "brave" {
                required_env("BRAVE_API_KEY")?
            } else {
                optional_env("BRAVE_API_KEY")
            },
            ve_access_key: if engine == "volc" {
                required_env("VE_ACCESS_KEY")?
            } else {
                optional_env("VE_ACCESS_KEY")
            },
            ve_secret_key: if engine == "volc" {
                required_env("VE_SECRET_KEY")?
            } else {
                optional_env("VE_SECRET_KEY")
            },
            http_proxy: cli
                .http_proxy
                .or(std::env::var("HTTP_PROXY").ok())
                .or(std::env::var("http_proxy").ok()),
            https_proxy: cli
                .https_proxy
                .or(std::env::var("HTTPS_PROXY").ok())
                .or(std::env::var("https_proxy").ok()),
            no_proxy: cli
                .no_proxy
                .or(std::env::var("NO_PROXY").ok())
                .or(std::env::var("no_proxy").ok()),
        })
    }

    pub fn volc_time_range(&self) -> Option<String> {
        if let (Some(after), Some(before)) = (self.date_after.as_deref(), self.date_before.as_deref()) {
            return Some(format!("{}..{}", after, before));
        }
        self.freshness
            .map(|freshness| freshness.as_volc_time_range().to_string())
    }

    pub fn forced_engine_warnings(&self) -> Vec<String> {
        if self.engine == "auto" {
            return Vec::new();
        }

        let mut warnings = Vec::new();
        match self.engine.as_str() {
            "bocha" => {
                if self.freshness.is_some() || self.date_after.is_some() || self.date_before.is_some() {
                    warnings.push("Bocha 当前不会原生下推 freshness/date_after/date_before，时间约束将被忽略。".to_string());
                }
                if self.country.is_some() || self.language.is_some() {
                    warnings.push("Bocha 当前不会原生下推 country/language，地域和语言约束将被忽略。".to_string());
                }
                if self.domain_filter.is_some() || self.block_hosts.is_some() {
                    warnings.push("Bocha 当前不会原生下推 domain_filter/block_hosts，站点过滤将被忽略。".to_string());
                }
            }
            "brave" => {
                if self.freshness.is_some() || self.date_after.is_some() || self.date_before.is_some() {
                    warnings.push("Brave 当前只原生下推 query/count/country/language，时间约束将被忽略。".to_string());
                }
                if self.domain_filter.is_some() || self.block_hosts.is_some() {
                    warnings.push("Brave 当前不会原生下推 domain_filter/block_hosts，站点过滤将被忽略。".to_string());
                }
            }
            "tavily" => {
                if self.language.is_some() {
                    warnings.push("Tavily 当前没有启用明确的 language 下推字段，语言约束将被忽略。".to_string());
                }
            }
            "volc" => {
                if self.country.is_some() || self.language.is_some() {
                    warnings.push("Volc 当前不会原生下推 country/language，地域和语言约束将被忽略。".to_string());
                }
            }
            _ => {}
        }
        warnings
    }
}

fn required_env(name: &str) -> Result<String, String> {
    std::env::var(name)
        .ok()
        .filter(|value| !value.trim().is_empty())
        .ok_or_else(|| format!("Missing required environment variable: {}", name))
}

fn optional_env(name: &str) -> String {
    std::env::var(name)
        .ok()
        .filter(|value| !value.trim().is_empty())
        .unwrap_or_default()
}

fn split_domains(input: Option<String>) -> Option<Vec<String>> {
    input
        .map(|value| normalize_domains(value.split('|').map(|item| item.to_string()).collect()))
        .filter(|items| !items.is_empty())
}

fn normalize_domains(items: Vec<String>) -> Vec<String> {
    items
        .into_iter()
        .map(|item| item.trim().trim_matches('"').trim_matches('\'').to_ascii_lowercase())
        .filter(|item| !item.is_empty())
        .collect()
}

fn normalize_country(input: Option<String>) -> Result<Option<String>, String> {
    input
        .map(|value| {
            let normalized = value.trim().to_ascii_uppercase();
            if normalized.len() != 2 || !normalized.chars().all(|ch| ch.is_ascii_alphabetic()) {
                return Err("--country must be a 2-letter country code such as CN or US.".to_string());
            }
            Ok(normalized)
        })
        .transpose()
}

fn normalize_language(input: Option<String>) -> Result<Option<String>, String> {
    input
        .map(|value| {
            let normalized = value.trim().to_ascii_lowercase();
            let valid = !normalized.is_empty()
                && normalized.len() <= 8
                && normalized
                    .chars()
                    .all(|ch| ch.is_ascii_alphabetic() || ch == '-');
            if !valid {
                return Err("--language must look like zh, en, or zh-cn.".to_string());
            }
            Ok(normalized)
        })
        .transpose()
}

fn parse_legacy_time_range(tr: &str) -> Result<(Option<Freshness>, Option<String>, Option<String>), String> {
    validate_time_range(tr)?;
    let freshness = match tr {
        "OneDay" => Some(Freshness::Pd),
        "OneWeek" => Some(Freshness::Pw),
        "OneMonth" => Some(Freshness::Pm),
        "OneYear" => Some(Freshness::Py),
        _ => None,
    };
    if freshness.is_some() {
        return Ok((freshness, None, None));
    }
    let parts: Vec<&str> = tr.splitn(2, "..").collect();
    Ok((
        None,
        Some(parts[0].to_string()),
        Some(parts[1].to_string()),
    ))
}

pub fn validate_time_range(tr: &str) -> Result<(), String> {
    if TIME_RANGE_SHORTCUTS.contains(&tr) {
        return Ok(());
    }
    let parts: Vec<&str> = tr.splitn(2, "..").collect();
    if parts.len() != 2 {
        return Err(
            "--time-range must be OneDay/OneWeek/OneMonth/OneYear or YYYY-MM-DD..YYYY-MM-DD"
                .to_string(),
        );
    }
    for part in &parts {
        validate_date(part)?;
    }
    if parts[0] > parts[1] {
        return Err("Start date must not be after end date.".to_string());
    }
    Ok(())
}

pub fn validate_date(date: &str) -> Result<(), String> {
    let chars: Vec<char> = date.chars().collect();
    let valid = chars.len() == 10
        && chars[4] == '-'
        && chars[7] == '-'
        && chars
            .iter()
            .enumerate()
            .all(|(idx, ch)| matches!(idx, 4 | 7) || ch.is_ascii_digit());
    if !valid {
        return Err(format!("Invalid date format: {}", date));
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::{parse_legacy_time_range, validate_date, validate_time_range, Freshness};

    #[test]
    fn validates_iso_dates() {
        assert!(validate_date("2026-03-24").is_ok());
        assert!(validate_date("2026/03/24").is_err());
    }

    #[test]
    fn parses_legacy_shortcuts() {
        let parsed = parse_legacy_time_range("OneWeek").unwrap();
        assert_eq!(parsed.0, Some(Freshness::Pw));
        assert!(parsed.1.is_none());
        assert!(parsed.2.is_none());
    }

    #[test]
    fn parses_legacy_date_range() {
        let parsed = parse_legacy_time_range("2026-03-01..2026-03-24").unwrap();
        assert_eq!(parsed.0, None);
        assert_eq!(parsed.1.as_deref(), Some("2026-03-01"));
        assert_eq!(parsed.2.as_deref(), Some("2026-03-24"));
    }

    #[test]
    fn rejects_invalid_time_range() {
        assert!(validate_time_range("bad-range").is_err());
    }
}
