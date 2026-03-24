use crate::models::{SearchFilter, SearchRequest};

pub fn build_request(
    query: &str,
    count: u32,
    domain_filter: Option<&Vec<String>>,
    block_hosts: Option<&Vec<String>>,
    time_range: Option<&str>,
    auth_level: u32,
) -> SearchRequest {
    let has_filter = domain_filter.is_some() || block_hosts.is_some() || auth_level > 0;
    let filter = if has_filter {
        Some(SearchFilter {
            sites: domain_filter.map(|values| values.join("|")),
            block_hosts: block_hosts.map(|values| values.join("|")),
            auth_info_level: if auth_level > 0 { Some(auth_level) } else { None },
        })
    } else {
        None
    };

    SearchRequest {
        query: query.to_string(),
        search_type: "web".to_string(),
        count,
        need_summary: Some(true),
        filter,
        time_range: time_range.map(|value| value.to_string()),
    }
}
