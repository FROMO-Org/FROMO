import { useEffect, useMemo } from "react";
import { MOBILE_WEB_URL } from "../lib/config";

export default function CheckoutRedirect({ status }) {
  const query = typeof window !== "undefined" ? window.location.search || "" : "";
  const mobilePath = status === "success" ? "/#/bookings" : "/#/map";

  const deepLink = useMemo(() => {
    return `fromo://checkout/${status}${query}`;
  }, [query, status]);

  const mobileWebLink = useMemo(() => {
    const version = status === "success" ? "checkout-success" : "checkout-cancel";
    return `${MOBILE_WEB_URL}/?v=${version}${mobilePath}`;
  }, [mobilePath, status]);

  useEffect(() => {
    const openAppTimer = window.setTimeout(() => {
      window.location.href = deepLink;
    }, 350);
    const fallbackTimer = window.setTimeout(() => {
      window.location.href = mobileWebLink;
    }, 1600);
    return () => {
      window.clearTimeout(openAppTimer);
      window.clearTimeout(fallbackTimer);
    };
  }, [deepLink, mobileWebLink]);

  const isSuccess = status === "success";

  return (
    <main className="flex min-h-[70vh] items-center justify-center px-6">
      <section className="max-w-md rounded-3xl border border-line bg-surface p-8 text-center shadow-soft">
        <p className="font-mono text-xs font-bold uppercase tracking-[0.18em] text-muted">
          Checkout {isSuccess ? "complete" : "cancelled"}
        </p>
        <h1 className="mt-3 font-display text-3xl font-extrabold text-ink">
          {isSuccess ? "Returning to FROMO" : "Back to FROMO"}
        </h1>
        <p className="mt-3 text-sm leading-6 text-muted">
          {isSuccess
            ? "Your payment is being confirmed. The app will refresh your booking status when it opens."
            : "No worries. You can reopen the event and try again whenever you are ready."}
        </p>
        <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:justify-center">
          <a
            href={deepLink}
            className="inline-flex rounded-full bg-teal px-5 py-3 text-sm font-bold text-white"
          >
            Open the app
          </a>
          <a
            href={mobileWebLink}
            className="inline-flex rounded-full border border-line px-5 py-3 text-sm font-bold text-ink"
          >
            Open mobile web
          </a>
        </div>
      </section>
    </main>
  );
}
