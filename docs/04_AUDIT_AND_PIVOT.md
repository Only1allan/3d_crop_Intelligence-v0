# 04 - Hackathon Audit, Verification Log & Demo Pivot (2026-09-27)

**Status: BINDING.** This document records the full pre-implementation audit of
2026-09-27: the challenge constraints, what was verified externally, what the
codebase and legacy-repo audits found, and every decision taken with its
rationale. For the hackathon window it supersedes any demo-path assumption in
`docs/00`-`03`; those documents remain authoritative for architecture and
schema contracts. Future sessions: read this before planning any demo work.

## 1. Challenge frame (verified constraints)

Sources: user answers 2026-09-27 (authoritative) + web verification below.

| Constraint | Value | Source |
|---|---|---|
| Event | GoMyCode hackathon, NVIDIA challenge track, **open 3D/GPU scope — Omniverse NOT specifically required** | user |
| Deadline | Same day; 4-8h execution window at time of audit | user |
| Judging | **Live pitch/demo** — the demo must run interactively in a browser | user |
| Team | 2 people | user |
| Compute | **Free Colab + free Kaggle only.** No local GPU, no cloud credits, browser-only workstations (even video capture must be notebook-rendered) | user |
| 3D reconstruction data | No real farm photos available; **public capture as proof-of-concept** | user (accepted) |
| GoMyCode brief text | **NOT obtained** — site is JS-walled, search engines captcha-walled. Open item #1; if the brief surfaces, re-align the pitch to its rubric (see §12) | audit limitation |

## 2. Audit method and limits

**Method.** Two read-only deep-dive agents (extension codebase; both legacy
repos) reading every source file; cross-checks of `docs/` claims against code
with file:line evidence; web verification of every post-cutoff claim via
Wikipedia / arXiv / PyPI JSON API / Google Colab FAQ / live HTTP HEAD checks;
invariant verification against AGENTS.md rules 1-7.

**Limits — what this audit could NOT do (do not treat these as verified):**

* `pytest` was **not re-executed** during the audit (audit box has no `pxr`;
  Python 3.14.7 only). The "9 tests green" claim is point-in-time and must be
  re-proven at T0 of the execution plan.
* Kaggle quota/session facts could not be fetched (docs pages are JS-rendered;
  content empty). Treat Kaggle GPU hours/session caps as **unverified**; Colab
  is the primary, Kaggle the fallback.
* The GoMyCode challenge rubric is unknown (§1).
* "Toga" 3DGS-in-USD format: **zero evidence found** through any reachable
  channel (see §3). Treated as nonexistent for the demo.
* Every claim below marked VERIFIED carries its source; anything else is
  explicitly labelled unverified or inferred.

## 3. External verification log (2026-09-27)

Every assumption was challenged, including the audit's own priors. Two priors
were proven WRONG — recorded here so nobody re-makes those mistakes.

| Claim under test | Verdict | Evidence (fetched 2026-09-27) |
|---|---|---|
| "Claude Fable 5 / Mythos" in the research doc is a hallucination | **WRONG — the model exists.** Claude Fable 5 released 2026-06-09, Fable 5.1 2026-09-01, Mythos 5 limited-access, all public | https://en.wikipedia.org/wiki/Claude_(AI) |
| arXiv citations in the research doc are fabricated | **Real, at least the spot-check.** arXiv:2609.16926 "Evaluating Mesh Reconstruction Methods for Crop Phenotyping" (Singh, Morales, Hua, Saini; submitted 2026-09-15) fetched successfully; recommends GGGS/PGSR/2DGS pipelines for crop phenotyping meshes | https://arxiv.org/abs/2609.16926 |
| Omniverse Kit can be the live demo from a free notebook | **DEAD.** Free Colab: T4-class GPUs subject to availability, 12h max runtime, **remote desktop / SSH / "bypassing the notebook UI" explicitly prohibited**; paid plans only remove those. Kit needs multi-GB SDK + Vulkan + RTX + display/stream — unavailable and partly ToS-violating | https://research.google.com/colaboratory/faq.html |
| `usd-core` runs on notebook Python | **VERIFIED.** Latest **26.8** (2026-07-20); `requires_python >=3.9,<3.15`; cp312 wheels since 24.11 (2024-11); cp313 since 25.8 (2025-07); cp314 in 26.5/26.8. Wheels only (no sdists), Linux x86_64 only, glibc ≥2.27/2.28 from 26.3. On Python 3.12 notebooks: pin **`usd-core==26.8`** | https://pypi.org/pypi/usd-core/json |
| "Toga" / `.usdg` Gaussian-splatting-in-USD format exists | **UNVERIFIABLE — assume absent.** Search engines captcha-walled (DDG, Mojeek, Bing junk); GitHub code search: 0 results for toga+gaussian-splatting; "usdg" returns only stablecoin (Paxos/Global Dollar) noise. No NVIDIA page reachable. Banned from the demo path; re-verify post-hackathon via NVIDIA channels | negative search evidence only |
| A public 3DGS capture is downloadable at runtime | **VERIFIED.** Inria 3DGS reference inputs (truck + train scenes) live: HTTP 200 | https://repo-sam.inria.fr/fungraph/3d-gaussian-splatting/datasets/input/tandt_db.zip (HEAD 200, 2026-09-27) |
| nerfstudio-hosted sample data | **DEAD (404)** — `data.nerf.studio/nerfstudio/poster.ply`; HF mirror 401. Do not re-walk these paths; use the Inria URL above | HEAD 404/401, 2026-09-27 |
| 3DGS training fits a free T4 | **Feasible with bounds.** Kerbl et al. (SIGGRAPH 2023): 7K iters ≈ InstantNGP-quality in 5-10 min on their hardware; 30K full. Memory can exceed 20GB on large scenes → cap resolution (~800px), iterations (≤30K), and scene size (truck subset). T4 16GB is sufficient under those caps; 7K-iter fallback if not | https://en.wikipedia.org/wiki/Gaussian_splatting |

**Net correction:** the governing research doc is *directionally real* (Fable,
citations check out) but remains an unreliable narrator for engineering
details — its Azure-era assumptions were already edited by the user, and its
unverifiable specifics ("12 brainstem loops") are irrelevant to the build.

## 4. Extension codebase audit (`exts/omniverse_crop_intelligence`)

**Invariants scorecard: 7/7 PASS (static).** Root layer purity enforced in code
(`stage_builder.py:103-104`) and tests (`test_headless.py:67`); Kit-free core
verified by import audit (only `extension.py`, `ui/control_panel.py`,
`tests/test_extension.py` import `omni.*`); phase discipline holds (no network
or model maths anywhere in the tree); schema pipeline is genuine
(`usdGenSchema` path math verified against the OpenUSD pip layout); Python
3.10/3.11 syntax throughout; `assets/layers/*` matches tool output.

**Findings (ranked; fixed at T0 unless noted):**

| # | Sev | Finding | Where |
|---|---|---|---|
| F1 | HIGH | `collect_daily_input()` drops legitimate zeros (rain=0mm, tmin=0°C read as "missing") and a test **blesses the bug**. Corrupts the Phase 2 SUBSTOR entry point | `phase2/substor_bridge.py:74`, `tests/test_headless.py:176-178` |
| F2 | HIGH | Path contract broken: `../agrifusion-aws` does not exist. Real AgriFusion lives at `/ope/code/ai-kenya` (git: `m0th3rch1p/agrifusion`, working branch `main-update`; `aws-migration` branch lineage) | `AGENTS.md:11`, `docs/00` origin note |
| F3 | HIGH | Nothing pinned: `usd-core>=25.5` floor-only, `.kit` app deps all `{}` unversioned, Kit surface claimed 106.x/107.x but **never executed anywhere, ever** (docs/00 item 7) | `requirements-dev.txt`, `apps/*.kit:12-28`, `config/extension.toml:2` |
| F4 | MEDIUM | Default `farmAssetPath` is a Nucleus URL (`omniverse://localhost/...`) — silently composes empty on every notebook/CI box. Demo must override with a local `file://` path (code already tolerates the miss via PlaceholderGround) | `settings.py:23`, `extension.toml:39`, `stage_builder.py:184-190` |
| F5 | MEDIUM | Demo RNG reseeded per wall-clock second → two ticks within 1s look identical on stage | `extension.py:183` |
| F6 | LOW | `RuntimeWriter` reaches into private `api._qualify()`; `gen_schema.py` dead import `runpy` + brittle placeholder patching; `~/Documents` output fallback is Windows-centric; duplicated `/World` + metadata opinions across sublayers (consistent today, fragile tomorrow); `TelemetryMessage.values: Dict[str,float]` type lie (status strings flow through); `write_model_state` has zero test coverage; dead `values()` wrapper | `phase2/runtime_writer.py:54,80,97`; `tools/gen_schema.py:13,40-44`; `extension.py:129`; `phase2/ingestion.py:39` |
| F7 | INFO | Repo hygiene: entire Phase 1 in one commit ("boiler-plate"); governing spec doc untracked in git; `assets/layers` sample committed (good). Legacy-repo secrets warning (§5) honored — nothing copied | git log |

**What the audit affirms (used as feasibility evidence):** the core is fully
GPU-free and runs on `pxr` alone — schema registration, layer-stack build,
sensor spawning, runtime writes, ingestion pump, bridge aggregation, and the
9-test suite all execute headless. This is *why* the project is salvageable
under the challenge constraints.

## 5. Legacy repository audit

### 5.1 AgriFusion (`/ope/code/ai-kenya`, a.k.a. the "agrifusion-aws" input)

* **Stack drift:** Phase-1 analysis (`docs/01` §2) predates the current tree.
  `src/lib/db.ts` is now a 29-byte re-export; `/api/sync` is a bearer-token
  proxy to a **new Go modular monolith** (`backend/`, :8080); 32 migrations
  replace the single `schema.sql`. `docs/01` line references are stale — Phase
  2 ingestion must be written against the *current* tree, not the documented
  one.
* **AWS footprint (real):** Aurora PostgreSQL (IAM/RDS-signer auth, PostGIS +
  pgvector), Bedrock (Claude 3 Haiku + Titan embeddings), S3/R2 photo storage.
  Deployed on Vercel; **no IaC in repo**.
* **Data:** none persisted. Seeds only: 30 farmers / 75 fields / 450+
  assessments, jittered around 6 real Uasin Gishu (Kenya) sub-county centroids;
  20-field longitudinal series; toy square boundaries. Weather never persisted
  (Open-Meteo fetched for advice only).
* **Confirmed absent:** IoT, MQTT, Kinesis, SQS, Lambda, soil moisture, soil
  temperature, sensors, photos (pipeline exists, zero images), SUBSTOR, SimCast.
* **Security (do not propagate):** `.env` with live-looking third-party keys
  (R2, Featherless, WhatsApp, Africa's Talking, iSDA); `test_isda.py` hardcodes
  iSDA credentials. **Never copy, commit, or mirror either.** Neither legacy
  repo has a LICENSE file — reuse is read-for-analysis only until resolved
  (§12).

### 5.2 FarmWise (`/ope/code/agriLegends`)

* **Stack:** FastAPI + Neo4j AuraDB, APScheduler pipelines, AgroMonitoring
  (NDVI/weather/GDD), OpenWeatherMap day summaries, iSDAsoil, Featherless LLM
  (+VLM for ground-truth photos), Twilio WhatsApp, Africa's Talking SMS,
  Masumi/Cardano. **Zero AWS.** Repo is a 5-day sprint (2026-06-26→07-01),
  3 months stale; seed script has a shadowed duplicate function that
  NameErrors on run.
* **Data:** none persisted. Seeds: 50 farmers / 80 plots around real
  Nyandarua/Nakuru/Kiambu county centroids; 30-day synthetic weather +
  NDVI-curve snapshots for the demo farmer. The 47-county Kenya coordinate
  database in `frontend/app/onboarding` is genuinely real and reusable for
  zone placement.
* **Fabrications to fence off** (ingest only with low-confidence flags, or
  exclude — `docs/01:92-94` already tags them): `evi = ndvi×0.82`,
  `savi = ndvi×0.8`, `ndwi = msi = 0` hardcoded; rolling 5/10/14-day windows
  set equal to same-day values; GDD fetched, never accumulated locally;
  humidity stored but unused by the rule engine.
* **Confirmed absent:** SUBSTOR, SimCast, blight/fungicide units, hourly data
  of any kind, soil moisture (one advisory string only), sensor hardware
  ("sensorType" is a rule-threshold label, not a device).
* **Salvage value:** WhatsApp dispatch flows (Twilio webhook + pipeline C
  06:30 EAT), GraphRAG chat, VLM ground-truth photo classification — the only
  "live integration" code in either legacy tree.

### 5.3 Consequence for the twin (unchanged from `docs/01`, now audit-confirmed)

The merge is a **schema-union exercise, not code reuse**: the twin authors NEW
attributes for every driver no legacy source can populate (soil moisture, soil
temperature, hourly RH, humid hours, SRAD, live Tmax/Tmin) and replays
seed/API data honestly. All demo claims must follow the ledger in §10.

## 6. Verdicts

* **Feasible: YES**, conditional on the pivot — the Kit-free core runs on free
  notebooks today (`usd-core==26.8`); the GPU showpiece (3DGS on public
  capture) fits a T4 under resolution/iteration caps; the browser viewer
  needs only GitHub Pages.
* **Optimal: architecture YES** (layer discipline, enforced write path,
  codeless dual-environment schema — all 7/7 invariants pass), **demo strategy
  NO** — the planned centerpiece (in-Kit smoke test) was unrunnable under the
  constraints and would have consumed the whole window.
* **Radical pivot: exactly one, presentation-level.** The data architecture
  needs no pivot — it is precisely what survives. Omniverse Kit/RTX/Nucleus
  move from "demo substrate" to "documented post-hackathon runtime" (§11).

## 7. Decisions (considered -> chosen -> rejected)

| ID | Decision | Rationale | Rejected alternatives |
|---|---|---|---|
| D1 | **Demo substrate = Colab notebook + GitHub Pages browser viewer; Kit GUI is out of the demo path.** Accepted by user 2026-09-27 | Free Colab ToS bans remote desktop/web-UI bypass; Kit needs RTX+Vulkan+Nucleus; live pitch must work in any browser. The Kit-free core already runs headless | Kit App Streaming from Colab (ToS + tech blockers); renting GPU credits (none available); abandoning USD for a game engine (throws away the only built, tested asset) |
| D2 | **3DGS on the verified Inria public capture ("truck") as labelled proof-of-concept**, trained live on T4 | User has no farm photos; Inria URL verified HTTP 200; outdoor vegetation scene; the training run itself is the GPU story for an NVIDIA-branded challenge | Claiming a farm scan (dishonest); pre-trained splat only (kills the GPU narrative; kept as last-resort fallback with honest labelling); 3DGS from synthetic renders (unverifiable realism, wastes window) |
| D3 | **PLY -> `UsdGeomPoints` converter (`tools/ply_to_usd_points.py`, pxr-only)** for the scan asset | Toga unverifiable (§3); points-with-colors works on pure usd-core everywhere; one ~80-line tool replaces the placeholder reference | `.usdg`/Toga (unverified, cannot gate a same-day demo); mesh extraction via SuGaR-style pipeline (hours of extra compute + risk for marginal judge value) |
| D4 | **No SUBSTOR/SimCast maths, no MQTT/AWS, no Cesium, no physics — today or in the demo.** Phase discipline (AGENTS.md rule 1) holds | A wrong implementation of published equations under time pressure is worse than an honest, demarcated stub; network egress from notebooks is fragile ground for a live pitch | Partial SUBSTOR port "for wow factor" (highest-risk item in the whole plan; refused) |
| D5 | **Fix F1 (zero-drop + test blessing) at T0, before anything new** | It is the Phase 2 entry point; shipping a demo on a corrupted aggregation seam bakes the bug into the story | Deferring (the bug is currently test-blessed — it would never be caught later) |
| D6 | **Pin `usd-core==26.8`** in requirements-dev.txt | Demo freeze discipline; cp312/313 wheels; verified on PyPI 2026-07-20 | Leaving `>=25.5` floor (F3 — nightly drift can break the live demo) |
| D7 | **Demo `farmAssetPath` defaults to a local `file://` path**; Nucleus URL moves to documentation | F4 — every notebook silently composes empty on the Nucleus default; the live pitch cannot depend on a server that does not exist | Keeping the default and overriding per-session (one forgotten setting kills the demo) |
| D8 | **Pitch claims ledger (§10) is a mandatory artifact** | Verified: no IoT, no moisture, no hourly data, no photos, no real records exist in either legacy repo. Judges probe exactly these. The twin's honest "NEW attributes = Phase 2 IoT requirements" line (docs/01) is the defensible answer | Bluffing a sensor deployment (audit-provable falsehood — disqualifying risk) |
| D9 | **Scope note for AGENTS.md rule 1:** the 3DGS PoC is a *notebook-scoped preview of Phase 3 item 2* (scan pipeline), authorized by the user via the accepted pivot; the extension core (`exts/`) gains only the pxr-only `tools/ply_to_usd_points.py` and a demo notebook. `docs/00` updated accordingly | Keeps the governance chain intact — phase gates stay real, no silent scope creep | Rewriting the phase plan wholesale mid-window (destabilizes the one tested asset) |

## 8. Execution plan (6h baseline; 4h compression = cut C-replay, one rehearsal)

**Track split: driver (repo + notebook) + second (pitch pack + viewer page).**
All artifacts must open with zero install in a browser.

* **T0:00-0:40 — Harden (gate: pytest 9/9 green on `usd-core==26.8`)**
  Fix F1 (+test), F2 (path contract → `/ope/code/ai-kenya`), F3/D6 (pin), F5
  (RNG), F4/D7 (farmAssetPath local default). Track the spec doc in git.
  New: `notebooks/twin_demo.ipynb` (install pins, run tests, build demo stack,
  print structure) — zero new core code.
* **T0:40-2:40 — GPU showpiece (Colab T4)**
  Download verified Inria capture → train 3DGS (≤800px, ≤30K iters, truck
  scene) → orbit video (mp4 from in-notebook frames), export `.ply`, print
  PSNR/SSIM. Fallback ladder: Kaggle P100 (unverified quota) → 7K iters →
  pre-trained public splat, honestly labelled.
* **T2:40-4:00 — USD integration**
  `tools/ply_to_usd_points.py` (pxr-only, per D3) → referenced as the real
  scan asset replacing PlaceholderGround. Runtime replay: FarmWise seed
  NDVI/GDD series authored as USD time samples on RUNTIME_LYR (the mechanism
  `docs/03` §history already prescribes) — the twin scrubs through 30 days.
* **T4:00-5:00 — Browser viewer (second track)**
  GitHub Pages + CDN three.js gaussian-splat viewer (mkkellogg/GaussianSplats3D
  or antimatter15/splat — no build step); upload trained `.ply` via web UI;
  public URL = interactive 3D on judges' phones.
* **T5:00-6:00 — Pitch pack + 2 rehearsals**
  Architecture one-pager (from docs/02), claims-ledger table (§10), demo
  script with fallback order (live notebook → Pages viewer → committed mp4),
  Kit/RTX roadmap slide.

## 9. Demo risk register

| Risk | Likelihood | Impact | Mitigation / fallback |
|---|---|---|---|
| T4 unavailable on free Colab at demo time | Med | High | Start training early, keep session warm; Kaggle P100 fallback (unverified); pre-trained splat last resort |
| Training exceeds T4 memory | Med | Med | 800px cap, 7K-iter early stop, scene crop to truck subset |
| Inria URL dies mid-window | Low | Med | Verified 200 today; re-download once, keep VM-local copy; dataset not committed to repo (size) |
| GitHub Pages viewer fails to load in venue browser | Low | Med | Committed orbit mp4 in repo; notebook cell renders frames inline |
| Live pitch machine blocks Colab/Drive login | Low | High | Share notebook link pre-authenticated (anyone-with-link view), mp4 + PDF pitch pack as full offline fallback |
| Fresh runtime at pitch time (Colab recycled) | High | Med | Notebook is fully deterministic: pins + runtime downloads only; rehearse the cold start twice |
| Judges probe "where is the sensor data?" | High | High | Claims ledger §10 — answer with the NEW-attribute roadmap, never bluff |
| Repo secrets leak via legacy copies | Low | Disqualifying | Nothing from legacy repos enters this repo except documented knowledge; never copy `.env`/`test_isda.py` |

## 10. Pitch claims ledger (honesty table — mandatory)

| Demo segment | Claim exactly as pitched | Truth class | Backing |
|---|---|---|---|
| 3DGS training | "3D Gaussian Splatting trained live on a free Colab T4 from the Inria public reference capture — PoC for the field-scan pipeline (Phase 3)" | REAL compute; PUBLIC capture, not farm | notebook log + PSNR/SSIM |
| Farm scan | "Placeholder reference today; real farm scan is post-hackathon 3DGS" | HONEST GAP | docs/00 Phase 3 item 2 |
| Soil chemistry (pH, EC, OC, N, P, K) | "AgriFusion assessment schema, values from its seed/demo set" | REAL schema; SYNTHETIC values | docs/01 §2, seed scripts |
| NDVI / GDD / weather | "FarmWise DailySnapshot products (AgroMonitoring/OWM at runtime); replay uses its seeded series" | REAL schema; MIXED provenance | docs/01 §3 |
| EVI / SAVI / NDWI / MSI | (not pitched) | FABRICATED upstream — excluded | docs/01 §3a; audit §5.2 |
| Soil moisture, soil temp, hourly RH, SRAD | "Schema supports them as NEW attributes — no legacy source populates them; Phase 2 IoT requirements" | ABSENT — roadmap | docs/01 §4 |
| SUBSTOR / SimCast | "Driver mapping complete; models run as external daily services in Phase 2 (DSSAT/container per docs/03)" | STUB BY DESIGN | phase2/, docs/03 |
| Live telemetry | "Simulated ticks write through the enforced RuntimeWriter path into RUNTIME_LYR — the same path real ingestion will use" | REAL mechanism; synthetic values | tests, runtime_writer.py |
| Layer composition | "Root layer never authored a prim; definitions and live values are physically separated files" | REAL, tested | test_headless.py:67, 97-104 |

## 11. Post-hackathon roadmap (priority order)

1. Kit/RTX in-Kit smoke test on any borrowed RTX machine (docs/00 item 7) —
   the extension surface is written but has never executed.
2. Toga/`.usdg` verification through NVIDIA developer channels; if real, swap
   `ply_to_usd_points` output for native splat prims.
3. Obtain the GoMyCode brief text; re-align pitch/demo to its rubric.
4. Phase 2 per `docs/03` (unchanged): AWS IoT Core MQTT-over-WebSocket (port
   443 — notebook-egress-friendly), adapters with unit conversion, legacy
   back-fill against the **current** AgriFusion tree (Go backend — §5.1).
5. Legacy hygiene: secrets removal, LICENSE decision, then real data.
6. Real-agriculture 3D data sources (verified 2026-09-27, no registration
   walls) for the twin side — both ship pre-reconstructed point clouds, NOT
   photo+pose captures, so they feed the USD-point-cloud path (`scan_io`
   family), not 3DGS training:
   - **BonnBeetClouds3D** (Uni Bonn, IROS 2024) — 11.1 GB zip, real
     sugar-beet field plots, aerial photogrammetry, per-point plant/leaf
     instance labels + phenotypic measurements.
     https://bonnbeetclouds3d.ipb.uni-bonn.de (DOI 10.60507/FK2/34W30T)
   - **Pheno4D** (Uni Bonn/ETH) — 4.4 GB zip, direct download; daily
     sub-millimeter 3D scans of the same maize/tomato plants across growth
     stages (~260M labeled points). Multi-temporal structure is a natural fit
     for the twin's time-sample replay (per-plant 4D).
     https://www.ipb.uni-bonn.de/data/pheno4d/index.html
   For 3DGS training on real fields (photos + poses), no public dataset
   exists (checked ricber/digital-agriculture-datasets catalog, ODM
   community, Mip-NeRF 360, INRIA tandt): Phase 3 must capture its own
   (30-60 phone/drone photos, calm morning; COLMAP included in the pipeline).

## 12. Open items / unverified assumptions

1. GoMyCode challenge rubric — unfetchable (JS-walled; search captchas). User
   action: paste brief text if it exists.
2. Kaggle GPU quotas/session limits — unverified today; Colab facts are
   verified, Kaggle is fallback-only by design.
3. Toga — negative-evidence conclusion only; revisit via NVIDIA channels.
4. Kit 106.x/107.x dependency names in `extension.toml`/`apps/*.kit` remain
   unexercised; treat as unverified until the smoke test lands.
5. `data.nerf.studio` is dead (404) — recorded so nobody re-walks it.
