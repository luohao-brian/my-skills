use crate::config::Config;
use crate::embedding::{cosine_similarity, embed_texts};
use crate::models::UnifiedSearchResult;
use chrono::{DateTime, Duration, NaiveDate, Utc};
use std::collections::HashSet;

pub fn fuse_results(config: &Config, mut results: Vec<UnifiedSearchResult>) -> Result<Vec<UnifiedSearchResult>, String> {
    results.retain(|item| !item.url.trim().is_empty() && !item.title.trim().is_empty());
    apply_filters(config, &mut results);
    dedup_by_url(&mut results);
    if results.is_empty() {
        return Ok(Vec::new());
    }

    let mut texts = Vec::with_capacity(results.len() + 1);
    texts.push(config.query.clone());
    texts.extend(results.iter().map(embedding_text));
    let embeddings = embed_texts(&config.embedding, &texts)?;
    let query_embedding = &embeddings[0];
    let item_embeddings = &embeddings[1..];

    for (item, embedding) in results.iter_mut().zip(item_embeddings.iter()) {
        let semantic_score = cosine_similarity(query_embedding, embedding);
        let rank_bonus = 1.0 / (item.raw_rank as f32);
        let authority_bonus = if item.auth_info_des.is_some() && config.auth_level > 0 {
            0.05
        } else {
            0.0
        };
        item.fused_score = semantic_score * 0.65 + item.provider_score * 0.25 + rank_bonus * 0.10 + authority_bonus;
    }

    dedup_by_embedding(&mut results, item_embeddings, 0.92);
    results.sort_by(|left, right| {
        right
            .fused_score
            .partial_cmp(&left.fused_score)
            .unwrap_or(std::cmp::Ordering::Equal)
    });
    results.truncate(config.count);
    Ok(results)
}

fn embedding_text(item: &UnifiedSearchResult) -> String {
    format!("{}\n{}\n{}", item.title, item.site_name, item.summary)
}

fn apply_filters(config: &Config, results: &mut Vec<UnifiedSearchResult>) {
    if let Some(sites) = &config.sites {
        results.retain(|item| host_matches(&item.url, sites));
    }
    if let Some(block_hosts) = &config.block_hosts {
        results.retain(|item| !host_matches(&item.url, block_hosts));
    }
    if let Some(time_range) = &config.time_range {
        results.retain(|item| matches_time_range(item.published_at.as_deref(), time_range));
    }
}

fn dedup_by_url(results: &mut Vec<UnifiedSearchResult>) {
    let mut seen = HashSet::new();
    results.retain(|item| seen.insert(normalize_url(&item.url)));
}

fn dedup_by_embedding(
    results: &mut Vec<UnifiedSearchResult>,
    embeddings: &[Vec<f32>],
    threshold: f32,
) {
    let mut keep = vec![true; results.len()];
    for i in 0..results.len() {
        if !keep[i] {
            continue;
        }
        for j in (i + 1)..results.len() {
            if !keep[j] {
                continue;
            }
            if cosine_similarity(&embeddings[i], &embeddings[j]) >= threshold {
                if results[i].fused_score >= results[j].fused_score {
                    keep[j] = false;
                } else {
                    keep[i] = false;
                    break;
                }
            }
        }
    }

    let mut idx = 0usize;
    results.retain(|_| {
        let should_keep = keep[idx];
        idx += 1;
        should_keep
    });
}

fn normalize_url(value: &str) -> String {
    if let Ok(mut url) = url::Url::parse(value) {
        let _ = url.set_username("");
        let _ = url.set_password(None);
        url.set_fragment(None);
        let _ = url.set_scheme(&url.scheme().to_ascii_lowercase());
        if let Some(host) = url.host_str().map(|host| host.to_ascii_lowercase()) {
            let _ = url.set_host(Some(&host));
        }
        if url.path().ends_with('/') && url.path() != "/" {
            let trimmed = url.path().trim_end_matches('/').to_string();
            url.set_path(&trimmed);
        }
        return url.to_string();
    }
    value.trim().to_ascii_lowercase()
}

fn host_matches(url: &str, domains: &[String]) -> bool {
    let host = url::Url::parse(url)
        .ok()
        .and_then(|parsed| parsed.host_str().map(|host| host.to_ascii_lowercase()));
    let Some(host) = host else {
        return false;
    };

    domains.iter().any(|domain| host == *domain || host.ends_with(&format!(".{}", domain)))
}

fn matches_time_range(published_at: Option<&str>, range: &str) -> bool {
    let Some(timestamp) = published_at.and_then(parse_datetime) else {
        return true;
    };
    let now = Utc::now();
    match range {
        "OneDay" => timestamp >= now - Duration::days(1),
        "OneWeek" => timestamp >= now - Duration::weeks(1),
        "OneMonth" => timestamp >= now - Duration::days(30),
        "OneYear" => timestamp >= now - Duration::days(365),
        _ => {
            let parts: Vec<&str> = range.splitn(2, "..").collect();
            if parts.len() != 2 {
                return true;
            }
            let start = NaiveDate::parse_from_str(parts[0], "%Y-%m-%d").ok();
            let end = NaiveDate::parse_from_str(parts[1], "%Y-%m-%d").ok();
            match (start, end) {
                (Some(start), Some(end)) => {
                    let day = timestamp.date_naive();
                    day >= start && day <= end
                }
                _ => true,
            }
        }
    }
}

fn parse_datetime(value: &str) -> Option<DateTime<Utc>> {
    DateTime::parse_from_rfc3339(value)
        .map(|dt| dt.with_timezone(&Utc))
        .ok()
        .or_else(|| DateTime::parse_from_rfc2822(value).map(|dt| dt.with_timezone(&Utc)).ok())
        .or_else(|| {
            NaiveDate::parse_from_str(value, "%Y-%m-%d")
                .ok()
                .and_then(|date| date.and_hms_opt(0, 0, 0))
                .map(|dt| DateTime::<Utc>::from_naive_utc_and_offset(dt, Utc))
        })
}
