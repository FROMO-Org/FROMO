import { useEffect } from "react";
import { Routes, Route, useLocation } from "react-router-dom";
import Header from "./components/Header.jsx";
import Home from "./pages/Home.jsx";
import Login from "./pages/Login.jsx";
import Signup from "./pages/Signup.jsx";
import PartnerLayout from "./layouts/PartnerLayout.jsx";
import Listings from "./pages/partner/Listings.jsx";
import Analytics from "./pages/partner/Analytics.jsx";
import PartnerSettings from "./pages/partner/PartnerSettings.jsx";
import Settings from "./pages/Settings.jsx";
import CheckoutRedirect from "./pages/CheckoutRedirect.jsx";
import EventDetail from "./pages/EventDetail.jsx";
import Bookings from "./pages/Bookings.jsx";

export default function App() {
  const { pathname } = useLocation();
  const isPartner = pathname.startsWith("/partner");

  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);

  return (
    <div className="flex min-h-full flex-col">
      {!isPartner && <Header />}
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/settings" element={<Settings />} />
        <Route
          path="/checkout/success"
          element={<CheckoutRedirect status="success" />}
        />
        <Route
          path="/checkout/cancel"
          element={<CheckoutRedirect status="cancel" />}
        />
        <Route path="/events/:id" element={<EventDetail />} />
        <Route path="/bookings" element={<Bookings />} />
        <Route path="/partner" element={<PartnerLayout />}>
          <Route index element={<Listings />} />
          <Route path="analytics" element={<Analytics />} />
          <Route path="settings" element={<PartnerSettings />} />
          <Route path="bookings" element={<Bookings />} />
        </Route>
      </Routes>
    </div>
  );
}
