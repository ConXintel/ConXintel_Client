# ConX Client

Standalone team workspace for ConX customers with **API access** (Agency plan or API-enabled accounts).

Team members sign in to this app and run investigations through the **owner's ConX API key**. Credits and monthly caps are shared from the main ConX account.

This folder is **self-contained**: theme CSS, search/report JavaScript, and templates live under `conx-client/` (no dependency on the parent ConX repo at runtime).

## Features

- Connect with ConX API token (`/api/v1/search`, `/api/v1/account`)
- Owner login + team member accounts (add / edit / delete)
- Investigation search UI (main ConX search theme + loading animation)
- Intelligence report view, print, and CSV export
- Audit logs and search logs per user
- Dashboard with credit snapshot and usage charts
- Owner **Settings** to update ConX URL / API token without re-setup

## Requirements

- Main **ConX** server running (default `http://127.0.0.1:8989`)
- ConX account with **API access enabled** and an active API token (ConX → API Access)

Production and LAN deployment: see **[instructions.md](instructions.md)**.

## Quick start (Windows)

```powershell
cd d:\path\to\conx-client
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
copy .env.example .env
.\.venv\Scripts\python app.py
```

Open **http://127.0.0.1:8990** and complete setup:

1. ConX server URL
2. API token from ConX (full `conx_live_…` value)
3. Owner username/password (for this client app only)

## Fix “Invalid API token”

1. Sign in as **owner**
2. Open **Settings** in the sidebar
3. Paste a **fresh** API token from ConX → API Access
4. Save, then try search again

The token is stored in `data/client_store.json` — if it was overwritten or rotated on ConX, searches return HTTP 401 until you update Settings.

## Ports & env

| Variable | Default | Purpose |
|----------|---------|---------|
| `CONX_CLIENT_PORT` | `8990` | Client app port |
| `CONX_CLIENT_SECRET_KEY` | (dev default) | Flask session secret |
| `CONX_CLIENT_DATA_DIR` | `./data` | Team + logs + report cache |
| `CONX_CLIENT_INTEL_IMAGE_ORIGIN` | (empty) | Search API origin for `/id-images/…` URLs |

## Roles

| Role | Access |
|------|--------|
| **Owner** | Dashboard, team, logs, settings, search |
| **Team member** | Search only |

## Bundled assets

Shipped under `static/` and `templates/partials/`:

- `conx.css`, `workspace-search-tabs.js`, `workspace-contextual-live.js`
- `intelligence-print-page.css`, `js/conx-preview-common.js`
- `dashboard_preview_section.html`, `search_type_icon.html`
- `user_intel.py` (image/email sanitization for reports)

To refresh from a dev checkout of main ConX (optional):

```powershell
python tools/sync_theme_from_conx.py
```

## Security notes

- Store `data/client_store.json` outside a public web root in production.
- Use a strong `CONX_CLIENT_SECRET_KEY`.
- The ConX API token is stored locally after setup — protect the client server.

## Main ConX API used

- `GET /api/v1/account` — credits, plan, billing period usage
- `POST /api/v1/search` — investigations (deducts owner credits)
