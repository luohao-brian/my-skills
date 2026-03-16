use crate::config::EmbeddingConfig;
use serde::{Deserialize, Serialize};

#[derive(Serialize)]
struct EmbeddingRequest<'a> {
    model: &'a str,
    input: Vec<&'a str>,
}

#[derive(Deserialize)]
struct EmbeddingResponse {
    data: Vec<EmbeddingDatum>,
}

#[derive(Deserialize)]
struct EmbeddingDatum {
    embedding: Vec<f32>,
}

pub fn embed_texts(config: &EmbeddingConfig, texts: &[String]) -> Result<Vec<Vec<f32>>, String> {
    if config.provider != "openai" {
        return Err(format!(
            "Unsupported SEARCH_EMBEDDING_PROVIDER: {}",
            config.provider
        ));
    }

    let endpoint = format!("{}/embeddings", config.base_url.trim_end_matches('/'));
    let input = texts.iter().map(|text| text.as_str()).collect::<Vec<_>>();
    let body = EmbeddingRequest {
        model: &config.model,
        input,
    };

    let resp = ureq::post(&endpoint)
        .set("Content-Type", "application/json")
        .set("Authorization", &format!("Bearer {}", config.api_key))
        .send_json(ureq::json!(body))
        .map_err(|e| format!("Embedding request failed: {}", e))?;

    let parsed: EmbeddingResponse = resp
        .into_json()
        .map_err(|e| format!("Embedding response parse failed: {}", e))?;

    if parsed.data.len() != texts.len() {
        return Err(format!(
            "Embedding response size mismatch: expected {}, got {}",
            texts.len(),
            parsed.data.len()
        ));
    }

    Ok(parsed.data.into_iter().map(|item| item.embedding).collect())
}

pub fn cosine_similarity(a: &[f32], b: &[f32]) -> f32 {
    if a.is_empty() || b.is_empty() || a.len() != b.len() {
        return 0.0;
    }
    let mut dot = 0.0f32;
    let mut norm_a = 0.0f32;
    let mut norm_b = 0.0f32;
    for (left, right) in a.iter().zip(b.iter()) {
        dot += left * right;
        norm_a += left * left;
        norm_b += right * right;
    }
    if norm_a == 0.0 || norm_b == 0.0 {
        return 0.0;
    }
    dot / (norm_a.sqrt() * norm_b.sqrt())
}
