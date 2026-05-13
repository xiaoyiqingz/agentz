# agentz

## Setup

Install project dependencies:

```bash
uv sync
```

Install project-local Codex skills:

```bash
uvx library-skills --all
```

This command installs library-provided skills into the project's `.agents/` directory.

## Run

Start the CLI app with:

```bash
uv run main.py
```

## MCP config

The app now supports loading MCP servers from a project-level `mcp.json`.
By default it reads `./mcp.json` from the current project directory.
You can override the location in `.env`:

```bash
MCP_CONFIG_PATH=/absolute/path/to/mcp.json
```

Example `mcp.json`:

```json
{
  "mcpServers": {
    "mysql": {
      "command": "${MYSQL_MCP_COMMAND}",
      "args": [],
      "env": {
        "MYSQL_HOST": "${MYSQL_HOST}",
        "MYSQL_PORT": "${MYSQL_PORT}",
        "MYSQL_USER": "${MYSQL_USER}",
        "MYSQL_PASS": "${MYSQL_PASS}",
        "MYSQL_DB": "${MYSQL_DB}",
        "ALLOW_INSERT_OPERATION": "${ALLOW_INSERT_OPERATION:-false}",
        "ALLOW_UPDATE_OPERATION": "${ALLOW_UPDATE_OPERATION:-false}",
        "ALLOW_DELETE_OPERATION": "${ALLOW_DELETE_OPERATION:-false}"
      }
    }
  }
}
```
