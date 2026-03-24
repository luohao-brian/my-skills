# 常用音色示例

以下不是完整音色表，而是按使用场景整理的一组高频示例。真正选择时，优先以官方音色列表中的 `voice_type` 为准。

## 通用场景

| 音色名 | `voice_type` | 语种 | 备注 |
| --- | --- | --- | --- |
| 灿灿 | `zh_female_cancan_mars_bigtts` | 中文 | 通用中文女声，适合默认起步 |
| Vivi 2.0 | `zh_female_vv_uranus_bigtts` | 中文、英语 | 2.0 女声 |
| 小何 2.0 | `zh_female_xiaohe_uranus_bigtts` | 中文 | 2.0 女声 |
| 云舟 2.0 | `zh_male_m191_uranus_bigtts` | 中文 | 2.0 男声 |
| 小天 2.0 | `zh_male_taocheng_uranus_bigtts` | 中文 | 2.0 男声 |

## 多情感音色

| 音色名 | `voice_type` | 常见适合情感 |
| --- | --- | --- |
| 冷酷哥哥（多情感） | `zh_male_lengkugege_emo_v2_mars_bigtts` | `angry` `coldness` `happy` `sad` `neutral` |
| 高冷御姐（多情感） | `zh_female_gaolengyujie_emo_v2_mars_bigtts` | `happy` `sad` `angry` `surprised` `excited` `neutral` |
| 甜心小美（多情感） | `zh_female_tianxinxiaomei_emo_v2_mars_bigtts` | `sad` `fear` `hate` `neutral` |

## 角色 / 风格音色

| 音色名 | `voice_type` | 场景 |
| --- | --- | --- |
| 可爱女生 | `saturn_zh_female_keainvsheng_tob` | 角色化配音 |
| 调皮公主 | `saturn_zh_female_tiaopigongzhu_tob` | 角色化配音 |
| 爽朗少年 | `saturn_zh_male_shuanglangshaonian_tob` | 角色化配音 |
| 天才同桌 | `saturn_zh_male_tiancaitongzhuo_tob` | 角色化配音 |
| 知性灿灿 | `saturn_zh_female_cancan_tob` | 角色化配音 |

## 选型建议

- 默认试跑：先用 `zh_female_cancan_mars_bigtts`
- 需要稳妥通用旁白：优先 `Vivi 2.0`、`云舟 2.0`
- 需要情感可控：优先多情感音色
- 需要角色感：优先 `saturn_*` 系列

## 情感示例

```bash
VOLC_TTS_RESOURCE_ID=volc.service_type.10029 \
{baseDir}/bin/volc-speech tts "欢迎来到今天的节目" \
  --speaker zh_female_gaolengyujie_emo_v2_mars_bigtts \
  --emotion storytelling \
  --emotion-scale 4
```

```bash
VOLC_TTS_RESOURCE_ID=volc.service_type.10029 \
{baseDir}/bin/volc-speech tts "这条消息非常紧急，请尽快处理" \
  --speaker zh_male_lengkugege_emo_v2_mars_bigtts \
  --emotion angry \
  --emotion-scale 3
```
