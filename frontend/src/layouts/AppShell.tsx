import { NavLink, useNavigate } from "react-router-dom";
import { LayoutDashboard, Truck, Users, Building2, Wallet, FileBarChart, Settings, Plus, Bell, Menu } from "lucide-react";
import { useEffect, useState } from "react";
import { useAuth } from "../auth";
import { setToken } from "../api/client";
import { Button, Modal } from "../components/ui/primitives";
import { QuickCreate } from "../components/QuickCreate";

const NAV = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/trips", label: "Trips & LR", icon: Truck },
  { to: "/fleet", label: "Fleet", icon: Truck },
  { to: "/people", label: "People", icon: Users },
  { to: "/parties", label: "Parties", icon: Building2 },
  { to: "/finance", label: "Finance", icon: Wallet },
  { to: "/reports", label: "Reports", icon: FileBarChart },
  { to: "/settings", label: "Settings", icon: Settings },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const { user, setUser } = useAuth();
  const navigate = useNavigate();
  const [quick, setQuick] = useState(false);
  const [online, setOnline] = useState(navigator.onLine);
  const [q, setQ] = useState("");
  useEffect(() => {
    const on = () => setOnline(true);
    const off = () => setOnline(false);
    window.addEventListener("online", on);
    window.addEventListener("offline", off);
    return () => {
      window.removeEventListener("online", on);
      window.removeEventListener("offline", off);
    };
  }, []);
  return (
    <div className="app-shell">
      <aside className="sidebar" aria-label="Primary">
        <div className="brand">{String(user?.tenant?.business_name || "OI Pulse")}</div>
        <nav>
          {NAV.map((item) => (
            <NavLink key={item.to} to={item.to} end={item.to === "/"}>
              <item.icon size={18} /> {item.label}
            </NavLink>
          ))}
          {user?.role === "PLATFORM_SUPER_ADMIN" ? (
            <NavLink to="/platform">
              <Settings size={18} /> Platform
            </NavLink>
          ) : null}
        </nav>
      </aside>
      <div className="app-main">
        {!online ? <div className="offline">You are offline. Changes will not save until the network returns.</div> : null}
        <header className="topbar">
          <Menu size={18} className="no-print" aria-hidden />
          <form
            style={{ flex: 1 }}
            onSubmit={(e) => {
              e.preventDefault();
              navigate(`/search?q=${encodeURIComponent(q)}`);
            }}
          >
            <label className="field" style={{ margin: 0 }}>
              <span className="sr-only" style={{ position: "absolute", left: -9999 }}>
                Search
              </span>
              <input className="input" placeholder="Search vehicle, party, trip, LR…" value={q} onChange={(e) => setQ(e.target.value)} aria-label="Global search" />
            </label>
          </form>
          <Button type="button" onClick={() => setQuick(true)} aria-label="Create">
            <Plus size={16} /> Create
          </Button>
          <button className="btn ghost" aria-label="Notifications" onClick={() => navigate("/notifications")}>
            <Bell size={18} />
          </button>
          <Button
            variant="secondary"
            onClick={() => {
              setToken(null);
              setUser(null);
              navigate("/login");
            }}
          >
            {user?.name || "Account"}
          </Button>
        </header>
        <main className="page">{children}</main>
        <nav className="bottom-nav" aria-label="Mobile">
          <NavLink to="/" end>
            Home
          </NavLink>
          <NavLink to="/trips">Trips</NavLink>
          <NavLink to="/finance">Money</NavLink>
          <NavLink to="/parties">Parties</NavLink>
          <NavLink to="/settings">More</NavLink>
        </nav>
        <button className="fab" aria-label="Quick create" onClick={() => setQuick(true)}>
          <Plus />
        </button>
      </div>
      {quick ? (
        <Modal title="Create" onClose={() => setQuick(false)}>
          <QuickCreate onDone={() => setQuick(false)} />
        </Modal>
      ) : null}
    </div>
  );
}
