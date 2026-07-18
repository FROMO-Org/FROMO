import { useEffect, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
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

const LEVEL_COLOR = { "not busy": "#2E9E6B", "as usual": "#F5A623", "busier": "#E53935" };

function venueIcon(busynessLevel, count) {
  const color = LEVEL_COLOR[busynessLevel] ?? "#F5A623";

  const w = 32, h = 46;
  const innerContent = count > 1
    ? `<text x="20" y="20" text-anchor="middle" dominant-baseline="central"
        font-size="12" font-weight="900" font-family="monospace" fill="${color}">${count}</text>`
    : "";

  const svg = `<div style="filter:drop-shadow(0 3px 4px rgba(0,0,0,0.4));">
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 56" width="${w}" height="${h}">
      <path d="M20 0C9 0 0 9 0 20c0 13 20 36 20 36S40 33 40 20C40 9 31 0 20 0z" fill="${color}" stroke="white" stroke-width="2.5"/>
      <circle cx="20" cy="19" r="10" fill="white"/>
      ${innerContent}
    </svg>
  </div>`;

  return L.divIcon({
    className: "",
    iconSize: [w, h],
    iconAnchor: [w / 2, h],
    popupAnchor: [0, -h],
    html: svg,
  });
}

function FlyTo({ focus }) {
  const map = useMap();
  useEffect(() => {
    if (focus) map.flyTo([focus.lat, focus.lng], 15, { duration: 0.6 });
  }, [focus, map]);
  return null;
}

function userLocationIcon() {
  const svg = `<div style="filter:drop-shadow(0 2px 5px rgba(0,0,0,0.45));">
    <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 22 22">
      <circle cx="11" cy="11" r="9" fill="#1D4ED8" fill-opacity="0.25"/>
      <circle cx="11" cy="11" r="6" fill="#1D4ED8" stroke="white" stroke-width="2.5"/>
    </svg>
  </div>`;

  return L.divIcon({
    className: "",
    iconSize: [22, 22],
    iconAnchor: [11, 11],
    popupAnchor: [0, -11],
    html: svg,
  });
}

export default function EventMap({ events, busynessAreas = [], getNearestBusynessLevel, focus, route, onSelect, userLocation }) {
  const navigate = useNavigate();
  const { user } = useAuth();
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
        if (!item.score?.level) return null;
        const levelColor = { "not busy": "#2E9E6B", "as usual": "#F5A623", "busier": "#E53935" };
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
          icon={venueIcon(getNearestBusynessLevel?.(v.lat, v.lng), evs.length)}
        >
          <Popup>
            <div style={{ minWidth: 170, maxWidth: 240 }}>
              <div style={{ fontSize: 11, fontWeight: 700, color: "#555", marginBottom: 8, textTransform: "uppercase", letterSpacing: "0.07em" }}>
                {v.name}
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                {evs.map((e) => (
                  <div
                    key={e.id}
                    onClick={() => user ? navigate(`/events/${e.id}`, { state: { event: e } }) : navigate("/login")}
                    style={{ cursor: "pointer", fontSize: 14, fontWeight: 700, color: "#000", padding: "5px 0", borderBottom: "1px solid #eee", lineHeight: 1.3 }}
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

      {userLocation && (
        <Marker position={[userLocation.lat, userLocation.lng]} icon={userLocationIcon()} zIndexOffset={1000}>
          <Popup>You are here</Popup>
        </Marker>
      )}

      <FlyTo focus={focus} />
    </MapContainer>
  );
}
