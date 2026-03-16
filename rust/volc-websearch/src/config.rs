use clap::Parser;

pub const TIME_RANGE_SHORTCUTS: &[&str] = &["OneDay", "OneWeek", "OneMonth", "OneYear"];

#[derive(Parser, Debug)]
#[command(
    name = "volc-websearch",
    about = "Fused web search across Tavily, Bocha, and Volc Search"
)]
pub struct Cli {
    /// Search query
    pub query: String,

    /// Search type, only web is supported
    #[arg(short = 't', long = "type", default_value = "web")]
    pub search_type: String,

    /// Number of final results to return
    #[arg(short = 'c', long, default_value_t = 15)]
    pub count: u32,

    /// Time range: OneDay/OneWeek/OneMonth/OneYear/YYYY-MM-DD..YYYY-MM-DD
    #[arg(long)]
    pub time_range: Option<String>,

    /// Limit to specific sites, pipe-separated
    #[arg(long)]
    pub sites: Option<String>,

    /// Exclude sites, pipe-separated
    #[arg(long)]
    pub block_hosts: Option<String>,

    /// Prioritize authoritative sources (0 or 1)
    #[arg(long, default_value_t = 0)]
    pub auth_level: u32,
}

#[derive(Clone, Debug)]
pub struct EmbeddingConfig {
    pub provider: String,
    pub model: String,
    pub base_url: String,
    pub api_key: String,
}

#[derive(Clone, Debug)]
pub struct Config {
    pub query: String,
    pub count: usize,
    pub time_range: Option<String>,
    pub sites: Option<Vec<String>>,
    pub block_hosts: Option<Vec<String>>,
    pub auth_level: u32,
    pub tavily_api_key: String,
    pub bocha_api_key: String,
    pub ve_access_key: String,
    pub ve_secret_key: String,
    pub embedding: EmbeddingConfig,
}

impl Config {
    pub fn from_env_and_cli(cli: Cli) -> Result<Self, String> {
        if cli.search_type != "web" {
            return Err("Only --type web is supported in fused search mode.".to_string());
        }
        if cli.count == 0 || cli.count > 50 {
            return Err("--count must be between 1 and 50.".to_string());
        }
        if let Some(ref tr) = cli.time_range {
            validate_time_range(tr)?;
        }

        Ok(Self {
            query: cli.query,
            count: cli.count as usize,
            time_range: cli.time_range,
            sites: split_domains(cli.sites),
            block_hosts: split_domains(cli.block_hosts),
            auth_level: cli.auth_level,
            tavily_api_key: required_env("TAVILY_API_KEY")?,
            bocha_api_key: required_env("BOCHA_API_KEY")?,
            ve_access_key: required_env("VE_ACCESS_KEY")?,
            ve_secret_key: required_env("VE_SECRET_KEY")?,
            embedding: EmbeddingConfig {
                provider: required_env("SEARCH_EMBEDDING_PROVIDER")?,
                model: required_env("SEARCH_EMBEDDING_MODEL")?,
                base_url: required_env("SEARCH_EMBEDDING_BASE_URL")?,
                api_key: required_env("SEARCH_EMBEDDING_API_KEY")?,
            },
        })
    }
}

fn required_env(name: &str) -> Result<String, String> {
    std::env::var(name)
        .ok()
        .filter(|value| !value.trim().is_empty())
        .ok_or_else(|| format!("Missing required environment variable: {}", name))
}

fn split_domains(input: Option<String>) -> Option<Vec<String>> {
    input.map(|value| {
        value
            .split('|')
            .map(|item| item.trim().to_ascii_lowercase())
            .filter(|item| !item.is_empty())
            .collect::<Vec<_>>()
    }).filter(|items| !items.is_empty())
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
        if part.len() != 10 || part.chars().filter(|c| *c == '-').count() != 2 {
            return Err(format!("Invalid date format: {}", part));
        }
    }
    if parts[0] > parts[1] {
        return Err("Start date must not be after end date.".to_string());
    }
    Ok(())
}
