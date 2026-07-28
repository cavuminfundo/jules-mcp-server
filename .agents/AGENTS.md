# Workspace Agent Router — Jules

> **Jules** is an AI execution & supervision workspace.

## 📖 Repository Documentation Index
Before starting any work, inspect the relevant documentation files below:

- **Global Agent Guidelines & Safety:** Refer to `~/.gemini/config/AGENTS.md` for execution rules, sub-agent invocation, skill orchestrator, and shell restrictions.
- **Lessons Learned & Past Bugs:** Read [.agents/memory/lessons.md](file:///home/federico/jules/.agents/memory/lessons.md) before making modifications to prevent known operational errors.

## 🧠 Memory Protocol
Always consult `.agents/memory/lessons.md` at the start of any task, and append newly learned lessons/fixes upon resolving issues.

## 🤖 Jules MCP Supervisor Protocol

> ⚠️ **STEP 0 OBBLIGATORIO (Skill Activation Protocol):**
> Prima di eseguire qualsiasi chiamata a tool MCP (`jules-mcp` o `github-mcp-server`), l'agente DEVE obbligatoriamente attivare lo **Skill Orchestrator**:
> 1. Cercare la skill `jules-supervisor` in `/home/federico/skills_library/CATALOG.json` tramite `grep_search`.
> 2. Leggere ed caricare le istruzioni complete da [`/home/federico/skills_library/jules-supervisor/SKILL.md`](file:///home/federico/skills_library/jules-supervisor/SKILL.md) tramite `view_file`.

When orchestrating and supervising Jules AI sessions via MCP:

1. **Session & Activity Inspection (`jules-mcp`)**:
   - Invocare `list_sessions()` (senza argomenti superflui) per ottenere l'elenco delle sessioni attive.
   - Usare `list_activities(session_id=...)` per ispezionare le attività ed i piani proposti (`plan_generated`) o i blocchi in attesa.

2. **Session Cleanup (Chiuse / Inattive)**:
   - Eliminare tutte le sessioni chiuse o inattive (`COMPLETED`, `FINISHED`, `TERMINATED`, `CANCELLED`, `FAILED`, `EXPIRED`, `CLOSED`) che **NON abbiano in sospeso la richiesta di approvazione piano o di input utente**.

3. **Plan Mentoring & Feasibility Check (Fino alla PR)**:
   - Valutare i piani estratti confrontandoli con le convenzioni del repository (`AGENTS.md`, `.agents/memory/lessons.md`).
   - Se il piano è consono e ben strutturato, approvarlo tramite `approve_session_plan(session_id=...)`.
   - Se il piano presenta lacune o deviazioni, inviare indicazioni puntuali di mentoring tramite `send_session_message(session_id=..., message=...)` guidando Jules fino all'apertura della PR.
   - 🛑 **NO PR MERGING**: La skill NON effettua il merge delle Pull Request su GitHub.

4. **Regola di Cancellazione Sessione su Rebase**:
   - Poiché Jules non può eseguire il git rebase, **se la PR generata da Jules richiede un rebase (presenta conflitti)**, eliminare immediatamente la sessione corrispettiva via `delete_session(session_id=...)`.
