import { useState } from "react";
import { useOutletContext } from "react-router-dom";
import { formatPrice } from "../../lib/format";

function formatEventDate(iso) {
  if (!iso) return "—";
  const d = new Date(iso);
  return (
    d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }) +
    " · " +
    d.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" })
  );
}

const TABS = [
  { key: "all", label: "All" },
  { key: "active", label: "Active" },
  { key: "expired", label: "Expired" },
  { key: "sold_out", label: "Sold Out" },
];

export default function Listings() {
  const { orgData } = useOutletContext();
  const [activeTab, setActiveTab] = useState("all");

  const summary = orgData?.dashboard?.summary ?? {};
  const listings = orgData?.dashboard?.listings ?? [];

  const filtered =
    activeTab === "all"
      ? listings
      : listings.filter((l) => l.display_status === activeTab);

  const {
    bookings_this_month: bookings = 0,
    active_listings: active = 0,
    revenue_this_week_cents: rev = 0,
  } = summary;

  return (
    <div style={{ background: "#fff", minHeight: "100%", padding: "40px 48px" }}>
      {/* Page header */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: 32,
          paddingBottom: 24,
          borderBottom: "1px solid #e8e2da",
        }}
      >
        <h1
          style={{
            fontSize: 30,
            fontWeight: 800,
            fontFamily: '"Bricolage Grotesque", Inter, system-ui',
            margin: 0,
            letterSpacing: "-0.02em",
          }}
        >
          My Listings
        </h1>
        <button
          style={{
            background: "#111",
            color: "#fff",
            border: "none",
            padding: "11px 22px",
            borderRadius: 8,
            fontSize: 13,
            fontWeight: 600,
            cursor: "pointer",
          }}
        >
          + Create Listing
        </button>
      </div>

      {/* Summary cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 18, marginBottom: 36 }}>
        <SummaryCard
          label="Total Bookings This Month"
          value={bookings.toLocaleString()}
        />
        <SummaryCard label="Active Listings" value={active.toLocaleString()} />
        <SummaryCard
          label="Revenue This Week"
          value={`$${(rev / 100).toLocaleString("en-US", { minimumFractionDigits: 0 })}`}
        />
      </div>

      {/* Tab bar */}
      <div style={{ display: "flex", gap: 28, borderBottom: "1px solid #e8e2da", marginBottom: 24 }}>
        {TABS.map(({ key, label }) => (
          <button
            key={key}
            onClick={() => setActiveTab(key)}
            style={{
              background: "none",
              border: "none",
              borderBottom: activeTab === key ? "2px solid #F5A623" : "2px solid transparent",
              marginBottom: -1,
              padding: "0 0 12px",
              fontSize: 14,
              fontWeight: activeTab === key ? 600 : 500,
              color: activeTab === key ? "#111" : "#888",
              cursor: "pointer",
              transition: "color 0.12s",
            }}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Table */}
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr>
            {["Activity", "Date & Time", "Price", "Sold", "Status", "Actions"].map((h) => (
              <th
                key={h}
                style={{
                  textAlign: "left",
                  fontSize: 11,
                  fontWeight: 600,
                  color: "#888",
                  letterSpacing: "0.08em",
                  textTransform: "uppercase",
                  padding: "0 16px 14px 0",
                  borderBottom: "1px solid #e8e2da",
                }}
              >
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {filtered.length === 0 ? (
            <tr>
              <td colSpan={6} style={{ padding: "28px 0", color: "#888", fontSize: 14 }}>
                No listings in this category.
              </td>
            </tr>
          ) : (
            filtered.map((l) => (
              <tr key={l.id} style={{ borderBottom: "1px solid #f0ebe3" }}>
                <td style={{ padding: "16px 16px 16px 0", fontWeight: 600, fontSize: 14, color: "#111" }}>
                  {l.title}
                </td>
                <td style={{ padding: "16px 16px 16px 0", color: "#555", fontSize: 13.5 }}>
                  {formatEventDate(l.starts_at)}
                </td>
                <td style={{ padding: "16px 16px 16px 0", fontSize: 14, color: "#333" }}>
                  {formatPrice(l.price_cents)}
                </td>
                <td style={{ padding: "16px 16px 16px 0", fontSize: 14, color: "#333" }}>
                  {l.sold ?? 0}/{l.capacity ?? "?"}
                </td>
                <td style={{ padding: "16px 16px 16px 0" }}>
                  <StatusBadge status={l.display_status} />
                </td>
                <td style={{ padding: "16px 0 16px 0", fontSize: 13, color: "#888" }}>
                  <span style={{ cursor: "pointer" }}>Edit</span>
                  <span style={{ margin: "0 6px" }}>·</span>
                  <span style={{ cursor: "pointer" }}>Hide</span>
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}

function SummaryCard({ label, value }) {
  return (
    <div
      style={{
        background: "#f5f0e8",
        borderLeft: "3px solid #F5A623",
        borderRadius: 10,
        padding: "24px 28px",
      }}
    >
      <div
        style={{
          fontSize: 38,
          fontWeight: 800,
          fontFamily: '"Bricolage Grotesque", Inter, system-ui',
          color: "#111",
          letterSpacing: "-0.02em",
          lineHeight: 1,
        }}
      >
        {value}
      </div>
      <div style={{ fontSize: 13, color: "#888", marginTop: 8 }}>{label}</div>
    </div>
  );
}

function StatusBadge({ status }) {
  const map = {
    active: { bg: "#F5A623", color: "#fff", label: "Active" },
    sold_out: { bg: "#E53935", color: "#fff", label: "Sold Out" },
    expired: { bg: "#888", color: "#fff", label: "Expired" },
    draft: { bg: "#ddd", color: "#555", label: "Draft" },
  };
  const s = map[status] ?? map.draft;
  return (
    <span
      style={{
        background: s.bg,
        color: s.color,
        padding: "4px 11px",
        borderRadius: 5,
        fontSize: 12,
        fontWeight: 700,
        display: "inline-block",
      }}
    >
      {s.label}
    </span>
  );
}
