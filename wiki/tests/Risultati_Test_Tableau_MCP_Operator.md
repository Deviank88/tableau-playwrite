---
title: "Risultati Test Tableau MCP Operator"
type: test_result
tags: [test, unittest, tableau-mcp-operator]
created: 2026-06-20
updated: 2026-06-20
sources: []
client: "Interno"
project: "Tableau MCP Operator"
request_id: "REQ-TABLEAU-MCP-001"
status: tested
authority: test_evidence
---

# Risultati Test Tableau MCP Operator

Verifica eseguita il 2026-06-20 nel workspace locale.

## Comandi

- `python -m unittest discover -s tests`
- `python -m compileall tableau_operator tests scripts`
- `validate_connection` tramite `TableauOperator(TableauConfig.from_env())`
- Snapshot Playwright live su Tableau `home` ed `explore`.
- Runner multi-step Playwright live su dialog `New Project` senza premere `Create`.

## Esito

- Unit test: 32 test eseguiti, tutti OK.
- Compilazione Python: completata senza errori.
- Server MCP: `build_server()` completato senza errori.
- Sessione Playwright Tableau: storage state valido in `.tableau-auth/storage-state.json`.
- Snapshot home: URL Tableau corretto, titolo `Home - Tableau Cloud`, testo/link/bottoni rilevati e screenshot prodotto.
- Snapshot explore: rilevati `Top-Level Projects`, `default`, `Samples` e menu `New`.
- Runner multi-step: aperto dialog `New Project` e compilato il primo textbox con `AI Sandbox Dry Run` senza confermare la creazione.
- API Tableau REST: non disponibile per assenza di PAT, come atteso.

## Copertura funzionale verificata

- Validazione `BiSpec` per riferimenti progetto e hash stabile.
- Diff planner per asset mancanti ed esclusione asset gia presenti.
- Safety gate per allowlist progetto e approval id errato.
- REST sign-in con payload PAT mockato.
- Audit log JSONL.
- Apply flow con preview approvata.
- URL Playwright per nuovo workbook con e senza datasource.
- Login Playwright via storage state autosave indipendente dal redirect URL.
- Snapshot UI read-only da Tableau Cloud autenticato.
- Click e fill Playwright controllati su dialog Tableau senza mutazione finale.

## Limiti non coperti

Non sono stati eseguiti test live REST contro Tableau Cloud per assenza di PAT. Le operazioni mutanti via UI sono ora tecnicamente possibili tramite step approvati, ma vanno eseguite solo con istruzioni esplicite e dopo preview/screenshot del dialog.