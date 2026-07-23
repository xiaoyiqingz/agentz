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
# or bind a specific project directory to this session
uv run main.py --project-path /path/to/project
# or resume an existing session and restore its bound project directory
uv run main.py --resume <session_id>
```

Current runtime layout:

```text
main.py                 # CLI startup entry
core/                   # runtime orchestration
config/                 # settings loading
ui/cli/                 # terminal input/output
ui/web/                 # web UI placeholder
interfaces/http/        # HTTP interface placeholder
infra/                  # observability and infrastructure
scripts/run_tests.py    # test runner helper
```

Session data is stored under:

```text
${AGENTZ_HOME:-~/.agentz}/sessions/<session_id>/
```

By default `AGENTZ_HOME` resolves to `~/.agentz`. You can override it in `.env`:

```bash
AGENTZ_HOME=~/.agentz
```

The bound project directory is stored in the current session metadata. If `--project-path` is omitted, the CLI defaults to the current working directory. When resuming with `--resume`, the stored project directory is restored and takes precedence over any new `--project-path` value.

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

## Skills config

The app uses the third-party `pydantic-ai-skills` package to load agent skills from a standard directory layout:

```bash
SKILLS_DIR=.agents/skills
```

Each skill should be stored as:

```text
.agents/skills/
  <skill_name>/
    SKILL.md
    REFERENCE.md        # optional
    resources/          # optional
    scripts/            # optional
```

At runtime the skills toolset exposes:

- `list_skills`
- `load_skill`
- `read_skill_resource`
- `run_skill_script`

The project wires this through `pydantic-ai-skills` `SkillsToolset`, with the skills directory coming from `SKILLS_DIR` and defaulting to `.agents/skills` under the current project.
