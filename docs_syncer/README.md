# MCP-Kit Documentation Syncer

Automatically generates comprehensive documentation for the mcp-kit Python SDK and syncs it to [agentiqs/docs](https://github.com/agentiqs/docs).

## What it does
- **User Guide**: Syncs hand-written docs from `docs/user-guide/`
- **Examples**: Auto-generates from `examples/*/README.md` files + syncs `docs/examples/`
- **API Reference**: Auto-generates from `src/mcp_kit/` using pydoc-markdown
- **GitHub Actions**: Triggers on push to main and moves the docs to our docs repo

**Note**: The system explicitly prevents `sidebar.json` files from being moved to the `../website` directory to maintain proper documentation structure and avoid conflicts. It uses `_category_.json` files for Docusaurus autosidebar functionality instead.

## Structure
- `docs_syncer/` - Documentation generation scripts and configuration
- `docs/` - Source documentation files (_category_.json, user-guide/, examples/, reference/)
- `examples/` - Example projects with README.md files that get auto-documented
- Generated files go to the separate `agentiqs/docs` repository

## Local Development

This project uses [uv](https://docs.astral.sh/uv/) for dependency management:

```bash
# Install dependencies
uv sync

# Run the documentation generator
uv run python generator.py

# Run tests (if any)
uv run pytest

# Run type checking
uv run mypy generator.py
```

## Setup
Set `DOCS_REPO_TOKEN` secret (see [GITHUB_SETUP.md](./GITHUB_SETUP.md)) and commit to main.

The documentation is served at [https://agentiqs.ai/docs](https://agentiqs.ai/docs).
