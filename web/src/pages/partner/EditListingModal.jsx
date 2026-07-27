import { useEffect, useState } from "react";
import { getEvent, getVenue, updateEvent } from "../../lib/api";

const CATEGORIES = ["Music", "Food", "Art", "Sport", "Comedy", "Wellness", "Networking", "Other"];
const STATUSES = ["draft", "active", "cancelled", "completed"];

function toDatetimeLocal(iso) {
  if (!iso) return "";
  return new Date(iso).toISOString().slice(0, 16);
}

function toIso(datetimeLocal) {
  if (!datetimeLocal) return null;
  return new Date(datetimeLocal).toISOString();
}

export default function EditListingModal({ eventId, onClose, onUpdated }) {
  const [loading, setLoading] = useState(true);
  const [venueName, setVenueName] = useState("");
  const [form, setForm] = useState({
    title: "",
    category: "",
    description: "",
    starts_at: "",
    ends_at: "",
    price: "",
    capacity: "",
    status: "active",
    image_url: "",
  });
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    let alive = true;
    getEvent(eventId)
      .then((ev) => {
        if (!alive) return;
        setForm({
          title: ev.title ?? "",
          category: ev.category ?? "",
          description: ev.description ?? "",
          starts_at: toDatetimeLocal(ev.starts_at),
          ends_at: toDatetimeLocal(ev.ends_at),
          price: ev.price_cents != null ? String(ev.price_cents / 100) : "",
          capacity: ev.capacity != null ? String(ev.capacity) : "",
          status: ev.status ?? "active",
          image_url: ev.image_url ?? "",
        });
        if (ev.venue_id) {
          getVenue(ev.venue_id)
            .then((v) => alive && setVenueName(v?.name ?? ""))
            .catch(() => {});
        }
      })
      .catch(() => setError("Couldn't load this listing."))
      .finally(() => alive && setLoading(false));
    return () => { alive = false; };
  }, [eventId]);

  function set(key, val) {
    setForm((f) => ({ ...f, [key]: val }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);

    if (!form.title.trim()) { setError("Title is required."); return; }
    if (!form.starts_at) { setError("Start date & time is required."); return; }

    const body = {
      title: form.title.trim(),
      starts_at: toIso(form.starts_at),
      ends_at: form.ends_at ? toIso(form.ends_at) : null,
      price_cents: form.price ? Math.round(parseFloat(form.price) * 100) : 0,
      capacity: form.capacity ? parseInt(form.capacity, 10) : null,
      description: form.description.trim() || null,
      category: form.category || null,
      status: form.status,
      image_url: form.image_url.trim() || null,
    };

    setSaving(true);
    try {
      await updateEvent(eventId, body);
      onUpdated();
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
        position: "fixed", inset: 0, zIndex: 9000,
        background: "rgba(0,0,0,0.45)", display: "flex",
        alignItems: "center", justifyContent: "center", padding: 24,
      }}
    >
      <div
        style={{
          background: "var(--color-paper)", borderRadius: 14, width: "100%", maxWidth: 560,
          maxHeight: "90vh", overflowY: "auto",
          boxShadow: "0 24px 64px rgba(0,0,0,0.18)",
        }}
      >
        <div style={{ padding: "28px 32px 0", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <h2 style={{ margin: 0, fontSize: 22, fontWeight: 800, fontFamily: '"Bricolage Grotesque", Inter, system-ui', letterSpacing: "-0.02em", color: "var(--color-ink)" }}>
            Edit Listing
          </h2>
          <button
            onClick={onClose}
            style={{ background: "none", border: "none", cursor: "pointer", fontSize: 22, color: "var(--color-muted)", lineHeight: 1, padding: 4 }}
            aria-label="Close"
          >
            ×
          </button>
        </div>

        {loading ? (
          <div style={{ padding: "40px 32px", fontSize: 14, color: "var(--color-muted)" }}>Loading…</div>
        ) : (
          <form onSubmit={handleSubmit} style={{ padding: "24px 32px 32px" }}>

            <Field label="Title *">
              <input
                required
                value={form.title}
                onChange={(e) => set("title", e.target.value)}
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

              <Field label="Venue">
                <div style={{ ...inputStyle, color: "var(--color-muted)", background: "var(--color-line)", cursor: "not-allowed" }}>
                  {venueName || "—"}
                </div>
              </Field>
            </Row>

            <Field label="Description">
              <textarea
                value={form.description}
                onChange={(e) => set("description", e.target.value)}
                rows={3}
                style={{ ...inputStyle, resize: "vertical" }}
              />
            </Field>

            <Field label="Image URL">
              <input
                type="url"
                value={form.image_url}
                onChange={(e) => set("image_url", e.target.value)}
                placeholder="Link to an image (optional)"
                style={inputStyle}
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
              <Field label="Status">
                <select
                  value={form.status}
                  onChange={(e) => set("status", e.target.value)}
                  style={inputStyle}
                >
                  {STATUSES.map((s) => (
                    <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>
                  ))}
                </select>
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
                disabled={saving}
                style={{
                  background: saving ? "#888" : "#111", color: "#fff", border: "none",
                  borderRadius: 8, padding: "11px 26px", fontSize: 13, fontWeight: 600,
                  cursor: saving ? "wait" : "pointer",
                }}
              >
                {saving ? "Saving…" : "Save Changes"}
              </button>
            </div>
          </form>
        )}
      </div>
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
