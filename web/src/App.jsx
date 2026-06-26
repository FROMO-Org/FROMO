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

export default function App() {
  const { pathname } = useLocation();
  const isPartner = pathname.startsWith("/partner");

  return (
    <div className="flex min-h-full flex-col">
      {!isPartner && <Header />}
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="/partner" element={<PartnerLayout />}>
          <Route index element={<Listings />} />
          <Route path="analytics" element={<Analytics />} />
          <Route path="settings" element={<PartnerSettings />} />
        </Route>
      </Routes>
    </div>
  );
}
