# README_VOLC_GEN

`volc-gen` 是火山引擎 Ark 图像/视频生成 skill，对应实现位于 [`/Users/bytedance/Documents/my-skills/rust/volc-gen`](/Users/bytedance/Documents/my-skills/rust/volc-gen)。

## 能力范围

- 文生图 `t2i`
- 图生图 `i2i`
- 图生视频 `i2v`
- 任务查询 `query`

## 运行入口

- skill：[`/Users/bytedance/Documents/my-skills/volc-gen/SKILL.md`](/Users/bytedance/Documents/my-skills/volc-gen/SKILL.md)
- Rust CLI：[`/Users/bytedance/Documents/my-skills/rust/volc-gen/src/main.rs`](/Users/bytedance/Documents/my-skills/rust/volc-gen/src/main.rs)

## 关键环境变量

- `ARK_API_KEY`
- `VOLC_IMAGE_MODEL_ID`
- `VOLC_VIDEO_MODEL_ID`

## 最小验证

```bash
cd /Users/bytedance/Documents/my-skills
bash scripts/volc-gen/verify.sh
```

带真实凭证：

```bash
cd /Users/bytedance/Documents/my-skills
bash scripts/volc-gen/verify.sh --live
```
