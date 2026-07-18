import { useEffect, useMemo } from "react";

export default function CheckoutRedirect({ status }) {
  const deepLink = useMemo(() => {
    const query = window.location.search || "";
    return `fromo://checkout/${status}${query}`;
  }, [status]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      window.location.href = deepLink;
    }, 350);
    return () => window.clearTimeout(timer);
  }, [deepLink]);

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
        <a
          href={deepLink}
          className="mt-6 inline-flex rounded-full bg-teal px-5 py-3 text-sm font-bold text-white"
        >
          Open the app
        </a>
      </section>
    </main>
  );
}
