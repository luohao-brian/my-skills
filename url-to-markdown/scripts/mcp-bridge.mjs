import fs from "node:fs";
import net from "node:net";
import os from "node:os";
import path from "node:path";
import process from "node:process";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

const SOCKET_PATH = path.join(os.tmpdir(), "url-to-markdown-mcp-bridge.sock");
const LOG_PATH = path.join(os.tmpdir(), "url-to-markdown-mcp-bridge.log");
const IDLE_TIMEOUT_MS = 10 * 60 * 1000;
const STARTUP_TIMEOUT_MS = 30 * 1000;
const TOOL_TIMEOUT_MS = 20 * 1000;
const MCP_COMMAND = "npx";
const MCP_ARGS = ["-y", "chrome-devtools-mcp@latest", "--autoConnect"];

let transport = null;
let client = null;
let tools = [];
let idleTimer = null;
let requestQueue = Promise.resolve();

function logLine(message) {
  try {
    fs.appendFileSync(LOG_PATH, `[${new Date().toISOString()}] ${message}\n`);
  } catch {}
}

function resetIdleTimer() {
  if (idleTimer) {
    clearTimeout(idleTimer);
  }
  idleTimer = setTimeout(() => {
    shutdown(0).catch(() => process.exit(0));
  }, IDLE_TIMEOUT_MS);
}

function getTool(name) {
  const tool = tools.find((entry) => entry.name === name);
  if (!tool) {
    throw new Error(`Required MCP tool not found: ${name}`);
  }
  return tool;
}

function getSchemaProperties(tool) {
  return tool.inputSchema?.properties ?? {};
}

function hasProperty(tool, name) {
  return Object.prototype.hasOwnProperty.call(getSchemaProperties(tool), name);
}

function summarizeContent(result) {
  if (!result || !Array.isArray(result.content)) {
    return [];
  }
  return result.content.map((item) => (item.type === "text" ? item.text : JSON.stringify(item)));
}

function extractSelectedPageId(text) {
  const match = text.match(/^\s*(\d+): .+\[selected\]\s*$/im);
  return match ? Number(match[1]) : null;
}

function parsePages(text) {
  return text
    .split("\n")
    .map((line) => {
      const match = line.match(/^\s*(\d+):\s+(.+?)(?:\s+\[selected\])?\s*$/);
      if (!match) {
        return null;
      }
      return {
        pageId: Number(match[1]),
        url: match[2],
        selected: /\[selected\]/.test(line),
      };
    })
    .filter(Boolean);
}

function parseEvaluateText(text) {
  const fencedJson = text.match(/```json\s*([\s\S]*?)\s*```/i);
  if (fencedJson) {
    try {
      return JSON.parse(fencedJson[1]);
    } catch {
      return fencedJson[1];
    }
  }

  const inlineJson = text.match(/returned:\s*(\{[\s\S]*\})\s*$/i);
  if (inlineJson) {
    try {
      return JSON.parse(inlineJson[1]);
    } catch {
      return inlineJson[1];
    }
  }

  return text;
}

async function withTimeout(promise, timeoutMs, label) {
  return await Promise.race([
    promise,
    new Promise((_, reject) => {
      setTimeout(() => reject(new Error(`${label} timed out after ${timeoutMs}ms`)), timeoutMs);
    }),
  ]);
}

async function ensureConnected() {
  if (client) {
    return;
  }

  const nextTransport = new StdioClientTransport({
    command: MCP_COMMAND,
    args: MCP_ARGS,
    stderr: "pipe",
    env: {
      ...process.env,
    },
  });

  const nextClient = new Client(
    {
      name: "url-to-markdown-mcp-bridge",
      version: "0.1.0",
    },
    {
      capabilities: {},
    },
  );

  try {
    await withTimeout(nextClient.connect(nextTransport), STARTUP_TIMEOUT_MS, "MCP connect");
    const listed = await nextClient.listTools();
    tools = listed.tools ?? [];
    logLine(`connected tools=${tools.map((tool) => tool.name).join(",")}`);
    client = nextClient;
    transport = nextTransport;
    resetIdleTimer();
  } catch (error) {
    logLine(`connect_failed error=${error instanceof Error ? error.stack ?? error.message : String(error)}`);
    await nextClient.close().catch(() => {});
    await nextTransport.close().catch(() => {});
    throw error;
  }
}

async function callTool(name, args) {
  await ensureConnected();
  return await withTimeout(
    client.callTool({
      name,
      arguments: args,
    }),
    TOOL_TIMEOUT_MS,
    `tool ${name}`,
  );
}

async function listPages() {
  const result = await callTool("list_pages", {});
  const text = summarizeContent(result).join("\n");
  return parsePages(text);
}

async function selectPage(pageId) {
  const tool = getTool("select_page");
  const args = hasProperty(tool, "pageId")
    ? { pageId }
    : hasProperty(tool, "pageIdx")
      ? { pageIdx: pageId }
      : {};
  await callTool("select_page", args);
}

async function handleRequest(request) {
  resetIdleTimer();
  logLine(`request action=${request.action}`);

  if (request.action !== "ping") {
    await ensureConnected();
  }

  switch (request.action) {
    case "ping":
      return { ok: true, data: { status: "ok" } };

    case "newPage": {
      const tool = getTool("new_page");
      const args = hasProperty(tool, "url") ? { url: "about:blank" } : {};
      const result = await callTool("new_page", args);
      const text = summarizeContent(result).join("\n");
      const pageId = extractSelectedPageId(text);
      return { ok: true, data: { pageId, raw: text, pages: parsePages(text) } };
    }

    case "navigate": {
      if (typeof request.pageId === "number") {
        await selectPage(request.pageId);
      }
      const tool = getTool("navigate_page");
      const args = hasProperty(tool, "url")
        ? { url: request.url }
        : hasProperty(tool, "navigate")
          ? { navigate: request.url }
          : {};
      const result = await callTool("navigate_page", args);
      return { ok: true, data: { raw: summarizeContent(result).join("\n") } };
    }

    case "evaluate": {
      if (typeof request.pageId === "number") {
        await selectPage(request.pageId);
      }
      const tool = getTool("evaluate_script");
      const args = hasProperty(tool, "function")
        ? { function: request.expression }
        : hasProperty(tool, "expression")
          ? { expression: request.expression }
          : hasProperty(tool, "script")
            ? { script: request.expression }
            : {};
      const result = await callTool("evaluate_script", args);
      const text = summarizeContent(result).join("\n");
      return { ok: true, data: { value: parseEvaluateText(text), raw: text } };
    }

    case "bringToFront": {
      if (typeof request.pageId !== "number") {
        throw new Error("bringToFront requires pageId");
      }
      await selectPage(request.pageId);
      return { ok: true, data: { status: "ok" } };
    }

    case "closePage": {
      if (typeof request.pageId !== "number") {
        throw new Error("closePage requires pageId");
      }
      const tool = getTool("close_page");
      const args = hasProperty(tool, "pageId")
        ? { pageId: request.pageId }
        : hasProperty(tool, "pageIdx")
          ? { pageIdx: request.pageId }
          : {};
      const result = await callTool("close_page", args);
      return { ok: true, data: { raw: summarizeContent(result).join("\n") } };
    }

    case "listPages": {
      return { ok: true, data: { pages: await listPages() } };
    }

    default:
      throw new Error(`Unknown action: ${request.action}`);
  }
}

async function shutdown(code = 0) {
  if (idleTimer) {
    clearTimeout(idleTimer);
  }
  if (client) {
    await client.close().catch(() => {});
  }
  if (transport) {
    await transport.close().catch(() => {});
  }
  try {
    fs.unlinkSync(SOCKET_PATH);
  } catch {}
  process.exit(code);
}

try {
  fs.unlinkSync(SOCKET_PATH);
} catch {}

const server = net.createServer((socket) => {
  let buffer = "";
  socket.setEncoding("utf8");

  socket.on("data", (chunk) => {
    buffer += chunk;
    if (!buffer.includes("\n")) {
      return;
    }

    const line = buffer.slice(0, buffer.indexOf("\n")).trim();
    buffer = "";

    requestQueue = requestQueue
      .then(async () => {
        const request = JSON.parse(line);
        const response = await handleRequest(request);
        socket.end(`${JSON.stringify(response)}\n`);
      })
      .catch((error) => {
        logLine(`request_failed error=${error instanceof Error ? error.stack ?? error.message : String(error)}`);
        socket.end(`${JSON.stringify({ ok: false, error: error instanceof Error ? error.message : String(error) })}\n`);
      });
  });
});

server.listen(SOCKET_PATH, () => {
  resetIdleTimer();
});

process.on("SIGINT", () => {
  shutdown(0).catch(() => process.exit(0));
});

process.on("SIGTERM", () => {
  shutdown(0).catch(() => process.exit(0));
});
