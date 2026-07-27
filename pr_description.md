🎯 **What:** Removed the unused `Context` import from `fastmcp` in `jules_mcp/jules_mcp.py`.
💡 **Why:** The `Context` class was imported but never used. Removing it reduces clutter and improves readability.
✅ **Verification:** Verified the script parses correctly with `python -m py_compile jules_mcp/jules_mcp.py`.
✨ **Result:** A cleaner codebase with fewer unnecessary imports.
