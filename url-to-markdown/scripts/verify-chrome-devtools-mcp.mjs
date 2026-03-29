import process from "node:process";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

function parseArgs(argv) {
  const options = {
    url: "https://example.com/",
    command: "npx",
    args: ["-y", "chrome-devtools-mcp@latest", "--autoConnect"],
    startupTimeoutMs: 30_000,
    toolTimeoutMs: 20_000,
    waitText: "Example Domain",
    waitSelector: undefined,
    script: undefined,
  };

  for (let index = 2; index < argv.length; index += 1) {
    const value = argv[index];
    if (value === "--url") {
      options.url = argv[index + 1];
      index += 1;
      continue;
    }
    if (value === "--command") {
      options.command = argv[index + 1];
      index += 1;
      continue;
    }
    if (value === "--args") {
      const raw = argv[index + 1];
      options.args = JSON.parse(raw);
      index += 1;
      continue;
    }
    if (value === "--startup-timeout-ms") {
      options.startupTimeoutMs = Number(argv[index + 1]);
      index += 1;
      continue;
    }
    if (value === "--tool-timeout-ms") {
      options.toolTimeoutMs = Number(argv[index + 1]);
      index += 1;
      continue;
    }
    if (value === "--wait-text") {
      options.waitText = argv[index + 1];
      index += 1;
      continue;
    }
    if (value === "--wait-selector") {
      options.waitSelector = argv[index + 1];
      index += 1;
      continue;
    }
    if (value === "--script") {
      options.script = argv[index + 1];
      index += 1;
      continue;
    }
    if (value === "--help" || value === "-h") {
      printHelp();
      process.exit(0);
    }
    throw new Error(`Unknown argument: ${value}`);
  }

  return options;
}

function printHelp() {
  console.log(`
Usage:
  node ./verify-chrome-devtools-mcp.mjs [options]

Options:
  --url <url>                  URL to load after opening a new page
  --command <cmd>              MCP server command (default: npx)
  --args <json-array>          MCP server args as JSON array
  --startup-timeout-ms <ms>    MCP server startup timeout
  --tool-timeout-ms <ms>       Timeout for each MCP tool call
  --wait-text <text>           Text to wait for when tool schema supports text waits
  --wait-selector <selector>   CSS selector to wait for when tool schema supports selector waits
  --script <js-function>       JS function string for evaluate_script
  --help                       Show help

Default MCP server:
  npx -y chrome-devtools-mcp@latest --autoConnect
`.trim());
}

function summarizeContent(result) {
  if (!result || !Array.isArray(result.content)) {
    return result;
  }
  return result.content.map((item) => {
    if (item.type === "text") {
      return item.text;
    }
    return item;
  });
}

function getTool(tools, name) {
  const tool = tools.find((entry) => entry.name === name);
  if (!tool) {
    throw new Error(`Required MCP tool not found: ${name}`);
  }
  return tool;
}

function getSchemaProperties(tool) {
  const schema = tool.inputSchema ?? {};
  return schema.properties ?? {};
}

function hasProperty(tool, name) {
  return Object.prototype.hasOwnProperty.call(getSchemaProperties(tool), name);
}

function buildNewPageArgs(tool) {
  if (hasProperty(tool, "url")) {
    return { url: "about:blank" };
  }
  return {};
}

function buildNavigateArgs(tool, url) {
  if (hasProperty(tool, "url")) {
    return { url };
  }
  if (hasProperty(tool, "navigate")) {
    return { navigate: url };
  }
  throw new Error(`Don't know how to call navigate_page with schema: ${JSON.stringify(tool.inputSchema)}`);
}

function buildWaitArgs(tool, options) {
  if (hasProperty(tool, "selector")) {
    return { selector: options.waitSelector ?? "body", timeout: 10_000 };
  }
  if (hasProperty(tool, "text")) {
    return { text: [options.waitText], timeout: 10_000 };
  }
  if (hasProperty(tool, "timeout")) {
    return { timeout: 2_000 };
  }
  if (hasProperty(tool, "milliseconds")) {
    return { milliseconds: 2_000 };
  }
  return {};
}

function buildEvaluateArgs(tool, options) {
  const expression = options.script ?? `() => ({
    title: document.title,
    url: window.location.href,
    readyState: document.readyState,
    bodyLength: document.body?.innerText?.length ?? 0
  })`;
  if (hasProperty(tool, "function")) {
    return { function: expression };
  }
  if (hasProperty(tool, "expression")) {
    return { expression };
  }
  if (hasProperty(tool, "script")) {
    return { script: expression };
  }
  throw new Error(`Don't know how to call evaluate_script with schema: ${JSON.stringify(tool.inputSchema)}`);
}

function buildCloseArgs(tool, pageRef) {
  if (!tool.inputSchema?.required?.length) {
    return {};
  }
  if (pageRef?.pageIdx !== undefined && hasProperty(tool, "pageIdx")) {
    return { pageIdx: pageRef.pageIdx };
  }
  if (pageRef?.uid && hasProperty(tool, "uid")) {
    return { uid: pageRef.uid };
  }
  if (pageRef?.pageId && hasProperty(tool, "pageId")) {
    return { pageId: pageRef.pageId };
  }
  throw new Error(`close_page requires page reference, but none was captured: ${JSON.stringify(tool.inputSchema)}`);
}

function extractPageRef(listResult) {
  const texts = summarizeContent(listResult)
    .filter((item) => typeof item === "string")
    .join("\n");

  const idxMatch = texts.match(/pageIdx["']?\s*[:=]\s*(\d+)/i) ?? texts.match(/\[(\d+)\]/);
  const uidMatch = texts.match(/uid["']?\s*[:=]\s*["']([^"'\n]+)["']/i);
  const pageIdMatch = texts.match(/pageId["']?\s*[:=]\s*["']?([^"'\n]+)["']?/i);
  const selectedMatch = texts.match(/^\s*(\d+): .+\[selected\]\s*$/im);

  return {
    pageIdx: idxMatch ? Number(idxMatch[1]) : undefined,
    uid: uidMatch?.[1],
    pageId: pageIdMatch ? Number(pageIdMatch[1]) : (selectedMatch ? Number(selectedMatch[1]) : undefined),
  };
}

async function main() {
  const options = parseArgs(process.argv);
  const transport = new StdioClientTransport({
    command: options.command,
    args: options.args,
    stderr: "pipe",
    env: {
      ...process.env,
    },
  });

  const client = new Client(
    {
      name: "url-to-markdown-chrome-devtools-mcp-verify",
      version: "0.1.0",
    },
    {
      capabilities: {},
    },
  );

  const startupTimer = setTimeout(() => {
    console.error(`Timed out connecting to MCP server after ${options.startupTimeoutMs}ms`);
    process.exit(1);
  }, options.startupTimeoutMs);

  async function callToolWithTimeout(name, args) {
    return await Promise.race([
      client.callTool({
        name,
        arguments: args,
      }),
      new Promise((_, reject) => {
        setTimeout(() => {
          reject(new Error(`Tool ${name} timed out after ${options.toolTimeoutMs}ms. If Chrome showed an access prompt, click Allow and retry.`));
        }, options.toolTimeoutMs);
      }),
    ]);
  }

  try {
    await client.connect(transport);
    clearTimeout(startupTimer);

    const listed = await client.listTools();
    const tools = listed.tools ?? [];
    const toolNames = tools.map((tool) => tool.name).sort();
    console.log("Connected to chrome-devtools-mcp");
    console.log("Tools:", toolNames.join(", "));

    const newPageTool = getTool(tools, "new_page");
    const navigateTool = getTool(tools, "navigate_page");
    const waitTool = getTool(tools, "wait_for");
    const evalTool = getTool(tools, "evaluate_script");
    const closeTool = getTool(tools, "close_page");

    console.log("If Chrome prompts for DevTools access, click Allow.");

    console.log("\n1) new_page");
    const newPageResult = await callToolWithTimeout("new_page", buildNewPageArgs(newPageTool));
    console.log(JSON.stringify(summarizeContent(newPageResult), null, 2));

    let pageRef;
    if (toolNames.includes("list_pages")) {
      const listResult = await callToolWithTimeout("list_pages", {});
      console.log("\nlist_pages");
      console.log(JSON.stringify(summarizeContent(listResult), null, 2));
      pageRef = extractPageRef(listResult);
    }

    console.log("\n2) navigate_page");
    const navigateResult = await callToolWithTimeout("navigate_page", buildNavigateArgs(navigateTool, options.url));
    console.log(JSON.stringify(summarizeContent(navigateResult), null, 2));

    console.log("\n3) wait_for");
    const waitResult = await callToolWithTimeout("wait_for", buildWaitArgs(waitTool, options));
    console.log(JSON.stringify(summarizeContent(waitResult), null, 2));

    console.log("\n4) evaluate_script");
    const evalResult = await callToolWithTimeout("evaluate_script", buildEvaluateArgs(evalTool, options));
    console.log(JSON.stringify(summarizeContent(evalResult), null, 2));

    console.log("\n5) close_page");
    const closeResult = await callToolWithTimeout("close_page", buildCloseArgs(closeTool, pageRef));
    console.log(JSON.stringify(summarizeContent(closeResult), null, 2));

    console.log("\nValidation completed.");
  } finally {
    clearTimeout(startupTimer);
    await client.close().catch(() => {});
    await transport.close().catch(() => {});
  }
}

main().catch((error) => {
  console.error(error instanceof Error ? error.stack ?? error.message : String(error));
  process.exit(1);
});
