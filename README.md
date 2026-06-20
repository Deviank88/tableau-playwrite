# Tableau MCP Operator

Declarative MCP server for Tableau Cloud. It combines Tableau REST, Metadata,
Hyper, and Playwright so agents can inspect BI assets, plan changes, preview
mutations, and apply approved operations inside a configured safety boundary.

## Quick Start

1. Copy `.env.example` to `.env` or export the same variables.
2. Install dependencies:

```powershell
pip install -e .[dev]
playwright install chromium
```

3. Validate local code:

```powershell
python -m unittest discover -s tests
```

4. Run the MCP server:

```powershell
tableau-mcp-operator
```

## Playwright Login Without PAT

If your Tableau account cannot create Personal Access Tokens, you can still
create a browser-authenticated session for UI automation:

```powershell
pip install -e .[dev]
playwright install chromium
python scripts/tableau_login.py --timeout 300
```

Complete SAML/MFA login in the opened browser. The script waits until Tableau
redirects away from the login URL, then saves the session to
`.tableau-auth/storage-state.json`, which is ignored by git.

If automatic redirect detection does not save the session, run:

```powershell
python scripts/tableau_login.py --autosave --timeout 300
```

Then complete login in the browser. The script writes state snapshots every few
seconds, so the cookies are persisted even when SAML/cookie consent changes URL.

If you prefer an explicit save point, run:

```powershell
python scripts/tableau_login.py --manual
```

Then complete login in the browser and press Enter in the terminal.

Without a PAT, REST and Metadata API tools remain unavailable. Playwright-backed
authoring tools can use the saved browser session.

## Playwright-Only Discovery

When PAT credentials are not configured, `discover_site` falls back to a
read-only Playwright snapshot of Tableau Explore. You can also call
`snapshot_tableau_ui` with `home`, `explore`, `projects`, `workbooks`,
`datasources`, or `views`.

For UI exploration, `click_tableau_ui` can click a visible `button`, `link`,
`menuitem`, `tab`, or text match and return a fresh snapshot. Keep this tool
approval-gated because clicks can mutate Tableau state.

For multi-step UI flows, `run_tableau_ui_steps` accepts approved steps with
`action` values `click`, `fill`, or `wait`, then returns a final snapshot. Keep
this tool approval-gated as well. Steps may specify `role`, `text`, `value`,
`exact`, `index`, and `timeout_ms`.

## Safety Model

All mutations require a preview-generated approval id. Writes are constrained to
the configured Tableau Cloud site and allowlisted projects. Delete operations are
blocked by default.
