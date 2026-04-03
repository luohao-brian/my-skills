import net from "node:net";
import os from "node:os";
import path from "node:path";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";

const SOCKET_PATH = path.join(os.tmpdir(), "url-to-markdown-mcp-bridge.sock");
const BRIDGE_STARTUP_TIMEOUT_MS = 30_000;
const BRIDGE_POLL_INTERVAL_MS = 250;
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const BRIDGE_SCRIPT_PATH = path.resolve(__dirname, "../../mcp-bridge.mjs");

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function sendRequest<T>(payload: object): Promise<T> {
  return await new Promise<T>((resolve, reject) => {
    const socket = net.createConnection(SOCKET_PATH);
    let response = "";

    socket.setEncoding("utf8");
    socket.once("error", reject);
    socket.on("data", (chunk) => {
      response += chunk;
      if (!response.includes("\n")) {
        return;
      }

      try {
        const message = JSON.parse(response.trim()) as { ok: boolean; data?: T; error?: string };
        socket.end();
        if (!message.ok) {
          reject(new Error(message.error ?? "Unknown MCP bridge error"));
          return;
        }
        resolve(message.data as T);
      } catch (error) {
        reject(error);
      }
    });

    socket.on("connect", () => {
      socket.write(`${JSON.stringify(payload)}\n`);
    });
  });
}

async function pingBridge(): Promise<boolean> {
  try {
    await sendRequest({ action: "ping" });
    return true;
  } catch {
    return false;
  }
}

async function waitForBridge(): Promise<void> {
  const startedAt = Date.now();
  while (Date.now() - startedAt < BRIDGE_STARTUP_TIMEOUT_MS) {
    if (await pingBridge()) {
      return;
    }
    await sleep(BRIDGE_POLL_INTERVAL_MS);
  }
  throw new Error(`Timed out waiting for MCP bridge at ${SOCKET_PATH}`);
}

async function ensureBridge(): Promise<void> {
  if (await pingBridge()) {
    return;
  }

  const child = spawn("node", [BRIDGE_SCRIPT_PATH], {
    detached: true,
    stdio: "ignore",
  });
  child.unref();

  await waitForBridge();
}

export interface McpBridgePage {
  pageId: number | null;
  raw: string;
  pages: Array<{ pageId: number; url: string; selected: boolean }>;
}

export class McpBridgeClient {
  async newPage(): Promise<McpBridgePage> {
    await ensureBridge();
    return await sendRequest<McpBridgePage>({ action: "newPage" });
  }

  async navigate(pageId: number | null, url: string): Promise<void> {
    await ensureBridge();
    await sendRequest({ action: "navigate", pageId, url });
  }

  async evaluate<T>(pageId: number | null, expression: string): Promise<T> {
    await ensureBridge();
    const result = await sendRequest<{ value: T }>({ action: "evaluate", pageId, expression });
    return result.value;
  }

  async bringToFront(pageId: number | null): Promise<void> {
    if (pageId === null) {
      return;
    }
    await ensureBridge();
    await sendRequest({ action: "bringToFront", pageId });
  }

  async closePage(pageId: number | null): Promise<void> {
    if (pageId === null) {
      return;
    }
    await ensureBridge();
    await sendRequest({ action: "closePage", pageId });
  }
}
