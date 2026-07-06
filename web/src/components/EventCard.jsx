import { formatDistance, formatTime, formatPrice } from "../lib/format.js";

const BUSYNESS_STYLE = {
  low:    { color: "#2E9E6B", bg: "rgba(46,158,107,0.12)" },
  medium: { color: "#F5A623", bg: "rgba(245,166,35,0.15)" },
  high:   { color: "#E53935", bg: "rgba(229,57,53,0.12)" },
};

function WheelIcon(props) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
      strokeLinecap="round" strokeLinejoin="round" {...props}>
      <circle cx="12" cy="4" r="2" />
      <path d="M19 13v-2a2 2 0 0 0-2-2h-3.5" />
      <path d="M9 4v9.5" />
      <circle cx="9" cy="17" r="4.5" />
      <path d="M13.2 16.5l2.3 4.5h3" />
    </svg>
  );
}

function BookmarkIcon({ filled }) {
  return (
    <svg viewBox="0 0 24 24" width="18" height="18"
      fill={filled ? "currentColor" : "none"}
      stroke="currentColor" strokeWidth="2"
      strokeLinecap="round" strokeLinejoin="round">
      <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z" />
    </svg>
  );
}

export default function EventCard({ event, active, onSelect, onDirections, saved, onSave, busynessLevel }) {
  const v = event.venue || {};
  const category = event.category || v.category;
  const accessible = v.is_accessible;
  const busy = busynessLevel ? BUSYNESS_STYLE[busynessLevel.toLowerCase()] : null;

  return (
    <article
      tabIndex={0}
      onClick={() => onSelect(event.id)}
      onKeyDown={(e) => e.key === "Enter" && onSelect(event.id)}
      className={`cursor-pointer rounded-[14px] border transition focus:outline-none focus-visible:ring-[3px] focus-visible:ring-amber/50 overflow-hidden ${
        active
          ? "border-amber ring-1 ring-amber"
          : "border-line hover:border-[#dccfb6] hover:shadow-[0_6px_22px_-14px_rgba(20,17,14,.4)]"
      }`}
      style={{ background: "rgba(245, 166, 35, 0.06)" }}
    >
      {/* Image with bookmark overlay */}
      <div className="relative">
        {event.image_url ? (
          <img
            src={event.image_url}
            alt={event.title}
            className="h-44 w-full object-cover"
            loading="lazy"
          />
        ) : (
          <div
            className="h-44 w-full flex items-center justify-center"
            style={{ background: "rgba(245,166,35,0.1)" }}
          >
            <span style={{ fontSize: 36, opacity: 0.3 }}>📍</span>
          </div>
        )}

        {/* Bookmark button */}
        {onSave && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onSave(event.id);
            }}
            aria-label={saved ? "Remove bookmark" : "Save event"}
            className={`absolute right-2.5 top-2.5 flex h-8 w-8 items-center justify-center rounded-full transition-colors ${
              saved
                ? "bg-amber text-[#231a09]"
                : "bg-black/40 text-white hover:bg-black/60"
            }`}
          >
            <BookmarkIcon filled={saved} />
          </button>
        )}
      </div>

      {/* Card body */}
      <div className="p-4">
        <div className="flex items-center justify-between gap-2">
          {category && (
            <div className="font-mono text-[11px] uppercase tracking-wider text-amber">
              {category}
            </div>
          )}
          {busy && (
            <span
              className="shrink-0 rounded-full px-2 py-0.5 font-mono text-[10px] font-bold uppercase tracking-wider"
              style={{ color: busy.color, background: busy.bg }}
            >
              {busynessLevel}
            </span>
          )}
        </div>

        <h3 className="mt-1 font-display text-lg font-semibold leading-tight tracking-tight">
          {event.title}
        </h3>
        <div className="text-[13.5px] text-muted">
          {v.name}
          {v.address ? ` · ${v.address}` : ""}
        </div>

        <div className="mt-3 flex flex-wrap items-center gap-x-3.5 gap-y-1 font-mono text-[12.5px] text-ink">
          {formatTime(event.starts_at) && (
            <span>🕒 {formatTime(event.starts_at)}</span>
          )}
          {formatDistance(event.distance_km) && (
            <span className="text-muted">{formatDistance(event.distance_km)}</span>
          )}
          {formatPrice(event.price_cents) != null && (
            <span>{formatPrice(event.price_cents)}</span>
          )}
        </div>

        <div className="mt-3.5 flex items-center justify-between gap-2 border-t border-line-soft pt-3">
          {accessible == null ? (
            <span />
          ) : accessible ? (
            <span className="inline-flex items-center gap-1.5 text-xs font-medium text-ok">
              <WheelIcon className="h-3.5 w-3.5" /> Step-free entrance
            </span>
          ) : (
            <span className="inline-flex items-center gap-1.5 text-xs font-medium text-muted">
              <WheelIcon className="h-3.5 w-3.5" /> Steps at entrance
            </span>
          )}
          <button
            onClick={(e) => {
              e.stopPropagation();
              onDirections(event);
            }}
            className="inline-flex items-center gap-1.5 rounded-[9px] bg-amber px-3 py-1.5 text-[12.5px] font-semibold text-[#231a09] hover:bg-amber-press"
          >
            Directions →
          </button>
        </div>
      </div>
    </article>
  );
}
