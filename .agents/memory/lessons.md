# Jules AI Agent - Lessons Learned & Behavioral Memory

This file serves as a memory bank to record past execution mistakes, lessons learned, and behavioral rules. Future agents working on this repository should review this file during startup to avoid repeating mistakes.

---

## 1. Jules MCP Native Tool & Single Worker Standard
- **Rule**: Tutte le interazioni con Jules (ispezione sessioni, lettura attività, approvazione piani, invio messaggi di guida) DEVONO avvenire esclusivamente tramite i tool nativi MCP (`jules-mcp` e `github-mcp-server`). É vietato l'uso di script Python o client RPC esterni.
- **Single Worker Execution**: Il Sub-Agente invocato per la supervisione è un esecutore finale diretto e non deve MAI invocare a sua volta `invoke_subagent`. Esegue direttamente tutte le chiamate ai tool MCP (`call_mcp_tool`).

## 2. Infrastruttura Docker Remota & Mappa di Topologia
- **Issue**: Tentativo errato di lanciare `docker build` / `docker run` sulla macchina di sviluppo locale per aggiornare il server `jules-mcp-server`.
- **Root Cause**: Mancata consultazione preventiva della mappa di topologia delle infrastrutture.
- **Checklist/Rule**: Il container `jules_mcp_server` viene eseguito in ambiente remoto dedicato. L'aggiornamento del server MCP avviene mediante push del codice su GitHub, attesa della build su GHCR (`ghcr.io/cavuminfundo/jules-mcp-server:latest`) e pull/restart effettuato sul server di deployment target. Gli agenti non devono mai eseguire comandi Docker per i server MCP sul host locale di sviluppo.

## 3. Gestione Obbligatoria Dual-Phase (Session & PR Management) e Resilienza Errori MCP
- **Issue**: Salto completo della fase 1 di gestione sessioni Jules (`jules-mcp`) per passare direttamente alla gestione PR su GitHub o per interruzione anticipata in presenza di un errore di chiamata MCP (es. errori di schema o parametri errati).
- **Root Cause**: Mancata gestione resiliente degli errori nelle chiamate ai tool MCP e assenza di esecuzione sequenziale rigorosa delle due fasi supervisionate.
- **Checklist/Rule**: L'agente Supervisore DEVE SEMPRE completare entrambe le fasi operative:
  1. **Fase 1 - Session Management (`jules-mcp`)**: recuperare le sessioni, ispezionare gli stati, approvare i piani e sbloccare le sessioni in attesa di input (`AWAITING_USER_FEEDBACK` / `AWAITING_INPUT`). Eventuali errori di schema o eccezioni iniziali sulle API MCP non devono mai portare a saltare o abbandonare questa fase.
  2. **Fase 2 - PR Management (`github-mcp-server`)**: scansionare, revisionare, testare e mergiare le PR attribuibili a Jules.
  Nessuna delle due fasi può essere omessa o scavalcata.

## 4. Cancellazione Immediata dei Branch Remote & Local dopo il Merge PR
- **REGOLA TASSATIVA**: Dopo il merge di ogni PR su GitHub, il supervisore DEVE sempre eliminare immediatamente il branch sia in remoto su GitHub che in locale.

## 5. Defensive Timeout and Error Handling in Jules MCP
- **Issue**: Missing defensive timeouts and error handling leading to blocked threads during API communication.
- **Root Cause**: `httpx` default timeouts can be indefinite if not properly configured, and errors weren't caught broadly enough.
- **Checklist/Rule**: Always use strict, explicit timeouts for HTTP requests (`httpx.Timeout(8.0, connect=3.0)`) in `jules_mcp.py`. Wrap API calls in `try...except (Exception, asyncio.CancelledError, asyncio.TimeoutError)` to fail fast without blocking threads.

## 6. Mandatory Pre-Compiled Container Images Policy (GHCR)
- **Issue**: Uso temporaneo di volume mounts in `compose.yaml` in produzione.
- **Root Cause**: Non attendere il completamento della build Docker automatica su GHCR.
- **Checklist/Rule**: In produzione, i container DEVONO utilizzare ESCLUSIVAMENTE immagini precompilate ufficiali da GitHub Container Registry (`image: ghcr.io/cavuminfundo/jules-mcp-server:latest`). È tassativamente vietato usare volume mounts di file python locali in produzione. Ogni modifica del codice deve essere committata su GitHub ed applicata via `docker compose pull`.
