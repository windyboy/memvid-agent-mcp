#!/usr/bin/env node

/**
 * Memvid MCP Server (TypeScript)
 *
 * A Model Context Protocol (MCP) server that exposes Memvid memory management
 * capabilities to AI clients like Claude Desktop and Codex CLI.
 *
 * This server provides tools for:
 * - Creating and managing memory files (.mv2)
 * - Adding text and file content to memory
 * - Searching memory with semantic queries
 * - Managing memory timeline and history
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool,
} from "@modelcontextprotocol/sdk/types.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import * as fs from "fs";
import * as path from "path";
import { fileURLToPath } from "url";
import { create, use } from "@memvid/sdk";

// Setup logging
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Configure logging to stderr
const logLevel = (process.env.MEMVID_LOG_LEVEL || "WARNING").toUpperCase();
const logLevelNum = {
  DEBUG: 0,
  INFO: 1,
  WARNING: 2,
  ERROR: 3,
}[logLevel] ?? 2;

function log(level: string, message: string): void {
  const levelNum = {
    DEBUG: 0,
    INFO: 1,
    WARNING: 2,
    ERROR: 3,
  }[level] ?? 2;

  if (levelNum >= logLevelNum) {
    const timestamp = new Date().toISOString();
    console.error(`[${timestamp}] [${level}] ${message}`);
  }
}

// ============================================================================
// Helper Functions
// ============================================================================

function normalizeFilePath(filePath: string): string {
  const expandedPath = filePath.startsWith("~")
    ? filePath.replace("~", process.env.HOME || "")
    : filePath;
  return path.resolve(expandedPath);
}

function tagsObjectToList(
  tags: Record<string, string> | undefined
): string[] | undefined {
  if (!tags) return undefined;
  return Object.entries(tags).map(([key, value]) => `${key}:${value}`);
}

async function getMemvidInstance(
  filePath: string,
  createIfMissing: boolean = false
): Promise<any> {
  const normalizedPath = normalizeFilePath(filePath);
  const parentDir = path.dirname(normalizedPath);

  if (createIfMissing && parentDir) {
    fs.mkdirSync(parentDir, { recursive: true });
  }

  if (!fs.existsSync(normalizedPath)) {
    if (!createIfMissing) {
      throw new Error(`Memory file not found: ${normalizedPath}`);
    }
    const mem = await create(normalizedPath);
    log("INFO", `Created new memory file: ${normalizedPath}`);
    return mem;
  }

  const stats = fs.statSync(normalizedPath);
  if (stats.size === 0) {
    if (createIfMissing) {
      const mem = await create(normalizedPath);
      log("INFO", `Created new memory file: ${normalizedPath}`);
      return mem;
    }
    throw new Error(
      `Memory file is empty or invalid at: ${normalizedPath}. Delete and recreate it.`
    );
  }

  try {
    const mem = await use("basic", normalizedPath, { mode: "open" });
    log("INFO", `Opened existing memory file: ${normalizedPath}`);
    return mem;
  } catch (error) {
    if (createIfMissing) {
      const mem = await create(normalizedPath);
      log("INFO", `Created new memory file: ${normalizedPath}`);
      return mem;
    }
    throw error;
  }
}

// ============================================================================
// Tool Implementations
// ============================================================================

async function memvidCreate(
  filePath: string,
  _description: string = ""
): Promise<string> {
  try {
    const normalizedPath = normalizeFilePath(filePath);
    const parentDir = path.dirname(normalizedPath);

    if (parentDir) {
      fs.mkdirSync(parentDir, { recursive: true });
    }

    if (fs.existsSync(normalizedPath)) {
      return `Memory file already exists at: ${normalizedPath}`;
    }

    await create(normalizedPath);
    log("INFO", `Created memory file: ${normalizedPath}`);
    return `Successfully created memory file at: ${normalizedPath}`;
  } catch (error) {
    log("ERROR", `Failed to create memory file: ${String(error)}`);
    return `ERROR: Failed to create memory file: ${String(error)}`;
  }
}

async function memvidAddText(
  filePath: string,
  content: string,
  title: string = "",
  uri: string = "",
  tags: Record<string, string> | undefined = undefined
): Promise<string> {
  try {
    const mem = await getMemvidInstance(filePath, true);

    const tagList = tagsObjectToList(tags);
    await mem.put({
      title: title || undefined,
      text: content,
      uri: uri || undefined,
      tags: tagList,
      metadata: tags,
    });

    log("INFO", `Added text to memory: ${filePath} (title: ${title})`);
    return `Successfully added text to memory. Title: ${title || "Untitled"}`;
  } catch (error) {
    log("ERROR", `Failed to add text to memory: ${String(error)}`);
    return `ERROR: Failed to add text: ${String(error)}`;
  }
}

async function memvidAddFile(
  filePath: string,
  sourceFile: string,
  title: string = "",
  tags: Record<string, string> | undefined = undefined
): Promise<string> {
  try {
    const normalizedSource = normalizeFilePath(sourceFile);

    if (!fs.existsSync(normalizedSource)) {
      return `ERROR: Source file not found: ${normalizedSource}`;
    }

    const mem = await getMemvidInstance(filePath, true);
    const tagList = tagsObjectToList(tags);
    const fileUri = path.resolve(normalizedSource);

    await mem.put({
      title: title || path.basename(normalizedSource),
      file: normalizedSource,
      uri: fileUri,
      tags: tagList,
      metadata: tags,
    });

    log("INFO", `Added file to memory: ${normalizedSource} (title: ${title})`);
    return `Successfully added file to memory. Title: ${title || "Untitled"}`;
  } catch (error) {
    log("ERROR", `Failed to add file to memory: ${String(error)}`);
    return `ERROR: Failed to add file: ${String(error)}`;
  }
}

async function memvidCommit(filePath: string): Promise<string> {
  try {
    const normalizedPath = normalizeFilePath(filePath);
    const mem = await getMemvidInstance(filePath);

    if (typeof mem.seal === "function") {
      await mem.seal();
      log("INFO", `Committed changes to memory: ${normalizedPath}`);
      return `Successfully committed changes to memory file: ${normalizedPath}`;
    }

    log("INFO", `Commit not supported by memvid-sdk: ${normalizedPath}`);
    return "Commit not supported by memvid-sdk; changes are already persisted.";
  } catch (error) {
    log("ERROR", `Failed to commit memory: ${String(error)}`);
    return `ERROR: Failed to commit: ${String(error)}`;
  }
}

async function memvidSearch(
  filePath: string,
  query: string,
  topK: number = 5,
  snippetChars: number = 200
): Promise<string> {
  try {
    const normalizedPath = normalizeFilePath(filePath);
    const mem = await getMemvidInstance(filePath);

    const response = await mem.find(query, { k: topK, snippetChars });

    const hits = response.hits || [];
    if (hits.length === 0) {
      return `No results found for query: ${query}`;
    }

    const results: string[] = [
      `Search Results for: '${query}'`,
      "=".repeat(50),
    ];

    hits.forEach((hit: any, i: number) => {
      const title = hit.title || "Untitled";
      const score = hit.score ?? "N/A";
      const snippet = hit.snippet || "";
      const text =
        snippet.length > snippetChars
          ? snippet.substring(0, snippetChars) + "..."
          : snippet;

      results.push(`\n[${i + 1}] ${title}`);
      results.push(`Score: ${score}`);
      results.push(`Text: ${text}`);
    });

    log(
      "INFO",
      `Searched memory: ${normalizedPath} (query: ${query}, results: ${hits.length})`
    );
    return results.join("\n");
  } catch (error) {
    log("ERROR", `Failed to search memory: ${String(error)}`);
    return `ERROR: Failed to search: ${String(error)}`;
  }
}

async function memvidSearchByTag(
  filePath: string,
  tagKey: string,
  tagValue: string = ""
): Promise<string> {
  try {
    const normalizedPath = normalizeFilePath(filePath);
    const mem = await getMemvidInstance(filePath);

    const entries = await mem.timeline({ limit: 500 });

    const matchToken = tagValue ? `${tagKey}:${tagValue}` : null;
    const results: string[] = [
      `Tag Search Results for: '${tagKey}=${tagValue}'`,
      "=".repeat(50),
    ];
    let matched = 0;

    for (const entry of entries) {
      const uri = entry.uri;
      if (!uri) continue;

      try {
        const frame = await mem.frame(uri);
        const frameTags = frame.tags || [];

        let matchedTag = false;
        if (matchToken) {
          matchedTag = frameTags.includes(matchToken);
        } else {
          matchedTag = frameTags.some(
            (tag: string) =>
              tag === tagKey || tag.startsWith(`${tagKey}:`)
          );
        }

        if (!matchedTag) continue;

        matched++;
        const title = frame.title || "Untitled";
        const preview = entry.preview || "";

        results.push(`\n[${matched}] ${title}`);
        results.push(
          `Tags: ${frameTags.length > 0 ? frameTags.join(", ") : "None"}`
        );
        if (preview) {
          results.push(`Preview: ${preview}`);
        }
      } catch {
        // Skip frames that can't be accessed
        continue;
      }
    }

    if (matched === 0) {
      return `No results found for tag: ${tagKey}=${tagValue}`;
    }

    log(
      "INFO",
      `Searched memory by tag: ${normalizedPath} (tag: ${tagKey}=${tagValue}, results: ${matched})`
    );
    return results.join("\n");
  } catch (error) {
    log("ERROR", `Failed to search by tag: ${String(error)}`);
    return `ERROR: Failed to search by tag: ${String(error)}`;
  }
}

async function memvidInfo(filePath: string): Promise<string> {
  try {
    const normalizedPath = normalizeFilePath(filePath);

    if (!fs.existsSync(normalizedPath)) {
      return `ERROR: Memory file not found: ${normalizedPath}`;
    }

    const stat = fs.statSync(normalizedPath);
    const sizeMb = stat.size / (1024 * 1024);

    const infoLines = [
      `Memory File: ${normalizedPath}`,
      `Size: ${sizeMb.toFixed(2)} MB`,
      `Created: ${stat.birthtime}`,
      `Modified: ${stat.mtime}`,
    ];

    log("INFO", `Retrieved info for memory: ${normalizedPath}`);
    return infoLines.join("\n");
  } catch (error) {
    log("ERROR", `Failed to get memory info: ${String(error)}`);
    return `ERROR: Failed to get info: ${String(error)}`;
  }
}

async function memvidListContents(
  filePath: string,
  limit: number = 20
): Promise<string> {
  try {
    const normalizedPath = normalizeFilePath(filePath);
    const mem = await getMemvidInstance(filePath);

    const entries = await mem.timeline({ limit });

    if (entries.length === 0) {
      return `No entries found in memory: ${normalizedPath}`;
    }

    const results: string[] = [
      `Memory Contents (limit: ${limit})`,
      "=".repeat(50),
    ];

    entries.forEach((entry: any, i: number) => {
      const uri = entry.uri;
      let title = "Untitled";

      if (uri) {
        try {
          const frame = mem.frame(uri);
          title = frame.title || title;
        } catch {
          // Use default title
        }
      }

      const preview = entry.preview || "";
      const timestamp = entry.timestamp;

      results.push(`\n[${i + 1}] ${title}`);
      if (timestamp !== undefined) {
        results.push(`Timestamp: ${timestamp}`);
      }
      if (preview) {
        results.push(`Preview: ${preview}`);
      }
    });

    log("INFO", `Listed contents of memory: ${normalizedPath}`);
    return results.join("\n");
  } catch (error) {
    log("ERROR", `Failed to list memory contents: ${String(error)}`);
    return `ERROR: Failed to list contents: ${String(error)}`;
  }
}

async function memvidGetStatus(): Promise<string> {
  try {
    let memvidVersion = "unknown";
    try {
      const packageJson = JSON.parse(
        fs.readFileSync(
          path.join(__dirname, "../node_modules/@memvid/sdk/package.json"),
          "utf-8"
        )
      );
      memvidVersion = packageJson.version || "unknown";
    } catch {
      memvidVersion = "not installed";
    }

    const statusLines = [
      "Memvid MCP Server Status",
      "=".repeat(50),
      "Server Version: 0.2.0",
      `Memvid SDK Version: ${memvidVersion}`,
      "MCP SDK: Available",
      "",
      "Available Features:",
      "✓ Memory creation and management",
      "✓ Text content addition",
      "✓ File content import",
      "✓ Semantic search",
      "✓ Tag-based search",
      "✓ Memory info and listing",
      "",
      "Status: Ready",
    ];

    log("INFO", "Server status requested");
    return statusLines.join("\n");
  } catch (error) {
    log("ERROR", `Failed to get status: ${String(error)}`);
    return `ERROR: Failed to get status: ${String(error)}`;
  }
}

async function memvidExportSearchResults(
  filePath: string,
  query: string,
  format: string = "text",
  topK: number = 10
): Promise<string> {
  try {
    const results = await memvidSearch(filePath, query, topK);

    if (format.toLowerCase() === "json") {
      return JSON.stringify({ query, results }, null, 2);
    } else if (format.toLowerCase() === "markdown") {
      return `# Search Results: ${query}\n\n${results}`;
    } else {
      return results;
    }
  } catch (error) {
    log("ERROR", `Failed to export search results: ${String(error)}`);
    return `ERROR: Failed to export results: ${String(error)}`;
  }
}

// ============================================================================
// MCP Server Setup
// ============================================================================

const tools: Tool[] = [
  {
    name: "memvid_create",
    description:
      "Create a new Memvid memory file. This file will store all memory data, embeddings, and indices in a single portable file.",
    inputSchema: {
      type: "object",
      properties: {
        file_path: {
          type: "string",
          description:
            "Path where the memory file will be created (e.g., 'memory.mv2')",
        },
        description: {
          type: "string",
          description: "Optional description of the memory's purpose",
        },
      },
      required: ["file_path"],
    },
  },
  {
    name: "memvid_add_text",
    description:
      "Add text content to memory. The content is indexed for semantic search and can be tagged for organization.",
    inputSchema: {
      type: "object",
      properties: {
        file_path: {
          type: "string",
          description: "Path to the memory file",
        },
        content: {
          type: "string",
          description: "Text content to add",
        },
        title: {
          type: "string",
          description: "Optional title for the content",
        },
        uri: {
          type: "string",
          description: "Optional URI identifier (e.g., 'mv2://documents/note-001')",
        },
        tags: {
          type: "object",
          description: "Optional dictionary of tags for categorization",
          additionalProperties: { type: "string" },
        },
      },
      required: ["file_path", "content"],
    },
  },
  {
    name: "memvid_add_file",
    description:
      "Add file content to memory. Reads a file from disk and adds its content to the memory.",
    inputSchema: {
      type: "object",
      properties: {
        file_path: {
          type: "string",
          description: "Path to the memory file",
        },
        source_file: {
          type: "string",
          description: "Path to the source file to add",
        },
        title: {
          type: "string",
          description: "Optional title for the content",
        },
        tags: {
          type: "object",
          description: "Optional dictionary of tags",
          additionalProperties: { type: "string" },
        },
      },
      required: ["file_path", "source_file"],
    },
  },
  {
    name: "memvid_commit",
    description:
      "Commit changes to memory file. Saves all pending changes to ensure they are persisted.",
    inputSchema: {
      type: "object",
      properties: {
        file_path: {
          type: "string",
          description: "Path to the memory file",
        },
      },
      required: ["file_path"],
    },
  },
  {
    name: "memvid_search",
    description:
      "Search memory with semantic query. Performs semantic search to find relevant content.",
    inputSchema: {
      type: "object",
      properties: {
        file_path: {
          type: "string",
          description: "Path to the memory file",
        },
        query: {
          type: "string",
          description: "Search query (natural language)",
        },
        top_k: {
          type: "number",
          description: "Number of top results to return (default: 5)",
        },
        snippet_chars: {
          type: "number",
          description: "Maximum characters to return in snippets (default: 200)",
        },
      },
      required: ["file_path", "query"],
    },
  },
  {
    name: "memvid_search_by_tag",
    description:
      "Search memory by tags. Finds content that has been tagged with specific key-value pairs.",
    inputSchema: {
      type: "object",
      properties: {
        file_path: {
          type: "string",
          description: "Path to the memory file",
        },
        tag_key: {
          type: "string",
          description: "Tag key to search for",
        },
        tag_value: {
          type: "string",
          description: "Optional tag value to match",
        },
      },
      required: ["file_path", "tag_key"],
    },
  },
  {
    name: "memvid_info",
    description:
      "Get information about memory file. Returns metadata including size, creation time, and modification time.",
    inputSchema: {
      type: "object",
      properties: {
        file_path: {
          type: "string",
          description: "Path to the memory file",
        },
      },
      required: ["file_path"],
    },
  },
  {
    name: "memvid_list_contents",
    description: "List contents of memory file. Lists all or recent entries.",
    inputSchema: {
      type: "object",
      properties: {
        file_path: {
          type: "string",
          description: "Path to the memory file",
        },
        limit: {
          type: "number",
          description: "Maximum number of entries to return (default: 20)",
        },
      },
      required: ["file_path"],
    },
  },
  {
    name: "memvid_get_status",
    description:
      "Get Memvid MCP server status. Returns information about the server including version and available features.",
    inputSchema: {
      type: "object",
      properties: {},
    },
  },
  {
    name: "memvid_export_search_results",
    description:
      "Export search results in specified format (text, json, or markdown).",
    inputSchema: {
      type: "object",
      properties: {
        file_path: {
          type: "string",
          description: "Path to the memory file",
        },
        query: {
          type: "string",
          description: "Search query",
        },
        format: {
          type: "string",
          description: "Output format ('text', 'json', or 'markdown')",
        },
        top_k: {
          type: "number",
          description: "Number of results to include (default: 10)",
        },
      },
      required: ["file_path", "query"],
    },
  },
];

async function main() {
  const server = new Server(
    {
      name: "memvid",
      version: "0.2.0",
    },
    {
      capabilities: {
        tools: {},
      },
    }
  );

  server.setRequestHandler(ListToolsRequestSchema, async () => ({
    tools,
  }));

  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { name, arguments: args } = request.params;
    let result: string;

    if (!args || typeof args !== "object") {
      return {
        content: [
          {
            type: "text" as const,
            text: "ERROR: Invalid arguments",
          },
        ],
      };
    }

    try {
      switch (name) {
        case "memvid_create":
          result = await memvidCreate(
            (args as any).file_path as string,
            ((args as any).description as string) || ""
          );
          break;
        case "memvid_add_text":
          result = await memvidAddText(
            (args as any).file_path as string,
            (args as any).content as string,
            ((args as any).title as string) || "",
            ((args as any).uri as string) || "",
            (args as any).tags as Record<string, string> | undefined
          );
          break;
        case "memvid_add_file":
          result = await memvidAddFile(
            (args as any).file_path as string,
            (args as any).source_file as string,
            ((args as any).title as string) || "",
            (args as any).tags as Record<string, string> | undefined
          );
          break;
        case "memvid_commit":
          result = await memvidCommit((args as any).file_path as string);
          break;
        case "memvid_search":
          result = await memvidSearch(
            (args as any).file_path as string,
            (args as any).query as string,
            ((args as any).top_k as number) || 5,
            ((args as any).snippet_chars as number) || 200
          );
          break;
        case "memvid_search_by_tag":
          result = await memvidSearchByTag(
            (args as any).file_path as string,
            (args as any).tag_key as string,
            ((args as any).tag_value as string) || ""
          );
          break;
        case "memvid_info":
          result = await memvidInfo((args as any).file_path as string);
          break;
        case "memvid_list_contents":
          result = await memvidListContents(
            (args as any).file_path as string,
            ((args as any).limit as number) || 20
          );
          break;
        case "memvid_get_status":
          result = await memvidGetStatus();
          break;
        case "memvid_export_search_results":
          result = await memvidExportSearchResults(
            (args as any).file_path as string,
            (args as any).query as string,
            ((args as any).format as string) || "text",
            ((args as any).top_k as number) || 10
          );
          break;
        default:
          result = `ERROR: Unknown tool: ${name}`;
      }
    } catch (error) {
      result = `ERROR: ${String(error)}`;
    }

    return {
      content: [
        {
          type: "text" as const,
          text: result,
        },
      ],
    };
  });

  const transport = new StdioServerTransport();
  await server.connect(transport);

  log("INFO", "Memvid MCP Server started");
}

main().catch((error) => {
  log("ERROR", `Server error: ${String(error)}`);
  process.exit(1);
});
