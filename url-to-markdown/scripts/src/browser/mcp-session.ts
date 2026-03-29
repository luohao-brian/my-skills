import { McpBridgeClient } from "./mcp-bridge-client";
import type { BrowserSessionLike } from "./session";

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

interface DomEvalResult {
  readyState?: string;
}

export class McpBrowserSession implements BrowserSessionLike {
  private constructor(
    private readonly bridge: McpBridgeClient,
    private readonly pageId: number | null,
  ) {}

  static async open(): Promise<McpBrowserSession> {
    const bridge = new McpBridgeClient();
    const page = await bridge.newPage();
    return new McpBrowserSession(bridge, page.pageId);
  }

  async goto(url: string, timeoutMs = 30_000): Promise<void> {
    await this.bridge.navigate(this.pageId, url);
    await this.waitForReadyState(timeoutMs);
  }

  async waitForReadyState(timeoutMs = 30_000): Promise<void> {
    const startedAt = Date.now();
    while (Date.now() - startedAt < timeoutMs) {
      const state = await this.evaluate<DomEvalResult>(`() => ({ readyState: document.readyState })`);
      if (state.readyState === "interactive" || state.readyState === "complete") {
        return;
      }
      await sleep(150);
    }
    throw new Error("Timed out waiting for document.readyState");
  }

  async evaluate<T>(expression: string): Promise<T> {
    return await this.bridge.evaluate<T>(this.pageId, this.normalizeExpression(expression));
  }

  private normalizeExpression(expression: string): string {
    const trimmed = expression.trim();
    if (
      trimmed.startsWith("() =>") ||
      trimmed.startsWith("async () =>") ||
      trimmed.startsWith("function")
    ) {
      return trimmed;
    }
    return `() => eval(${JSON.stringify(trimmed)})`;
  }

  async getHTML(): Promise<string> {
    return await this.evaluate<string>("() => document.documentElement.outerHTML");
  }

  async getTitle(): Promise<string> {
    return await this.evaluate<string>("() => document.title");
  }

  async getURL(): Promise<string> {
    return await this.evaluate<string>("() => window.location.href");
  }

  async bringToFront(): Promise<void> {
    await this.bridge.bringToFront(this.pageId);
  }

  async click(selector: string): Promise<void> {
    const result = await this.evaluate<{ ok: boolean; error?: string }>(`
      () => {
        const element = document.querySelector(${JSON.stringify(selector)});
        if (!element) {
          return { ok: false, error: "Element not found" };
        }
        element.scrollIntoView({ block: "center", inline: "center" });
        if (element instanceof HTMLElement) {
          element.click();
          return { ok: true };
        }
        return { ok: false, error: "Element is not clickable" };
      }
    `);

    if (!result.ok) {
      throw new Error(result.error ?? `Failed to click ${selector}`);
    }
  }

  async scrollToEnd(options: { stepPx?: number; delayMs?: number; maxSteps?: number } = {}): Promise<void> {
    const stepPx = options.stepPx ?? 1_400;
    const delayMs = options.delayMs ?? 250;
    const maxSteps = options.maxSteps ?? 6;

    for (let step = 0; step < maxSteps; step += 1) {
      const done = await this.evaluate<boolean>(`
        () => {
          const before = window.scrollY;
          window.scrollBy(0, ${stepPx});
          const atBottom = window.innerHeight + window.scrollY >= document.body.scrollHeight - 4;
          return atBottom || window.scrollY === before;
        }
      `);
      if (done) {
        break;
      }
      await sleep(delayMs);
    }
  }

  async close(): Promise<void> {
    await this.bridge.closePage(this.pageId);
  }
}
