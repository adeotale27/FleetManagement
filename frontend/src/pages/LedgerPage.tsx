import { useQuery } from "@tanstack/react-query";
import { useParams, Link } from "react-router-dom";
import { api } from "../api/client";
import { ErrorState, Skeleton } from "../components/ui/primitives";
import { DataTable } from "../components/tables/DataTable";

export function LedgerPage({ accountType }: { accountType: string }) {
  const { id } = useParams();
  const q = useQuery({
    queryKey: ["ledger", accountType, id],
    queryFn: () => api<{ entries: Record<string, unknown>[]; balance: number }>(`/finance/ledger/${accountType}/${id}`),
    enabled: Boolean(id),
  });
  if (q.isLoading) return <Skeleton />;
  if (q.isError) return <ErrorState message={(q.error as Error).message} onRetry={() => q.refetch()} />;
  return (
    <section>
      <h1 className="h1">Ledger</h1>
      <p className="muted">Running balance {q.data?.balance}. Click a row to open the source document when linked.</p>
      <DataTable
        rows={(q.data?.entries || []).map((e) => ({ ...e, id: String(e.id || e.ref_id || "") }))}
        columns={[
          { key: "created_at", label: "Date" },
          { key: "description", label: "Description" },
          { key: "debit", label: "Debit" },
          { key: "credit", label: "Credit" },
          { key: "balance", label: "Balance" },
          { key: "ref_type", label: "Source" },
        ]}
      />
      {accountType === "party" && id ? (
        <div className="toolbar" style={{ marginTop: 12 }}>
          <Link className="btn" to={`/lrs/new`}>
            Create LR
          </Link>
          <Link className="btn secondary" to="/collections/new">
            Record payment
          </Link>
        </div>
      ) : null}
    </section>
  );
}
