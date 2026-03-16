mod api;
mod config;
mod embedding;
mod fusion;
mod models;
mod output;
mod providers;
mod sign;

use clap::Parser;
use config::{Cli, Config};
use std::process;
use std::time::Instant;

fn run() -> Result<String, String> {
    let cli = Cli::parse();
    let config = Config::from_env_and_cli(cli)?;
    let started_at = Instant::now();

    let provider_results = providers::fetch_all(&config)?;
    let fused_results = fusion::fuse_results(&config, provider_results)?;

    Ok(output::format_output(&fused_results, started_at.elapsed().as_millis()))
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
