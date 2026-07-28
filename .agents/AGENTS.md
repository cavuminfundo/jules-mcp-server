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
   - Invocare `list_sessions` per ottenere l'elenco delle sessioni attive.
   - Usare `list_activities(session_id=...)` per ispezionare le attività ed i piani proposti (`plan_generated`) o i blocchi in attesa.

2. **Plan Mentoring & Feasibility Check**:
   - Valutare i piani estratti confrontandoli con le convenzioni del repository (`AGENTS.md`, `.agents/memory/lessons.md`).
   - Se il piano è consono e ben strutturato, approvarlo tramite `approve_session_plan(session_id=...)`.
   - Se il piano presenta lacune, deviazioni o richiede chiarimenti, inviare indicazioni puntuali di mentoring tramite `send_session_message(session_id=..., message=...)`.

3. **User Input / Feedback Mentoring**:
   - Per le sessioni in `AWAITING_USER_FEEDBACK` o `AWAITING_INPUT`, leggere l'ultima richiesta e fornire indicazioni operative via `send_session_message` per far avanzare Jules.

4. **Post-PR & Completed Session Cleanup**:
   - Quando Jules ha ultimato il lavoro, aperto la PR o completato il task (`COMPLETED`, `FINISHED`, `TERMINATED`), eliminare la sessione via `delete_session(session_id=...)` per mantenere pulita l'interfaccia di Jules.
