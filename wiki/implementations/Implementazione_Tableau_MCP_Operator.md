---
title: "Implementazione Tableau MCP Operator"
type: implementation
tags: [python, mcp, tableau, safety]
created: 2026-06-20
updated: 2026-06-20
sources: []
client: "Interno"
project: "Tableau MCP Operator"
request_id: "REQ-TABLEAU-MCP-001"
status: implemented
authority: validated_report
---

# Implementazione Tableau MCP Operator

L'implementazione e modulare e separa transport MCP, configurazione, modelli, planner, safety gate, audit log, REST client, Metadata client, Hyper boundary, Playwright boundary, snapshot UI ed executor.

## Safety model

Le mutazioni sono vincolate da tre livelli:

- `preview_bi_spec` calcola azioni e approval id deterministico.
- `SafetyGate` blocca progetti fuori allowlist, prefissi non validi e azioni distruttive non abilitate.
- `apply_bi_spec` richiede approval id corrispondente a una preview gia registrata.

I tool Playwright che possono interagire con la UI, come `click_tableau_ui` e `run_tableau_ui_steps`, sono configurati con approval prompt in Codex per evitare click automatici su azioni mutanti.

## Executor

`ActionExecutor` audita in JSONL inizio e fine di ogni azione. La prima azione API implementata e la creazione progetto Tableau via REST. I flussi workbook authoring passano dal boundary Playwright, che costruisce URL Tableau Cloud `newWorkbook` o `authoringNewWorkbook` e verifica la presenza dello storage state.

## Playwright-only mode

Quando non sono disponibili PAT Tableau, il sistema usa `.tableau-auth/storage-state.json` per aprire Tableau Cloud come browser autenticato. `snapshot_tableau_ui` acquisisce testo, link, bottoni e screenshot. `run_tableau_ui_steps` supporta step `click`, `fill` e `wait`, con selezione per ruolo/testo o per indice del ruolo quando un campo non ha accessible name stabile.

## Configurazione

La configurazione viene caricata da variabili ambiente documentate in `.env.example`. Se le variabili non sono gia esportate nel processo, il loader legge automaticamente il file `.env` nella root del workspace.

Il file `.env` locale contiene l'host Tableau Cloud `https://prod-ch-a.online.tableau.com` e il site content URL `fjtcqsqlonlagocati-1069f3ed9b`; i campi PAT restano vuoti. `.env` e incluso in `.gitignore`.

## Configurazione Codex

E stata aggiunta una configurazione project-scoped in `.codex/config.toml` per avviare il server MCP locale con `python -m tableau_operator.mcp_server`. I tool di lettura e preview sono in approval automatico; `apply_bi_spec`, `open_authoring_session`, `click_tableau_ui` e `run_tableau_ui_steps` richiedono prompt di approvazione.