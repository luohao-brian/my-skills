pub const DEFAULT_TTS_RESOURCE_ID: &str = "volc.service_type.10029";
pub const DEFAULT_STT_RESOURCE_ID: &str = "volc.seedasr.sauc.duration";

#[derive(Debug, Clone)]
pub struct TtsEnv {
    pub app_id: String,
    pub access_key: String,
    pub resource_id: String,
}

#[derive(Debug, Clone)]
pub struct SttEnv {
    pub app_id: String,
    pub access_key: String,
    pub resource_id: String,
}

pub fn load_tts_env() -> Result<TtsEnv, String> {
    Ok(TtsEnv {
        app_id: required_env(&["VOLC_TTS_APP_ID", "VOLC_AUDIO_APP_ID", "TTS_APP_ID"])?,
        access_key: required_env(&[
            "VOLC_TTS_ACCESS_KEY",
            "VOLC_AUDIO_ACCESS_KEY",
            "TTS_ACCESS_KEY",
        ])?,
        resource_id: optional_env(&[
            "VOLC_TTS_RESOURCE_ID",
            "VOLC_AUDIO_RESOURCE_ID",
            "TTS_RESOURCE_ID",
        ])
        .unwrap_or_else(|| DEFAULT_TTS_RESOURCE_ID.to_string()),
    })
}

pub fn load_stt_env() -> Result<SttEnv, String> {
    Ok(SttEnv {
        app_id: required_env(&["VOLC_STT_APP_ID", "VOLC_AUDIO_APP_ID", "VOLC_APP_ID"])?,
        access_key: required_env(&[
            "VOLC_STT_ACCESS_KEY",
            "VOLC_AUDIO_ACCESS_KEY",
            "VOLC_ACCESS_KEY",
        ])?,
        resource_id: optional_env(&[
            "VOLC_STT_RESOURCE_ID",
            "VOLC_AUDIO_RESOURCE_ID",
            "VOLC_RESOURCE_ID",
        ])
        .unwrap_or_else(|| DEFAULT_STT_RESOURCE_ID.to_string()),
    })
}

fn required_env(names: &[&str]) -> Result<String, String> {
    optional_env(names).ok_or_else(|| {
        format!(
            "Missing required environment variable. Set one of: {}",
            names.join(", ")
        )
    })
}

fn optional_env(names: &[&str]) -> Option<String> {
    names.iter().find_map(|name| {
        std::env::var(name)
            .ok()
            .map(|value| value.trim().to_string())
            .filter(|value| !value.is_empty())
    })
}
