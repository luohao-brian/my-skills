use crate::models::UnifiedSearchResult;

pub fn format_output(results: &[UnifiedSearchResult], time_cost_ms: u128) -> String {
    if results.is_empty() {
        return format!("结果数: 0  耗时: {}ms\n", time_cost_ms);
    }

    let mut lines = vec![format!("结果数: {}  耗时: {}ms\n", results.len(), time_cost_ms)];

    for (idx, item) in results.iter().enumerate() {
        lines.push(format!("[{}] {}", idx + 1, item.title));

        let mut meta = Vec::new();
        if !item.site_name.is_empty() {
            meta.push(item.site_name.as_str());
        }
        if let Some(auth) = &item.auth_info_des {
            if !auth.is_empty() {
                meta.push(auth.as_str());
            }
        }
        meta.push(item.provider.label());
        lines.push(format!("    {}", meta.join(" | ")));

        lines.push(format!("    {}", item.url));
        if !item.summary.is_empty() {
            let truncated: String = item.summary.chars().take(300).collect();
            lines.push(format!("    {}", truncated));
        }
        lines.push(String::new());
    }

    lines.join("\n")
}
