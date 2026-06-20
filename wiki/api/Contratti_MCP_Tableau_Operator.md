---
title: "Contratti MCP Tableau Operator"
type: api
tags: [mcp, tableau, api-contracts]
created: 2026-06-20
updated: 2026-06-20
sources: []
client: "Interno"
project: "Tableau MCP Operator"
request_id: "REQ-TABLEAU-MCP-001"
status: implemented
authority: validated_report
---

# Contratti MCP Tableau Operator

Questa pagina dettaglia i contratti esposti da [[Tableau MCP Operator]].

Il server espone strumenti MCP dichiarativi e strumenti Playwright controllati, pensati per lavorare con Tableau Cloud anche quando non sono disponibili Personal Access Token.

## Tool

- `validate_connection`: verifica configurazione API, autenticazione Tableau e presenza dello storage state Playwright.
- `discover_site`: legge lo stato Tableau via REST quando possibile; senza PAT usa snapshot Playwright read-only di Explore.
- `query_tableau_data`: interroga la Metadata API per asset e lineage quando le API sono disponibili.
- `plan_bi_spec`: produce una bozza iniziale di specifica BI da un obiettivo utente.
- `preview_bi_spec`: valida una `BiSpec`, calcola il diff e produce un `approval_id`.
- `apply_bi_spec`: applica solo preview gia approvate e registrate in memoria.
- `open_authoring_session`: costruisce una sessione authoring Tableau Cloud via Playwright boundary.
- `snapshot_tableau_ui`: acquisisce testo, link, bottoni e screenshot da `home`, `explore`, `projects`, `workbooks`, `datasources` o `views`.
- `click_tableau_ui`: esegue un click approvato su `button`, `link`, `menuitem`, `tab` o testo e restituisce snapshot.
- `run_tableau_ui_steps`: esegue una sequenza approvata di step UI `click`, `fill` e `wait`, poi restituisce snapshot finale.
- `capture_state`: crea il riferimento alla directory di cattura per run operativi.

## Risorse

- `tableau://catalog`
- `tableau://lineage/{asset_id}`
- `tableau://runs/{run_id}`
- `tableau://screenshots/{run_id}`

## Modello dati

`BiSpec` contiene progetti, datasource, workbook, permessi e metadati. La validazione blocca duplicati e riferimenti a progetti inesistenti quando la specifica dichiara esplicitamente i progetti.