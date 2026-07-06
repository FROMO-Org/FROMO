import { TICKETMASTER_KEY, UNSPLASH_KEY } from "./config";

const TM_BASE = "https://app.ticketmaster.com/discovery/v2";
const SESSION_PREFIX = "fromo_tm_img::";

function readCache(key) {
  try {
    const val = sessionStorage.getItem(SESSION_PREFIX + key);
    return val !== null ? val : undefined;
  } catch { return undefined; }
}

function writeCache(key, url) {
  try { sessionStorage.setItem(SESSION_PREFIX + key, url ?? ""); } catch {}
}

function pickBestImage(images = []) {
  if (!images.length) return null;
  const sixteenNine = images.filter((img) => img.ratio === "16_9");
  const pool = sixteenNine.length ? sixteenNine : images;
  return pool.sort((a, b) => b.width - a.width)[0]?.url ?? null;
}

async function fetchFromTicketmaster(title) {
  if (!TICKETMASTER_KEY) return null;

  const cached = readCache(title);
  if (cached !== undefined) return cached || null;

  try {
    const res = await fetch(
      `${TM_BASE}/events.json?apikey=${TICKETMASTER_KEY}&keyword=${encodeURIComponent(title)}&size=5`
    );
    if (!res.ok) throw new Error(res.status);
    const data = await res.json();
    const events = data._embedded?.events ?? [];
    let url = null;
    for (const ev of events) {
      url = pickBestImage(ev.images);
      if (url) break;
    }
    writeCache(title, url);
    return url;
  } catch {
    writeCache(title, null);
    return null;
  }
}

async function fetchFromUnsplash(category) {
  if (!UNSPLASH_KEY) return null;

  const cached = readCache(`us::${category}`);
  if (cached !== undefined) return cached || null;

  try {
    const res = await fetch(
      `https://api.unsplash.com/search/photos?query=${encodeURIComponent(category)}&per_page=3&orientation=landscape&client_id=${UNSPLASH_KEY}`
    );
    if (!res.ok) throw new Error(res.status);
    const data = await res.json();
    const url = data.results?.[0]?.urls?.regular ?? null;
    writeCache(`us::${category}`, url);
    return url;
  } catch {
    writeCache(`us::${category}`, null);
    return null;
  }
}

// 1. Try Ticketmaster by event title (specific match)
// 2. Fall back to Unsplash by category (generic but always relevant)
export async function fetchEventImage(title, category) {
  const tmUrl = await fetchFromTicketmaster(title);
  if (tmUrl) return tmUrl;
  if (category) return fetchFromUnsplash(category);
  return null;
}
