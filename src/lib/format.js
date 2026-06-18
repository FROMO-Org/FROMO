export const kmToMi = (km) => (km == null ? null : km * 0.621371);

export function formatDistance(km) {
  const mi = kmToMi(km);
  if (mi == null) return null;
  return `${mi < 0.1 ? "0.1" : mi.toFixed(1)} mi`;
}

export function formatTime(iso) {
  if (!iso) return null;
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return null;
  const day = d.toLocaleDateString(undefined, { weekday: "short" });
  const time = d.toLocaleTimeString(undefined, {
    hour: "numeric",
    minute: "2-digit",
  });
  return `${day} · ${time}`;
}

export function formatPrice(cents) {
  if (cents == null) return null;
  if (cents === 0) return "Free";
  return `$${(cents / 100).toFixed(2).replace(/\.00$/, "")}`;
}
