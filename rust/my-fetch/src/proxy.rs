use crate::config::Config;
use reqwest::blocking::Client;
use reqwest::Proxy;
use reqwest::Url;
use std::time::Duration;

pub fn build_client(config: &Config) -> Result<Client, String> {
    let mut builder = Client::builder()
        .timeout(Duration::from_secs(config.timeout_seconds))
        .connect_timeout(Duration::from_secs(config.timeout_seconds.min(10)))
        .redirect(reqwest::redirect::Policy::limited(config.max_redirects))
        .user_agent(config.user_agent.clone())
        .brotli(true)
        .gzip(true)
        .deflate(true);

    if config.http_proxy.is_some() || config.https_proxy.is_some() {
        let http_proxy = config.http_proxy.clone();
        let https_proxy = config.https_proxy.clone();
        let no_proxy_rules = config.no_proxy_rules.clone();
        builder = builder.proxy(Proxy::custom(move |url| {
            if should_bypass_proxy(url, &no_proxy_rules) {
                return None;
            }
            match url.scheme() {
                "https" => https_proxy.clone().or_else(|| http_proxy.clone()),
                _ => http_proxy.clone().or_else(|| https_proxy.clone()),
            }
        }));
    }

    builder.build().map_err(|err| format!("Failed to build HTTP client: {}", err))
}

fn should_bypass_proxy(url: &Url, rules: &[String]) -> bool {
    let host = match url.host_str() {
        Some(value) => value.to_ascii_lowercase(),
        None => return false,
    };
    let port = url.port_or_known_default();
    rules.iter().any(|rule| rule_matches(rule, &host, port))
}

fn rule_matches(rule: &str, host: &str, port: Option<u16>) -> bool {
    if rule == "*" {
        return true;
    }

    let trimmed = rule
        .trim()
        .trim_start_matches("http://")
        .trim_start_matches("https://")
        .trim_end_matches('/');

    if trimmed.is_empty() {
        return false;
    }

    if let Some((rule_host, rule_port)) = trimmed.rsplit_once(':') {
        if let Ok(parsed_port) = rule_port.parse::<u16>() {
            return port == Some(parsed_port) && host_matches(rule_host, host);
        }
    }

    host_matches(trimmed, host)
}

fn host_matches(rule_host: &str, host: &str) -> bool {
    let normalized = rule_host.trim_start_matches('.');
    if normalized.is_empty() {
        return false;
    }
    host == normalized || host.ends_with(&format!(".{}", normalized))
}

#[cfg(test)]
mod tests {
    use super::{host_matches, rule_matches};

    #[test]
    fn matches_exact_and_suffix_hosts() {
        assert!(host_matches("example.com", "example.com"));
        assert!(host_matches("example.com", "api.example.com"));
        assert!(host_matches(".example.com", "api.example.com"));
        assert!(!host_matches("example.com", "example.org"));
    }

    #[test]
    fn matches_port_scoped_rule() {
        assert!(rule_matches("localhost:8080", "localhost", Some(8080)));
        assert!(!rule_matches("localhost:8080", "localhost", Some(3000)));
    }
}
