import { useState } from "react";
import { createVenue } from "../../lib/api";
import { DEFAULT_CENTER } from "../../lib/config";

const CATEGORIES = ["Music", "Food", "Art", "Sport", "Comedy", "Wellness", "Networking", "Other"];

export default function CreateVenueModal({ orgId, onClose, onCreated }) {
  const [form, setForm] = useState({
    name: "",
    address: "",
    category: "",
    lat: DEFAULT_CENTER.lat,
    lng: DEFAULT_CENTER.lng,
    is_accessible: false,
  });
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);

  function set(key, val) {
    setForm((f) => ({ ...f, [key]: val }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);

    if (!form.name.trim()) { setError("Venue name is required."); return; }
    const lat = parseFloat(form.lat);
    const lng = parseFloat(form.lng);
    if (Number.isNaN(lat) || Number.isNaN(lng)) { setError("Latitude and longitude must be numbers."); return; }

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

          <Field label="Address">
            <input
              value={form.address}
              onChange={(e) => set("address", e.target.value)}
              placeholder="Street address (optional)"
              style={inputStyle}
            />
          </Field>

          <Row>
            <Field label="Latitude *">
              <input
                required
                type="number"
                step="any"
                value={form.lat}
                onChange={(e) => set("lat", e.target.value)}
                style={inputStyle}
              />
            </Field>
            <Field label="Longitude *">
              <input
                required
                type="number"
                step="any"
                value={form.lng}
                onChange={(e) => set("lng", e.target.value)}
                style={inputStyle}
              />
            </Field>
          </Row>

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
