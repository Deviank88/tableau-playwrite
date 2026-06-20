---
title: "Tableau MCP Operator"
type: overview
tags: [tableau, mcp, business-intelligence, playwright]
created: 2026-06-20
updated: 2026-06-20
sources: []
client: "Interno"
project: "Tableau MCP Operator"
request_id: "REQ-TABLEAU-MCP-001"
status: implemented
authority: validated_report
---

# Tableau MCP Operator

Tableau MCP Operator e un server MCP progettato per permettere ad agenti AI di interagire con Tableau Cloud in modo dichiarativo e controllato.

L'obiettivo e coprire l'intero ciclo operativo di una business intelligence assistita da AI: scoperta degli asset esistenti, pianificazione di nuovi setup, preview delle mutazioni, applicazione approvata delle azioni e cattura dello stato operativo.

## Architettura

La soluzione usa un modello ibrido:

- REST API per operazioni stabili come autenticazione PAT, discovery e creazione progetto.
- Metadata API per interrogazioni GraphQL, lineage e lettura metadati.
- Hyper API come boundary per estratti Tableau-owned.
- Playwright come boundary per authoring web quando Tableau non espone una API stabile.

Vedi anche [[Contratti MCP Tableau Operator]], [[Implementazione Tableau MCP Operator]] e [[Risultati Test Tableau MCP Operator]].

## Stato

La prima implementazione crea una base modulare eseguibile e testata localmente. Le azioni mutanti passano da preview, controllo sicurezza, approval id ed executor auditato.