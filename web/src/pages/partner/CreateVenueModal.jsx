import { useState } from "react";
import { createVenue } from "../../lib/api";
import { geocodeAddress } from "../../lib/directions";

const CATEGORIES = ["Music", "Food", "Art", "Sport", "Comedy", "Wellness", "Networking", "Other"];

export default function CreateVenueModal({ orgId, onClose, onCreated }) {
  const [form, setForm] = useState({
    name: "",
    address: "",
    category: "",
    lat: "",
    lng: "",
    is_accessible: false,
  });
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);

  const [geocoding, setGeocoding] = useState(false);
  const [geocodeError, setGeocodeError] = useState(null);
  const [resolvedLabel, setResolvedLabel] = useState(null);
  const [manualMode, setManualMode] = useState(false);

  function set(key, val) {
    setForm((f) => ({ ...f, [key]: val }));
  }

  function handleAddressChange(val) {
    set("address", val);
    setResolvedLabel(null);
    setGeocodeError(null);
    if (!manualMode) { set("lat", ""); set("lng", ""); }
  }

  async function handleFindLocation() {
    if (!form.address.trim()) { setGeocodeError("Enter an address first."); return; }
    setGeocoding(true);
    setGeocodeError(null);
    try {
      const { lat, lng, label } = await geocodeAddress(form.address.trim());
      set("lat", lat);
      set("lng", lng);
      setResolvedLabel(label);
    } catch {
      setGeocodeError("Couldn't find that address — try refining it, or enter coordinates manually.");
    } finally {
      setGeocoding(false);
    }
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);

    if (!form.name.trim()) { setError("Venue name is required."); return; }
    const lat = parseFloat(form.lat);
    const lng = parseFloat(form.lng);
    if (Number.isNaN(lat) || Number.isNaN(lng)) { setError("Find a location for the address first (or enter coordinates manually)."); return; }

    setSaving(true);
    try {
      const venue = await createVenue({
        organisation_id: orgId,
        name: form.name.trim(),
        address: form.address.trim() || null,
        lat,
        lng,
        category: form.category || null,
        is_accessible: form.is_accessible,
      });
      onCreated(venue);
    } catch (err) {
      const msg = err?.response?.data?.detail ?? err?.message ?? "Something went wrong.";
      setError(typeof msg === "string" ? msg : JSON.stringify(msg));
    } finally {
      setSaving(false);
    }
  }

  return (
    <div
      onClick={(e) => e.target === e.currentTarget && onClose()}
      style={{
        position: "fixed", inset: 0, zIndex: 9100,
        background: "rgba(0,0,0,0.45)", display: "flex",
        alignItems: "center", justifyContent: "center", padding: 24,
      }}
    >
      <div
        style={{
          background: "var(--color-paper)", borderRadius: 14, width: "100%", maxWidth: 480,
          maxHeight: "90vh", overflowY: "auto",
          boxShadow: "0 24px 64px rgba(0,0,0,0.18)",
        }}
      >
        <div style={{ padding: "28px 32px 0", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <h2 style={{ margin: 0, fontSize: 22, fontWeight: 800, fontFamily: '"Bricolage Grotesque", Inter, system-ui', letterSpacing: "-0.02em", color: "var(--color-ink)" }}>
            New Venue
          </h2>
          <button
            onClick={onClose}
            style={{ background: "none", border: "none", cursor: "pointer", fontSize: 22, color: "var(--color-muted)", lineHeight: 1, padding: 4 }}
            aria-label="Close"
          >
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit} style={{ padding: "24px 32px 32px" }}>
          <Field label="Name *">
            <input
              required
              value={form.name}
              onChange={(e) => set("name", e.target.value)}
              placeholder="e.g. Blue Note Jazz Club"
              style={inputStyle}
            />
          </Field>

          <Field label="Address *">
            <div style={{ display: "flex", gap: 8 }}>
              <input
                value={form.address}
                onChange={(e) => handleAddressChange(e.target.value)}
                placeholder="e.g. 131 W 3rd St, New York, NY"
                style={inputStyle}
              />
              <button
                type="button"
                onClick={handleFindLocation}
                disabled={geocoding}
                style={{
                  flexShrink: 0, background: geocoding ? "#888" : "#F5A623", color: "#231a09",
                  border: "none", borderRadius: 8, padding: "0 16px", fontSize: 13, fontWeight: 700,
                  cursor: geocoding ? "wait" : "pointer",
                }}
              >
                {geocoding ? "Finding…" : "Find"}
              </button>
            </div>

            {resolvedLabel && (
              <div style={{ fontSize: 12.5, color: "#2E9E6B", marginTop: 6 }}>
                📍 Found: {resolvedLabel}
              </div>
            )}
            {geocodeError && (
              <div style={{ fontSize: 12.5, color: "#E53935", marginTop: 6 }}>
                {geocodeError}
              </div>
            )}

            <button
              type="button"
              onClick={() => setManualMode((v) => !v)}
              style={{ background: "none", border: "none", padding: 0, marginTop: 8, fontSize: 12.5, fontWeight: 600, color: "var(--color-muted)", cursor: "pointer", textDecoration: "underline" }}
            >
              {manualMode ? "Hide manual coordinates" : "Enter coordinates manually instead"}
            </button>

            {manualMode && (
              <Row>
                <Field label="Latitude">
                  <input
                    type="number"
                    step="any"
                    value={form.lat}
                    onChange={(e) => set("lat", e.target.value)}
                    style={inputStyle}
                  />
                </Field>
                <Field label="Longitude">
                  <input
                    type="number"
                    step="any"
                    value={form.lng}
                    onChange={(e) => set("lng", e.target.value)}
                    style={inputStyle}
                  />
                </Field>
              </Row>
            )}
          </Field>

          <Field label="Category">
            <select
              value={form.category}
              onChange={(e) => set("category", e.target.value)}
              style={inputStyle}
            >
              <option value="">— Select —</option>
              {CATEGORIES.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </Field>

          <label style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 18, fontSize: 13.5, color: "var(--color-ink)", cursor: "pointer" }}>
            <input
              type="checkbox"
              checked={form.is_accessible}
              onChange={(e) => set("is_accessible", e.target.checked)}
            />
            Wheelchair accessible
          </label>

          {error && (
            <div style={{ fontSize: 13, color: "#E53935", background: "#FFF0F0", border: "1px solid #FFCDD2", borderRadius: 8, padding: "10px 14px", marginBottom: 20 }}>
              {error}
            </div>
          )}

          <div style={{ display: "flex", gap: 12, justifyContent: "flex-end", marginTop: 8 }}>
            <button
              type="button"
              onClick={onClose}
              style={{ background: "none", border: "1px solid var(--color-line)", borderRadius: 8, padding: "11px 22px", fontSize: 13, fontWeight: 600, cursor: "pointer", color: "var(--color-muted)" }}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              style={{
                background: saving ? "#888" : "#111", color: "#fff", border: "none",
                borderRadius: 8, padding: "11px 26px", fontSize: 13, fontWeight: 600,
                cursor: saving ? "wait" : "pointer",
              }}
            >
              {saving ? "Creating…" : "Create Venue"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function Field({ label, children }) {
  return (
    <div style={{ marginBottom: 18 }}>
      <label style={{ display: "block", fontSize: 11, fontWeight: 700, letterSpacing: "0.07em", textTransform: "uppercase", color: "var(--color-muted)", marginBottom: 7 }}>
        {label}
      </label>
      {children}
    </div>
  );
}

function Row({ children }) {
  return (
    <div style={{ display: "flex", gap: 16 }}>
      {children}
    </div>
  );
}

const inputStyle = {
  width: "100%",
  border: "1px solid var(--color-line)",
  borderRadius: 8,
  padding: "10px 12px",
  fontSize: 14,
  color: "var(--color-ink)",
  background: "var(--color-surface)",
  outline: "none",
  boxSizing: "border-box",
  fontFamily: "Inter, system-ui, sans-serif",
};
