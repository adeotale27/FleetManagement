import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import { ErrorState, Skeleton } from "../components/ui/primitives";

function inr(n: number | undefined) {
  return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(n || 0);
}

export function DeewanjiPage() {
  const q = useQuery({ queryKey: ["deewanji"], queryFn: () => api<Record<string, number>>("/finance/deewanji") });
  if (q.isLoading) return <Skeleton />;
  if (q.isError) return <ErrorState message={(q.error as Error).message} onRetry={() => q.refetch()} />;
  const d = q.data!;
  return (
    <section>
      <h1 className="h1">Deewanji desk</h1>
      <div className="kpis">
        <div className="metric"><span>Today</span><b>{inr(d.today_collection)}</b></div>
        <div className="metric"><span>Cash</span><b>{inr(d.cash)}</b></div>
        <div className="metric"><span>UPI</span><b>{inr(d.upi)}</b></div>
        <div className="metric"><span>Bank</span><b>{inr(d.bank)}</b></div>
        <div className="metric"><span>Cash with me</span><b>{inr(d.cash_with_me)}</b></div>
      </div>
      <div className="toolbar" style={{ marginTop: 16 }}>
        <a className="btn" href="/collections/new">Collect money</a>
        <a className="btn secondary" href="/handovers">Handover</a>
      </div>
    </section>
  );
}
