import { useEffect, useState } from "react";
import { createEvent, listVenues } from "../../lib/api";
import CreateVenueModal from "./CreateVenueModal";

const CATEGORIES = ["Music", "Food", "Art", "Sport", "Comedy", "Wellness", "Networking", "Other"];

function toDatetimeLocal(iso) {
  if (!iso) return "";
  return new Date(iso).toISOString().slice(0, 16);
}

function toIso(datetimeLocal) {
  if (!datetimeLocal) return null;
  return new Date(datetimeLocal).toISOString();
}

export default function CreateListingModal({ orgId, onClose, onCreated }) {
  const [venues, setVenues] = useState([]);
  const [venuesLoading, setVenuesLoading] = useState(true);

  const [form, setForm] = useState({
    title: "",
    category: "",
    description: "",
    venue_id: "",
    starts_at: "",
    ends_at: "",
    price: "",
    original_price: "",
    capacity: "",
  });
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);
  const [showVenueModal, setShowVenueModal] = useState(false);

  function loadVenues() {
    setVenuesLoading(true);
    return listVenues({ organisation_id: orgId, limit: 100 })
      .then((v) => {
        setVenues(v);
        return v;
      })
      .catch(() => [])
      .finally(() => setVenuesLoading(false));
  }

  useEffect(() => {
    loadVenues().then((v) => {
      if (v.length === 1) setForm((f) => ({ ...f, venue_id: v[0].id }));
    });
  }, [orgId]);

  function handleVenueCreated(venue) {
    setShowVenueModal(false);
    loadVenues().then(() => {
      set("venue_id", venue.id);
    });
  }

  function set(key, val) {
    setForm((f) => ({ ...f, [key]: val }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);

    if (!form.venue_id) { setError("Please select a venue."); return; }
    if (!form.starts_at) { setError("Start date & time is required."); return; }

    const body = {
      title: form.title.trim(),
      host_organisation_id: orgId,
      venue_id: form.venue_id,
      starts_at: toIso(form.starts_at),
      ends_at: form.ends_at ? toIso(form.ends_at) : null,
      price_cents: form.price ? Math.round(parseFloat(form.price) * 100) : 0,
      original_price_cents: form.original_price
        ? Math.round(parseFloat(form.original_price) * 100)
        : null,
      capacity: form.capacity ? parseInt(form.capacity, 10) : null,
      description: form.description.trim() || null,
      category: form.category || null,
      status:"active",
    };

    setSaving(true);
    try {
      await createEvent(body);
      onCreated();
    } catch (err) {
      const msg = err?.response?.data?.detail ?? err?.message ?? "Something went wrong.";
      setError(typeof msg === "string" ? msg : JSON.stringify(msg));
    } finally {
      setSaving(false);
    }
  }

  return (
    /* Backdrop */
    <div
      onClick={(e) => e.target === e.currentTarget && onClose()}
      style={{
        position: "fixed", inset: 0, zIndex: 9000,
        background: "rgba(0,0,0,0.45)", display: "flex",
        alignItems: "center", justifyContent: "center", padding: 24,
      }}
    >
      {/* Panel */}
      <div
        style={{
          background: "var(--color-paper)", borderRadius: 14, width: "100%", maxWidth: 560,
          maxHeight: "90vh", overflowY: "auto",
          boxShadow: "0 24px 64px rgba(0,0,0,0.18)",
        }}
      >
        {/* Header */}
        <div style={{ padding: "28px 32px 0", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <h2 style={{ margin: 0, fontSize: 22, fontWeight: 800, fontFamily: '"Bricolage Grotesque", Inter, system-ui', letterSpacing: "-0.02em", color: "var(--color-ink)" }}>
            New Listing
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

          <Field label="Title *">
            <input
              required
              value={form.title}
              onChange={(e) => set("title", e.target.value)}
              placeholder="e.g. Jazz Night at Blue Note"
              style={inputStyle}
            />
          </Field>

          <Row>
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

            <Field label="Venue *">
              {venuesLoading ? (
                <div style={{ fontSize: 13, color: "#888", padding: "12px 0" }}>Loading venues…</div>
              ) : (
                <>
                  {venues.length === 0 ? (
                    <div style={{ fontSize: 13, color: "#E53935", marginBottom: 8 }}>
                      No venues found for this organisation.
                    </div>
                  ) : (
                    <select
                      value={form.venue_id}
                      onChange={(e) => set("venue_id", e.target.value)}
                      style={{ ...inputStyle, marginBottom: 8 }}
                    >
                      <option value="">— Select venue —</option>
                      {venues.map((v) => (
                        <option key={v.id} value={v.id}>{v.name}</option>
                      ))}
                    </select>
                  )}
                  <button
                    type="button"
                    onClick={() => setShowVenueModal(true)}
                    style={{ background: "none", border: "none", padding: 0, fontSize: 13, fontWeight: 600, color: "#F5A623", cursor: "pointer" }}
                  >
                    + Add a venue
                  </button>
                </>
              )}
            </Field>
          </Row>

          <Field label="Description">
            <textarea
              value={form.description}
              onChange={(e) => set("description", e.target.value)}
              placeholder="What's happening? (optional)"
              rows={3}
              style={{ ...inputStyle, resize: "vertical" }}
            />
          </Field>

          <Row>
            <Field label="Starts *">
              <input
                required
                type="datetime-local"
                value={form.starts_at}
                onChange={(e) => set("starts_at", e.target.value)}
                style={inputStyle}
              />
            </Field>
            <Field label="Ends">
              <input
                type="datetime-local"
                value={form.ends_at}
                onChange={(e) => set("ends_at", e.target.value)}
                style={inputStyle}
              />
            </Field>
          </Row>

          <Row>
            <Field label="Price ($)">
              <input
                type="number"
                min="0"
                step="1"
                value={form.price}
                onChange={(e) => set("price", e.target.value)}
                placeholder="0.00 = Free"
                style={inputStyle}
              />
            </Field>
            <Field label="Original price ($)">
              <input
                type="number"
                min="0"
                step="1"
                value={form.original_price}
                onChange={(e) => set("original_price", e.target.value)}
                placeholder="Optional — shows strikethrough"
                style={inputStyle}
              />
            </Field>
            <Field label="Capacity">
              <input
                type="number"
                min="1"
                value={form.capacity}
                onChange={(e) => set("capacity", e.target.value)}
                placeholder="Unlimited"
                style={inputStyle}
              />
            </Field>
          </Row>

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
              disabled={saving || venues.length === 0}
              style={{
                background: saving ? "#888" : "#111", color: "#fff", border: "none",
                borderRadius: 8, padding: "11px 26px", fontSize: 13, fontWeight: 600,
                cursor: saving ? "wait" : "pointer",
              }}
            >
              {saving ? "Creating…" : "Create Listing"}
            </button>
          </div>
        </form>
      </div>

      {showVenueModal && (
        <CreateVenueModal
          orgId={orgId}
          onClose={() => setShowVenueModal(false)}
          onCreated={handleVenueCreated}
        />
      )}
    </div>
  );
}

function Field({ label, children }) {
  return (
    <div style={{ marginBottom: 18, flex: 1 }}>
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
