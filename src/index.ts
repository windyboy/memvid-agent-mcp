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
import { promises as fsPromises } from "fs";
import * as path from "path";
import { fileURLToPath } from "url";
import { create, use } from "@memvid/sdk";

// Setup logging
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Configure logging to stderr
const LOG_LEVELS = {
  DEBUG: 0,
  INFO: 1,
  WARNING: 2,
  ERROR: 3,
} as const;

const logLevel = (process.env.MEMVID_LOG_LEVEL || "WARNING").toUpperCase();
const logLevelNum = LOG_LEVELS[logLevel as keyof typeof LOG_LEVELS] ?? 2;

function log(level: string, message: string): void {
  const levelNum = LOG_LEVELS[level as keyof typeof LOG_LEVELS] ?? 2;

  if (levelNum >= logLevelNum) {
    const timestamp = new Date().toISOString();
    console.error(`[${timestamp}] [${level}] ${message}`);
  }
}

// ============================================================================
// Type Definitions
// ============================================================================

// Tool argument interfaces
interface MemvidCreateArgs {
  file_path: string;
  description?: string;
}

interface MemvidAddTextArgs {
  file_path: string;
  content: string;
  title?: string;
  uri?: string;
  tags?: Record<string, string>;
}

interface MemvidAddFileArgs {
  file_path: string;
  source_file: string;
  title?: string;
  tags?: Record<string, string>;
}

interface MemvidCommitArgs {
  file_path: string;
}

interface MemvidSearchArgs {
  file_path: string;
  query: string;
  top_k?: number;
  snippet_chars?: number;
}

interface MemvidSearchByTagArgs {
  file_path: string;
  tag_key: string;
  tag_value?: string;
  limit?: number;
}

interface MemvidInfoArgs {
  file_path: string;
}

interface MemvidListContentsArgs {
  file_path: string;
  limit?: number;
}

interface MemvidExportSearchResultsArgs {
  file_path: string;
  query: string;
  format?: string;
  top_k?: number;
}

// Memvid SDK instance interface
interface MemvidInstance {
  put(options: {
    title?: string;
    text?: string;
    file?: string;
    uri?: string;
    tags?: string[];
    metadata?: Record<string, string>;
  }): Promise<void>;
  seal?(): Promise<void>;
  find(
    query: string,
    options: { k: number; snippetChars: number }
  ): Promise<{ hits: Array<{ title?: string; score?: number; snippet?: string }> }>;
  timeline(options: { limit: number }): Promise<
    Array<{ uri?: string; preview?: string; timestamp?: number }>
  >;
  frame(uri: string): Promise<{ title?: string; tags?: string[] }>;
}

// ============================================================================
// Helper Functions
// ============================================================================

function normalizeFilePath(filePath: string): string {
  const expandedPath = filePath.startsWith("~")
    ? filePath.replace("~", process.env.HOME || "")
    : filePath;
  const resolved = path.resolve(expandedPath);

  // Optional: Validate against allowed directories
  const allowedDirs = process.env.MEMVID_ALLOWED_DIRS?.split(':');
  if (allowedDirs && allowedDirs.length > 0) {
    const isAllowed = allowedDirs.some(dir => {
      const normalizedDir = path.resolve(dir);
      return resolved.startsWith(normalizedDir);
    });

    if (!isAllowed) {
      throw new Error(
        `Access denied: ${resolved} is not in allowed directories`
      );
    }
  }

  return resolved;
}

function tagsObjectToList(
  tags: Record<string, string> | undefined
): string[] | undefined {
  if (!tags) return undefined;
  return Object.entries(tags).map(([key, value]) => `${key}:${value}`);
}

function validateRequiredString(value: unknown, fieldName: string): string {
  if (typeof value !== "string" || value.trim().length === 0) {
    throw new Error(`${fieldName} is required and must be a non-empty string`);
  }
  return value;
}

function validateOptionalNumber(
  value: unknown,
  fieldName: string,
  min?: number,
  max?: number
): number | undefined {
  if (value === undefined || value === null) return undefined;

  const num = Number(value);
  if (isNaN(num)) {
    throw new Error(`${fieldName} must be a valid number`);
  }

  if (min !== undefined && num < min) {
    throw new Error(`${fieldName} must be at least ${min}`);
  }

  if (max !== undefined && num > max) {
    throw new Error(`${fieldName} must be at most ${max}`);
  }

  return num;
}

async function getMemvidInstance(
  filePath: string,
  createIfMissing: boolean = false
): Promise<MemvidInstance> {
  const normalizedPath = normalizeFilePath(filePath);
  const parentDir = path.dirname(normalizedPath);

  if (createIfMissing && parentDir) {
    await fsPromises.mkdir(parentDir, { recursive: true });
  }

  let fileExists = false;
  try {
    await fsPromises.access(normalizedPath);
    fileExists = true;
  } catch {
    fileExists = false;
  }

  if (!fileExists) {
    if (!createIfMissing) {
      throw new Error(`Memory file not found: ${normalizedPath}`);
    }
    const mem = await create(normalizedPath);
    log("INFO", `Created new memory file: ${normalizedPath}`);
    return mem as unknown as MemvidInstance;
  }

  const stats = await fsPromises.stat(normalizedPath);
  if (stats.size === 0) {
    if (createIfMissing) {
      const mem = await create(normalizedPath);
      log("INFO", `Created new memory file: ${normalizedPath}`);
      return mem as unknown as MemvidInstance;
    }
    throw new Error(
      `Memory file is empty or invalid at: ${normalizedPath}. Delete and recreate it.`
    );
  }

  try {
    const mem = await use("basic", normalizedPath, { mode: "open" });
    log("INFO", `Opened existing memory file: ${normalizedPath}`);
    return mem as unknown as MemvidInstance;
  } catch (error) {
    if (createIfMissing) {
      const mem = await create(normalizedPath);
      log("INFO", `Created new memory file: ${normalizedPath}`);
      return mem as unknown as MemvidInstance;
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
      await fsPromises.mkdir(parentDir, { recursive: true });
    }

    let fileExists = false;
    try {
      await fsPromises.access(normalizedPath);
      fileExists = true;
    } catch {
      fileExists = false;
    }

    if (fileExists) {
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
    validateRequiredString(filePath, "file_path");
    validateRequiredString(content, "content");

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
    validateRequiredString(filePath, "file_path");
    validateRequiredString(sourceFile, "source_file");

    const normalizedSource = normalizeFilePath(sourceFile);

    try {
      await fsPromises.access(normalizedSource);
    } catch {
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
    validateRequiredString(filePath, "file_path");
    validateRequiredString(query, "query");
    const validatedTopK = validateOptionalNumber(topK, "top_k", 1, 100) ?? topK;
    const validatedSnippetChars = validateOptionalNumber(snippetChars, "snippet_chars", 1, 10000) ?? snippetChars;

    const normalizedPath = normalizeFilePath(filePath);
    const mem = await getMemvidInstance(filePath);

    const response = await mem.find(query, { k: validatedTopK, snippetChars: validatedSnippetChars });

    const hits = response.hits || [];
    if (hits.length === 0) {
      return `No results found for query: ${query}`;
    }

    const results: string[] = [
      `Search Results for: '${query}'`,
      "=".repeat(50),
    ];

    hits.forEach((hit: { title?: string; score?: number; snippet?: string }, i: number) => {
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
  tagValue: string = "",
  limit: number = 10000
): Promise<string> {
  try {
    validateRequiredString(filePath, "file_path");
    validateRequiredString(tagKey, "tag_key");
    const validatedLimit = validateOptionalNumber(limit, "limit", 1, 100000) ?? limit;

    const normalizedPath = normalizeFilePath(filePath);
    const mem = await getMemvidInstance(filePath);

    const entries = await mem.timeline({ limit: validatedLimit });

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
      } catch (error) {
        log("WARNING", `Failed to access frame ${uri}: ${String(error)}`);
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

    try {
      await fsPromises.access(normalizedPath);
    } catch {
      return `ERROR: Memory file not found: ${normalizedPath}`;
    }

    const stat = await fsPromises.stat(normalizedPath);
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

    for (let i = 0; i < entries.length; i++) {
      const entry = entries[i];
      const uri = entry.uri;
      let title = "Untitled";

      if (uri) {
        try {
          const frame = await mem.frame(uri);
          title = frame.title || title;
        } catch (error) {
          log("WARNING", `Failed to get frame title for ${uri}: ${String(error)}`);
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
    }

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
        await fsPromises.readFile(
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
      "Create a new Memvid memory file (.mv2 format). This file stores all memory data, embeddings, and indices in a single portable file. Use this to initialize a new memory storage location. Supports tilde (~) expansion for home directory paths.",
    inputSchema: {
      type: "object",
      properties: {
        file_path: {
          type: "string",
          description:
            "Path where the memory file will be created. Supports absolute paths, relative paths, and tilde (~) expansion for home directory (e.g., 'memory.mv2', '~/.codex/memory/memvid.mv2'). The parent directory will be created if it doesn't exist.",
        },
        description: {
          type: "string",
          description: "Optional description of the memory's purpose. This can help document the intended use case of the memory file.",
        },
      },
      required: ["file_path"],
    },
  },
  {
    name: "memvid_add_text",
    description:
      "Add text content to memory with optional metadata. The content is automatically indexed for semantic search and can be organized using tags. Use this for storing decisions, preferences, constraints, and other persistent information. Tags are converted from key-value pairs to 'key:value' format internally. Input validation: file_path and content must be non-empty strings.",
    inputSchema: {
      type: "object",
      properties: {
        file_path: {
          type: "string",
          description: "Path to the memory file. Supports tilde (~) expansion. The file will be created if it doesn't exist.",
        },
        content: {
          type: "string",
          description: "Text content to add to memory. This will be indexed for semantic search, so use clear, descriptive text for better search results.",
        },
        title: {
          type: "string",
          description: "Optional title for the content. Helps identify entries when browsing or searching. If omitted, entries may be labeled as 'Untitled'.",
        },
        uri: {
          type: "string",
          description: "Optional URI identifier for the content (e.g., 'mv2://documents/note-001'). Useful for creating structured references between entries.",
        },
        tags: {
          type: "object",
          description: "Optional dictionary of tags for categorization (e.g., {'type': 'decision', 'project': 'backend'}). Tags are converted to 'key:value' format internally. Recommended keys: type, category, project, status.",
          additionalProperties: { type: "string" },
        },
      },
      required: ["file_path", "content"],
    },
  },
  {
    name: "memvid_add_file",
    description:
      "Read a file from disk and add its content to memory. The file content is indexed for semantic search. Use this to import documents, configuration files, or other text-based files into memory. If title is not provided, the filename will be used as the title. Input validation: file_path and source_file must be non-empty strings.",
    inputSchema: {
      type: "object",
      properties: {
        file_path: {
          type: "string",
          description: "Path to the memory file. Supports tilde (~) expansion. The file will be created if it doesn't exist.",
        },
        source_file: {
          type: "string",
          description: "Path to the source file to add. Must be an absolute or relative path to an existing file. The file will be read and its content added to memory.",
        },
        title: {
          type: "string",
          description: "Optional title for the content. If omitted, the basename of the source file will be used as the title.",
        },
        tags: {
          type: "object",
          description: "Optional dictionary of tags for categorization (e.g., {'type': 'file', 'category': 'config'}). Tags are converted to 'key:value' format internally.",
          additionalProperties: { type: "string" },
        },
      },
      required: ["file_path", "source_file"],
    },
  },
  {
    name: "memvid_commit",
    description:
      "Commit and persist all pending changes to the memory file. Ensures that all previously added content is safely written to disk. Some SDK versions may auto-persist changes, but calling this explicitly is recommended after batch operations or when data integrity is critical.",
    inputSchema: {
      type: "object",
      properties: {
        file_path: {
          type: "string",
          description: "Path to the memory file. Supports tilde (~) expansion.",
        },
      },
      required: ["file_path"],
    },
  },
  {
    name: "memvid_search",
    description:
      "Perform semantic search across memory content using natural language queries. Returns the most relevant results based on semantic similarity, ordered by relevance score. Use natural language questions or descriptive phrases for best results (e.g., 'What database did we choose?' or 'code style preferences'). Input validation: file_path and query must be non-empty strings; top_k must be 1-100; snippet_chars must be 1-10000.",
    inputSchema: {
      type: "object",
      properties: {
        file_path: {
          type: "string",
          description: "Path to the memory file. Supports tilde (~) expansion.",
        },
        query: {
          type: "string",
          description: "Search query in natural language. Use descriptive questions or phrases rather than keywords for better semantic matching (e.g., 'What database did we choose?' instead of 'database').",
        },
        top_k: {
          type: "number",
          description: "Number of top results to return (default: 5). Typically 5-10 results are sufficient for most use cases. Higher values may reduce precision.",
        },
        snippet_chars: {
          type: "number",
          description: "Maximum characters to return in result snippets (default: 200). Longer snippets provide more context but increase response size.",
        },
      },
      required: ["file_path", "query"],
    },
  },
  {
    name: "memvid_search_by_tag",
    description:
      "Search memory by tag key-value pairs. Returns all entries that match the specified tag criteria. This is typically faster than semantic search when you know the exact tags. If tag_value is provided, matches exact 'key:value' pairs; if omitted, matches any entry with the tag key (regardless of value). Input validation: file_path and tag_key must be non-empty strings; limit must be 1-100000.",
    inputSchema: {
      type: "object",
      properties: {
        file_path: {
          type: "string",
          description: "Path to the memory file. Supports tilde (~) expansion.",
        },
        tag_key: {
          type: "string",
          description: "Tag key to search for (e.g., 'type', 'project', 'category'). If tag_value is not provided, matches any entry with this tag key.",
        },
        tag_value: {
          type: "string",
          description: "Optional tag value to match. If provided, only entries with exact 'key:value' tag match. If omitted, returns all entries with the tag key (any value).",
        },
        limit: {
          type: "number",
          description: "Maximum number of entries to fetch from timeline (default: 10000). Higher values allow searching through more entries but may impact performance.",
        },
      },
      required: ["file_path", "tag_key"],
    },
  },
  {
    name: "memvid_info",
    description:
      "Get metadata and statistics about a memory file. Returns file size (in MB), creation time, and last modification time. Useful for monitoring memory file growth and understanding file status.",
    inputSchema: {
      type: "object",
      properties: {
        file_path: {
          type: "string",
          description: "Path to the memory file. Supports tilde (~) expansion. The file must exist.",
        },
      },
      required: ["file_path"],
    },
  },
  {
    name: "memvid_list_contents",
    description:
      "List entries in the memory file in chronological order (timeline). Returns entries with their titles, timestamps, and previews. Useful for browsing all stored content or reviewing recent additions. Results are ordered by creation time.",
    inputSchema: {
      type: "object",
      properties: {
        file_path: {
          type: "string",
          description: "Path to the memory file. Supports tilde (~) expansion.",
        },
        limit: {
          type: "number",
          description: "Maximum number of entries to return (default: 20). Use higher values to see more entries, but note that very large limits may impact performance.",
        },
      },
      required: ["file_path"],
    },
  },
  {
    name: "memvid_get_status",
    description:
      "Get the status and version information of the Memvid MCP server. Returns server version, Memvid SDK version, available features, and server health status. Useful for debugging and verifying server configuration.",
    inputSchema: {
      type: "object",
      properties: {},
    },
  },
  {
    name: "memvid_export_search_results",
    description:
      "Perform a semantic search and export the results in a specified format. Combines memvid_search with format conversion. Useful for generating reports, documentation, or structured data from search queries. Supports text (human-readable), JSON (structured data), and Markdown (formatted documentation) formats.",
    inputSchema: {
      type: "object",
      properties: {
        file_path: {
          type: "string",
          description: "Path to the memory file. Supports tilde (~) expansion.",
        },
        query: {
          type: "string",
          description: "Search query in natural language (same as memvid_search).",
        },
        format: {
          type: "string",
          description: "Output format: 'text' (human-readable, default), 'json' (structured JSON), or 'markdown' (formatted Markdown).",
        },
        top_k: {
          type: "number",
          description: "Number of results to include in the export (default: 10).",
        },
      },
      required: ["file_path", "query"],
    },
  },
];

async function main(): Promise<void> {
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
        case "memvid_create": {
          const createArgs = args as unknown as MemvidCreateArgs;
          result = await memvidCreate(
            createArgs.file_path,
            createArgs.description || ""
          );
          break;
        }
        case "memvid_add_text": {
          const addTextArgs = args as unknown as MemvidAddTextArgs;
          result = await memvidAddText(
            addTextArgs.file_path,
            addTextArgs.content,
            addTextArgs.title || "",
            addTextArgs.uri || "",
            addTextArgs.tags
          );
          break;
        }
        case "memvid_add_file": {
          const addFileArgs = args as unknown as MemvidAddFileArgs;
          result = await memvidAddFile(
            addFileArgs.file_path,
            addFileArgs.source_file,
            addFileArgs.title || "",
            addFileArgs.tags
          );
          break;
        }
        case "memvid_commit": {
          const commitArgs = args as unknown as MemvidCommitArgs;
          result = await memvidCommit(commitArgs.file_path);
          break;
        }
        case "memvid_search": {
          const searchArgs = args as unknown as MemvidSearchArgs;
          result = await memvidSearch(
            searchArgs.file_path,
            searchArgs.query,
            searchArgs.top_k || 5,
            searchArgs.snippet_chars || 200
          );
          break;
        }
        case "memvid_search_by_tag": {
          const searchByTagArgs = args as unknown as MemvidSearchByTagArgs;
          result = await memvidSearchByTag(
            searchByTagArgs.file_path,
            searchByTagArgs.tag_key,
            searchByTagArgs.tag_value || "",
            searchByTagArgs.limit || 10000
          );
          break;
        }
        case "memvid_info": {
          const infoArgs = args as unknown as MemvidInfoArgs;
          result = await memvidInfo(infoArgs.file_path);
          break;
        }
        case "memvid_list_contents": {
          const listContentsArgs = args as unknown as MemvidListContentsArgs;
          result = await memvidListContents(
            listContentsArgs.file_path,
            listContentsArgs.limit || 20
          );
          break;
        }
        case "memvid_get_status":
          result = await memvidGetStatus();
          break;
        case "memvid_export_search_results": {
          const exportArgs = args as unknown as MemvidExportSearchResultsArgs;
          result = await memvidExportSearchResults(
            exportArgs.file_path,
            exportArgs.query,
            exportArgs.format || "text",
            exportArgs.top_k || 10
          );
          break;
        }
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
