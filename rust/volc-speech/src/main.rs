mod api;
mod config;
mod models;

use clap::{Args, Parser, Subcommand};
use models::{SttOptions, TtsOptions};
use std::process;

#[derive(Parser)]
#[command(
    name = "volc-speech",
    about = "Volcengine speech synthesis and recognition tool"
)]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Text to Speech
    #[command(name = "tts")]
    Tts(TtsArgs),
    /// Speech to Text
    #[command(name = "stt")]
    Stt(SttArgs),
}

#[derive(Args, Debug)]
struct TtsArgs {
    /// Input text to synthesize
    text: String,
    /// Speaker / voice name
    #[arg(long, default_value = "zh_female_cancan_mars_bigtts")]
    speaker: String,
    /// Output audio format
    #[arg(long, default_value = "mp3")]
    format: String,
    /// Output sample rate
    #[arg(long, default_value_t = 24_000)]
    sample_rate: u32,
    /// Optional emotion label, e.g. happy/sad/angry
    #[arg(long)]
    emotion: Option<String>,
    /// Emotion intensity from 1 to 5
    #[arg(long)]
    emotion_scale: Option<u8>,
    /// Speech rate in the official V3 scale [-50, 100]
    #[arg(long, visible_alias = "speed-ratio", default_value_t = 0)]
    speech_rate: i32,
    /// Loudness rate in the official V3 scale [-50, 100]
    #[arg(long, visible_alias = "volume-ratio", default_value_t = 0)]
    loudness_rate: i32,
    /// Output file path
    #[arg(long)]
    output: Option<String>,
    /// User id passed to the API
    #[arg(long, default_value = "demo_user")]
    uid: String,
}

#[derive(Args, Debug)]
struct SttArgs {
    /// Local audio file path
    file: String,
    /// Audio container format; defaults to extension-based inference
    #[arg(long)]
    format: Option<String>,
    /// Audio codec; defaults to a format-based inference
    #[arg(long)]
    codec: Option<String>,
    /// Audio sample rate
    #[arg(long, default_value_t = 16_000)]
    rate: u32,
    /// Audio bit depth
    #[arg(long, default_value_t = 16)]
    bits: u16,
    /// Audio channel count
    #[arg(long, default_value_t = 1)]
    channels: u16,
    /// Delay in milliseconds between audio packets
    #[arg(long, default_value_t = 200)]
    seg_duration: u64,
    /// Include the final raw payload in the JSON output
    #[arg(long)]
    json: bool,
    /// User id passed to the API
    #[arg(long, default_value = "demo_user")]
    uid: String,
}

fn run() -> Result<String, String> {
    let cli = Cli::parse();

    match cli.command {
        Commands::Tts(args) => {
            let env = config::load_tts_env()?;
            let options = TtsOptions {
                text: args.text,
                speaker: args.speaker,
                format: args.format,
                sample_rate: args.sample_rate,
                emotion: args.emotion,
                emotion_scale: args.emotion_scale,
                speech_rate: args.speech_rate,
                loudness_rate: args.loudness_rate,
                output: args.output,
                uid: args.uid,
            };
            api::synthesize(&env, &options)
        }
        Commands::Stt(args) => {
            let env = config::load_stt_env()?;
            let audio_format = args
                .format
                .unwrap_or_else(|| api::infer_audio_format(&args.file));
            let codec = args
                .codec
                .unwrap_or_else(|| api::infer_codec(&audio_format));
            let options = SttOptions {
                file_path: args.file,
                audio_format,
                codec,
                rate: args.rate,
                bits: args.bits,
                channels: args.channels,
                seg_duration_ms: args.seg_duration,
                json_output: args.json,
                uid: args.uid,
            };
            api::transcribe(&env, &options)
        }
    }
}

fn main() {
    match run() {
        Ok(output) => println!("{}", output),
        Err(err) => {
            eprintln!("Error: {}", err);
            process::exit(1);
        }
    }
}
