# my-knowledge-wiki MCP server

This directory adds a read-only MCP adapter while preserving the existing
`openclaw-skills/my-knowledge-wiki` REST skill. The adapter exposes
`server/discover`, `initialize`, `tools/list`, and `tools/call` on `POST /mcp`
and forwards tool calls to the existing Knowledge API. It supports MCP
2026-07-28 stateless discovery/tool requests and retains the 2025
initialization handshake for older clients.

## Run

```bash
export MY_KNOWLEDGE_WIKI_API_URL="https://<host>/api/knowledge"
export MY_KNOWLEDGE_WIKI_API_KEY="<backend-readonly-key>"
export MY_KNOWLEDGE_WIKI_MCP_KEY="<same-read-only-key-as-backend>"
export MY_KNOWLEDGE_WIKI_MCP_AUTH=none
export MY_KNOWLEDGE_WIKI_MCP_PORT=8080
python3 mcp/my-knowledge-wiki/server.py
```

The backend and optional MCP key reuse the same read-only Knowledge API key.
`MCP_AUTH=none` is the ChatGPT deployment mode: the key stays server-side and
the public MCP endpoint does not require a client key. Set `MCP_AUTH=bearer`
when using a client that can send `Authorization: Bearer ...`. Use
`nginx.conf.tmpl` to publish `https://<host>/mcp` with TLS. The server is
intentionally read-only.

## Client contract

Send JSON-RPC 2.0 requests to `/mcp`. In bearer mode include
`Authorization: Bearer <MCP key>`; in no-auth mode omit it. The server
supports the eight `wiki_*` tools listed by `tools/list`.

ChatGPT connects to a remote MCP server. Create a custom app in Developer
Mode, scan this endpoint, and select or mention the app in the target Project.
The app is selected per message; it is not permanently attached to a Project.
