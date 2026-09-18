import { useQuery } from "@tanstack/react-query";
import { useNavigate, Navigate } from "react-router-dom";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "../api/client";
import { ErrorState, Skeleton } from "../components/ui/primitives";
import { useAuth } from "../auth";

type Dash = {
  fleet: Record<string, number>;
  trips: Record<string, number>;
  finance: Record<string, number>;
  alerts: { title: string; body: string }[];
  expense_breakdown: { category: string; amount: number }[];
  daily: { date: string; in: number; out: number }[];
};

function inr(n: number | undefined) {
  return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(n || 0);
}

export function DashboardPage() {
  const { user } = useAuth();
  const nav = useNavigate();
  const isPlatform = user?.role === "PLATFORM_SUPER_ADMIN";
  const q = useQuery({ queryKey: ["owner-dash"], queryFn: () => api<Dash>("/dashboard/owner"), enabled: !isPlatform });
  if (isPlatform) return <Navigate to="/platform" replace />;
  if (q.isLoading) return <Skeleton />;
  if (q.isError) return <ErrorState message={(q.error as Error).message} onRetry={() => q.refetch()} />;
  const d = q.data!;
  const f = d.finance;
  return (
    <section>
      <div className="page-head">
        <div>
          <h1 className="h1">Ops board</h1>
          <p className="muted">What is moving, what is owed, what needs a call.</p>
        </div>
      </div>
      <div className="kpis">
        <button className="metric" onClick={() => nav("/drivers")}><span>Drivers</span><b>{d.fleet.drivers}</b></button>
        <button className="metric" onClick={() => nav("/vehicles")}><span>Vehicles</span><b>{d.fleet.vehicles}</b></button>
        <button className="metric" onClick={() => nav("/trips")}><span>Active trips</span><b>{d.trips.live}</b></button>
        <button className="metric" onClick={() => nav("/vehicles")}><span>In workshop</span><b>{d.fleet.repair}</b></button>
      </div>
      <div className="kpis" style={{ marginTop: 12 }}>
        <button className="metric" onClick={() => nav("/finance?view=receivables")}><span>To receive</span><b>{inr(f.receivable)}</b></button>
        <button className="metric" onClick={() => nav("/finance")}><span>To pay</span><b>{inr(f.payable)}</b></button>
        <button className="metric"><span>Collected today</span><b>{inr(f.today_collection)}</b></button>
        <button className="metric"><span>Cash with Deewanji</span><b>{inr(f.deewanji_cash)}</b></button>
        <button className="metric"><span>Cash in office</span><b>{inr(f.cash_balance)}</b></button>
        <button className="metric"><span>Bank</span><b>{inr(f.bank_balance)}</b></button>
      </div>
      <div className="split">
        <div className="panel">
          <h2 className="h1">Money in vs out</h2>
          <div style={{ height: 240 }}>
            <ResponsiveContainer>
              <AreaChart data={d.daily || []}>
                <CartesianGrid stroke="#ece6da" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Area dataKey="in" name="In" stroke="#1f6b45" fill="#1f6b45" fillOpacity={0.15} />
                <Area dataKey="out" name="Out" stroke="#b4532a" fill="#b4532a" fillOpacity={0.12} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div className="panel">
          <h2 className="h1">Needs attention</h2>
          {(d.alerts || []).length === 0 ? <p className="muted">No document alerts.</p> : d.alerts.map((a) => <p key={a.title}>{a.title} — {a.body}</p>)}
          <h2 className="h1" style={{ marginTop: 16 }}>Spend by type</h2>
          {(d.expense_breakdown || []).length === 0 ? <p className="muted">No expenses posted yet.</p> : d.expense_breakdown.map((e) => (
            <p key={e.category}>{e.category} · {inr(e.amount)}</p>
          ))}
        </div>
      </div>
    </section>
  );
}
