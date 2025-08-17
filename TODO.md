# RReverie Agricultural Emissions Initiative — Weekend Plan (Small Scope)

This plan assumes no GPU. Today focuses on local setup and a quick preliminary agricultural methane analysis over the Chesapeake Bay watershed using Google Earth Engine (GEE). Future weekends build capability incrementally.

## Accounts and Access Checklist
- Google Earth Engine: create an account and sign in to the Code Editor: [Google Earth Engine Code Editor](https://code.earthengine.google.com)
- NASA Earthdata Login (for future EMIT/OCO downloads): [NASA Earthdata](https://urs.earthdata.nasa.gov)
- AWS account (for future IMI runs; not needed today): [AWS](https://aws.amazon.com)
- Copernicus Data Space (optional, alternate access to Sentinel): [Copernicus Data Space](https://dataspace.copernicus.eu)
- GitHub (repo hosting): [GitHub](https://github.com)
- Optional (later): Mapbox token for web maps: [Mapbox](https://account.mapbox.com)

Notes:
- GEE Code Editor requires a Google account; no API key.
- For local Python use of GEE later, you’ll run `earthengine authenticate` once.

## Today (2–4 hours): Local Setup + Preliminary Analysis (Chesapeake CH4)
1) Repo setup
- Keep this folder as the working repo. We added:
  - `requirements.txt` (lightweight deps)
  - `scripts/gee_ch4_chesapeake.js` (GEE Code Editor script for methane)
  - `TODO.md` (this file)

2) Python environment (optional today)
- Create a virtualenv and install requirements:
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
  ```
- You do NOT need to authenticate Earth Engine locally today if you use the GEE Code Editor. If you want to prepare for later Python use:
  ```bash
  pip install earthengine-api
  earthengine authenticate
  ```

3) Preliminary CH4 analysis in GEE
- Open the Code Editor at `https://code.earthengine.google.com`.
- Create a new script and paste the contents of `scripts/gee_ch4_chesapeake.js`.
- Run it. You’ll get monthly composite layers of Sentinel‑5P CH4 (XCH4) over the Chesapeake/Delmarva region for the last 12 months, plus a chart.
- Take 1–2 screenshots for your first micro‑post (e.g., seasonal contrast). Save them to `outputs/` locally.

4) Micro‑deliverable
- Title idea: “Methane over the Chesapeake (S5P)”. Two images and a 2–3 sentence caption explaining seasonal differences and that this is the foundation for CAFO hotspot analysis.

Definition of done for today
- GEE account working
- NO2 map layers render and a time‑series chart prints
- 1–2 screenshots saved locally

## Python-first Repo Structure (lightweight)
```
.
├─ src/
│  ├─ __init__.py
│  └─ config.py          # Chesapeake bbox and common constants
├─ scripts/
│  └─ gee_ch4_chesapeake.js   # Run in GEE Code Editor
├─ data/
│  └─ sources/
│     └─ cafo_sources.csv     # Build this next weekend
├─ outputs/              # Screenshots/exports
├─ requirements.txt
├─ .env.example          # placeholders for later (AWS, etc.)
├─ .gitignore
└─ TODO.md
```

Code style: PEP8, type hints on functions, clear names. Prefer notebooks only for exploration; keep reusable logic in `src/`.

## Weekend 2: Build a CAFO Source Registry (Small, Actionable)
Goal: a simple CSV of CAFOs and related agricultural methane sources in the Chesapeake Bay watershed.
- Create `data/sources/cafo_sources.csv` with columns: `name,type,lat,lon,county,state,notes,source_url`.
- Start with Delmarva Peninsula (MD Eastern Shore, DE, VA Eastern Shore):
  - Poultry/dairy CAFOs, large swine operations
  - Manure lagoons, digesters
  - Nearby agricultural landfills/waste sites
- Data leads:
  - State permitting databases (MDE, VA DEQ, Delaware DNREC)
  - EPA FLIGHT reporters (cross-check)
  - Academic studies and FOIA where needed
- Deliverable: `cafo_sources.csv` with ≥30 entries and links.

## Weekend 3: EMIT Plume Cross‑check (Optional, Low Lift)
Goal: see if any EMIT CH4 plume detections intersect Delmarva/Chesapeake hotspots.
- Browse EMIT methane plume datasets (NASA LP DAAC or published catalogs) for MD/DE/VA Eastern Shore.
- If present, record plume date/time/location; add to `cafo_sources.csv` with a note.

## Weekend 4: IMI Familiarization (Plan Only; no heavy compute yet)
Goal: get ready to run the Integrated Methane Inversion (IMI) on AWS next month.
- Read the IMI docs and prerequisites.
- Prepare an S3 bucket naming scheme, region, and IAM role (no costs yet).
- Define bounding box and period (e.g., Chesapeake watershed/Delmarva, last 12–24 months).
- Deliverable: a 1‑page runbook outlining region, period, and expected outputs (CH4 flux grids).

## Weekend 5: First IMI Run (If budget allows; otherwise postpone)
- Spin up IMI on AWS for a 3–6 month window over Chesapeake/Delmarva to limit cost.
- Export gridded methane fluxes to S3, then download small PNG/GeoTIFF overviews for inspection.
- Deliverable: PNG tiles + notes on agricultural hotspots.

## Weekend 6: Modeling On‑Ramp (No GPU)
- Clone NeuralGCM and confirm environment install without running heavy jobs.
- Read tracer examples or plan a passive‑tracer stub (we’ll plug fluxes later).
- Deliverable: short note on feasibility and next steps; no big runs.

## Scope Guardrails (to keep it small and sensible)
- CH4 first; CO2 later when data continuity is clearer.
- GEE Code Editor for first visuals; no complex local geospatial stack.
- Keep deliverables small: screenshots, a CSV, and short notes.
- Defer paid/commercial data (e.g., GHGSat) until useful partners/funding.

## Risks and When to Escalate
- Sparse EMIT coverage: fine—use source registry + IMI later.
- GEE throttling: run monthly windows, keep region small.
- Time/cost for IMI: start with 3–6 months; stop if costs exceed plan.

## Updated QPLAN (Lightweight for Current Constraints)
- Phase A (Weeks 1–2): GEE CH4 baseline over Chesapeake + CAFO registry v0.1 (no GPU)
- Phase B (Weeks 3–4): EMIT cross‑check and IMI runbook (no spend yet)
- Phase C (Weeks 5–6): First limited IMI run if budget allows; otherwise expand CAFO registry + publish CH4 brief
- Phase D (Weeks 7–8): NeuralGCM environment validation (no heavy runs), tracer plan

## Optional Next Adds (Only if time permits)
- Simple static site to host images and short writeups.
- Add a `data/nyc_bbox.geojson` to standardize the region.

