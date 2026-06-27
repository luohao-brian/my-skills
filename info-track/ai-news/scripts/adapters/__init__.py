"""Source adapters for the ai-news skill."""

from __future__ import annotations

from .html_index import fetch_anthropic, fetch_generic_html, fetch_hex2077, fetch_maomu, fetch_tmtpost, fetch_xiaohu
from .json_api import fetch_tensorfeed_json
from .rss import fetch_rss


ADAPTERS = {
    "rss": fetch_rss,
    "tensorfeed_json": fetch_tensorfeed_json,
    "anthropic": fetch_anthropic,
    "tmtpost": fetch_tmtpost,
    "maomu": fetch_maomu,
    "xiaohu": fetch_xiaohu,
    "hex2077": fetch_hex2077,
    "html": fetch_generic_html,
}
