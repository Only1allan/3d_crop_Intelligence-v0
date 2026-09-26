# 01 - Repository Analysis and Variable Mapping

Phase 1, step 1 of the handoff packet. Read the two legacy repositories and
map their data to the `FarmSensorAPI` / `FarmZoneAPI` schemas.

## 1. Headline findings (read this first)

The prompt describes the inputs as a "Soil Intelligence Platform with data
ingestion protocols" and a "Potato Farming Project containing SUBSTOR-Potato
and SimCast". The code does not match that description:

| Assumption in the prompt | What the repository actually contains |
|---|---|
| AgriFusion (`agrifusion-aws`) has IoT ingestion (MQTT / IoT Core) and soil moisture | No IoT, no devices, no MQTT, no soil moisture or soil temperature. It is an offline-first Next.js PWA where extension agents hand-enter one **assessment** per field visit (pH, EC, organic carbon, N, P, K, visual soil scores) that syncs to Aurora PostgreSQL. The only "gridded" soil source is a synthetic 5x5 iSDA grid with random values. |
| FarmWise (`agriLegends`) has SUBSTOR-Potato (dry matter partitioning, temperature equations, yield) | No SUBSTOR. Growth stage advances on calendar days after planting (Emergence 0-21, Tuber Initiation 22-45, Bulking 46-80, Maturation 81-110). GDD is fetched from AgroMonitoring, not computed, and is not used for staging. Yield is an LLM guess from 14 daily snapshots. |
| FarmWise has SimCast (blight units, fungicide units, RH >= 90 % hours) | No SimCast. Disease risk is five threshold rules on daily precipitation / temperature / NDVI (humidity is stored but unused) followed by an LLM call. |
| Sensors have IDs and telemetry protocols | Neither repo has a sensor or device concept. FarmWise's per-day `DailySnapshot` node and AgriFusion's `Assessment` record are the closest analogues. |

Consequence for the architecture: the schema below is the **union** of what
the legacy systems actually produce and what SUBSTOR / SimCast need as
drivers. Attributes that no legacy source can populate are marked *NEW* and
become Phase 2 IoT requirements. This was verified by exhaustive grep of both
trees (terms: substor, simcast, blight unit, fungicide unit, dry matter,
partition, bulking, LAI, radiation, mqtt, iot, kinesis, sqs, lambda).

## 2. AgriFusion (`agrifusion-aws`) - soil chemistry

Stack: Next.js 16 App Router, Dexie/IndexedDB offline queue, Aurora
PostgreSQL (PostGIS + pgvector), Bedrock (Titan embed, Claude 3 Haiku),
Open-Meteo, iSDA Africa. Deploys to Vercel; no IaC in repo.

Canonical record: `Assessment` (`src/lib/db.ts:3-112`) mirrored by the
`assessments` table (`scripts/schema.sql:225-278`). Ingestion is the wizard
-> Dexie -> `POST /api/sync` (`src/app/api/sync/route.ts`) batch path; there
is also `POST /api/assess` for live QUEFTS recommendations.

| AgriFusion field | Type / unit | FarmSensorAPI attribute | Notes |
|---|---|---|---|
| `chemicalConstraints.ph` (`ph`) | REAL, pH 0-14 | `farmSensor:soilPH` | direct |
| `chemicalConstraints.ec` (`ec`) | REAL, dS/m | `farmSensor:soilEC` | direct |
| `chemicalConstraints.organicCarbon` | REAL, % | `farmSensor:soilOrganicCarbon` | direct |
| `chemicalConstraints.nitrogen` | REAL, % total N | `farmSensor:nitrogenLevel` | direct |
| `chemicalConstraints.phosphorus` | REAL, ppm | `farmSensor:phosphorusLevel` | ppm == mg/kg |
| `chemicalConstraints.potassium` | REAL, meq/100 g | `farmSensor:potassiumLevel` | meq/100 g == cmol(+)/kg numerically |
| `visualAssessment.textureClass` | enum ("Sandy Loam" ...) | `farmSensor:soilTextureClass` | lower_snake_case the label |
| `gpsLat`, `gpsLng` | REAL, WGS84 deg | `farmSensor:latitude/longitude` | single precision upstream |
| `id` (SERIAL) + `integrityHash` | int / sha256 | `farmSensor:externalRef` = `"assessments.id=<id>"` | id spaces differ client vs server; use the server id |
| `createdAt` | ISO-8601 UTC | `farmSensor:lastUpdateTime` | convert to epoch seconds |
| `fieldProfile.fieldSize` | number, **acres in UI, ha in compute** | `farmZone:areaHa` | multiply acres by 0.4047; flag the upstream inconsistency |
| `fieldProfile.plantingDate` | DATE | `farmZone:plantingDate` | direct |
| `farmerName`, `county`, `subCounty` | text | `farmZone:displayName` | concatenated |
| `IsdaGridPoint {lat, lon, ph, organicCarbon, nitrogen, phosphorus, potassium}` | numbers | one `assessment_virtual` sensor per grid point, `source = agrifusion_isda_grid` | values are `Math.random()` in `/api/cache/isda/bulk`; demo only |
| `recommendations.soilStatus.*_status` | critical / warning / good | `farmSensor:status` | map critical->critical, warning->warning, good->nominal |
| `visualAssessment.structureScore`, `rootHealth`, `soilColor`, `erosionType`, `compaction` | 0-3 scores / enums | not mapped | qualitative; stays in AgriFusion |
| soil moisture, soil temperature | - | `farmSensor:soilMoisture`, `soilTemperature` | **NEW** - not measured by AgriFusion |

Sensor kind for every AgriFusion-sourced point: `assessment_virtual`,
`source = agrifusion_assessment`.

Upstream defects that Phase 2 ingestion must tolerate:
* `sync/route.ts` substitutes defaults (pH 6.0, N 0.15, P 15, K 0.3, OC 1.5) for missing values, so stored numbers may not be measurements. Carry a confidence flag or skip rows whose `confidence.breakdown.*.source` is not "Field Test".
* `structureScore || null` turns a legitimate 0 into NULL.
* `phMethod` is dropped before sync.
* `test_isda.py` contains plaintext iSDA credentials; do not copy that file anywhere.

## 3. FarmWise (`agriLegends`) - weather, satellite, phenology

Stack: FastAPI + Neo4j AuraDB, APScheduler pipelines (A ingest 00:00 UTC, B
evaluate 00:05, C dispatch 03:30), AgroMonitoring (NDVI, weather, GDD),
OpenWeatherMap day summary, iSDAsoil, Featherless LLM, Twilio, Masumi/Cardano.

Canonical per-day record: `DailySnapshot` (written by
`backend/pipelines/pipeline_a_ingestion.py`, typed in
`frontend/lib/api.ts:78-86`). Per-plot static data: `Plot` and `Season`
nodes. Per-plot soil baseline from iSDA in `backend/agents/soil.py`.

### 3a. Zone-level (FarmZoneAPI)

| FarmWise field | Type / unit | FarmZoneAPI attribute | Notes |
|---|---|---|---|
| `Plot.plotId` (uuid4) | str | `farmZone:externalRef` | |
| `Season.seasonId` | str | `farmZone:seasonRef` | |
| `Plot.agromonitoringPolygonId` / `boundaryPolygon` | str | `farmZone:polygonRef` | synthetic square, not a surveyed boundary |
| `Plot.name` | str | `farmZone:displayName` | |
| `Plot.latitude/longitude` or `Plot.location` JSON `{lat,lng}` or county centroid | WGS84 (implicit) | `farmZone:centroidLatitude/Longitude` | three storage forms; `_parse_location` handles them |
| `Plot.areaHa` / `acres` / `sizeAcres` | ha / acres | `farmZone:areaHa` | acres x 0.4047 |
| `Season.varietyName` / `PotatoVariety.name` | str | `farmZone:variety` | Shangi, Kenya Mpya, Dutch Robjin, Tigoni, Asante |
| `Season.plantingDate` | Neo4j date | `farmZone:plantingDate` | ISO string |
| `GrowthStage.name` via `AT_STAGE` / `HAS_GROWTH_STAGE` | enum | `farmZone:growthStage` | normalise to snake tokens |
| days since planting (computed) | int | `farmZone:daysAfterPlanting` | |
| `Plot.accumulatedGDD` | float, degC-day base 8 | `farmZone:accumulatedGDD` | |
| `DailySnapshot.mean_ndvi` | float 0-1 | `farmZone:ndvi` | |
| `DailySnapshot.mean_evi` | float | `farmZone:evi` | derived `ndvi*0.82`, low confidence |
| `DailySnapshot.cloud_cover_percentage` | % | `farmZone:cloudCover` | gate: > 95 skipped upstream |

### 3b. Sensor-level (FarmSensorAPI, kind `weather_station`, source `farmwise_snapshot`)

| FarmWise field | Type / unit | FarmSensorAPI attribute | Notes |
|---|---|---|---|
| `DailySnapshot.daily_avg_temp_c` | degC (day value, from K) | `farmSensor:ambientTemperature` | |
| `DailySnapshot.daily_avg_humidity` | % (afternoon) | `farmSensor:relativeHumidity` | single value per day; not enough for SimCast |
| `DailySnapshot.daily_precip_mm` | mm/day | `farmSensor:precipitation` | |
| `Observation_Weather.tempMax / tempMin` | degC | `farmSensor:temperatureMax / Min` | **seed data only**; no live writer |
| `DailySnapshot.date` | YYYY-MM-DD | `farmSensor:lastUpdateTime` | midnight UTC epoch |
| `snapshotId` | uuid4 | `farmSensor:externalRef` | |

### 3c. Soil baseline (FarmSensorAPI, kind `soil_probe`, source `farmwise_isda_baseline`)

| FarmWise field | iSDA unit | FarmSensorAPI attribute | Conversion |
|---|---|---|---|
| `Plot.soilBaseline_pH` | pH | `farmSensor:soilPH` | none |
| `Plot.soilBaseline_N` (`nitrogen_total`) | g/kg | `farmSensor:nitrogenLevel` (%) | divide by 10 |
| `Plot.soilBaseline_OC` (`carbon_organic`) | g/kg | `farmSensor:soilOrganicCarbon` (%) | divide by 10 |
| `Plot.soilBaseline_Al` | cmol(+)/kg | `farmSensor:aluminiumLevel` | none |
| `Plot.soilBaseline_C` | g/kg | not mapped | total carbon; keep upstream |

Note the unit trap: AgriFusion's iSDA proxy labels the same iSDA numbers as
"%" without dividing by 10. Phase 2 ingestion must normalise at the source
adapter, never in the scene.

Upstream defects to tolerate: Pipeline B queries `date = today` while
Pipeline A writes `date = yesterday` (so B usually finds nothing);
`farmer.py` calls `ingest_weather` with shifted arguments and imports two
functions that do not exist; `snapshotId` MERGE with a fresh uuid can
duplicate days; alert timestamps are epoch **milliseconds** while API calls
use epoch **seconds**.

## 4. Model driver coverage

### SUBSTOR-Potato (daily drivers)

| Driver | FarmSensorAPI / FarmZoneAPI | Legacy source | Gap |
|---|---|---|---|
| SRAD solar radiation, MJ/m2/day | `farmSensor:solarRadiation` | none | **NEW**: IoT pyranometer or NASA POWER / Open-Meteo shortwave_radiation_sum |
| TMAX / TMIN, degC | `farmSensor:temperatureMax/Min` | FarmWise seed only | **NEW** live: weather station or Open-Meteo daily |
| RAIN, mm | `farmSensor:precipitation` | FarmWise `daily_precip_mm` | ok |
| Soil water | `farmSensor:soilMoisture` | none | **NEW**: IoT probe |
| Soil N | `farmSensor:nitrogenLevel` | AgriFusion (%), FarmWise iSDA (g/kg) | ok after /10 |
| Planting date, cultivar | `farmZone:plantingDate`, `farmZone:variety` | FarmWise Season | ok; cultivar coefficients live with the model |
| Outputs | `cropModel:substor*`, `farmZone:growthStage` | - | written by Phase 2 bridge |

### SimCast (late blight)

| Driver | FarmSensorAPI | Legacy source | Gap |
|---|---|---|---|
| Hours with RH >= 90 % per day | `farmSensor:humidHours` | none (FarmWise has one afternoon RH value) | **NEW**: hourly RH from IoT or edge aggregation |
| Mean T during humid hours | `farmSensor:humidPeriodTemperature` | none | **NEW** |
| Rain (fungicide wash-off) | `farmSensor:precipitation` | FarmWise | ok |
| Cultivar resistance | `farmZone:variety` -> `PotatoVariety.blightResistance` (low / medium) | FarmWise knowledge graph | ok |
| Outputs | `cropModel:simcast*`, sensor `status` | - | written by Phase 2 bridge |

## 5. Conventions adopted in the twin

* **IDs**: `farmSensor:sensorId` == prim name (`^[A-Za-z_][A-Za-z0-9_]*$`). Upstream keys go to `externalRef`, never into prim names (uuids start with digits and contain hyphens).
* **Time**: `lastUpdateTime` is Unix epoch **seconds**, UTC, double. Adapters convert ISO strings, Neo4j dates and epoch ms.
* **Units** on the schema are the AgriFusion units (pH, dS/m, %, %, mg/kg, cmol/kg) plus SI for weather (degC, %, mm/day, MJ/m2/day).
* **Coordinates**: stage is Z-up, metres, local farm frame. WGS84 lat/lon are carried as attributes for Cesium anchoring in Phase 3.
* **Source tagging**: every value carries `farmSensor:source`, so mixed-provenance zones (a manual assessment next to an IoT probe) remain auditable.
