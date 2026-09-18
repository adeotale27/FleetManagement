import { useQuery } from "@tanstack/react-query";
import { useNavigate, Navigate } from "react-router-dom";
import { api } from "../api/client";
import { ErrorState, Skeleton, StatCard } from "../components/ui/primitives";
import { useAuth } from "../auth";

type Dash = {
  fleet: Record<string, number>;
  trips: Record<string, number>;
  finance: Record<string, number>;
  alerts: { title: string; body: string }[];
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
  const role = user?.role;
  return (
    <section>
      <div className="page-header">
        <div>
          <h1 className="h1">Today at a glance</h1>
          <p className="muted">What needs attention, and where the money is.</p>
        </div>
      </div>
      {role === "DEEWANJI" ? (
        <div className="grid kpis">
          <StatCard label="Today's collection" value={inr(d.finance.today_collection)} onClick={() => nav("/collections/new")} />
          <StatCard label="Cash with me" value={inr(d.finance.deewanji_cash)} onClick={() => nav("/finance")} />
          <StatCard label="Money to receive" value={inr(d.finance.receivable)} onClick={() => nav("/finance")} />
        </div>
      ) : role === "DRIVER" ? (
        <div className="grid kpis">
          <StatCard label="Active trips" value={d.trips.live} onClick={() => nav("/trips")} />
          <StatCard label="Vehicles" value={d.fleet.vehicles} />
        </div>
      ) : (
        <>
          <div className="grid kpis">
            <StatCard label="Money to receive" value={inr(d.finance.receivable)} onClick={() => nav("/finance?view=receivables")} />
            <StatCard label="Money to pay" value={inr(d.finance.payable)} onClick={() => nav("/finance")} />
            <StatCard label="Today's collection" value={inr(d.finance.today_collection)} />
            <StatCard label="Cash" value={inr(d.finance.cash_balance)} />
            <StatCard label="Bank" value={inr(d.finance.bank_balance)} />
            <StatCard label="Cash with Deewanji" value={inr(d.finance.deewanji_cash)} />
          </div>
          <div className="grid kpis" style={{ marginTop: 12 }}>
            <StatCard label="Vehicles" value={d.fleet.vehicles} onClick={() => nav("/vehicles")} />
            <StatCard label="Working now" value={d.fleet.available_vehicles} />
            <StatCard label="Active trips" value={d.trips.live} onClick={() => nav("/trips")} />
            <StatCard label="Overdue / alerts" value={d.alerts.length} />
          </div>
        </>
      )}
      <div className="card" style={{ marginTop: 16 }}>
        <h2 className="h1">Needs attention</h2>
        {d.alerts.length === 0 ? <p className="muted">No document or maintenance alerts.</p> : d.alerts.map((a) => <p key={a.title}>{a.title} — {a.body}</p>)}
      </div>
    </section>
  );
}
