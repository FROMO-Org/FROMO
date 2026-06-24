import { useMemo } from "react";
import { useOutletContext } from "react-router-dom";
import { formatPrice } from "../../lib/format";

export default function Analytics() {
  const { orgData } = useOutletContext();
  const summary = orgData?.dashboard?.summary ?? {};
  const listings = orgData?.dashboard?.listings ?? [];

  const {
    bookings_this_month: bookings = 0,
    active_listings: active = 0,
    revenue_this_week_cents: rev = 0,
  } = summary;

  const avgPriceCents = useMemo(() => {
    const priced = listings.filter((l) => l.price_cents > 0);
    if (!priced.length) return 0;
    return Math.round(priced.reduce((sum, l) => sum + l.price_cents, 0) / priced.length);
  }, [listings]);

  const topListings = useMemo(
    () => [...listings].sort((a, b) => (b.revenue_cents ?? 0) - (a.revenue_cents ?? 0)).slice(0, 5),
    [listings]
  );

  const chartData = useMemo(() => {
    const days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
    const totals = Array(7).fill(0);
    listings.forEach((l) => {
      if (!l.starts_at) return;
      const dow = new Date(l.starts_at).getDay();
      const idx = dow === 0 ? 6 : dow - 1;
      totals[idx] += l.bookings_count ?? 0;
    });
    return days.map((label, i) => ({ label, value: totals[i] }));
  }, [listings]);

  return (
    <div style={{ background: "#fff", minHeight: "100%", padding: "40px 48px" }}>
      {/* Header */}
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
          Analytics
        </h1>
        <span style={{ fontSize: 13, color: "#F5A623", fontWeight: 600, cursor: "pointer" }}>
          Last 7 days ▾
        </span>
      </div>

      {/* Summary cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 16, marginBottom: 32 }}>
        <MiniCard label="Total Bookings" value={bookings.toLocaleString()} sub="This month" />
        <MiniCard
          label="Revenue"
          value={`$${(rev / 100).toLocaleString("en-US", { minimumFractionDigits: 0 })}`}
          sub="This week"
        />
        <MiniCard label="Active Listings" value={active.toLocaleString()} sub="Right now" />
        <MiniCard label="Avg. Ticket Price" value={formatPrice(avgPriceCents) ?? "—"} sub="Across listings" />
      </div>

      {/* Charts row */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20, marginBottom: 28 }}>
        {/* Line chart */}
        <div style={{ background: "#f5f0e8", borderRadius: 12, padding: "24px 28px" }}>
          <h3 style={{ margin: "0 0 20px", fontSize: 16, fontWeight: 700, color: "#111" }}>
            Bookings Over Time
          </h3>
          <LineChart data={chartData} />
        </div>

        {/* Top listings */}
        <div style={{ background: "#f5f0e8", borderRadius: 12, padding: "24px 28px" }}>
          <h3 style={{ margin: "0 0 20px", fontSize: 16, fontWeight: 700, color: "#111" }}>
            Top Listings
          </h3>
          {topListings.length === 0 ? (
            <p style={{ color: "#888", fontSize: 13 }}>No listings yet.</p>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
              {topListings.map((l) => (
                <div key={l.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                  <div>
                    <div style={{ fontSize: 14, fontWeight: 600, color: "#111" }}>{l.title}</div>
                    <div style={{ fontSize: 12, color: "#888", marginTop: 2 }}>
                      {l.bookings_count ?? 0} tickets sold
                    </div>
                  </div>
                  <div style={{ fontSize: 15, fontWeight: 700, color: "#F5A623" }}>
                    {formatPrice(l.revenue_cents) ?? "—"}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Event Performance table */}
      <div style={{ background: "#f5f0e8", borderRadius: 12, padding: "24px 28px" }}>
        <h3 style={{ margin: "0 0 20px", fontSize: 16, fontWeight: 700, color: "#111" }}>
          Event Performance
        </h3>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr>
              {["Event", "Bookings", "Revenue", "Capacity", "Status"].map((h) => (
                <th
                  key={h}
                  style={{
                    textAlign: "left",
                    fontSize: 11,
                    fontWeight: 600,
                    color: "#888",
                    letterSpacing: "0.07em",
                    textTransform: "uppercase",
                    paddingBottom: 12,
                    borderBottom: "1px solid #ddd8d0",
                  }}
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {listings.map((l) => (
              <tr key={l.id} style={{ borderBottom: "1px solid #e8e2d8" }}>
                <td style={{ padding: "14px 0", fontWeight: 600, fontSize: 14, color: "#111" }}>
                  {l.title}
                </td>
                <td style={{ padding: "14px 12px 14px 0", fontSize: 14, color: "#333" }}>
                  {l.bookings_count ?? 0}
                </td>
                <td style={{ padding: "14px 12px 14px 0", fontSize: 14, color: "#333" }}>
                  {formatPrice(l.revenue_cents) ?? "—"}
                </td>
                <td style={{ padding: "14px 12px 14px 0", fontSize: 14, color: "#333" }}>
                  {l.sold ?? 0}/{l.capacity ?? "?"}
                </td>
                <td style={{ padding: "14px 0" }}>
                  <PerformanceBadge status={l.display_status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function MiniCard({ label, value, sub }) {
  return (
    <div style={{ background: "#f5f0e8", borderLeft: "3px solid #F5A623", borderRadius: 10, padding: "20px 22px" }}>
      <div style={{ fontSize: 12, color: "#888", marginBottom: 6 }}>{label}</div>
      <div style={{ fontSize: 30, fontWeight: 800, fontFamily: '"Bricolage Grotesque", Inter, system-ui', color: "#111", letterSpacing: "-0.02em", lineHeight: 1 }}>
        {value}
      </div>
      <div style={{ fontSize: 11, color: "#aaa", marginTop: 6 }}>{sub}</div>
    </div>
  );
}

function PerformanceBadge({ status }) {
  const map = {
    active: { bg: "#F5A623", color: "#fff", label: "Active" },
    sold_out: { bg: "#E53935", color: "#fff", label: "Sold Out" },
    expired: { bg: "#888", color: "#fff", label: "Expired" },
    draft: { bg: "#ddd", color: "#555", label: "Draft" },
  };
  const s = map[status] ?? map.draft;
  return (
    <span style={{ background: s.bg, color: s.color, padding: "3px 10px", borderRadius: 4, fontSize: 11, fontWeight: 700, display: "inline-block" }}>
      {s.label}
    </span>
  );
}

function LineChart({ data }) {
  const W = 460, H = 140;
  const PAD = { t: 10, r: 10, b: 28, l: 28 };
  const innerW = W - PAD.l - PAD.r;
  const innerH = H - PAD.t - PAD.b;
  const maxY = Math.max(...data.map((d) => d.value), 1);
  const xOf = (i) => PAD.l + (i / (data.length - 1)) * innerW;
  const yOf = (v) => PAD.t + innerH - (v / maxY) * innerH;
  const pts = data.map((d, i) => `${xOf(i)},${yOf(d.value)}`).join(" ");
  const fillPts = `${PAD.l},${PAD.t + innerH} ${pts} ${xOf(data.length - 1)},${PAD.t + innerH}`;

  return (
    <svg viewBox={`0 0 ${W} ${H}`} style={{ width: "100%", height: "auto", display: "block" }}>
      {/* Fill */}
      <polygon points={fillPts} fill="#F5A623" fillOpacity="0.12" />
      {/* Line */}
      <polyline points={pts} fill="none" stroke="#F5A623" strokeWidth="2.5" strokeLinejoin="round" strokeLinecap="round" />
      {/* Dots */}
      {data.map((d, i) => (
        <circle key={i} cx={xOf(i)} cy={yOf(d.value)} r="4" fill="#F5A623" />
      ))}
      {/* X-axis labels */}
      {data.map((d, i) => (
        <text key={i} x={xOf(i)} y={H - 4} textAnchor="middle" fontSize="10" fill="#999" fontFamily="Inter, system-ui">
          {d.label}
        </text>
      ))}
      {/* Y-axis zero line */}
      <line x1={PAD.l} y1={PAD.t + innerH} x2={W - PAD.r} y2={PAD.t + innerH} stroke="#ddd" strokeWidth="1" />
    </svg>
  );
}
