# web/ — Crop Intelligence demo site (Vite + React)

Presentation layer for the hackathon pitch: a value-prop landing page, an
interactive 3D farm twin you can click and talk to, and a page showing the
real 3D/4D data behind the pipeline. Implements `../frontend plan.md`, with
the stack changed to Vite + React + React Three Fiber on request.

## Run

```bash
cd web
npm install
cp .env.example .env.local        # paste VITE_OPENROUTER_API_KEY (free tier is fine)
npm run dev                       # http://localhost:5173
npm run build && npm run preview  # production check on :4173
```

`/twin-assets/*` is served straight from `../docs` (the existing splat
viewers, `scan.ply`, `pheno.bin`, `orbit.mp4`) by a small plugin in
`vite.config.js`, so the ~150 MB of 3D data is never duplicated in git. The
build copies those folders into `dist/twin-assets/`.

## Routes

| Route | What |
|---|---|
| `/` | Landing: hero, problem, solution (3 layers + live 3D preview), features, metrics grid, real-data teaser, comparison, honesty band, roadmap, CTA |
| `/twin` | The demo. Procedural 3D farm (6 plots). Click a plot or press 1–6; Esc resets. Data layers: Health / NDVI / Moisture / pH. Right panel: telemetry card + AI advisor |
| `/lab` | Pheno4D real plant growth (native R3F replay of `pheno.bin`), both Gaussian-splat viewers (iframed from `docs/`), orbit video |
| `/credits` | Image and dataset credits |

## Data and AI

* `src/data/zones.js` — synthetic plot values keyed by the real OpenUSD
  attribute names (`farmSensor:*`, `farmZone:*`, `cropModel:*`). One zone per
  status token: nominal, warning, critical, offline.
* `src/lib/rag.js` — client-side BM25 over zone cards + `src/data/farmFacts.js`.
  The selected plot's card is always in context.
* `src/lib/llm.js` — OpenRouter streaming with a fallback chain
  (NVIDIA Nemotron 3 Super → Gemma 4 → Qwen → Nemotron Lightning), one retry on
  overload, bad model ids skipped for the session, and a guard that rejects
  answers that leak chain-of-thought.
* `src/lib/offline.js` — keyword advisor used when there is no key, the API
  fails, or the wifi dies. The chat never renders a broken bubble.
* Voice: mic input (Web Speech API, Chrome/Edge) and optional read-aloud.

## Key handling

`VITE_*` variables are inlined into the browser bundle. Put a spend cap on the
OpenRouter key and revoke it after the event. A key can also be pasted at
runtime via the key button in the chat header (stored in localStorage).

## Honesty rules

Follows the claims ledger in `docs/04_AUDIT_AND_PIVOT.md` §10: every screen
with numbers carries the synthetic-data badge; the scans are labelled public
reference captures; the chat is described as a real LLM over demo data.
Photos are Unsplash License (see `/credits`).
