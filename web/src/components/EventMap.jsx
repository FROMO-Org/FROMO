import { useEffect, useMemo } from "react";
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  GeoJSON,
  Circle,
  useMap,
} from "react-leaflet";
import L from "leaflet";
import { DEFAULT_CENTER } from "../lib/config.js";
import { useTheme } from "../context/ThemeContext.jsx";

const AMBER = "#F5A623";
const OK = "#2E9E6B";

function venueIcon(accessible, count) {
  const color = accessible ? OK : AMBER;
  const size = count > 1 ? 28 : 16;
  const html = count > 1
    ? `<div style="
        width:${size}px;height:${size}px;border-radius:50%;
        background:${color};color:#231a09;
        font-size:11px;font-weight:800;font-family:monospace;
        display:flex;align-items:center;justify-content:center;
        box-shadow:0 2px 6px rgba(0,0,0,0.25);border:2px solid #fff;
      ">${count}</div>`
    : `<div class="fromo-pin"><div class="dot" style="background:${color}"></div></div>`;
  return L.divIcon({
    className: "",
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
    html,
  });
}

function FlyTo({ focus }) {
  const map = useMap();
  useEffect(() => {
    if (focus) map.flyTo([focus.lat, focus.lng], 15, { duration: 0.6 });
  }, [focus, map]);
  return null;
}

export default function EventMap({ events, busynessAreas = [], focus, route, onSelect }) {
  const { isDark } = useTheme();
  const tileUrl = isDark
    ? "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
    : "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png";

  // Group events by venue so stacked markers show a count badge
  const venueGroups = useMemo(() => {
    const map = {};
    events.forEach((e) => {
      const v = e.venue || {};
      if (v.lat == null || v.lng == null) return;
      const key = `${v.lat},${v.lng}`;
      if (!map[key]) map[key] = { venue: v, events: [] };
      map[key].events.push(e);
    });
    return Object.values(map);
  }, [events]);

  return (
    <MapContainer
      center={[DEFAULT_CENTER.lat, DEFAULT_CENTER.lng]}
      zoom={13}
      scrollWheelZoom={true}
      zoomControl={false}
      className="h-full w-full"
    >
      <TileLayer
        key={tileUrl}
        url={tileUrl}
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>'
        subdomains="abcd"
        maxZoom={20}
      />

      {busynessAreas.map((item, i) => {
        const a = item.area ?? item;
        if (a.lat == null || a.lng == null) return null;
        if (!item.score?.level) return null; // no prediction yet — don't draw
        const levelColor = { low: "#2E9E6B", medium: "#F5A623", high: "#E53935" };
        const color = levelColor[item.score.level] ?? "#F5A623";
        return (
          <Circle
            key={i}
            center={[Number(a.lat), Number(a.lng)]}
            radius={a.radius_metres ?? 400}
            pathOptions={{ color, fillColor: color, fillOpacity: 0.3, weight: 0 }}
          />
        );
      })}

      {venueGroups.map(({ venue: v, events: evs }) => (
        <Marker
          key={`${v.lat},${v.lng}`}
          position={[v.lat, v.lng]}
          icon={venueIcon(v.is_accessible, evs.length)}
        >
          <Popup>
            <div style={{ minWidth: 160, maxWidth: 220 }}>
              <div style={{ fontSize: 12, fontWeight: 700, color: "#888", marginBottom: 6, textTransform: "uppercase", letterSpacing: "0.06em" }}>
                {v.name}
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                {evs.map((e) => (
                  <div
                    key={e.id}
                    onClick={() => onSelect(e.id)}
                    style={{ cursor: "pointer", fontSize: 13, fontWeight: 600, color: "#14110E", padding: "4px 0", borderBottom: "1px solid #f0ebe3" }}
                  >
                    {e.title}
                  </div>
                ))}
              </div>
            </div>
          </Popup>
        </Marker>
      ))}

      {route && (
        <GeoJSON
          key={JSON.stringify(route).slice(0, 64)}
          data={route}
          style={{ color: "#14110E", weight: 4, opacity: 0.8 }}
        />
      )}

      <FlyTo focus={focus} />
    </MapContainer>
  );
}
