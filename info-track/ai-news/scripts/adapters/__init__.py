"""Source adapters for the ai-news skill.

ADAPTERS is keyed by the source `kind` declared in references/sources.json,
so adding or removing a source never requires dispatch changes here.
"""

from __future__ import annotations

from .html_index import fetch_anthropic, fetch_generic_html, fetch_hex2077, fetch_maomu, fetch_tmtpost
from .json_api import fetch_json_articles
from .rss import fetch_rss


ADAPTERS = {
    "rss": fetch_rss,
    "json": fetch_json_articles,
    "html_index": fetch_generic_html,
    "html_daily": fetch_hex2077,
    "anthropic_list": fetch_anthropic,
    "tmtpost_daily": fetch_tmtpost,
    "maomu_timeline": fetch_maomu,
}
