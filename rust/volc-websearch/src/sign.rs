use chrono::Utc;
use hmac::{Hmac, Mac};
use sha2::{Digest, Sha256};

const SERVICE: &str = "volc_torchlight_api";
const REGION: &str = "cn-beijing";

type HmacSha256 = Hmac<Sha256>;

fn hmac_sha256(key: &[u8], content: &str) -> Vec<u8> {
    let mut mac = HmacSha256::new_from_slice(key).expect("HMAC key error");
    mac.update(content.as_bytes());
    mac.finalize().into_bytes().to_vec()
}

fn hash_sha256(content: &str) -> String {
    let mut hasher = Sha256::new();
    hasher.update(content.as_bytes());
    hex::encode(hasher.finalize())
}

fn norm_query(params: &[(&str, &str)]) -> String {
    let mut sorted: Vec<(&str, &str)> = params.to_vec();
    sorted.sort_by_key(|&(k, _)| k);
    sorted
        .iter()
        .map(|(k, v)| {
            format!(
                "{}={}",
                urlencoding::encode(k),
                urlencoding::encode(v)
            )
        })
        .collect::<Vec<_>>()
        .join("&")
}

pub struct SignedRequest {
    pub url: String,
    pub headers: Vec<(String, String)>,
}

pub fn sign_request(
    ak: &str,
    sk: &str,
    body: &str,
    action: &str,
    version: &str,
    host: &str,
) -> SignedRequest {
    let now = Utc::now();
    let x_date = now.format("%Y%m%dT%H%M%SZ").to_string();
    let short_date = &x_date[..8];
    let x_content_sha256 = hash_sha256(body);
    let content_type = "application/json";

    let query_params = [("Action", action), ("Version", version)];

    let signed_headers_str = "content-type;host;x-content-sha256;x-date";
    let canonical_headers = format!(
        "content-type:{}\nhost:{}\nx-content-sha256:{}\nx-date:{}",
        content_type, host, x_content_sha256, x_date
    );

    let canonical_request = format!(
        "POST\n/\n{}\n{}\n\n{}\n{}",
        norm_query(&query_params),
        canonical_headers,
        signed_headers_str,
        x_content_sha256
    );

    let credential_scope = format!("{}/{}/{}/request", short_date, REGION, SERVICE);
    let string_to_sign = format!(
        "HMAC-SHA256\n{}\n{}\n{}",
        x_date,
        credential_scope,
        hash_sha256(&canonical_request)
    );

    let k_date = hmac_sha256(sk.as_bytes(), short_date);
    let k_region = hmac_sha256(&k_date, REGION);
    let k_service = hmac_sha256(&k_region, SERVICE);
    let k_signing = hmac_sha256(&k_service, "request");
    let signature = hex::encode(hmac_sha256(&k_signing, &string_to_sign));

    let authorization = format!(
        "HMAC-SHA256 Credential={}/{}, SignedHeaders={}, Signature={}",
        ak, credential_scope, signed_headers_str, signature
    );

    let url = format!(
        "https://{}?Action={}&Version={}",
        host, action, version
    );

    SignedRequest {
        url,
        headers: vec![
            ("Content-Type".to_string(), content_type.to_string()),
            ("Host".to_string(), host.to_string()),
            ("X-Date".to_string(), x_date),
            ("X-Content-Sha256".to_string(), x_content_sha256),
            ("Authorization".to_string(), authorization),
        ],
    }
}
