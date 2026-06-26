import React, { useEffect } from "react";
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

const TILE_LIGHT = "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png";
const TILE_DARK  = "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png";

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

function BusynessLegend({ isDark }) {
  const map = useMap();
  useEffect(() => {
    const legend = L.control({ position: "bottomleft" });
    legend.onAdd = () => {
      const div = L.DomUtil.create("div");
      div.style.cssText = [
        `background: ${isDark ? "#262220" : "#fff"}`,
        `border: 1px solid ${isDark ? "#3A3430" : "#EAE4D9"}`,
        `color: ${isDark ? "#F0EAE2" : "#14110E"}`,
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
        "box-shadow: 0 1px 6px rgba(0,0,0,0.2)",
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
  }, [map, isDark]);
  return null;
}

export default function EventMap({ events, busynessAreas = [], focus, route, onSelect }) {
  const { isDark } = useTheme();
  return (
    <MapContainer
      center={[DEFAULT_CENTER.lat, DEFAULT_CENTER.lng]}
      zoom={13}
      scrollWheelZoom={true}
      zoomControl={false}
      className="h-full w-full"
    >
      <TileLayer
        key={isDark ? "dark" : "light"}
        url={isDark ? TILE_DARK : TILE_LIGHT}
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>'
        subdomains="abcd"
        maxZoom={20}
      />

      {/* Busyness heatmap — three concentric fading circles per area to create a radial gradient effect */}
      {busynessAreas.map(({ area, score }) => {
        if (!score) return null;
        const color = LEVEL_COLORS[score.level] ?? AMBER;
        const r = Math.max(area.radius_metres > 0 ? area.radius_metres : 0, 450);
        const base = { stroke: false, fillColor: color };
        return (
          <React.Fragment key={area.id}>
            <Circle center={[area.lat, area.lng]} radius={r}        pathOptions={{ ...base, fillOpacity: 0.08 }} />
            <Circle center={[area.lat, area.lng]} radius={r * 0.55} pathOptions={{ ...base, fillOpacity: 0.20 }} />
            <Circle center={[area.lat, area.lng]} radius={r * 0.25} pathOptions={{ ...base, fillOpacity: 0.50 }} />
          </React.Fragment>
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
          style={{ color: isDark ? "#F0EAE2" : "#14110E", weight: 4, opacity: 0.8 }}
        />
      )}

      <BusynessLegend isDark={isDark} />
      <FlyTo focus={focus} />
    </MapContainer>
  );
}
