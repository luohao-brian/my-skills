mod classify;
mod config;
mod extract;
mod fetch;
mod models;
mod proxy;

use clap::Parser;
use config::{Cli, Config, JinaMode};
use extract::process_raw_fetch;
use fetch::{fetch_via_jina, fetch_with_fallback};
use models::WebFetchPayload;
use std::process;

fn run() -> Result<String, String> {
    let cli = Cli::parse();
    let config = Config::from_env_and_cli(cli)?;
    let client = proxy::build_client(&config)?;

    let mut outcome = fetch_with_fallback(&client, &config)?;
    let mut payload = process_raw_fetch(
        &config,
        outcome.raw,
        outcome.fallback_chain.clone(),
        outcome.extractor_hint,
    )?;

    if config.jina_mode == JinaMode::Auto && payload.empty {
        if let Ok(jina_raw) = fetch_via_jina(&client, &config) {
            outcome.fallback_chain = vec!["direct_fetch".to_string(), "jina_reader".to_string()];
            payload = process_raw_fetch(
                &config,
                jina_raw,
                outcome.fallback_chain,
                Some(models::Extractor::JinaReader),
            )?;
        }
    }

    if payload.status >= 400 {
        return Err(format!("web_fetch HTTP {}: {}", payload.status, payload.url));
    }

    Ok(format_payload(payload))
}

fn format_payload(payload: WebFetchPayload) -> String {
    let mut lines = vec!["[web_fetch]".to_string()];
    lines.push(format!("url: {}", payload.url));
    if payload.final_url != payload.url {
        lines.push(format!("final_url: {}", payload.final_url));
    }
    lines.push(format!("status: {}", payload.status));
    if let Some(content_type) = payload.content_type {
        lines.push(format!("content_type: {}", content_type));
    }
    lines.push(format!("extract_mode: {}", payload.extract_mode));
    lines.push(format!("extractor: {}", payload.extractor));
    if let Some(title) = payload.title {
        lines.push(format!("title: {}", title));
    }
    if payload.truncated {
        lines.push(format!("truncated: true (original {} chars)", payload.raw_length));
    }
    if let Some(warning) = payload.warning {
        lines.push(format!("warning: {}", warning));
    }

    let body = if payload.empty {
        "(no content)".to_string()
    } else {
        payload.text
    };
    format!("{}\n\n{}", lines.join("\n"), body)
}

fn main() {
    match run() {
        Ok(output) => print!("{}", output),
        Err(err) => {
            eprintln!("Error: {}", err);
            process::exit(1);
        }
    }
}
