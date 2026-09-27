// Offline advisor: keyword intents -> answers interpolated from the plot data.
// Used when no key is set, the API fails, or the venue wifi dies. Never blank.
import { ZONES, STAGES } from '../data/zones'
import { phBand, moistureBand, blightBand, STATUS_LABEL, ago } from './status'

const has = (q, ...w) => w.some((x) => q.includes(x))

function one(z, q) {
  const s = z.soil, c = z.crop, a = z.agronomy
  const stale = z.status === 'offline' ? `\n\nNote: this plot's probe has been offline since ${ago(z.lastUpdateTime)}, so treat these readings as stale.` : ''
  if (has(q, 'real', 'live', 'sensor', 'fake', 'synthetic'))
    return `Honest answer: every value on this farm is synthetic demo data on the real OpenUSD schema. There are no live sensors yet. Live IoT ingestion is Phase 2 of the roadmap.`
  if (has(q, 'ph', 'lime', 'acid', 'alkal'))
    return `Soil pH on ${z.displayName} is ${z.soilPH}. ${phBand(z.soilPH).text}. ${z.soilPH < 5.5 ? `Aluminium is ${s.aluminiumLevel} cmol/kg${s.aluminiumLevel > 1 ? ', which is toxic to roots' : ''}. Apply agricultural lime (about 1 to 2 t/ha, confirmed by a lab test) between seasons.` : 'No lime is needed.'}${stale}`
  if (has(q, 'irrigat', 'water', 'moisture', 'dry', 'rain'))
    return `Soil moisture is ${s.soilMoisture}% VWC, down from ${z.series.soilMoisture[0]}% a week ago. ${moistureBand(s.soilMoisture).text}. ${s.soilMoisture < 18 ? `The crop is in ${STAGES[c.growthStage].toLowerCase()}, when drought hurts yield most. Irrigate within the next day.` : s.soilMoisture > 34 ? `Do not irrigate. Rain was ${z.atmosphere.precipitation} mm in the last 24 h.` : 'No irrigation needed right now.'}${stale}`
  if (has(q, 'blight', 'spray', 'disease', 'fung', 'sick'))
    return `Blight risk is ${a.simcastBlightRisk}. ${blightBand(a.simcastBlightRisk).text}. Humidity is ${z.atmosphere.relativeHumidity}% and NDVI is ${c.ndvi}. ${a.simcastSprayRecommended ? 'Spray a protectant fungicide within 24 hours and scout the lower leaves for dark lesions.' : 'No spray needed now; keep scouting after wet spells.'}${stale}`
  if (has(q, 'harvest', 'ready', 'mature', 'when'))
    return `${z.displayName} is at ${STAGES[c.growthStage].toLowerCase()}, ${c.daysAfterPlanting} days after planting (${c.accumulatedGDD} GDD). ${c.growthStage === 'maturation' ? 'Harvest in about 2 weeks, once vines die back and skins set.' : `Harvest is still roughly ${Math.max(2, Math.round((100 - c.daysAfterPlanting) / 7))} weeks away for ${a.variety}.`} Yield outlook is ${a.substorTuberFreshYield} t/ha (model stub).${stale}`
  if (has(q, 'fertil', 'npk', 'nitrogen', 'phosph', 'potass', 'apply', 'feed'))
    return `N is ${s.nitrogenLevel}%, P is ${s.phosphorusLevel} ppm, K is ${s.potassiumLevel} cmol/kg, organic carbon ${s.soilOrganicCarbon}%. ${[s.nitrogenLevel < 0.15 && 'Top-dress nitrogen.', s.phosphorusLevel < 12 && 'Phosphorus is low; use DAP at next planting.', s.potassiumLevel < 0.35 && 'Potassium is low; apply potash.', z.soilPH < 5.5 && 'Lime first, since acidity locks up P.'].filter(Boolean).join(' ') || 'Nutrients are adequate; no extra fertiliser this week.'}${stale}`
  if (has(q, 'ndvi', 'green', 'canopy', 'health'))
    return `NDVI is ${c.ndvi} (EVI ${c.evi}), trending ${z.series.ndvi[0]} to ${c.ndvi} this week. ${c.growthStage === 'maturation' ? 'That drop is normal senescence.' : c.ndvi < 0.55 ? 'The canopy is weak; check water, nutrients and disease.' : 'The canopy is vigorous.'}${stale}`
  return `${z.displayName} (${z.zoneId}) is ${STATUS_LABEL[z.status].toLowerCase()}. ${z.insight} Key numbers: pH ${z.soilPH}, moisture ${s.soilMoisture}%, NDVI ${c.ndvi}, ${STAGES[c.growthStage].toLowerCase()} at day ${c.daysAfterPlanting}.${stale}`
}

export function offlineAnswer(question, zone) {
  const q = question.toLowerCase()
  if (zone) return one(zone, q)
  const worst = ZONES.filter((z) => z.status !== 'nominal')
  if (has(q, 'real', 'live', 'sensor', 'fake', 'synthetic')) return one(ZONES[0], q)
  return `Farm overview: ${ZONES.length} plots. ${worst.map((z) => `${z.zoneId} ${z.displayName} is ${STATUS_LABEL[z.status].toLowerCase()}: ${z.insight}`).join(' ')} The other plots are healthy. Click a plot to ask about it directly.`
}
