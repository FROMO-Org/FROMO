import { useEffect } from "react";
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  GeoJSON,
  CircleMarker,
  useMap,
} from "react-leaflet";
import L from "leaflet";
import { DEFAULT_CENTER } from "../lib/config.js";
import { useTheme } from "../context/ThemeContext.jsx";

const AMBER = "#F5A623";
const OK = "#2E9E6B";

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

export default function EventMap({ events, busynessAreas = [], focus, route, onSelect }) {
  const { isDark } = useTheme();
  const tileUrl = isDark
    ? "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
    : "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png";

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

      {busynessAreas.map((area, i) => {
        const level = area.level ?? area.busyness_score ?? 0.5;
        return (
          <CircleMarker
            key={i}
            center={[area.lat, area.lng]}
            radius={28}
            pathOptions={{
              color: "#F5A623",
              fillColor: "#F5A623",
              fillOpacity: level * 0.35,
              weight: 0,
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

      <FlyTo focus={focus} />
    </MapContainer>
  );
}
