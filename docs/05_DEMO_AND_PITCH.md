# 05 - Demo Run-of-Show & Pitch Pack (2026-09-27)

Operational companion to `docs/04_AUDIT_AND_PIVOT.md` (the decision record).
Everything here assumes the accepted pivot: **notebook + browser demo, live
pitch, free Kaggle/Colab only.**

## Artifacts

| Artifact | Where | What judges see |
|---|---|---|
| Twin notebook | `notebooks/twin_demo.ipynb` (Kaggle CPU kernel or Colab) | 20 green invariant tests, layer stack build, layer separation, 30-day time-sample replay + scrub, farm map, scan composition |
| GPU notebook | `notebooks/gs_scan.ipynb` (Kaggle T4x2 kernel `allankariuki/crop-gs-scan`, or Colab T4) | Real 3DGS training (7k iters, PSNR), orbit `orbit.mp4` render, `scan.ply` + `scan_viewer.ply` + `farm_scan.usda` export |
| Browser viewer | `docs/viewer/index.html` + `scan.ply` (committed) - serve locally (`python -m http.server`) or GitHub Pages if the repo ever goes public | Interactive 3D splat, honest badge overlay |
| Garden variant | `docs/viewer-garden/` (same viewer, Mip-NeRF 360 `garden` scene) | Lush-vegetation scene, **PSNR 27.3**, full 360° orbit; stronger "green" visual |
| REAL plant growth (4D) | `docs/pitch/pheno_days.png` + `pheno_growth.png/.json`, `assets/pheno_plant.usda` | Pheno4D maize: 12 daily laser scans of the SAME plant as USD time samples, 0.66 m -> 3.66 m, composed into the twin as a session overlay (base files hash-unchanged) |
| Backup video | `docs/viewer/orbit.mp4` + `docs/viewer-garden/orbit.mp4` (committed) | Plays even if everything live fails |
| USD scan assets | `assets/farm_scan.usda` + `assets/farm_scan_garden.usda` (committed, from the real runs) | The 3DGS outputs as OpenUSD, composing into the twin headless |
| Decision record | `docs/04` | Verification log, decisions, risk register, claims ledger |

## How the demo was produced (reproducible, executed 2026-09-27)

1. Kaggle dataset `allankariuki/3dcrop-twin-src` = clean `git archive` of
   `pivot` + py312 wheels (offline pip insurance).
2. Kaggle kernel `allankariuki/crop-gs-scan` (T4 x2, internet ON) runs
   `notebooks/gs_scan.ipynb`: clone INRIA repo (three CUDA submodules, GLM
   headers installed - the rotated Kaggle image dropped `libglm-dev`), download
   `tandt_db.zip` (COLMAP poses included), train `truck` 7k iters
   (**PSNR 22.36 @3.5k, 24.98 @7k**, 1,697,292 gaussians), render a 160-frame
   orbit from training cameras sorted by azimuth (978x546, 10.6 MB), convert
   via `scan_io` to `farm_scan.usda` (141,441 points after the 150k cap), cap
   `scan_viewer.ply` (35.1 MB, 62 properties preserved).
   Artifacts are persisted to `/kaggle/working` as they are produced, so a
   late-cell failure never costs the trained model (learned the hard way:
   kernel versions 1-10 each caught a different platform failure).
3. Kaggle kernel `allankariuki/crop-twin-demo` (CPU) attaches the scan kernel's
   output as a data source (`kernel_sources`) and runs `notebooks/twin_demo.ipynb`
   end-to-end - zero manual upload steps. Validated locally first via
   `jupyter nbconvert --execute` (21 tests green, replay, scrub, plot, scan
   composition).
4. Kernel outputs are downloaded, verified structurally (point counts,
   extents, PSNR), and committed to this repo: `docs/viewer/scan.ply` (capped
   PLY served to the browser viewer), `docs/viewer/orbit.mp4`,
   `docs/viewer/metrics.json`, `assets/farm_scan.usda` (the real scan as
   OpenUSD, verified composing under `/World/Farm/FarmScan`, extent
   ~217 x 153 m).

Same notebooks run unchanged on free Colab if Kaggle is unavailable.

## Garden variant (second real run, same day)

`notebooks/gs_garden.ipynb` -> Kaggle kernel `allankariuki/crop-gs-garden`
(COMPLETE, first green run of this variant): Mip-NeRF 360 `garden` - 185
photos, 3.0 GB, COLMAP poses included (verified from the zip central
directory before the run). **PSNR 25.58 @3.5k / 27.29 @7k**, 3,594,793
gaussians (891.5 MB full PLY), orbit 160 frames @ 1600x1036 (49 MB, full
360° circle), `farm_scan_garden.usda` 149,784 points (composes into the
twin - verified), `scan_viewer.ply` 37.1 MB committed as
`docs/viewer-garden/scan.ply` with its own camera framing computed from the
PLY bounds. Demo-wise: same pipeline, greener scene, better orbit.

## Pheno4D real-growth beat (CPU kernel, no GPU)

`notebooks/pheno4d_demo.ipynb` -> Kaggle kernel `allankariuki/crop-pheno4d-replay`
(COMPLETE): Pheno4D (Uni Bonn/ETH, PLoS ONE 2021) Maize01 - 12 daily
sub-millimeter laser scans of the same plant, authored as **USD time
samples** on one `UsdGeomPoints` prim (`assets/pheno_plant.usda`, 47 MB),
then composed into the farm stage **as a session-layer overlay** - the farm
files stay byte-identical (sha256-proven in the kernel log) and the base
stage alone shows no plant (overlay is session-only). Real heights from the
scans: 0.664 m (Mar 13) -> 3.660 m (Mar 25). Pitch visual:
`docs/pitch/pheno_days.png` (day 1 / 6 / 12 rendered from the actual USD
time samples) and `docs/pitch/pheno_growth.png` (height curve).
Honesty: greenhouse laser scans, not a field, not photos->3DGS - it is the
twin's 4D time-sample mechanic fed with real agricultural data.

## Run of show (~10 min)

1. **0:00-1:30 Problem.** Two real Kenyan agri platforms (AgriFusion soil
   chemistry, FarmWise potato phenology) that cannot see each other. We merged
   them into one OpenUSD digital twin.
2. **1:30-4:30 Twin notebook.** Run cells live in order: tests -> build ->
   show the two layer files side by side ("definitions live here, live values
   there - wipe one, the other survives") -> replay -> scrub table (day 42 vs
   55 vs 67 - same stage, no reload). This is the architecture story.
3. **4:30-7:30 GPU kernel.** Show the completed Kaggle kernel page (logs, PSNR)
   + `orbit.mp4`. "Trained on a free T4 in under 20 minutes - the same
   pipeline a drone capture feeds. The PLY converts to OpenUSD and composes
   into the twin."
4. **7:30-9:30 Browser viewer** on a phone: interactive splat. Badge on screen
   says exactly what is real (public capture PoC) - credibility beats bluff.
5. **9:30-10:00 Roadmap:** Kit/RTX runtime (post-hackathon), AWS IoT Core
   MQTT-over-WebSocket ingestion, SUBSTOR/SimCast as external services.
   `docs/03` + `docs/04` §11.

## Pre-pitch checklist (T-60 min)

- [x] Notebooks hardened against current gaussian-splatting HEAD
      (`--recursive`, `--test_iterations`, `--disable_viewer`, new log format).
- [x] `scan_io` numpy fast-path fixed + equivalence test (21 tests green).
- [x] GPU run completed on Kaggle; artifacts verified + committed
      (`docs/viewer/metrics.json`: PSNR 22.36 @3.5k / 24.98 @7k; both kernels
      show status COMPLETE - `crop-gs-scan` v12, `crop-twin-demo` v3).
- [x] Twin kernel ran end-to-end on Kaggle; outputs on the kernel page,
      including the full 1,695,890-point scan composing into the twin.
- [x] `orbit.mp4` + viewer PLY committed under `docs/viewer/`.
- [ ] On the pitch laptop: `cd docs/viewer && python -m http.server 8000`
      -> `http://localhost:8000` (serves the interactive viewer; file:// will
      NOT work due to module CORS).
- [ ] Phone loads the viewer from the laptop IP on venue Wi-Fi/hotspot.

## Hosting note (Pages)

GitHub Pages is **not available**: the repo is private and the account is on
the GitHub Free plan (Pages API returns 404). Options if a public URL is
wanted: make the repo public (one API call - content was scanned clean), use
GitHub Pro, or upload the PLY to <https://supersplat.playcanvas.com> for a
hosted share link. The live demo does not depend on any of these.

## Fallback ladder

| Failure | Fallback |
|---|---|
| Venue Wi-Fi dead | offline bundle: `orbit.mp4` + `farm_map.png` + scrub-table screenshots |
| Viewer heavy on venue hardware | `orbit.mp4` (committed) or SuperSplat share link |
| Kaggle quota exhausted at pitch time | Colab T4 - same notebooks, no edits |
| Judge asks for sensor data | claims ledger (docs/04 §10): schema supports, values are synthetic, IoT is Phase 2 - never bluff |

## Hard pushbacks (do not do these at the venue)

- Do not claim the scan is a farm capture.
- Do not claim live sensors, soil moisture, or hourly RH exist.
- Do not hand-implement SUBSTOR/SimCast maths on stage or overnight.
- Do not depend on Toga/`.usdg`, Nucleus, AWS, or any unverified format live.
