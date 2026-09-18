import { useQuery } from "@tanstack/react-query";
import { useNavigate, useSearchParams } from "react-router-dom";
import { api } from "../api/client";
import { ErrorState, Skeleton, StatCard } from "../components/ui/primitives";
import { DataTable } from "../components/tables/DataTable";

function inr(n: number | undefined) {
  return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(n || 0);
}

export function FinancePage() {
  const nav = useNavigate();
  const [params] = useSearchParams();
  const view = params.get("view");
  const dash = useQuery({ queryKey: ["owner-dash"], queryFn: () => api<{ finance: Record<string, number> }>("/dashboard/owner") });
  const rec = useQuery({ queryKey: ["receivables"], queryFn: () => api<{ items: { party_id: string; outstanding: number; name?: string }[] }>("/finance/receivables") });
  if (dash.isLoading) return <Skeleton />;
  if (dash.isError) return <ErrorState message={(dash.error as Error).message} onRetry={() => dash.refetch()} />;
  const f = dash.data!.finance;
  return (
    <section>
      <h1 className="h1">Money</h1>
      <p className="muted">Every number comes from recorded payments and invoices — not typed balances.</p>
      <div className="grid kpis" style={{ marginTop: 12 }}>
        <StatCard label="Money in" value={inr(f.money_in)} />
        <StatCard label="Money out" value={inr(f.money_out)} />
        <StatCard label="To receive" value={inr(f.receivable)} onClick={() => nav("/finance?view=receivables")} />
        <StatCard label="To pay" value={inr(f.payable)} />
        <StatCard label="Cash" value={inr(f.cash_balance)} />
        <StatCard label="Bank" value={inr(f.bank_balance)} />
      </div>
      <div className="grid kpis" style={{ marginTop: 12 }}>
        <StatCard label="Collected today" value={inr(f.today_collection)} />
        <StatCard label="Spent today" value={inr(f.today_expenses)} />
        <StatCard label="Cash with Deewanji" value={inr(f.deewanji_cash)} />
        <StatCard label="Staff advances" value={inr((f.employee_advances || 0) + (f.driver_advances || 0))} />
      </div>
      {view === "receivables" ? (
        <div style={{ marginTop: 16 }}>
          <h2 className="h1">Pending parties</h2>
          <DataTable
            rows={(rec.data?.items || []).map((i) => ({ id: i.party_id, name: i.name || i.party_id, outstanding: i.outstanding }))}
            columns={[
              { key: "name", label: "Party" },
              { key: "outstanding", label: "Outstanding" },
              { key: "aging", label: "Age" },
            ]}
            onRow={(r) => nav(`/parties/${r.id}`)}
          />
        </div>
      ) : null}
    </section>
  );
}
