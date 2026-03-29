import type { NetworkEntry, NetworkJournalLike } from "./network-journal";

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export class NoopNetworkJournal implements NetworkJournalLike {
  async start(): Promise<void> {}

  stop(): void {}

  getEntries(): NetworkEntry[] {
    return [];
  }

  findEntries(): NetworkEntry[] {
    return [];
  }

  async waitForIdle(options: { idleMs?: number; timeoutMs?: number } = {}): Promise<void> {
    await sleep(Math.min(options.idleMs ?? 400, 400));
  }

  async waitForResponse(): Promise<NetworkEntry> {
    throw new Error("Network response waiting is unavailable in MCP-backed sessions");
  }

  async ensureBody(): Promise<string | undefined> {
    return undefined;
  }

  async getJsonBody(): Promise<unknown | null> {
    return null;
  }

  async toJSON(): Promise<NetworkEntry[]> {
    return [];
  }
}
