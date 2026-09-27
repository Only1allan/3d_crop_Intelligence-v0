// Small client-side RAG: ~40 chunks, BM25 keyword scoring, no embeddings.
// Contract: the SELECTED plot's full card is always in context.
import { ZONES, STAGES, TEXTURE, SOURCE_LABEL, FARM } from '../data/zones'
import { FARM_FACTS } from '../data/farmFacts'
import { phBand, moistureBand, blightBand, STATUS_LABEL, ago } from './status'

export function zoneCard(z) {
  const s = z.soil, c = z.crop, a = z.agronomy, at = z.atmosphere
  return [
    `PLOT ${z.zoneId} "${z.displayName}". Status: ${z.status} (${STATUS_LABEL[z.status]}). Last update ${ago(z.lastUpdateTime)}.`,
    `Summary: ${z.insight}`,
    `Weather now: air ${at.ambientTemperature} °C, humidity ${at.relativeHumidity}%, rain last 24h ${at.precipitation} mm.`,
    `Soil (${SOURCE_LABEL[z.source.soil]}): moisture ${s.soilMoisture}% VWC (${moistureBand(s.soilMoisture).text}), soil temperature ${s.soilTemperature} °C, EC ${s.soilEC} dS/m, organic carbon ${s.soilOrganicCarbon}%, nitrogen ${s.nitrogenLevel}%, phosphorus ${s.phosphorusLevel} ppm, potassium ${s.potassiumLevel} cmol/kg, aluminium ${s.aluminiumLevel} cmol/kg, texture ${TEXTURE[s.soilTextureClass]}.`,
    `pH: ${z.soilPH} (${phBand(z.soilPH).text}).`,
    `Crop (${SOURCE_LABEL[z.source.crop]}): NDVI ${c.ndvi}, EVI ${c.evi}, cloud cover ${c.cloudCover}%, growth stage ${STAGES[c.growthStage]}, ${c.daysAfterPlanting} days after planting, ${c.accumulatedGDD} GDD accumulated.`,
    `Agronomy (${SOURCE_LABEL[z.source.model]}): variety ${a.variety}, planted ${a.plantingDate}, area ${a.areaHa} ha, yield outlook ${a.substorTuberFreshYield} t/ha, leaf area index ${a.substorLeafAreaIndex}, blight risk ${a.simcastBlightRisk} (${blightBand(a.simcastBlightRisk).text}), spray recommended: ${a.simcastSprayRecommended ? 'yes' : 'no'}.`,
    `7-day trend: soil moisture ${z.series.soilMoisture.join(' → ')}%; NDVI ${z.series.ndvi.join(' → ')}.`,
  ].join('\n')
}

function farmOverview() {
  return `FARM OVERVIEW: ${FARM.name}, ${FARM.region}, crop ${FARM.crop}, ${ZONES.length} plots, ${FARM.totalHa} ha. ` +
    ZONES.map((z) => `${z.zoneId} ${z.displayName}: ${z.status}, pH ${z.soilPH}, moisture ${z.soil.soilMoisture}%, NDVI ${z.crop.ndvi}, blight ${z.agronomy.simcastBlightRisk}`).join('; ') + '.'
}

// ----- corpus --------------------------------------------------------------
const CHUNKS = [
  { id: 'farm', title: 'Farm overview', text: farmOverview() },
  ...ZONES.map((z) => ({ id: `zone-${z.zoneId}`, zoneId: z.zoneId, title: `Plot ${z.zoneId} · ${z.displayName}`, text: zoneCard(z) })),
  ...FARM_FACTS,
]

const STOP = new Set('a an the is are was were be to of and or in on at for with this that it its my our i we you do does can should what how when why which there their any me plot please tell about'.split(' '))
const tok = (s) => s.toLowerCase().replace(/[^a-z0-9.\s]/g, ' ').split(/\s+/).filter((w) => w && !STOP.has(w))
  .map((w) => w.replace(/(ing|ed|es|s)$/, ''))

// Synonyms so farmer language hits the technical chunks.
const SYN = {
  water: 'moisture irrigat', irrigat: 'moisture', dry: 'moisture irrigat', rain: 'precipitation moisture',
  acid: 'ph lime', lime: 'ph acid', sour: 'ph acid', green: 'ndvi canopy', health: 'ndvi status', sick: 'blight disease',
  disease: 'blight', fungu: 'blight spray', spray: 'blight fungicide', harvest: 'maturation stage', ready: 'harvest maturation',
  fertili: 'nitrogen phosphorus potassium npk', feed: 'nitrogen phosphorus potassium', yield: 'yield outlook tonne',
  heat: 'gdd', weather: 'humidity temperature rain', sensor: 'offline status', real: 'synthetic honesty live',
}
function expand(tokens) {
  const out = [...tokens]
  for (const t of tokens) for (const k in SYN) if (t.startsWith(k)) out.push(...tok(SYN[k]))
  return out
}

const DOCS = CHUNKS.map((c) => ({ ...c, toks: tok(c.title + ' ' + c.text) }))
const N = DOCS.length
const avgdl = DOCS.reduce((s, d) => s + d.toks.length, 0) / N
const df = {}
DOCS.forEach((d) => new Set(d.toks).forEach((t) => (df[t] = (df[t] || 0) + 1)))

function bm25(qToks, d, k1 = 1.4, b = 0.75) {
  let score = 0
  const tf = {}
  d.toks.forEach((t) => (tf[t] = (tf[t] || 0) + 1))
  for (const q of new Set(qToks)) {
    if (!tf[q]) continue
    const idf = Math.log(1 + (N - df[q] + 0.5) / (df[q] + 0.5))
    score += idf * (tf[q] * (k1 + 1)) / (tf[q] + k1 * (1 - b + b * d.toks.length / avgdl))
  }
  return score
}

export function retrieve(question, selectedZoneId, k = 4) {
  const q = expand(tok(question))
  // A named plot ("A2", "hillside") pulls that plot's card in too.
  const named = ZONES.filter((z) => new RegExp(`\\b${z.zoneId}\\b`, 'i').test(question) ||
    question.toLowerCase().includes(z.displayName.toLowerCase().split(' ')[0].toLowerCase()))
  const forced = new Set([selectedZoneId ? `zone-${selectedZoneId}` : 'farm', ...named.map((z) => `zone-${z.zoneId}`)])
  const scored = DOCS.filter((d) => !forced.has(d.id))
    .map((d) => ({ d, s: bm25(q, d) }))
    .filter((x) => x.s > 0.4)
    .sort((a, b) => b.s - a.s)
    .slice(0, k)
    .map((x) => x.d)
  const forcedDocs = DOCS.filter((d) => forced.has(d.id))
  if (selectedZoneId && !scored.find((d) => d.id === 'farm') && /farm|all|every|other|compare|which|worst|best/i.test(question)) {
    scored.unshift(DOCS.find((d) => d.id === 'farm'))
  }
  return [...forcedDocs, ...scored]
}

export function systemPrompt(zone) {
  return `You are the AI field advisor inside "Omniverse Crop Intelligence", a 3D digital twin of a potato farm. The farmer is talking to ${zone ? `plot ${zone.zoneId} "${zone.displayName}"` : 'the whole farm'}.
Rules:
- Answer ONLY from the CONTEXT below. Quote the plot's numbers with units.
- Be practical and farmer-friendly: say what to do and why, in at most 110 words. Plain sentences, no tables, no markdown headers. Short bullet points are fine.
- If the context does not contain the answer, say so plainly. Never invent readings.
- The values are synthetic demo data on the real schema. Never claim live sensors or real-time IoT. If asked, say so honestly.
- If the plot is offline, warn that the readings are stale.`
}

export function buildMessages(history, question, zone) {
  const docs = retrieve(question, zone?.zoneId)
  const context = docs.map((d) => `### ${d.title}\n${d.text}`).join('\n\n')
  const msgs = [
    { role: 'system', content: systemPrompt(zone) + `\n\nCONTEXT:\n${context}` },
    ...history.slice(-6).map((m) => ({ role: m.role, content: m.content })),
    { role: 'user', content: question },
  ]
  return { msgs, docs }
}
