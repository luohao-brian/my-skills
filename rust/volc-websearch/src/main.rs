mod api;
mod models;
mod sign;

use clap::Parser;
use std::process;

const TIME_RANGE_SHORTCUTS: &[&str] = &["OneDay", "OneWeek", "OneMonth", "OneYear"];

#[derive(Parser)]
#[command(
    name = "volc-websearch",
    about = "Volcengine Web Search API\nhttps://www.volcengine.com/docs/85508/1650263"
)]
struct Cli {
    /// Search query
    query: String,

    /// Search type: web or image
    #[arg(short = 't', long = "type", default_value = "web")]
    search_type: String,

    /// Number of results (web max 50, image max 5)
    #[arg(short = 'c', long, default_value_t = 5)]
    count: u32,

    /// Time range: OneDay/OneWeek/OneMonth/OneYear/YYYY-MM-DD..YYYY-MM-DD
    #[arg(long)]
    time_range: Option<String>,

    /// Limit to specific sites, pipe-separated
    #[arg(long)]
    sites: Option<String>,

    /// Exclude sites, pipe-separated
    #[arg(long)]
    block_hosts: Option<String>,

    /// Prioritize authoritative sources (0 or 1)
    #[arg(long, default_value_t = 0)]
    auth_level: u32,
}

fn validate_time_range(tr: &str) -> Result<(), String> {
    if TIME_RANGE_SHORTCUTS.contains(&tr) {
        return Ok(());
    }
    // Check date range format: YYYY-MM-DD..YYYY-MM-DD
    let parts: Vec<&str> = tr.splitn(2, "..").collect();
    if parts.len() != 2 {
        return Err(
            "--time-range must be OneDay/OneWeek/OneMonth/OneYear or YYYY-MM-DD..YYYY-MM-DD"
                .to_string(),
        );
    }
    // Basic date format validation
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

enum AuthMethod {
    ApiKey(String),
    AkSk(String, String),
}

fn get_auth() -> Result<AuthMethod, String> {
    // Priority 1: TORCHLIGHT_API_KEY
    if let Ok(key) = std::env::var("TORCHLIGHT_API_KEY") {
        if !key.is_empty() {
            return Ok(AuthMethod::ApiKey(key));
        }
    }

    // Priority 2: VE_ACCESS_KEY + VE_SECRET_KEY
    let ak = std::env::var("VE_ACCESS_KEY").unwrap_or_default();
    let sk = std::env::var("VE_SECRET_KEY").unwrap_or_default();
    if !ak.is_empty() && !sk.is_empty() {
        return Ok(AuthMethod::AkSk(ak, sk));
    }

    Err(
        "No credentials found. Set one of:\n\
         1) TORCHLIGHT_API_KEY\n\
         2) VE_ACCESS_KEY + VE_SECRET_KEY"
            .to_string(),
    )
}

fn run() -> Result<String, String> {
    let cli = Cli::parse();

    // Validate
    if cli.search_type == "image" && cli.count > 5 {
        return Err("image type supports max 5 results.".to_string());
    }
    if cli.search_type == "web" && cli.count > 50 {
        return Err("web type supports max 50 results.".to_string());
    }
    if let Some(ref tr) = cli.time_range {
        validate_time_range(tr)?;
    }

    let auth = get_auth()?;

    let req = api::build_request(
        &cli.query,
        &cli.search_type,
        cli.count,
        cli.sites.as_deref(),
        cli.block_hosts.as_deref(),
        cli.time_range.as_deref(),
        cli.auth_level,
    );
    let body = serde_json::to_string(&req).unwrap();

    let resp = match auth {
        AuthMethod::ApiKey(key) => api::search_with_api_key(&body, &key)?,
        AuthMethod::AkSk(ak, sk) => api::search_with_aksk(&body, &ak, &sk)?,
    };

    // Check for API error
    if let Some(meta) = &resp.response_metadata {
        if let Some(err) = &meta.error {
            return Err(err.to_string());
        }
    }

    Ok(api::format_output(&resp, &cli.search_type))
}

fn main() {
    match run() {
        Ok(output) => print!("{}", output),
        Err(e) => {
            eprintln!("Error: {}", e);
            process::exit(1);
        }
    }
}
