import type { Adapter } from "../types";
import { detectInteractionGate } from "../../browser/interaction-gates";
import { captureNormalizedPageSnapshot } from "../../browser/page-snapshot";
import { convertHtmlToMarkdown } from "../../extract/html-to-markdown";

function detectBlockedDocument(markdown: string) {
  const compact = markdown.replace(/\s+/g, " ").trim();
  const lower = compact.toLowerCase();
  const looksShort = compact.length < 1_500;
  const blocked =
    lower.includes("您当前请求存在异常") ||
    lower.includes("暂时限制本次访问") ||
    lower.includes('"code":40362') ||
    lower.includes('"code":403') ||
    lower.includes("access denied") ||
    lower.includes("forbidden") ||
    lower.includes("sign in to continue") ||
    lower.includes("login to continue");

  if (!looksShort || !blocked) {
    return null;
  }

  return {
    type: "wait_for_interaction" as const,
    kind: "login" as const,
    provider: "generic_access_gate",
    reason: "The page returned an access restriction or anti-bot response",
    prompt: "The page appears to require login or manual verification. Please complete it in the opened Chrome window. Extraction will continue automatically after the page becomes accessible.",
    requiresVisibleBrowser: true,
  };
}

function normalizeDocumentTitle(title: string | undefined): string | undefined {
  if (!title) {
    return title;
  }
  return title.replace(/^\([^)]*(?:消息|私信|通知|notification|notifications)[^)]*\)\s*/i, "").trim();
}

export const genericAdapter: Adapter = {
  name: "generic",
  match() {
    return true;
  },
  async process(context) {
    context.log.info(`Loading ${context.input.url.toString()} with generic adapter`);
    await context.browser.goto(context.input.url.toString(), context.timeoutMs);

    try {
      await context.network.waitForIdle({
        idleMs: 1_200,
        timeoutMs: Math.min(context.timeoutMs, 15_000),
      });
    } catch {
      context.log.debug("Network idle timed out on initial load; continuing.");
    }

    await context.browser.scrollToEnd({ maxSteps: 4, delayMs: 300 });

    try {
      await context.network.waitForIdle({
        idleMs: 900,
        timeoutMs: Math.min(context.timeoutMs, 10_000),
      });
    } catch {
      context.log.debug("Network idle timed out after scrolling; continuing.");
    }

    const interaction = await detectInteractionGate(context.browser);
    if (interaction) {
      return {
        status: "needs_interaction",
        interaction,
      };
    }

    const snapshot = await captureNormalizedPageSnapshot(context.browser);
    const converted = await convertHtmlToMarkdown(snapshot.html, snapshot.finalUrl, {
      enableRemoteMarkdownFallback: context.outputFormat === "markdown",
      preserveBase64Images: context.downloadMedia,
    });
    const blockedDocument = converted.markdown ? detectBlockedDocument(converted.markdown) : null;
    if (blockedDocument) {
      return {
        status: "needs_interaction",
        interaction: blockedDocument,
      };
    }
    const document = {
      url: snapshot.finalUrl,
      canonicalUrl: converted.metadata.canonicalUrl,
      title: normalizeDocumentTitle(converted.metadata.title),
      author: converted.metadata.author,
      siteName: converted.metadata.siteName,
      publishedAt: converted.metadata.publishedAt,
      summary: converted.metadata.summary,
      adapter: "generic",
      metadata: {
        coverImage: converted.metadata.coverImage,
        language: converted.metadata.language,
        capturedAt: converted.metadata.capturedAt,
        conversionMethod: converted.conversionMethod,
        fallbackReason: converted.fallbackReason,
        kind: "generic/article",
      },
      content: converted.markdown ? [{ type: "markdown" as const, markdown: converted.markdown }] : [],
    };

    return {
      status: "ok",
      document,
      media: converted.media,
    };
  },
};
