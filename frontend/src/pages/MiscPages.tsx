import { useMutation, useQuery } from "@tanstack/react-query";
import { FormEvent, useState } from "react";
import { api } from "../api/client";
import { Button, ErrorState, Input, Skeleton, StatCard } from "../components/ui/primitives";
import { DataTable, StatusBadge } from "../components/tables/DataTable";
import type { PageResult } from "../types";
import { useNavigate } from "react-router-dom";

export function LoginPage({ onLogin }: { onLogin: (token: string, user: unknown) => void }) {
  const [email, setEmail] = useState("owner@demo.local");
  const [password, setPassword] = useState("Owner@123");
  const [err, setErr] = useState<string | null>(null);
  async function submit(e: FormEvent) {
    e.preventDefault();
    try {
      const data = await api<{ access_token: string; user: unknown }>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      onLogin(data.access_token, data.user);
    } catch (error) {
      setErr((error as Error).message);
    }
  }
  return (
    <div className="login">
      <form className="card grid" onSubmit={submit}>
        <h1 className="h1">Sign in</h1>
        <p className="muted">Fleet and logistics for transport businesses.</p>
        <Input label="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required autoComplete="username" />
        <Input label="Password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required autoComplete="current-password" />
        {err ? <ErrorState message={err} /> : null}
        <Button type="submit">Continue</Button>
      </form>
    </div>
  );
}

export function TripsPage() {
  const nav = useNavigate();
  const q = useQuery({ queryKey: ["trips"], queryFn: () => api<PageResult<Record<string, string>>>("/trips") });
  if (q.isLoading) return <Skeleton />;
  if (q.isError) return <ErrorState message={(q.error as Error).message} onRetry={() => q.refetch()} />;
  return (
    <section>
      <div className="page-header">
        <h1 className="h1">Trips & LR</h1>
        <div className="toolbar">
          <Button onClick={() => nav("/trips/new")}>New trip</Button>
          <Button variant="secondary" onClick={() => nav("/lrs/new")}>
            New LR
          </Button>
        </div>
      </div>
      <DataTable
        rows={q.data?.items || []}
        columns={[
          { key: "trip_number", label: "Trip" },
          { key: "trip_kind", label: "Type" },
          { key: "origin_name", label: "From" },
          { key: "destination_name", label: "To" },
          { key: "vehicle_number", label: "Vehicle" },
          { key: "driver_name", label: "Driver" },
          { key: "status", label: "Status", render: (r) => <StatusBadge status={String(r.status || "")} /> },
        ]}
        onRow={(r) => r.id && nav(`/trips/${r.id}`)}
      />
    </section>
  );
}

export function RecordDetailPage({ resource }: { resource: string }) {
  const id = location.pathname.split("/").pop() || "";
  const q = useQuery({ queryKey: [resource, id], queryFn: () => api<Record<string, unknown>>(`/${resource}/${id}`) });
  const status = useMutation({
    mutationFn: (next: string) => api(`/trips/${id}/status`, { method: "POST", body: JSON.stringify({ status: next }) }),
    onSuccess: () => q.refetch(),
  });
  if (q.isLoading) return <Skeleton />;
  if (q.isError) return <ErrorState message={(q.error as Error).message} onRetry={() => q.refetch()} />;
  const item = q.data!;
  return (
    <section className="grid">
      <h1 className="h1">{String(item.trip_number || item.lr_number || item.name || item.vehicle_number || "Record")}</h1>
      <div className="card">
        {Object.entries(item)
          .filter(([k]) => !["password_hash"].includes(k))
          .slice(0, 24)
          .map(([k, v]) => (
            <p key={k}>
              <span className="muted">{k}</span> {typeof v === "object" ? JSON.stringify(v) : String(v ?? "—")}
            </p>
          ))}
      </div>
      {resource === "trips" ? (
        <div className="toolbar">
          {["assigned", "started", "in_transit", "delivered", "completed", "closed", "cancelled"].map((s) => (
            <Button key={s} variant="secondary" onClick={() => status.mutate(s)}>
              Mark {s}
            </Button>
          ))}
        </div>
      ) : null}
      {resource === "lrs" ? (
        <a className="btn" href={`/api/v1/lrs/${id}/print`} target="_blank" rel="noreferrer">
          Print LR
        </a>
      ) : null}
    </section>
  );
}

export function ReportsPage() {
  const reports = ["trips", "vehicles", "drivers", "lrs", "parties", "collections", "expenses", "fuel", "maintenance", "partners"];
  return (
    <section>
      <h1 className="h1">Reports</h1>
      <div className="grid">
        {reports.map((r) => (
          <div className="card" key={r}>
            <strong>{r}</strong>
            <div className="toolbar">
              <a className="btn secondary" href={`/api/v1/reports/${r}`}>
                View
              </a>
              <a className="btn secondary" href={`/api/v1/reports/${r}?format=csv`}>
                CSV
              </a>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

export function PlatformPage() {
  const overview = useQuery({ queryKey: ["plat"], queryFn: () => api<Record<string, number>>("/platform/overview") });
  const tenants = useQuery({ queryKey: ["tenants"], queryFn: () => api<PageResult<Record<string, string>>>("/platform/tenants") });
  const [form, setForm] = useState({ business_name: "", owner_email: "", owner_password: "Owner@123", mobile: "" });
  const create = useMutation({
    mutationFn: () => api("/platform/tenants", { method: "POST", body: JSON.stringify(form) }),
    onSuccess: () => tenants.refetch(),
  });
  if (overview.isLoading) return <Skeleton />;
  return (
    <section>
      <h1 className="h1">Platform</h1>
      <div className="grid kpis">
        <StatCard label="Tenants" value={overview.data?.total_tenants || 0} />
        <StatCard label="Active" value={overview.data?.active_tenants || 0} />
        <StatCard label="Users" value={overview.data?.active_users || 0} />
        <StatCard label="Health" value={String(overview.data?.system_health || "—")} />
      </div>
      <form
        className="card grid"
        style={{ marginTop: 16 }}
        onSubmit={(e) => {
          e.preventDefault();
          create.mutate();
        }}
      >
        <h2>Onboard tenant</h2>
        <Input label="Business name" value={form.business_name} onChange={(e) => setForm({ ...form, business_name: e.target.value })} required />
        <Input label="Owner email" value={form.owner_email} onChange={(e) => setForm({ ...form, owner_email: e.target.value })} required />
        <Input label="Mobile" value={form.mobile} onChange={(e) => setForm({ ...form, mobile: e.target.value })} />
        <Button type="submit">Create tenant</Button>
      </form>
      <DataTable rows={tenants.data?.items || []} columns={[{ key: "business_name", label: "Business" }, { key: "status", label: "Status" }, { key: "plan", label: "Plan" }]} />
    </section>
  );
}

export function SettingsPage() {
  const q = useQuery({ queryKey: ["settings"], queryFn: () => api<Record<string, unknown>>("/settings") });
  if (q.isLoading) return <Skeleton />;
  return (
    <section>
      <h1 className="h1">Settings</h1>
      <pre className="card" style={{ overflow: "auto" }}>
        {JSON.stringify(q.data, null, 2)}
      </pre>
    </section>
  );
}

export function SearchPage() {
  const q = new URLSearchParams(location.search).get("q") || "";
  const data = useQuery({ queryKey: ["search", q], queryFn: () => api<Record<string, Record<string, string>[]>>(`/search?q=${encodeURIComponent(q)}`), enabled: q.length > 1 });
  return (
    <section>
      <h1 className="h1">Search</h1>
      {data.isLoading ? <Skeleton /> : null}
      {Object.entries(data.data || {}).map(([k, items]) => (
        <div key={k} className="card" style={{ marginBottom: 8 }}>
          <strong>{k}</strong>
          {(items || []).map((i) => (
            <p key={i.id}>{i.name || i.vehicle_number || i.trip_number || i.lr_number}</p>
          ))}
        </div>
      ))}
    </section>
  );
}

export function NotificationsPage() {
  const q = useQuery({ queryKey: ["notifications"], queryFn: () => api<PageResult<Record<string, string>>>("/notifications") });
  if (q.isLoading) return <Skeleton />;
  return (
    <section>
      <h1 className="h1">Notifications</h1>
      {(q.data?.items || []).length === 0 ? <p className="muted">No alerts.</p> : (q.data?.items || []).map((n) => <div className="card" key={n.id}>{n.title}<div className="muted">{n.body}</div></div>)}
    </section>
  );
}

export function ExpensePage() {
  const [form, setForm] = useState({ category: "Toll", amount: "", payment_mode: "Cash", remarks: "" });
  const mutate = useMutation({
    mutationFn: () => api("/finance/expenses", { method: "POST", body: JSON.stringify({ ...form, amount: Number(form.amount) }) }),
  });
  return (
    <form className="grid" onSubmit={(e) => { e.preventDefault(); mutate.mutate(); }}>
      <h1 className="h1">Expense</h1>
      <label className="field">
        Category
        <select className="input" value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}>
          {["Fuel", "Toll", "Tea & Food", "Loading", "Unloading", "Parking", "Maintenance", "Repair", "Other"].map((c) => (
            <option key={c}>{c}</option>
          ))}
        </select>
      </label>
      <label className="field">
        Paid from
        <select className="input" value={form.payment_mode} onChange={(e) => setForm({ ...form, payment_mode: e.target.value })}>
          <option>Cash</option>
          <option>UPI</option>
          <option>Bank</option>
        </select>
      </label>
      <Input label="Amount" type="number" value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} required />
      <Input label="Remarks" value={form.remarks} onChange={(e) => setForm({ ...form, remarks: e.target.value })} />
      <Button type="submit">Save expense</Button>
      {mutate.isSuccess ? <p>Saved.</p> : null}
    </form>
  );
}

export function FuelPage() {
  const providers = useQuery({ queryKey: ["fp"], queryFn: () => api<PageResult<Record<string, string>>>("/fuel-providers") });
  const vehicles = useQuery({ queryKey: ["vehicles"], queryFn: () => api<PageResult<Record<string, string>>>("/vehicles") });
  const [form, setForm] = useState({ provider_id: "", vehicle_id: "", quantity: "", rate: "", payment_mode: "Cash" });
  const mutate = useMutation({
    mutationFn: () => api("/fuel/entries", { method: "POST", body: JSON.stringify({ ...form, quantity: Number(form.quantity), rate: Number(form.rate), amount: Number(form.quantity) * Number(form.rate) }) }),
  });
  return (
    <form className="grid" onSubmit={(e) => { e.preventDefault(); mutate.mutate(); }}>
      <h1 className="h1">Fuel entry</h1>
      <select className="input" value={form.provider_id} onChange={(e) => setForm({ ...form, provider_id: e.target.value })}>
        <option value="">Pump</option>
        {(providers.data?.items || []).map((p) => (
          <option key={p.id} value={p.id}>{p.name}</option>
        ))}
      </select>
      <select className="input" value={form.vehicle_id} onChange={(e) => setForm({ ...form, vehicle_id: e.target.value })}>
        <option value="">Vehicle</option>
        {(vehicles.data?.items || []).map((p) => (
          <option key={p.id} value={p.id}>{p.vehicle_number}</option>
        ))}
      </select>
      <Input label="Quantity (L)" value={form.quantity} onChange={(e) => setForm({ ...form, quantity: e.target.value })} />
      <Input label="Rate" value={form.rate} onChange={(e) => setForm({ ...form, rate: e.target.value })} />
      <Button type="submit">Save</Button>
    </form>
  );
}

export function HandoverPage() {
  const [form, setForm] = useState({ deewanji_id: "", amount: "", handed_to: "owner" });
  const mutate = useMutation({
    mutationFn: () => api("/finance/handovers", { method: "POST", body: JSON.stringify({ ...form, amount: Number(form.amount) }) }),
  });
  return (
    <form className="grid" onSubmit={(e) => { e.preventDefault(); mutate.mutate(); }}>
      <h1 className="h1">Handover cash</h1>
      <Input label="Deewanji user id" value={form.deewanji_id} onChange={(e) => setForm({ ...form, deewanji_id: e.target.value })} />
      <Input label="Amount" type="number" value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} />
      <Button type="submit">Record handover</Button>
    </form>
  );
}
