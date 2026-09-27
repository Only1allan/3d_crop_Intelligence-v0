# 05 - Demo Run-of-Show & Pitch Pack (2026-09-27)

Operational companion to `docs/04_AUDIT_AND_PIVOT.md` (the decision record).
Everything here assumes the accepted pivot: **notebook + browser demo, live
pitch, free Colab/Kaggle only, browser-only workstations.**

## Artifacts

| Artifact | Where | What judges see |
|---|---|---|
| Twin notebook | `notebooks/twin_demo.ipynb` (Colab, CPU is fine) | 18 green invariant tests, layer stack build, layer separation, 30-day time-sample replay + scrub, farm map, optional scan composition |
| GPU notebook | `notebooks/gs_scan.ipynb` (Colab, T4) | Real 3DGS training (~7k iters, PSNR printed), flythrough mp4, `scan.ply` export |
| Browser viewer | `docs/viewer/index.html` (+ `scan.ply` uploaded) via GitHub Pages (branch `main`, folder `/docs`) | Interactive 3D splat on any laptop/phone, honest badge overlay |
| Backup video | `orbit.mp4` (committed or linked) | Plays even if everything live fails |
| Decision record | `docs/04` | Verification log, decisions, risk register, claims ledger |

## Run of show (~10 min)

1. **0:00-1:30 Problem.** Two real Kenyan agri platforms (AgriFusion soil
   chemistry, FarmWise potato phenology) that cannot see each other. We merged
   them into one OpenUSD digital twin.
2. **1:30-4:30 Twin notebook.** Run cells live in order: tests -> build ->
   show the two layer files side by side ("definitions live here, live values
   there - wipe one, the other survives") -> replay -> scrub table (day 42 vs
   55 vs 67 - same stage, no reload). This is the architecture story.
3. **4:30-7:30 GPU notebook (pre-trained before the pitch, rerun 7k live only
   if the venue is brave).** Show PSNR lines + orbit.mp4 generation. "Trained
   on a free T4 in under 20 minutes - the same pipeline a drone capture feeds."
4. **7:30-9:30 Browser viewer** on a phone: interactive splat. Badge on screen
   says exactly what is real (public capture PoC) - credibility beats bluff.
5. **9:30-10:00 Roadmap:** Kit/RTX runtime (post-hackathon), AWS IoT Core
   MQTT-over-WebSocket ingestion, SUBSTOR/SimCast as external services.
   `docs/03` + `docs/04` §11.

## Pre-pitch checklist (T-60 min)

- [ ] `pivot` branch **merged into `main`** (GitHub web UI: PR `pivot` -> `main`,
      merge). Pages and the notebooks' default clone both follow `main`.
- [ ] Repo pushed to `main` (notebooks, viewer page, docs).
- [ ] GitHub Pages enabled: Settings > Pages > Deploy from branch `main`,
      folder `/docs`. Viewer URL:
      `https://only1allan.github.io/3d_crop_Intelligence-v0/viewer/`
- [ ] `scan.ply` (<100 MB) uploaded to `docs/viewer/` via GitHub web UI.
- [ ] Twin notebook ran end-to-end once today; outputs left in place.
- [ ] gs notebook: training done once, `orbit.mp4` downloaded and committed;
      PLY size checked.
- [ ] Offline fallback bundle on the pitch laptop: `orbit.mp4` + `farm_map.png`
      + a PDF export of the scrub-table cell output.

## Fallback ladder

| Failure | Fallback |
|---|---|
| Colab cold-start slow at pitch time | pre-run notebook with outputs + orbit.mp4 |
| No T4 granted today | Kaggle P100/T4x2, or show pre-trained run + logs |
| Pages viewer broken in venue browser | mp4 + SuperSplat share link (upload PLY at supersplat.playcanvas.com) || Judge asks for sensor data | claims ledger (docs/04 §10): schema supports, values are synthetic, IoT is Phase 2 - never bluff |

## Hard pushbacks (do not do these at the venue)

- Do not claim the scan is a farm capture.
- Do not claim live sensors, soil moisture, or hourly RH exist.
- Do not hand-implement SUBSTOR/SimCast maths on stage or overnight.
- Do not depend on Toga/`.usdg`, Nucleus, AWS, or any unverified format live.
