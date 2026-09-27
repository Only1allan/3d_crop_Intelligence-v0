// Demo farm fixtures. SYNTHETIC values keyed by the REAL OpenUSD attribute
// names from schema/farmSensor/schema.usda (FarmSensorAPI, FarmZoneAPI,
// CropModelStateAPI), so this card can later point at live USD values
// without renaming anything. At least one zone per status token is present.

export const FARM = {
  name: 'Demo Farm',
  region: 'Kenyan highlands (synthetic demo farm)',
  crop: 'Potato',
  totalHa: 9.6,
  today: '2026-09-27',
}

// grid: col 0..2 (west->east), row 0..1 (north->south) on the 3D farm
export const ZONES = [
  {
    zoneId: 'A1', displayName: 'North Terrace', grid: [0, 0],
    status: 'nominal', source: { soil: 'agrifusion_assessment', crop: 'farmwise_snapshot', model: 'synthetic' },
    lastUpdateTime: '2026-09-27T08:40:00Z',
    atmosphere: { ambientTemperature: 19.4, relativeHumidity: 68, precipitation: 2.1 },
    soil: { soilMoisture: 27.5, soilTemperature: 17.8, soilEC: 0.42, soilOrganicCarbon: 2.6, nitrogenLevel: 0.22, phosphorusLevel: 21, potassiumLevel: 0.61, aluminiumLevel: 0.4, soilTextureClass: 'loam' },
    soilPH: 6.1,
    crop: { ndvi: 0.74, evi: 0.61, cloudCover: 12, growthStage: 'tuber_bulking', daysAfterPlanting: 62, accumulatedGDD: 905 },
    agronomy: { variety: 'Shangi', plantingDate: '2026-07-27', areaHa: 1.8, substorTuberFreshYield: 31.5, substorLeafAreaIndex: 3.9, simcastBlightRisk: 'low', simcastSprayRecommended: false },
    series: { soilMoisture: [29, 28.2, 27.9, 28.6, 27.1, 27.8, 27.5], soilPH: [6.1, 6.1, 6.0, 6.1, 6.1, 6.1, 6.1], ndvi: [0.69, 0.7, 0.71, 0.72, 0.72, 0.73, 0.74], accumulatedGDD: [815, 830, 846, 861, 876, 890, 905] },
    insight: 'Healthy canopy, soil and moisture in range. Keep the current plan.',
  },
  {
    zoneId: 'A2', displayName: 'Hillside Block', grid: [1, 0],
    status: 'warning', source: { soil: 'agrifusion_assessment', crop: 'farmwise_snapshot', model: 'synthetic' },
    lastUpdateTime: '2026-09-27T08:32:00Z',
    atmosphere: { ambientTemperature: 18.7, relativeHumidity: 71, precipitation: 2.4 },
    soil: { soilMoisture: 24.1, soilTemperature: 17.1, soilEC: 0.21, soilOrganicCarbon: 1.5, nitrogenLevel: 0.13, phosphorusLevel: 9, potassiumLevel: 0.29, aluminiumLevel: 1.45, soilTextureClass: 'clay_loam' },
    soilPH: 5.1,
    crop: { ndvi: 0.58, evi: 0.48, cloudCover: 14, growthStage: 'tuber_initiation', daysAfterPlanting: 48, accumulatedGDD: 690 },
    agronomy: { variety: 'Kenya Mpya', plantingDate: '2026-08-10', areaHa: 1.4, substorTuberFreshYield: 19.2, substorLeafAreaIndex: 2.3, simcastBlightRisk: 'low', simcastSprayRecommended: false },
    series: { soilMoisture: [25, 24.6, 24.9, 24.2, 24.5, 24.0, 24.1], soilPH: [5.3, 5.3, 5.2, 5.2, 5.2, 5.1, 5.1], ndvi: [0.6, 0.6, 0.59, 0.59, 0.58, 0.58, 0.58], accumulatedGDD: [604, 619, 633, 647, 662, 676, 690] },
    insight: 'Soil is acidic (pH 5.1) with high aluminium. Lime is advised; low P and K are holding growth back.',
  },
  {
    zoneId: 'A3', displayName: 'East Valley', grid: [2, 0],
    status: 'critical', source: { soil: 'agrifusion_assessment', crop: 'farmwise_snapshot', model: 'synthetic' },
    lastUpdateTime: '2026-09-27T08:45:00Z',
    atmosphere: { ambientTemperature: 16.9, relativeHumidity: 92, precipitation: 14.2 },
    soil: { soilMoisture: 36.4, soilTemperature: 16.2, soilEC: 0.51, soilOrganicCarbon: 2.9, nitrogenLevel: 0.25, phosphorusLevel: 18, potassiumLevel: 0.55, aluminiumLevel: 0.5, soilTextureClass: 'clay_loam' },
    soilPH: 5.9,
    crop: { ndvi: 0.52, evi: 0.43, cloudCover: 38, growthStage: 'tuber_bulking', daysAfterPlanting: 71, accumulatedGDD: 1040 },
    agronomy: { variety: 'Dutch Robjin', plantingDate: '2026-07-18', areaHa: 1.6, substorTuberFreshYield: 22.8, substorLeafAreaIndex: 2.8, simcastBlightRisk: 'high', simcastSprayRecommended: true },
    series: { soilMoisture: [30, 31.2, 33.5, 34.1, 35.2, 36.0, 36.4], soilPH: [5.9, 5.9, 5.9, 5.9, 5.9, 5.9, 5.9], ndvi: [0.66, 0.65, 0.62, 0.6, 0.57, 0.54, 0.52], accumulatedGDD: [950, 966, 981, 996, 1011, 1026, 1040] },
    insight: 'Late-blight weather: humidity above 90% after heavy rain, and the canopy is losing greenness. Spray is recommended.',
  },
  {
    zoneId: 'B1', displayName: 'River Flats', grid: [0, 1],
    status: 'nominal', source: { soil: 'agrifusion_assessment', crop: 'farmwise_snapshot', model: 'synthetic' },
    lastUpdateTime: '2026-09-27T08:38:00Z',
    atmosphere: { ambientTemperature: 20.3, relativeHumidity: 64, precipitation: 1.2 },
    soil: { soilMoisture: 25.8, soilTemperature: 19.2, soilEC: 0.38, soilOrganicCarbon: 2.2, nitrogenLevel: 0.18, phosphorusLevel: 24, potassiumLevel: 0.72, aluminiumLevel: 0.35, soilTextureClass: 'sandy_loam' },
    soilPH: 6.4,
    crop: { ndvi: 0.47, evi: 0.39, cloudCover: 8, growthStage: 'maturation', daysAfterPlanting: 96, accumulatedGDD: 1410 },
    agronomy: { variety: 'Tigoni', plantingDate: '2026-06-23', areaHa: 2.2, substorTuberFreshYield: 34.6, substorLeafAreaIndex: 1.6, simcastBlightRisk: 'none', simcastSprayRecommended: false },
    series: { soilMoisture: [27, 26.5, 26.8, 26.1, 25.9, 26.0, 25.8], soilPH: [6.4, 6.4, 6.4, 6.4, 6.4, 6.4, 6.4], ndvi: [0.61, 0.58, 0.56, 0.53, 0.51, 0.49, 0.47], accumulatedGDD: [1310, 1327, 1344, 1361, 1377, 1394, 1410] },
    insight: 'Crop is maturing on schedule. Falling NDVI is normal senescence. Plan harvest in about 2 weeks.',
  },
  {
    zoneId: 'B2', displayName: 'South Slope', grid: [1, 1],
    status: 'warning', source: { soil: 'agrifusion_assessment', crop: 'farmwise_snapshot', model: 'synthetic' },
    lastUpdateTime: '2026-09-27T08:41:00Z',
    atmosphere: { ambientTemperature: 23.6, relativeHumidity: 49, precipitation: 0 },
    soil: { soilMoisture: 13.2, soilTemperature: 23.1, soilEC: 0.66, soilOrganicCarbon: 1.3, nitrogenLevel: 0.16, phosphorusLevel: 15, potassiumLevel: 0.47, aluminiumLevel: 0.6, soilTextureClass: 'sandy_loam' },
    soilPH: 6.3,
    crop: { ndvi: 0.55, evi: 0.45, cloudCover: 3, growthStage: 'tuber_initiation', daysAfterPlanting: 41, accumulatedGDD: 610 },
    agronomy: { variety: 'Asante', plantingDate: '2026-08-17', areaHa: 1.5, substorTuberFreshYield: 17.4, substorLeafAreaIndex: 2.1, simcastBlightRisk: 'none', simcastSprayRecommended: false },
    series: { soilMoisture: [21, 19.4, 17.9, 16.5, 15.2, 14.1, 13.2], soilPH: [6.3, 6.3, 6.3, 6.3, 6.3, 6.3, 6.3], ndvi: [0.62, 0.61, 0.6, 0.58, 0.57, 0.56, 0.55], accumulatedGDD: [520, 535, 550, 565, 580, 595, 610] },
    insight: 'Dry spell: soil moisture fell from 21% to 13% in a week during tuber initiation. Irrigate now.',
  },
  {
    zoneId: 'B3', displayName: 'Seedbed West', grid: [2, 1],
    status: 'offline', source: { soil: 'agrifusion_assessment', crop: 'farmwise_snapshot', model: 'synthetic' },
    lastUpdateTime: '2026-09-24T06:10:00Z',
    atmosphere: { ambientTemperature: 18.2, relativeHumidity: 70, precipitation: 3.0 },
    soil: { soilMoisture: 29.0, soilTemperature: 16.5, soilEC: 0.33, soilOrganicCarbon: 2.4, nitrogenLevel: 0.2, phosphorusLevel: 19, potassiumLevel: 0.58, aluminiumLevel: 0.45, soilTextureClass: 'loam' },
    soilPH: 6.0,
    crop: { ndvi: 0.41, evi: 0.34, cloudCover: 22, growthStage: 'emergence', daysAfterPlanting: 18, accumulatedGDD: 190 },
    agronomy: { variety: 'Shangi', plantingDate: '2026-09-09', areaHa: 1.1, substorTuberFreshYield: 28.0, substorLeafAreaIndex: 1.2, simcastBlightRisk: 'low', simcastSprayRecommended: false },
    series: { soilMoisture: [30, 29.8, 29.4, 29.0, 29.0, 29.0, 29.0], soilPH: [6.0, 6.0, 6.0, 6.0, 6.0, 6.0, 6.0], ndvi: [0.3, 0.33, 0.36, 0.39, 0.41, 0.41, 0.41], accumulatedGDD: [120, 138, 155, 172, 190, 190, 190] },
    insight: 'Soil probe offline for 3 days, so these readings are stale. Check the probe battery before trusting them.',
  },
]

export const STAGES = {
  unplanted: 'Unplanted', emergence: 'Emergence', tuber_initiation: 'Tuber initiation',
  tuber_bulking: 'Tuber bulking', maturation: 'Maturation', harvested: 'Harvested',
}
export const STAGE_ORDER = ['emergence', 'tuber_initiation', 'tuber_bulking', 'maturation', 'harvested']

export const TEXTURE = { sandy_loam: 'Sandy loam', loam: 'Loam', clay_loam: 'Clay loam' }

export const SOURCE_LABEL = {
  agrifusion_assessment: 'soil assessment schema',
  farmwise_snapshot: 'crop snapshot schema',
  synthetic: 'model stub (Phase 2)',
}

// Metric metadata: label, unit, schema attribute and a one-line meaning.
export const METRICS = {
  soilMoisture: { label: 'Soil moisture', unit: '% VWC', attr: 'farmSensor:soilMoisture', digits: 1 },
  soilTemperature: { label: 'Soil temperature', unit: '°C', attr: 'farmSensor:soilTemperature', digits: 1 },
  soilEC: { label: 'Electrical conductivity', unit: 'dS/m', attr: 'farmSensor:soilEC', digits: 2 },
  soilOrganicCarbon: { label: 'Organic carbon', unit: '%', attr: 'farmSensor:soilOrganicCarbon', digits: 1 },
  nitrogenLevel: { label: 'Nitrogen (N)', unit: '%', attr: 'farmSensor:nitrogenLevel', digits: 2 },
  phosphorusLevel: { label: 'Phosphorus (P)', unit: 'ppm', attr: 'farmSensor:phosphorusLevel', digits: 0 },
  potassiumLevel: { label: 'Potassium (K)', unit: 'cmol/kg', attr: 'farmSensor:potassiumLevel', digits: 2 },
  aluminiumLevel: { label: 'Aluminium', unit: 'cmol/kg', attr: 'farmSensor:aluminiumLevel', digits: 2 },
  soilPH: { label: 'Soil pH', unit: '', attr: 'farmSensor:soilPH', digits: 1 },
  ndvi: { label: 'NDVI', unit: '', attr: 'farmZone:ndvi', digits: 2 },
  evi: { label: 'EVI', unit: '', attr: 'farmZone:evi', digits: 2 },
  cloudCover: { label: 'Cloud cover', unit: '%', attr: 'farmZone:cloudCover', digits: 0 },
  daysAfterPlanting: { label: 'Days after planting', unit: 'days', attr: 'farmZone:daysAfterPlanting', digits: 0 },
  accumulatedGDD: { label: 'Growing degree days', unit: 'GDD', attr: 'farmZone:accumulatedGDD', digits: 0 },
  ambientTemperature: { label: 'Air temp', unit: '°C', attr: 'farmSensor:ambientTemperature', digits: 1 },
  relativeHumidity: { label: 'Humidity', unit: '%', attr: 'farmSensor:relativeHumidity', digits: 0 },
  precipitation: { label: 'Rain (24h)', unit: 'mm', attr: 'farmSensor:precipitation', digits: 1 },
  areaHa: { label: 'Area', unit: 'ha', attr: 'farmZone:areaHa', digits: 1 },
  substorTuberFreshYield: { label: 'Yield outlook', unit: 't/ha', attr: 'cropModel:substorTuberFreshYield', digits: 1 },
  substorLeafAreaIndex: { label: 'Leaf area index', unit: '', attr: 'cropModel:substorLeafAreaIndex', digits: 1 },
}

export const zoneById = (id) => ZONES.find((z) => z.zoneId === id)
