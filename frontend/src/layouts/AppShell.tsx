import { NavLink, useLocation, useNavigate } from "react-router-dom";
import { Bell, Plus, Truck } from "lucide-react";
import { useEffect, useState } from "react";
import { useAuth } from "../auth";
import { LOGIN_HIDDEN } from "../config";
import { QuickCreate } from "../components/QuickCreate";

const TOP = [
  { to: "/ops", label: "Business Dashboard" },
  { to: "/vehicles", label: "Vehicle Master" },
  { to: "/drivers", label: "Driver Master" },
  { to: "/parties", label: "Party Master" },
  { to: "/locations", label: "Location Master" },
  { to: "/settings", label: "Settings" },
];

const SIDES: Record<string, { group: string; items: { to: string; label: string }[] }[]> = {
  ops: [
    { group: "Ops", items: [{ to: "/ops", label: "Ops board" }, { to: "/finance", label: "Money" }, { to: "/trips", label: "Trips" }, { to: "/lrs", label: "LR" }] },
    { group: "Work", items: [{ to: "/collections/new", label: "Collection" }, { to: "/deewanji", label: "Deewanji" }, { to: "/expenses/new", label: "Expense" }, { to: "/reports", label: "Reports" }] },
  ],
  vehicles: [{ group: "Fleet", items: [{ to: "/vehicles", label: "Vehicle listing" }, { to: "/vehicle-models", label: "Vehicle models" }, { to: "/vehicle-documents", label: "Documents" }, { to: "/maintenance", label: "Maintenance" }] }],
  drivers: [{ group: "People", items: [{ to: "/drivers", label: "Drivers" }, { to: "/employees", label: "Employees" }, { to: "/handovers", label: "Handover" }] }],
  parties: [{ group: "Parties", items: [{ to: "/parties", label: "Clients" }, { to: "/partners", label: "3PL partners" }, { to: "/fuel-providers", label: "Fuel pumps" }] }],
  locations: [{ group: "Network", items: [{ to: "/locations", label: "Locations" }, { to: "/routes", label: "Indoor routes" }] }],
};

function sideKey(path: string) {
  if (path.startsWith("/vehicle")) return "vehicles";
  if (path.startsWith("/driver") || path.startsWith("/employee") || path.startsWith("/handover") || path.startsWith("/people")) return "drivers";
  if (path.startsWith("/part") || path.startsWith("/fuel") || path.startsWith("/partner")) return "parties";
  if (path.startsWith("/location") || path.startsWith("/route")) return "locations";
  return "ops";
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth();
  const loc = useLocation();
  const nav = useNavigate();
  const [quick, setQuick] = useState(false);
  const [online, setOnline] = useState(navigator.onLine);
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
  const side = SIDES[sideKey(loc.pathname)];
  return (
    <div className="shell">
      <header className="top">
        <button className="wordmark linkish" onClick={() => nav("/home")}>
          <Truck size={18} /> {String(user?.tenant?.business_name || "Demo Transport")}
        </button>
        {TOP.map((t) => (
          <NavLink key={t.to} to={t.to}>
            {t.label}
          </NavLink>
        ))}
        <span style={{ flex: 1 }} />
        <button className="linkish" onClick={() => nav("/notifications")} aria-label="Notifications">
          <Bell size={16} />
        </button>
        <button className="btn" onClick={() => setQuick(true)}>
          <Plus size={16} /> Create
        </button>
        {LOGIN_HIDDEN ? (
          <button className="linkish" onClick={() => { logout(); nav("/"); }}>
            Switch role
          </button>
        ) : (
          <button className="linkish" onClick={() => { logout(); nav("/login"); }}>
            {user?.name}
          </button>
        )}
      </header>
      {!online ? <div className="offline">Offline — wait for network before saving money or trips.</div> : null}
      <div className="body">
        <aside className="side">
          {side.map((g) => (
            <div key={g.group}>
              <div className="group">{g.group}</div>
              {g.items.map((i) => (
                <NavLink key={i.to} to={i.to} end>
                  {i.label}
                </NavLink>
              ))}
            </div>
          ))}
        </aside>
        <div className="main">
          <div className="page">{children}</div>
        </div>
      </div>
      <nav className="bottom">
        <NavLink to="/ops">Home</NavLink>
        <NavLink to="/trips">Trips</NavLink>
        <NavLink to="/finance">Money</NavLink>
        <NavLink to="/parties">Parties</NavLink>
        <NavLink to="/home">More</NavLink>
      </nav>
      <button className="fab" aria-label="Create" onClick={() => setQuick(true)}>
        <Plus />
      </button>
      {quick ? (
        <div className="overlay" onClick={() => setQuick(false)}>
          <div className="sheet" onClick={(e) => e.stopPropagation()}>
            <h2 className="h1">Create</h2>
            <QuickCreate onDone={() => setQuick(false)} />
          </div>
        </div>
      ) : null}
    </div>
  );
}
