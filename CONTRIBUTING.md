# Contributing to Jules MCP Server

Thank you for considering contributing to `jules-mcp-server`! Contributions are welcome from the community.

## Development Setup

1. **Fork and Clone**:
   ```bash
   git clone https://github.com/your-username/jules-mcp-server.git
   cd jules-mcp-server
   ```

2. **Environment & Dependencies**:
   Ensure you have [uv](https://github.com/astral-sh/uv) or Python 3.10+ installed.
   ```bash
   uv sync
   ```

3. **Running the Server Locally**:
   ```bash
   export JULES_API_KEY="your_jules_api_key"
   uv run python -m jules_mcp.jules_mcp
   ```

## Pull Request Guidelines

- **Branch Naming**: Use descriptive branch names like `feature/add-activity-filter` or `fix/httpx-timeout`.
- **Code Style & Formatting**: Follow PEP8 conventions and keep FastMCP tool type annotations clean (avoid optional types without explicit defaults).
- **Commit Messages**: Follow [Conventional Commits](https://www.conventionalcommits.org/) (e.g. `feat(mcp): ...`, `fix(api): ...`, `docs(readme): ...`).
- **PR Description**: Describe the problem solved, changes introduced, and how to test.
