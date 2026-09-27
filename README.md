# Omniverse Crop Intelligence

**Your farm, digitized. And able to talk back.**

A 3D digital twin of the farm, built on OpenUSD for NVIDIA Omniverse, that
farmers can talk to. Click a plot, see its intelligence, ask it anything.

## The problem

Farmers make the calls that decide a season blind: irrigate or not, lime or
not, spray or not. The data that would answer them exists in fragments: a soil
lab PDF, a weather app, a field notebook. There is no single view of the farm,
and no way to simply ask it a question. The cost is wasted water, wasted
inputs and crop loss that could have been prevented.

## The solution

One digital twin of the farm, built in three layers.

| Layer | What it does |
|---|---|
| **Ingestion** | Every plot in 3D, with the data around it: soil chemistry, pH, weather, crop signals |
| **Processing** | Raw data becomes insight: crop health, stress and blight-risk flags, growth stage, yield outlook |
| **Communication** | The farmer talks to those insights, by text or voice. WhatsApp and SMS next |

Ask "Should I irrigate the South Slope?" and get an answer built from that
plot's own numbers: moisture fell from 21% to 13.2% this week, below the 18%
floor, during tuber initiation, so irrigate today.

## Why it is different

- **A farm you talk to**, not charts you have to interpret.
- **An interactive 3D twin**, plot by plot, not a flat map.
- **One data model for the whole farm** on OpenUSD, so a real sensor drops in without renaming anything.
- **Honest by design**: every answer shows its sources, and every screen labels what is real.

## Try the demo

```bash
cd web && npm install && npm run dev    # http://localhost:5173
```

Open the farm, click a plot, ask it anything. No login. Add a free OpenRouter
key in `web/.env.local` for live AI answers; without one, the advisor answers
offline from the same data.

## Toolkit

| Area | Tools |
|---|---|
| Digital twin | OpenUSD (custom farm sensor schema, layered stage), NVIDIA Omniverse Kit extension |
| AI advisor | NVIDIA Nemotron 3 Super via OpenRouter, in-browser retrieval over the plot data, Web Speech API for voice |
| 3D scanning | 3D Gaussian Splatting trained on **NVIDIA Brev** GPU instances, with free Kaggle / Colab T4 as fallback |
| 4D growth | Pheno4D real maize laser scans replayed as USD time samples |
| Web app | React, Vite, Three.js, React Three Fiber, Framer Motion |
| Tooling | Python, pytest, Jupyter notebooks |

## What is real today

- **Real:** the 3D twin, the AI conversation, the OpenUSD schema and its tests, the 3D scan training runs, and the plant-growth replay from real laser scans.
- **Synthetic:** plot values (on the real schema). Yield and blight values are placeholders until the models run.
- **Not yet:** live sensors, a scan of our own farm, and a run inside Omniverse Kit on RTX.

## Roadmap

1. WhatsApp and SMS access to the same advisor
2. Live soil, weather and satellite data through AWS IoT
3. Yield (SUBSTOR) and blight (SimCast) models behind the insights
4. A drone scan of a real partner farm, and the full Omniverse Kit / RTX runtime

GoMyCode × NVIDIA Hackathon 2026.
