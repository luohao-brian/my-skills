mod api;
mod config;
mod models;
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

    let results = providers::fetch_selected(&config)?;

    Ok(format!("结果数: {} 耗时: {}ms\n\n{}",
        results.len(),
        started_at.elapsed().as_millis(),
        providers::format_raw_results(&results)
    ))
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
