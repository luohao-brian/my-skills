#!/usr/bin/env python3
"""Install, uninstall, and configure the Hermes Ark plugin."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

PLUGIN_ID = "ark"
DEFAULT_API_KEY_ENV = "VOLC_AGENT_PLAN_API_KEY"
DEFAULT_TTS_VOICE = "zh_female_vv_uranus_bigtts"

TTS_VOICES = [
    {"alias": "vivi", "id": "zh_female_vv_uranus_bigtts", "label": "Vivi 2.0", "language": "语种：中文、日文、印尼、墨西哥西班牙语 方言：四川、陕西、东北", "style": "通用场景"},
    {"alias": "xiaohe", "id": "zh_female_xiaohe_uranus_bigtts", "label": "小何 2.0", "language": "中文", "style": "通用场景"},
    {"alias": "yunzhou", "id": "zh_male_m191_uranus_bigtts", "label": "云舟 2.0", "language": "中文", "style": "通用场景"},
    {"alias": "xiaotian", "id": "zh_male_taocheng_uranus_bigtts", "label": "小天 2.0", "language": "中文", "style": "通用场景"},
    {"alias": "liufei", "id": "zh_male_liufei_uranus_bigtts", "label": "刘飞 2.0", "language": "中文", "style": "通用场景"},
    {"alias": "sophie", "id": "zh_female_sophie_uranus_bigtts", "label": "魅力苏菲 2.0", "language": "中文", "style": "通用场景"},
    {"alias": "qingxinnvsheng", "id": "zh_female_qingxinnvsheng_uranus_bigtts", "label": "清新女声 2.0", "language": "中文", "style": "通用场景"},
    {"alias": "cancan", "id": "zh_female_cancan_uranus_bigtts", "label": "知性灿灿 2.0", "language": "中文", "style": "角色扮演"},
    {"alias": "sajiaoxuemei", "id": "zh_female_sajiaoxuemei_uranus_bigtts", "label": "撒娇学妹 2.0", "language": "中文", "style": "角色扮演"},
    {"alias": "tianmeixiaoyuan", "id": "zh_female_tianmeixiaoyuan_uranus_bigtts", "label": "甜美小源 2.0", "language": "中文", "style": "通用场景"},
    {"alias": "tianmeitaozi", "id": "zh_female_tianmeitaozi_uranus_bigtts", "label": "甜美桃子 2.0", "language": "中文", "style": "通用场景"},
    {"alias": "shuangkuaisisi", "id": "zh_female_shuangkuaisisi_uranus_bigtts", "label": "爽快思思 2.0", "language": "中文", "style": "通用场景"},
    {"alias": "peiqi", "id": "zh_female_peiqi_uranus_bigtts", "label": "佩奇猪 2.0", "language": "中文", "style": "视频配音"},
    {"alias": "linjianvhai", "id": "zh_female_linjianvhai_uranus_bigtts", "label": "邻家女孩 2.0", "language": "中文", "style": "通用场景"},
    {"alias": "shaonianzixin", "id": "zh_male_shaonianzixin_uranus_bigtts", "label": "少年梓辛/Brayan 2.0", "language": "中文", "style": "通用场景"},
    {"alias": "sunwukong", "id": "zh_male_sunwukong_uranus_bigtts", "label": "猴哥 2.0", "language": "中文", "style": "视频配音"},
    {"alias": "yingyujiaoxue", "id": "zh_female_yingyujiaoxue_uranus_bigtts", "label": "Tina老师 2.0", "language": "中文、英式英语", "style": "教育场景"},
    {"alias": "kefunvsheng", "id": "zh_female_kefunvsheng_uranus_bigtts", "label": "暖阳女声 2.0", "language": "中文", "style": "客服场景"},
    {"alias": "xiaoxue", "id": "zh_female_xiaoxue_uranus_bigtts", "label": "儿童绘本 2.0", "language": "中文", "style": "有声阅读"},
    {"alias": "dayi", "id": "zh_male_dayi_uranus_bigtts", "label": "大壹 2.0", "language": "中文", "style": "视频配音"},
    {"alias": "mizai", "id": "zh_female_mizai_uranus_bigtts", "label": "黑猫侦探社咪仔 2.0", "language": "中文", "style": "视频配音"},
    {"alias": "jitangnv", "id": "zh_female_jitangnv_uranus_bigtts", "label": "鸡汤女 2.0", "language": "中文", "style": "视频配音"},
    {"alias": "meilinvyou", "id": "zh_female_meilinvyou_uranus_bigtts", "label": "魅力女友 2.0", "language": "中文", "style": "通用场景"},
    {"alias": "liuchangnv", "id": "zh_female_liuchangnv_uranus_bigtts", "label": "流畅女声 2.0", "language": "中文", "style": "视频配音"},
    {"alias": "ruyayichen", "id": "zh_male_ruyayichen_uranus_bigtts", "label": "儒雅逸辰 2.0", "language": "中文", "style": "视频配音"},
    {"alias": "tim", "id": "en_male_tim_uranus_bigtts", "label": "Tim", "language": "美式英语", "style": "多语种"},
    {"alias": "dacey", "id": "en_female_dacey_uranus_bigtts", "label": "Dacey", "language": "美式英语", "style": "多语种"},
    {"alias": "stokie", "id": "en_female_stokie_uranus_bigtts", "label": "Stokie", "language": "美式英语", "style": "多语种"},
    {"alias": "wenroumama", "id": "zh_female_wenroumama_uranus_bigtts", "label": "温柔妈妈 2.0", "language": "中文", "style": "通用场景"},
    {"alias": "jieshuoxiaoming", "id": "zh_male_jieshuoxiaoming_uranus_bigtts", "label": "解说小明 2.0", "language": "中文", "style": "通用场景"},
    {"alias": "tvbnv", "id": "zh_female_tvbnv_uranus_bigtts", "label": "TVB女声 2.0", "language": "中文", "style": "通用场景"},
    {"alias": "yizhipiannan", "id": "zh_male_yizhipiannan_uranus_bigtts", "label": "译制片男 2.0", "language": "中文", "style": "通用场景"},
    {"alias": "qiaopinv", "id": "zh_female_qiaopinv_uranus_bigtts", "label": "俏皮女声 2.0", "language": "中文", "style": "通用场景"},
    {"alias": "zhishuaiyingzi", "id": "zh_female_zhishuaiyingzi_uranus_bigtts", "label": "直率英子 2.0", "language": "中文", "style": "角色扮演"},
    {"alias": "linjiananhai", "id": "zh_male_linjiananhai_uranus_bigtts", "label": "邻家男孩 2.0", "language": "中文", "style": "通用场景"},
    {"alias": "silang", "id": "zh_male_silang_uranus_bigtts", "label": "四郎 2.0", "language": "中文", "style": "角色扮演"},
    {"alias": "ruyaqingnian", "id": "zh_male_ruyaqingnian_uranus_bigtts", "label": "儒雅青年 2.0", "language": "中文", "style": "通用场景"},
    {"alias": "qingcang", "id": "zh_male_qingcang_uranus_bigtts", "label": "擎苍 2.0", "language": "中文", "style": "角色扮演"},
    {"alias": "xionger", "id": "zh_male_xionger_uranus_bigtts", "label": "熊二 2.0", "language": "中文", "style": "角色扮演"},
    {"alias": "yingtaowanzi", "id": "zh_female_yingtaowanzi_uranus_bigtts", "label": "樱桃丸子 2.0", "language": "中文", "style": "角色扮演"},
    {"alias": "wennuanahu", "id": "zh_male_wennuanahu_uranus_bigtts", "label": "温暖阿虎/Alvin 2.0", "language": "中文", "style": "通用场景"},
    {"alias": "naiqimengwa", "id": "zh_male_naiqimengwa_uranus_bigtts", "label": "奶气萌娃 2.0", "language": "中文", "style": "通用场景"},
    {"alias": "popo", "id": "zh_female_popo_uranus_bigtts", "label": "婆婆 2.0", "language": "中文", "style": "通用场景"},
    {"alias": "gaolengyujie", "id": "zh_female_gaolengyujie_uranus_bigtts", "label": "高冷御姐 2.0", "language": "中文", "style": "通用场景"},
    {"alias": "aojiaobazong", "id": "zh_male_aojiaobazong_uranus_bigtts", "label": "傲娇霸总 2.0", "language": "中文", "style": "通用场景"},
    {"alias": "lanyinmianbao", "id": "zh_male_lanyinmianbao_uranus_bigtts", "label": "懒音绵宝 2.0", "language": "中文", "style": "角色扮演"},
    {"alias": "fanjuanqingnian", "id": "zh_male_fanjuanqingnian_uranus_bigtts", "label": "反卷青年 2.0", "language": "中文", "style": "通用场景"},
    {"alias": "wenroushunv", "id": "zh_female_wenroushunv_uranus_bigtts", "label": "温柔淑女 2.0", "language": "中文", "style": "通用场景"},
    {"alias": "gufengshaoyu", "id": "zh_female_gufengshaoyu_uranus_bigtts", "label": "古风少御 2.0", "language": "中文", "style": "角色扮演"},
    {"alias": "huolixiaoge", "id": "zh_male_huolixiaoge_uranus_bigtts", "label": "活力小哥 2.0", "language": "中文", "style": "通用场景"},
    {"alias": "baqiqingshu", "id": "zh_male_baqiqingshu_uranus_bigtts", "label": "霸气青叔 2.0", "language": "中文", "style": "有声阅读"},
    {"alias": "xuanyijieshuo", "id": "zh_male_xuanyijieshuo_uranus_bigtts", "label": "悬疑解说 2.0", "language": "中文", "style": "有声阅读"},
    {"alias": "mengyatou", "id": "zh_female_mengyatou_uranus_bigtts", "label": "萌丫头/Cutey 2.0", "language": "中文", "style": "通用场景"},
    {"alias": "tiexinnvsheng", "id": "zh_female_tiexinnvsheng_uranus_bigtts", "label": "贴心女声/Candy 2.0", "language": "中文", "style": "通用场景"},
    {"alias": "jitangmei", "id": "zh_female_jitangmei_uranus_bigtts", "label": "鸡汤妹妹/Hope 2.0", "language": "中文", "style": "通用场景"},
    {"alias": "cixingjieshuonan", "id": "zh_male_cixingjieshuonan_uranus_bigtts", "label": "磁性解说男声/Morgan 2.0", "language": "中文", "style": "通用场景"},
    {"alias": "liangsangmengzai", "id": "zh_male_liangsangmengzai_uranus_bigtts", "label": "亮嗓萌仔 2.0", "language": "中文", "style": "通用场景"},
    {"alias": "kailangjiejie", "id": "zh_female_kailangjiejie_uranus_bigtts", "label": "开朗姐姐 2.0", "language": "中文", "style": "通用场景"},
    {"alias": "gaolengchenwen", "id": "zh_male_gaolengchenwen_uranus_bigtts", "label": "高冷沉稳 2.0", "language": "中文", "style": "通用场景"},
    {"alias": "shenyeboke", "id": "zh_male_shenyeboke_uranus_bigtts", "label": "深夜播客 2.0", "language": "中文", "style": "通用场景"},
    {"alias": "lubanqihao", "id": "zh_male_lubanqihao_uranus_bigtts", "label": "鲁班七号 2.0", "language": "中文", "style": "角色扮演"},
    {"alias": "jiaochuannv", "id": "zh_female_jiaochuannv_uranus_bigtts", "label": "娇喘女声 2.0", "language": "中文", "style": "通用场景"},
    {"alias": "linxiao", "id": "zh_female_linxiao_uranus_bigtts", "label": "林潇 2.0", "language": "中文", "style": "角色扮演"},
    {"alias": "lingling", "id": "zh_female_lingling_uranus_bigtts", "label": "玲玲姐姐 2.0", "language": "中文", "style": "角色扮演"},
    {"alias": "chunribu", "id": "zh_female_chunribu_uranus_bigtts", "label": "春日部姐姐 2.0", "language": "中文", "style": "角色扮演"},
    {"alias": "tangseng", "id": "zh_male_tangseng_uranus_bigtts", "label": "唐僧 2.0", "language": "中文", "style": "角色扮演"},
    {"alias": "zhuangzhou", "id": "zh_male_zhuangzhou_uranus_bigtts", "label": "庄周 2.0", "language": "中文", "style": "角色扮演"},
    {"alias": "kailangdidi", "id": "zh_male_kailangdidi_uranus_bigtts", "label": "开朗弟弟 2.0", "language": "中文", "style": "通用场景"},
    {"alias": "zhubajie", "id": "zh_male_zhubajie_uranus_bigtts", "label": "猪八戒 2.0", "language": "中文", "style": "角色扮演"},
    {"alias": "ganmaodianyin", "id": "zh_female_ganmaodianyin_uranus_bigtts", "label": "感冒电音姐姐 2.0", "language": "中文", "style": "角色扮演"},
    {"alias": "chanmeinv", "id": "zh_female_chanmeinv_uranus_bigtts", "label": "谄媚女声 2.0", "language": "中文", "style": "通用场景"},
    {"alias": "nvleishen", "id": "zh_female_nvleishen_uranus_bigtts", "label": "女雷神 2.0", "language": "中文", "style": "角色扮演"},
    {"alias": "qinqienv", "id": "zh_female_qinqienv_uranus_bigtts", "label": "亲切女声 2.0", "language": "中文", "style": "通用场景"},
    {"alias": "kuailexiaodong", "id": "zh_male_kuailexiaodong_uranus_bigtts", "label": "快乐小东 2.0", "language": "中文", "style": "通用场景"},
    {"alias": "kailangxuezhang", "id": "zh_male_kailangxuezhang_uranus_bigtts", "label": "开朗学长 2.0", "language": "中文", "style": "通用场景"},
    {"alias": "youyoujunzi", "id": "zh_male_youyoujunzi_uranus_bigtts", "label": "悠悠君子 2.0", "language": "中文", "style": "通用场景"},
    {"alias": "wenjingmaomao", "id": "zh_female_wenjingmaomao_uranus_bigtts", "label": "文静毛毛 2.0", "language": "中文", "style": "通用场景"},
    {"alias": "zhixingnv", "id": "zh_female_zhixingnv_uranus_bigtts", "label": "知性女声 2.0", "language": "中文", "style": "通用场景"},
    {"alias": "qingshuangnanda", "id": "zh_male_qingshuangnanda_uranus_bigtts", "label": "清爽男大 2.0", "language": "中文", "style": "通用场景"},
    {"alias": "yuanboxiaoshu", "id": "zh_male_yuanboxiaoshu_uranus_bigtts", "label": "渊博小叔 2.0", "language": "中文", "style": "通用场景"},
    {"alias": "yangguangqingnian", "id": "zh_male_yangguangqingnian_uranus_bigtts", "label": "阳光青年 2.0", "language": "中文", "style": "通用场景"},
    {"alias": "qingchezizi", "id": "zh_female_qingchezizi_uranus_bigtts", "label": "清澈梓梓 2.0", "language": "中文", "style": "通用场景"},
    {"alias": "tianmeiyueyue", "id": "zh_female_tianmeiyueyue_uranus_bigtts", "label": "甜美悦悦 2.0", "language": "中文", "style": "通用场景"},
    {"alias": "xinlingjitang", "id": "zh_female_xinlingjitang_uranus_bigtts", "label": "心灵鸡汤 2.0", "language": "中文", "style": "通用场景"},
    {"alias": "wenrouxiaoge", "id": "zh_male_wenrouxiaoge_uranus_bigtts", "label": "温柔小哥 2.0", "language": "中文", "style": "通用场景"},
    {"alias": "roumeinvyou", "id": "zh_female_roumeinvyou_uranus_bigtts", "label": "柔美女友 2.0", "language": "中文", "style": "通用场景"},
    {"alias": "dongfanghaoran", "id": "zh_male_dongfanghaoran_uranus_bigtts", "label": "东方浩然 2.0", "language": "中文", "style": "通用场景"},
    {"alias": "wenrouxiaoya", "id": "zh_female_wenrouxiaoya_uranus_bigtts", "label": "温柔小雅 2.0", "language": "中文", "style": "通用场景"},
    {"alias": "tiancaitongsheng", "id": "zh_male_tiancaitongsheng_uranus_bigtts", "label": "天才童声 2.0", "language": "中文", "style": "通用场景"},
    {"alias": "wuzetian", "id": "zh_female_wuzetian_uranus_bigtts", "label": "武则天 2.0", "language": "中文", "style": "角色扮演"},
    {"alias": "gujie", "id": "zh_female_gujie_uranus_bigtts", "label": "顾姐 2.0", "language": "中文", "style": "角色扮演"},
    {"alias": "guanggaojieshuo", "id": "zh_male_guanggaojieshuo_uranus_bigtts", "label": "广告解说 2.0", "language": "中文", "style": "通用场景"},
    {"alias": "shaoergushi", "id": "zh_female_shaoergushi_uranus_bigtts", "label": "少儿故事 2.0", "language": "中文", "style": "有声阅读"},
]

_TTS_VOICE_BY_ALIAS = {item["alias"]: item for item in TTS_VOICES}
_TTS_VOICE_BY_ID = {item["id"]: item for item in TTS_VOICES}


def _repo_root() -> Path:
    return Path(__file__).resolve().parent


def _hermes_home() -> Path:
    return Path(os.getenv("HERMES_HOME", str(Path.home() / ".hermes"))).expanduser()


def _plugin_target() -> Path:
    return _hermes_home() / "plugins" / PLUGIN_ID


def _resolve_tts_voice(value: str | None) -> str:
    raw = (value or "").strip()
    if not raw:
        return DEFAULT_TTS_VOICE
    return _TTS_VOICE_BY_ALIAS.get(raw, {}).get("id", raw)


def _voice_display(voice_id: str | None) -> str:
    voice = _TTS_VOICE_BY_ID.get(str(voice_id or ""))
    if not voice:
        return str(voice_id or "")
    return f"{voice['id']} ({voice['alias']} / {voice['label']})"


def _load_effective_config() -> dict[str, Any]:
    try:
        from hermes_cli.config import load_config
    except Exception as exc:
        raise SystemExit(
            "Could not import hermes_cli.config. Run this CLI with Hermes' "
            f"Python environment. Import error: {exc}"
        ) from exc
    return load_config()


def _load_raw_config_pair() -> tuple[dict[str, Any], Any]:
    try:
        from hermes_cli.config import get_config_path, read_raw_config
        from utils import atomic_yaml_write
    except Exception as exc:
        raise SystemExit(
            "Could not import Hermes config helpers. Run this CLI with Hermes' "
            f"Python environment. Import error: {exc}"
        ) from exc
    return read_raw_config(), lambda data: atomic_yaml_write(get_config_path(), data, sort_keys=False)


def _ensure_plugins_section(config: dict[str, Any]) -> dict[str, Any]:
    plugins = config.setdefault("plugins", {})
    if not isinstance(plugins, dict):
        plugins = {}
        config["plugins"] = plugins
    plugins.setdefault("enabled", [])
    plugins.setdefault("disabled", [])
    plugins.setdefault("entries", {})
    return plugins


def _enable_plugin(config: dict[str, Any]) -> None:
    plugins = _ensure_plugins_section(config)
    enabled = plugins.get("enabled")
    if not isinstance(enabled, list):
        enabled = []
        plugins["enabled"] = enabled
    if PLUGIN_ID not in enabled:
        enabled.append(PLUGIN_ID)
        enabled.sort()
    disabled = plugins.get("disabled")
    if isinstance(disabled, list) and PLUGIN_ID in disabled:
        plugins["disabled"] = [item for item in disabled if item != PLUGIN_ID]


def _disable_plugin(config: dict[str, Any]) -> None:
    plugins = _ensure_plugins_section(config)
    enabled = plugins.get("enabled")
    if isinstance(enabled, list):
        plugins["enabled"] = [item for item in enabled if item != PLUGIN_ID]


def _default_ark_entry(api_key_env: str, *, voice: str | None = None) -> dict[str, Any]:
    voice_id = _resolve_tts_voice(voice)
    return {
        "api_key": "${" + api_key_env + "}",
        "ark": {
            "base_url": "https://ark.cn-beijing.volces.com/api/plan/v3",
            "timeout_seconds": 300,
        },
        "text_to_speech": {
            "base_url": "https://openspeech.bytedance.com/api/v3/plan/tts/unidirectional",
            "resource_id": "seed-tts-2.0",
            "voice": voice_id,
            "language": "auto",
            "output_format": "mp3",
            "timeout_seconds": 120,
            "max_text_length": 4000,
        },
        "transcribe_audio": {
            "base_url": "wss://openspeech.bytedance.com/api/v3/plan/sauc/bigmodel_nostream",
            "resource_id": "volc.seedasr.sauc.duration",
            "language": "zh",
            "output_format": "txt",
            "timeout_seconds": 180,
        },
        "image_generate": {
            "model": "doubao-seedream-5.0-lite",
            "timeout_seconds": 180,
        },
        "video_generate": {
            "model": "doubao-seedance-2.0-fast",
            "timeout_seconds": 300,
            "poll_interval_seconds": 5,
        },
        "vision_analyze": {
            "model": "doubao-seed-2.0-lite",
            "timeout_seconds": 300,
            "max_tokens": 2000,
            "temperature": 0.1,
        },
        "video_analyze": {
            "model": "doubao-seed-2.0-lite",
            "timeout_seconds": 300,
            "max_tokens": 4000,
            "temperature": 0.1,
            "fps": 1,
        },
    }


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = dict(base)
    for key, value in override.items():
        if isinstance(result.get(key), dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _write_ark_config(
    *,
    api_key_env: str,
    voice: str | None,
    activate_providers: bool,
    overwrite: bool,
) -> None:
    config, save_config = _load_raw_config_pair()
    plugins = _ensure_plugins_section(config)
    entries = plugins.setdefault("entries", {})
    if not isinstance(entries, dict):
        entries = {}
        plugins["entries"] = entries

    desired = _default_ark_entry(api_key_env, voice=voice)
    current = entries.get(PLUGIN_ID)
    if overwrite or not isinstance(current, dict):
        entries[PLUGIN_ID] = desired
    else:
        entries[PLUGIN_ID] = _deep_merge(desired, current)
        if voice:
            entries[PLUGIN_ID].setdefault("text_to_speech", {})["voice"] = desired["text_to_speech"]["voice"]

    if activate_providers:
        config.setdefault("tts", {})["provider"] = PLUGIN_ID
        stt = config.setdefault("stt", {})
        stt["enabled"] = True
        stt["provider"] = PLUGIN_ID
        image_gen = config.setdefault("image_gen", {})
        image_gen["provider"] = PLUGIN_ID
        image_gen.setdefault("model", desired["image_generate"]["model"])
        video_gen = config.setdefault("video_gen", {})
        video_gen["provider"] = PLUGIN_ID
        video_gen.setdefault("model", desired["video_generate"]["model"])

    _enable_plugin(config)
    save_config(config)


def _install_requirements(requirements_path: Path) -> None:
    uv = shutil.which("uv")
    if uv:
        cmd = [
            uv,
            "pip",
            "install",
            "--python",
            sys.executable,
            "-r",
            str(requirements_path),
        ]
    else:
        cmd = [
            sys.executable,
            "-m",
            "pip",
            "install",
            "-r",
            str(requirements_path),
        ]
    subprocess.run(cmd, check=True)


def cmd_install(args: argparse.Namespace) -> None:
    source = _repo_root()
    target = _plugin_target()
    target.parent.mkdir(parents=True, exist_ok=True)

    if target.exists() or target.is_symlink():
        if not args.force:
            raise SystemExit(f"{target} already exists. Use --force to replace it.")
        if target.is_symlink() or target.is_file():
            target.unlink()
        else:
            shutil.rmtree(target)

    if args.symlink:
        target.symlink_to(source, target_is_directory=True)
        mode = "symlinked"
    else:
        ignore = shutil.ignore_patterns(".git", "__pycache__", "*.pyc")
        shutil.copytree(source, target, ignore=ignore)
        mode = "copied"

    config, save_config = _load_raw_config_pair()
    _enable_plugin(config)
    save_config(config)

    if args.with_deps:
        _install_requirements(source / "requirements.txt")

    print(f"Installed ark plugin: {target} ({mode})")
    print("Enabled plugin: ark")
    print("Run `python cli.py config` to select Ark providers.")


def cmd_uninstall(args: argparse.Namespace) -> None:
    target = _plugin_target()
    if target.exists() or target.is_symlink():
        if target.is_symlink() or target.is_file():
            target.unlink()
        else:
            shutil.rmtree(target)

    config, save_config = _load_raw_config_pair()
    _disable_plugin(config)
    if args.remove_config:
        plugins = _ensure_plugins_section(config)
        entries = plugins.get("entries")
        if isinstance(entries, dict):
            entries.pop(PLUGIN_ID, None)
    save_config(config)

    print("Uninstalled ark plugin")
    if args.remove_config:
        print("Removed plugins.entries.ark")
    else:
        print("Preserved plugins.entries.ark")


def cmd_config(args: argparse.Namespace) -> None:
    _write_ark_config(
        api_key_env=args.api_key_env,
        voice=args.voice,
        activate_providers=args.activate_providers,
        overwrite=args.overwrite,
    )
    print("Wrote Hermes plugin config block:")
    print("  plugins.enabled += ark")
    print("  plugins.entries.ark = full Ark defaults")
    if args.voice:
        print(f"Selected TTS voice: {_voice_display(_resolve_tts_voice(args.voice))}")
    if args.activate_providers:
        print("Activated providers: tts/stt/image_gen/video_gen -> ark")


def cmd_voices(_args: argparse.Namespace) -> None:
    print("Ark TTS voices (common presets):")
    print("  alias              speaker_id                                label       language  style")
    for item in TTS_VOICES:
        print(
            f"  {item['alias']:<18} {item['id']:<41} "
            f"{item['label']:<10} {item['language']:<8} {item['style']}"
        )
    print()
    print("Use:")
    print("  python cli.py config --voice vivi")
    print("  python cli.py config --voice zh_male_m191_uranus_bigtts")
    print()
    print("Note: --voice also accepts any raw Ark speaker ID not shown above.")


def cmd_status(_args: argparse.Namespace) -> None:
    target = _plugin_target()
    config = _load_effective_config()
    plugins = config.get("plugins") if isinstance(config.get("plugins"), dict) else {}
    enabled = plugins.get("enabled") if isinstance(plugins.get("enabled"), list) else []
    entries = plugins.get("entries") if isinstance(plugins.get("entries"), dict) else {}

    print(f"install_path: {target}")
    print(f"installed: {target.exists() or target.is_symlink()}")
    print(f"install_mode: {'symlink' if target.is_symlink() else 'copy/dir' if target.exists() else 'none'}")
    print(f"enabled: {PLUGIN_ID in enabled}")
    print(f"has_config: {PLUGIN_ID in entries}")
    print(f"tts.provider: {config.get('tts', {}).get('provider') if isinstance(config.get('tts'), dict) else None}")
    print(f"stt.provider: {config.get('stt', {}).get('provider') if isinstance(config.get('stt'), dict) else None}")
    print(f"image_gen.provider: {config.get('image_gen', {}).get('provider') if isinstance(config.get('image_gen'), dict) else None}")
    print(f"video_gen.provider: {config.get('video_gen', {}).get('provider') if isinstance(config.get('video_gen'), dict) else None}")
    ark_entry = entries.get(PLUGIN_ID) if isinstance(entries.get(PLUGIN_ID), dict) else {}
    tts_entry = ark_entry.get("text_to_speech") if isinstance(ark_entry.get("text_to_speech"), dict) else {}
    print(f"tts.voice: {_voice_display(tts_entry.get('voice'))}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage the Hermes Ark plugin")
    sub = parser.add_subparsers(dest="command", required=True)

    install = sub.add_parser("install", help="Install plugin into ~/.hermes/plugins/ark")
    install.add_argument("--force", action="store_true", help="Replace an existing install")
    install.add_argument("--symlink", action="store_true", help="Create a symlink instead of copying files")
    install.add_argument("--with-deps", action="store_true", help="Install requirements into this Python environment")
    install.set_defaults(func=cmd_install)

    uninstall = sub.add_parser("uninstall", aliases=["remove"], help="Uninstall plugin")
    uninstall.add_argument("--remove-config", action="store_true", help="Remove plugins.entries.ark")
    uninstall.set_defaults(func=cmd_uninstall)

    config = sub.add_parser("config", help="Write plugins.entries.ark config")
    config.add_argument("--api-key-env", default=DEFAULT_API_KEY_ENV, help="Environment variable referenced by api_key")
    config.add_argument(
        "--voice",
        help="TTS voice alias or raw Ark speaker ID. Run `python cli.py voices` to list common presets.",
    )
    config.add_argument(
        "--no-activate-providers",
        action="store_false",
        dest="activate_providers",
        help="Only write plugins.entries.ark; do not switch Hermes providers to ark",
    )
    config.set_defaults(activate_providers=True)
    config.add_argument("--overwrite", action="store_true", help="Overwrite existing plugins.entries.ark instead of preserving user values")
    config.set_defaults(func=cmd_config)

    status = sub.add_parser("status", help="Show install and config status")
    status.set_defaults(func=cmd_status)

    voices = sub.add_parser("voices", help="List common Ark TTS voices")
    voices.set_defaults(func=cmd_voices)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
