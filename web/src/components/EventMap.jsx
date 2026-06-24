import { useEffect } from "react";
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

const AMBER = "#F5A623";
const OK = "#2E9E6B";
const DANGER = "#E5533C";

const LEVEL_COLORS = {
  low: OK,
  medium: AMBER,
  high: DANGER,
};

function pinIcon(accessible) {
  const color = accessible ? OK : AMBER;
  return L.divIcon({
    className: "",
    iconSize: [16, 16],
    iconAnchor: [8, 8],
    html: `<div class="fromo-pin"><div class="dot" style="background:${color}"></div></div>`,
  });
}

function FlyTo({ focus }) {
  const map = useMap();
  useEffect(() => {
    if (focus) map.flyTo([focus.lat, focus.lng], 15, { duration: 0.6 });
  }, [focus, map]);
  return null;
}

function BusynessLegend() {
  const map = useMap();
  useEffect(() => {
    const legend = L.control({ position: "bottomleft" });
    legend.onAdd = () => {
      const div = L.DomUtil.create("div");
      div.style.cssText = [
        "background: #fff",
        "border: 1px solid #EAE4D9",
        "border-radius: 10px",
        "padding: 7px 13px",
        "font-size: 11px",
        "font-weight: 700",
        "font-family: 'Inter', system-ui, sans-serif",
        "letter-spacing: 0.06em",
        "text-transform: uppercase",
        "display: flex",
        "align-items: center",
        "gap: 10px",
        "pointer-events: none",
        "box-shadow: 0 1px 6px rgba(20,17,14,0.08)",
      ].join(";");

      const dot = (color) =>
        `<span style="width:8px;height:8px;border-radius:50%;background:${color};display:inline-block;margin-right:4px;"></span>`;

      div.innerHTML = [
        `<span>Busyness:</span>`,
        `<span>${dot(OK)}Low</span>`,
        `<span>${dot(AMBER)}Medium</span>`,
        `<span>${dot(DANGER)}High</span>`,
      ].join("");

      return div;
    };
    legend.addTo(map);
    return () => legend.remove();
  }, [map]);
  return null;
}

export default function EventMap({ events, busynessAreas = [], focus, route, onSelect }) {
  return (
    <MapContainer
      center={[DEFAULT_CENTER.lat, DEFAULT_CENTER.lng]}
      zoom={13}
      scrollWheelZoom={true}
      zoomControl={false}
      className="h-full w-full"
    >
      <TileLayer
        url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>'
        subdomains="abcd"
        maxZoom={20}
      />

      {/* Busyness zone circles — drawn below event markers */}
      {busynessAreas.map(({ area, score }) => {
        const color = score ? (LEVEL_COLORS[score.level] ?? AMBER) : "#BBBBBB";
        const r = area.radius_metres > 0 ? area.radius_metres : 200;
        return (
          <Circle
            key={area.id}
            center={[area.lat, area.lng]}
            radius={r}
            pathOptions={{
              color,
              fillColor: color,
              fillOpacity: score ? 0.22 : 0.1,
              weight: 1.5,
              opacity: score ? 0.6 : 0.3,
            }}
          />
        );
      })}

      {events.map((e) => {
        const v = e.venue || {};
        if (v.lat == null || v.lng == null) return null;
        return (
          <Marker
            key={e.id}
            position={[v.lat, v.lng]}
            icon={pinIcon(v.is_accessible)}
            eventHandlers={{ click: () => onSelect(e.id) }}
          >
            <Popup>
              <div className="font-display text-[15px] font-semibold">
                {e.title}
              </div>
              <div className="text-xs text-muted">
                {v.name}
                {v.is_accessible ? " · ♿ Step-free" : ""}
              </div>
            </Popup>
          </Marker>
        );
      })}

      {route && (
        <GeoJSON
          key={JSON.stringify(route).slice(0, 64)}
          data={route}
          style={{ color: "#14110E", weight: 4, opacity: 0.8 }}
        />
      )}

      <BusynessLegend />
      <FlyTo focus={focus} />
    </MapContainer>
  );
}
