mod api;
mod models;

use clap::{Parser, Subcommand};
use std::process;

#[derive(Parser)]
#[command(name = "volc-gen", about = "Volcengine Ark Content Generation Tool")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Text to Image
    #[command(name = "t2i")]
    TextToImage {
        /// Prompt text
        prompt: String,
        /// Output size preset or exact size, e.g. 16:9, 1:1, 2848x1600
        #[arg(long, default_value = "16:9")]
        size: String,
    },
    /// Image to Image
    #[command(name = "i2i")]
    ImageToImage {
        /// Prompt text
        prompt: String,
        /// Reference image input: local path or data URL
        image_input: String,
        /// Output size preset or exact size, e.g. 16:9, 1:1, 2848x1600
        #[arg(long, default_value = "16:9")]
        size: String,
    },
    /// Image to Video
    #[command(name = "i2v")]
    ImageToVideo {
        /// Motion description
        text: String,
        /// Start image input: local path or data URL
        image_input: String,
    },
    /// Query task(s) or list recent tasks
    #[command(name = "query", alias = "list")]
    Query {
        /// Task ID, page number, or empty for default listing
        arg1: Option<String>,
        /// Page size (when arg1 is a page number)
        arg2: Option<u32>,
    },
}

fn get_api_key() -> String {
    match std::env::var("ARK_API_KEY") {
        Ok(key) if !key.is_empty() => key,
        _ => {
            eprintln!("Error: ARK_API_KEY environment variable is not set.");
            eprintln!("Please set it using: export ARK_API_KEY='your_api_key_here'");
            process::exit(1);
        }
    }
}

fn run() -> Result<String, String> {
    let cli = Cli::parse();
    let api_key = get_api_key();

    match cli.command {
        Commands::TextToImage { prompt, size } => {
            api::text_to_image(&api_key, &prompt, &size)
        }
        Commands::ImageToImage { prompt, image_input, size } => {
            api::image_to_image(&api_key, &prompt, &image_input, &size)
        }
        Commands::ImageToVideo { text, image_input } => {
            api::image_to_video(&api_key, &text, &image_input)
        }
        Commands::Query { arg1, arg2 } => {
            match arg1 {
                None => api::list_tasks(&api_key, 1, 10),
                Some(ref s) if s.parse::<u32>().is_ok() => {
                    let page = s.parse::<u32>().unwrap();
                    let size = arg2.unwrap_or(10);
                    api::list_tasks(&api_key, page, size)
                }
                Some(task_id) => api::query_task(&api_key, &task_id),
            }
        }
    }
}

fn main() {
    match run() {
        Ok(output) => println!("{}", output),
        Err(e) => {
            eprintln!("Error: {}", e);
            process::exit(1);
        }
    }
}
