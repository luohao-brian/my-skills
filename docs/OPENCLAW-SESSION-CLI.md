# OpenClaw Session CLI 实战手册

这篇文档整理了几个高频的 OpenClaw session 运维场景，基于本机实际排查过程总结。

默认假设：

- OpenClaw 状态目录在 `~/.openclaw/`
- 主 agent 的 session store 在 `~/.openclaw/agents/main/sessions/sessions.json`
- transcript JSONL 在 `~/.openclaw/agents/main/sessions/*.jsonl`

## 1. 根据对话内容查找指定 session

最直接的方法不是先猜 session key，而是先在 transcript 里搜对话原文。

示例：根据一段报错或用户原话查找 session。

```bash
rg -n "SEARCH_EMBEDDING_PROVIDER|你再试试这个技能|用的哪个技能目录" \
  ~/.openclaw/agents/main/sessions \
  ~/.openclaw/agents/*/sessions
```

如果命中的是某个 transcript：

```text
/root/.openclaw/agents/main/sessions/1229a84f-e53b-4f2a-bf89-81eab65828f4.jsonl
```

那么这个文件名基本就是你要找的 `sessionId`。

接下来再去 session store 里反查 `session key`、`channel`、`origin`：

```bash
jq -r 'to_entries[] | [.key, .value.sessionId, .value.lastChannel, (.value.origin.provider // ""), (.value.deliveryContext.channel // "")] | @tsv' \
  ~/.openclaw/agents/main/sessions/sessions.json
```

输出示例：

```text
agent:main:main	46b3a328-b3ac-4074-b363-b506172ef4b7	webchat	webchat	webchat
agent:main:feishu:direct:ou_4f79bcd0bfe245478f50efdfb1687514	1229a84f-e53b-4f2a-bf89-81eab65828f4	feishu	feishu	feishu
```

这样就能确定：

- session key：`agent:main:feishu:direct:ou_4f79bcd0bfe245478f50efdfb1687514`
- session id：`1229a84f-e53b-4f2a-bf89-81eab65828f4`

## 2. 使用这个 session 用 `openclaw agent` 发送 chat message

先确认 Gateway 正常：

```bash
openclaw health
```

然后直接对指定 session id 发一条消息：

```bash
openclaw agent \
  --session-id 1229a84f-e53b-4f2a-bf89-81eab65828f4 \
  --message "请只回复：OK" \
  --thinking low \
  --json
```

成功返回示例：

```json
{
  "status": "ok",
  "summary": "completed",
  "result": {
    "payloads": [
      { "text": "OK" }
    ]
  }
}
```

如果你想确认这条消息真的写进 transcript 了：

```bash
tail -n 12 ~/.openclaw/agents/main/sessions/1229a84f-e53b-4f2a-bf89-81eab65828f4.jsonl
```

## 3. 删除 / reset 指定 session

OpenClaw 目前没有一个现成的 `openclaw sessions reset <id>` CLI。
实战里通常分两种 reset：

### 3.1 软 reset

保留 transcript，只删 session store 里的部分状态字段。

适合：

- 想保留历史对话
- 只想让某些运行态字段重新生成

### 3.2 硬 reset

删除 session store 条目，加上删除 transcript 文件。

适合：

- 彻底清掉这个 session
- 下次消息让 OpenClaw 当作新会话处理

先建议备份：

```bash
cp ~/.openclaw/agents/main/sessions/sessions.json ~/.openclaw/agents/main/sessions/sessions.json.bak.$(date +%s)
```

#### 硬 reset 示例

删除 session store 里的条目：

```bash
python3 -c 'import json, os; p=os.path.expanduser("~/.openclaw/agents/main/sessions/sessions.json"); key="agent:main:feishu:direct:ou_4f79bcd0bfe245478f50efdfb1687514"; data=json.load(open(p)); data.pop(key, None); json.dump(data, open(p, "w"), ensure_ascii=False, indent=2)'
```

如果要连 transcript 一起删：

```bash
rm -f ~/.openclaw/agents/main/sessions/1229a84f-e53b-4f2a-bf89-81eab65828f4.jsonl
```

注意：

- 这是彻底删除，会丢历史
- 删除前最好确认 session id 和 key 对应正确

## 4. reset `skillsSnapshot` 让更新后的 skill 立即生效

这是最常用也最安全的一种“定向刷新”。

适合：

- skill 目录已经更新
- 但某个旧 session 还在用旧的 skill snapshot
- 不想删整个 transcript

要删的字段通常是：

- `skillsSnapshot`
- `systemPromptReport`

这样下一条消息到这个 session 时，OpenClaw 会按当前 skill 重新构建上下文。

### reset 指定 session 的 `skillsSnapshot`

```bash
python3 -c 'import json, os; p=os.path.expanduser("~/.openclaw/agents/main/sessions/sessions.json"); key="agent:main:feishu:direct:ou_4f79bcd0bfe245478f50efdfb1687514"; data=json.load(open(p)); entry=data[key]; entry.pop("skillsSnapshot", None); entry.pop("systemPromptReport", None); json.dump(data, open(p, "w"), ensure_ascii=False, indent=2)'
```

然后确认：

```bash
jq '."agent:main:feishu:direct:ou_4f79bcd0bfe245478f50efdfb1687514" | {sessionId, hasSkillsSnapshot:(has("skillsSnapshot")), hasSystemPromptReport:(has("systemPromptReport"))}' \
  ~/.openclaw/agents/main/sessions/sessions.json
```

理想输出：

```json
{
  "sessionId": "1229a84f-e53b-4f2a-bf89-81eab65828f4",
  "hasSkillsSnapshot": false,
  "hasSystemPromptReport": false
}
```

接下来只要再发一条新消息到这个 session，就会按当前 skill 重建。

## 常见判断顺序

当你怀疑“skill 改了但 session 还在用旧逻辑”，建议按下面顺序排：

1. 先搜 transcript，确认到底是哪一个 session 在出问题
2. 看 `sessions.json`，确认 session key、session id、channel
3. 看当前磁盘上的实际 skill 目录和二进制
4. 看该 session 的 `skillsSnapshot` 是否还是旧版本
5. 先 reset `skillsSnapshot`
6. 如果还不对，再检查是不是 `SKILL.md` 和 `bin/<tool>` 本身不一致

## 一页速查

根据原话查 session：

```bash
rg -n "关键词" ~/.openclaw/agents/main/sessions ~/.openclaw/agents/*/sessions
```

列出 session key 与 session id：

```bash
jq -r 'to_entries[] | [.key, .value.sessionId] | @tsv' ~/.openclaw/agents/main/sessions/sessions.json
```

向指定 session 发消息：

```bash
openclaw agent --session-id <session-id> --message "请只回复：OK" --thinking low --json
```

reset 某个 session 的 skill snapshot：

```bash
python3 -c 'import json, os; p=os.path.expanduser("~/.openclaw/agents/main/sessions/sessions.json"); key="SESSION_KEY"; data=json.load(open(p)); entry=data[key]; entry.pop("skillsSnapshot", None); entry.pop("systemPromptReport", None); json.dump(data, open(p, "w"), ensure_ascii=False, indent=2)'
```

硬删除某个 session：

```bash
python3 -c 'import json, os; p=os.path.expanduser("~/.openclaw/agents/main/sessions/sessions.json"); key="SESSION_KEY"; data=json.load(open(p)); data.pop(key, None); json.dump(data, open(p, "w"), ensure_ascii=False, indent=2)'
rm -f ~/.openclaw/agents/main/sessions/<session-id>.jsonl
```
