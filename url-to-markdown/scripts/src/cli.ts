#!/usr/bin/env bun

import {
  runConvertCommand,
  type ConvertCommandOptions,
  type OutputFormat,
  type WaitMode,
} from "./commands/convert";
import { normalizeUrl } from "./utils/url";

export const HELP_TEXT = `
web-fetch - Read a URL into Markdown or JSON with Chrome CDP

Usage:
  web-fetch <url> [options]

Options:
  --output <file>       Save output to file
  --format <type>       Output format: markdown | json
  --json                Alias for --format json
  --adapter <name>      Force an adapter (e.g. x, generic)
  --download-media      Download adapter-reported media into ./imgs and ./videos, then rewrite markdown links
  --media-dir <dir>     Base directory for downloaded media. Defaults to the output directory
  --debug-dir <dir>     Write debug artifacts
  --cdp-url <url>       Reuse an existing Chrome DevTools endpoint
  --browser-path <path> Explicit Chrome binary path
  --chrome-profile-dir <path>
                        Chrome user data dir. Defaults to WEB_FETCH_CHROME_PROFILE_DIR
                        or web-fetch/chrome-profile.
  --headless            Launch a temporary headless Chrome if needed
  --wait-for <mode>     Wait mode: interaction | force
                        interaction: start visible Chrome and auto-wait only when login or verification is required
                        force: start visible Chrome, then auto-continue after it detects login/challenge progress
                               or continue immediately when you press Enter
  --wait-for-interaction
                        Alias for --wait-for interaction
  --wait-for-login      Alias for --wait-for interaction
  --interaction-timeout <ms>
                        How long to wait for manual interaction before failing (default: 600000)
  --interaction-poll-interval <ms>
                        How often to poll interaction state while waiting (default: 1500)
  --login-timeout <ms>  Alias for --interaction-timeout
  --login-poll-interval <ms>
                        Alias for --interaction-poll-interval
  --timeout <ms>        Page timeout in milliseconds (default: 30000)
  --help                Show help

Environment:
  URL_TO_MARKDOWN_OUTPUT_DIR                 Default output base directory (default: ./url-to-markdown)
  URL_TO_MARKDOWN_OUTPUT_PATH                Explicit output file path
  URL_TO_MARKDOWN_FORMAT                     markdown | json
  URL_TO_MARKDOWN_DOWNLOAD_MEDIA             true | false
  URL_TO_MARKDOWN_WAIT_FOR                   none | interaction | force
  URL_TO_MARKDOWN_TIMEOUT_MS                 Page timeout in milliseconds
  URL_TO_MARKDOWN_INTERACTION_TIMEOUT_MS     Manual interaction timeout in milliseconds
  URL_TO_MARKDOWN_INTERACTION_POLL_INTERVAL_MS
                                             Manual interaction polling interval in milliseconds
  URL_TO_MARKDOWN_ADAPTER                    Force adapter
  URL_TO_MARKDOWN_MEDIA_DIR                  Default media dir
  URL_TO_MARKDOWN_DEBUG_DIR                  Default debug dir
  URL_TO_MARKDOWN_CDP_URL                    Default CDP endpoint
  URL_TO_MARKDOWN_BROWSER_PATH               Default browser path
  URL_TO_MARKDOWN_CHROME_PROFILE_DIR         Default Chrome profile dir
  WEB_FETCH_CHROME_PROFILE_DIR              Default Chrome profile dir alias

Examples:
  web-fetch https://example.com
  web-fetch https://example.com --format markdown --output article.md --download-media
  web-fetch https://example.com --format json --output article.json
  web-fetch https://x.com/lennysan/status/2036483059407810640 --wait-for interaction
  web-fetch https://x.com/lennysan/status/2036483059407810640 --wait-for force
`.trim();

interface CliOptions extends ConvertCommandOptions {
  url?: string;
  help: boolean;
}

function getEnvValue(name: string): string | undefined {
  const value = process.env[name]?.trim();
  return value ? value : undefined;
}

function parseBooleanValue(raw: string, name: string): boolean {
  const value = raw.trim().toLowerCase();
  if (["1", "true", "yes", "on"].includes(value)) {
    return true;
  }
  if (["0", "false", "no", "off"].includes(value)) {
    return false;
  }
  throw new Error(`Invalid boolean for ${name}: ${raw}`);
}

function parsePositiveIntValue(raw: string, name: string): number {
  const parsed = Number(raw);
  if (!Number.isFinite(parsed) || parsed <= 0) {
    throw new Error(`Invalid number for ${name}: ${raw}`);
  }
  return parsed;
}

function slugify(value: string): string {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 80) || "index";
}

function buildDefaultOutputPath(rawUrl: string, format: OutputFormat, baseDir: string): string {
  const url = new URL(normalizeUrl(rawUrl));
  const host = slugify(url.hostname.replace(/^www\./, ""));
  const segments = url.pathname
    .split("/")
    .map((segment) => slugify(segment))
    .filter((segment) => segment && segment !== "index");
  const slug = segments.length > 0 ? segments.slice(-2).join("-") : "index";
  const ext = format === "json" ? "json" : "md";
  return `${baseDir.replace(/\/+$/, "")}/${host}/${slug}/${slug}.${ext}`;
}

function buildInitialOptions(): CliOptions {
  const formatRaw = getEnvValue("URL_TO_MARKDOWN_FORMAT");
  const waitModeRaw = getEnvValue("URL_TO_MARKDOWN_WAIT_FOR");
  const timeoutRaw = getEnvValue("URL_TO_MARKDOWN_TIMEOUT_MS");
  const interactionTimeoutRaw = getEnvValue("URL_TO_MARKDOWN_INTERACTION_TIMEOUT_MS");
  const interactionPollRaw = getEnvValue("URL_TO_MARKDOWN_INTERACTION_POLL_INTERVAL_MS");
  const downloadMediaRaw = getEnvValue("URL_TO_MARKDOWN_DOWNLOAD_MEDIA");

  return {
    format: formatRaw ? normalizeOutputFormat(formatRaw) : "markdown",
    headless: true,
    downloadMedia: downloadMediaRaw ? parseBooleanValue(downloadMediaRaw, "URL_TO_MARKDOWN_DOWNLOAD_MEDIA") : false,
    waitMode: waitModeRaw ? normalizeWaitMode(waitModeRaw) : "none",
    interactionTimeoutMs: interactionTimeoutRaw
      ? parsePositiveIntValue(interactionTimeoutRaw, "URL_TO_MARKDOWN_INTERACTION_TIMEOUT_MS")
      : 600_000,
    interactionPollIntervalMs: interactionPollRaw
      ? parsePositiveIntValue(interactionPollRaw, "URL_TO_MARKDOWN_INTERACTION_POLL_INTERVAL_MS")
      : 1_500,
    timeoutMs: timeoutRaw ? parsePositiveIntValue(timeoutRaw, "URL_TO_MARKDOWN_TIMEOUT_MS") : 30_000,
    adapter: getEnvValue("URL_TO_MARKDOWN_ADAPTER"),
    output: getEnvValue("URL_TO_MARKDOWN_OUTPUT_PATH"),
    mediaDir: getEnvValue("URL_TO_MARKDOWN_MEDIA_DIR"),
    debugDir: getEnvValue("URL_TO_MARKDOWN_DEBUG_DIR"),
    cdpUrl: getEnvValue("URL_TO_MARKDOWN_CDP_URL"),
    browserPath: getEnvValue("URL_TO_MARKDOWN_BROWSER_PATH"),
    chromeProfileDir:
      getEnvValue("URL_TO_MARKDOWN_CHROME_PROFILE_DIR") ?? getEnvValue("WEB_FETCH_CHROME_PROFILE_DIR"),
    help: false,
  };
}

function normalizeWaitMode(raw: string): WaitMode {
  const value = raw.toLowerCase();
  if (value === "interaction" || value === "auto") {
    return "interaction";
  }
  if (value === "force" || value === "manual" || value === "always") {
    return "force";
  }
  throw new Error(`Invalid wait mode: ${raw}. Expected interaction or force.`);
}

function normalizeOutputFormat(raw: string): OutputFormat {
  const value = raw.toLowerCase();
  if (value === "markdown" || value === "json") {
    return value;
  }

  throw new Error(`Invalid output format: ${raw}. Expected markdown or json.`);
}

export function parseArgs(argv: string[]): CliOptions {
  const options: CliOptions = buildInitialOptions();

  const args = argv.slice(2);
  for (let index = 0; index < args.length; index += 1) {
    const value = args[index];

    if (value === "--help" || value === "-h") {
      options.help = true;
      continue;
    }
    if (value === "--format") {
      const format = args[index + 1];
      if (!format) {
        throw new Error("--format requires a value");
      }
      options.format = normalizeOutputFormat(format);
      index += 1;
      continue;
    }
    if (value === "--json") {
      options.format = "json";
      continue;
    }
    if (value === "--download-media") {
      options.downloadMedia = true;
      continue;
    }
    if (value === "--headless") {
      options.headless = true;
      continue;
    }
    if (value === "--wait-for") {
      const mode = args[index + 1];
      if (!mode) {
        throw new Error("--wait-for requires a mode");
      }
      options.waitMode = normalizeWaitMode(mode);
      index += 1;
      continue;
    }
    if (value === "--wait-for-interaction" || value === "--wait-for-login") {
      options.waitMode = "interaction";
      continue;
    }
    if (value === "--output") {
      options.output = args[index + 1];
      index += 1;
      continue;
    }
    if (value === "--adapter") {
      options.adapter = args[index + 1];
      index += 1;
      continue;
    }
    if (value === "--debug-dir") {
      options.debugDir = args[index + 1];
      index += 1;
      continue;
    }
    if (value === "--media-dir") {
      options.mediaDir = args[index + 1];
      index += 1;
      continue;
    }
    if (value === "--cdp-url") {
      options.cdpUrl = args[index + 1];
      index += 1;
      continue;
    }
    if (value === "--browser-path") {
      options.browserPath = args[index + 1];
      index += 1;
      continue;
    }
    if (value === "--chrome-profile-dir") {
      options.chromeProfileDir = args[index + 1];
      index += 1;
      continue;
    }
    if (value === "--timeout") {
      const parsed = Number(args[index + 1]);
      if (!Number.isFinite(parsed) || parsed <= 0) {
        throw new Error(`Invalid timeout: ${args[index + 1]}`);
      }
      options.timeoutMs = parsed;
      index += 1;
      continue;
    }
    if (value === "--interaction-timeout" || value === "--login-timeout") {
      const parsed = Number(args[index + 1]);
      if (!Number.isFinite(parsed) || parsed <= 0) {
        throw new Error(`Invalid interaction timeout: ${args[index + 1]}`);
      }
      options.interactionTimeoutMs = parsed;
      index += 1;
      continue;
    }
    if (value === "--interaction-poll-interval" || value === "--login-poll-interval") {
      const parsed = Number(args[index + 1]);
      if (!Number.isFinite(parsed) || parsed <= 0) {
        throw new Error(`Invalid interaction poll interval: ${args[index + 1]}`);
      }
      options.interactionPollIntervalMs = parsed;
      index += 1;
      continue;
    }
    if (value.startsWith("-")) {
      throw new Error(`Unknown option: ${value}`);
    }
    if (!options.url) {
      options.url = value;
      continue;
    }
    throw new Error(`Unexpected argument: ${value}`);
  }

  if (!options.output && options.url) {
    const outputDir = getEnvValue("URL_TO_MARKDOWN_OUTPUT_DIR") ?? "./url-to-markdown";
    options.output = buildDefaultOutputPath(options.url, options.format, outputDir);
  }

  return options;
}

async function main(): Promise<void> {
  try {
    const options = parseArgs(process.argv);
    if (options.help || !options.url) {
      console.log(HELP_TEXT);
      return;
    }

    await runConvertCommand(options);
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    console.error(message);
    process.exitCode = 1;
  }
}

if (import.meta.main) {
  void main();
}
