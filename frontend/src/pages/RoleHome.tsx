import { useNavigate } from "react-router-dom";
import { useState } from "react";
import { api } from "../api/client";
import { LOGIN_HIDDEN } from "../config";
import { useAuth } from "../auth";

export function RoleHome({ onLogin }: { onLogin: (token: string, user: unknown) => void }) {
  const [err, setErr] = useState<string | null>(null);
  const nav = useNavigate();
  async function pick(persona: "platform" | "owner" | "deewanji") {
    try {
      const data = await api<{ access_token: string; user: { role: string } }>("/auth/dev-session", {
        method: "POST",
        body: JSON.stringify({ persona }),
      });
      onLogin(data.access_token, data.user);
      nav(persona === "platform" ? "/platform" : "/home");
    } catch (e) {
      setErr((e as Error).message);
    }
  }
  if (!LOGIN_HIDDEN) return null;
  return (
    <div className="gate">
      <div className="gate-card">
        <h1>Who is using the desk today?</h1>
        <p>Login is hidden for this environment. Pick a working seat. Data stays tenant-scoped.</p>
        {err ? <p className="muted">{err}</p> : null}
        <div className="personas">
          <button className="persona" onClick={() => pick("owner")}>
            <strong>Business owner</strong>
            See trips, money, fleet, and collections for your transport company.
          </button>
          <button className="persona" onClick={() => pick("deewanji")}>
            <strong>Deewanji</strong>
            Record collections and hand over cash. Fast path for field recovery.
          </button>
          <button className="persona" onClick={() => pick("platform")}>
            <strong>Platform operator</strong>
            Onboard tenants and support access. Never mixed with a company’s books.
          </button>
        </div>
      </div>
    </div>
  );
}

export function OwnerHome() {
  const { user } = useAuth();
  const tiles =
    user?.role === "DEEWANJI"
      ? [
          ["/collections/new", "Collect money", "Party, amount, mode — save in seconds."],
          ["/deewanji", "Today’s board", "Cash with me and what is still due."],
          ["/handovers", "Handover", "Give cash to owner, office, or bank."],
          ["/parties", "Parties", "Find who still owes."],
        ]
      : [
          ["/ops", "Ops board", "Drivers, vehicles, trips, money — what needs you now."],
          ["/trips", "Trips & LR", "Indoor/outdoor trips and lorry receipts."],
          ["/vehicles", "Vehicle master", "Numbers, make/model, status."],
          ["/drivers", "Drivers", "People on the road and advances."],
          ["/parties", "Parties", "Senders and outstanding."],
          ["/locations", "Locations & routes", "Editable indoor routes. Nothing hard-coded."],
          ["/finance", "Money", "To receive, to pay, cash, Deewanji cash."],
          ["/collections/new", "Collection", "Record a receipt against a party."],
          ["/lrs/new", "New LR", "From a trip — sender, receiver, paid or not paid."],
          ["/reports", "Reports", "CSV export, tenant filtered."],
        ];
  return (
    <section>
      <div className="page-head">
        <div>
          <h1 className="h1">Where do you want to go?</h1>
          <p className="muted">
            {user?.name} · {String(user?.role || "").replaceAll("_", " ")}
          </p>
        </div>
      </div>
      <div className="tiles">
        {tiles.map(([to, title, body]) => (
          <a className="tile" key={to} href={to}>
            <b>{title}</b>
            <span className="muted">{body}</span>
          </a>
        ))}
      </div>
    </section>
  );
}
