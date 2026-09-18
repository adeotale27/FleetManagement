import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import type { PageResult } from "../types";
import { Button, EmptyState, ErrorState, Input, Skeleton } from "../components/ui/primitives";
import { DataTable, StatusBadge } from "../components/tables/DataTable";

export function ResourcePage({
  title,
  resource,
  columns,
  createFields,
  primaryLabel = "Create",
}: {
  title: string;
  resource: string;
  columns: { key: string; label: string }[];
  createFields: { key: string; label: string; type?: string }[];
  primaryLabel?: string;
}) {
  const [search, setSearch] = useState("");
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);
  const nav = useNavigate();
  const q = useQuery({
    queryKey: [resource, search],
    queryFn: () => api<PageResult<Record<string, unknown>>>(`/${resource}?search=${encodeURIComponent(search)}`),
  });
  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await api(`/${resource}`, { method: "POST", body: JSON.stringify({ ...form, status: "active" }) });
      setOpen(false);
      await q.refetch();
    } catch (err) {
      setError((err as Error).message);
    }
  }
  if (q.isLoading) return <Skeleton />;
  if (q.isError) return <ErrorState message={(q.error as Error).message} onRetry={() => q.refetch()} />;
  const rows = q.data?.items || [];
  return (
    <section>
      <div className="page-header">
        <div>
          <h1 className="h1">{title}</h1>
          <p className="muted">{q.data?.total ?? 0} records</p>
        </div>
        <Button onClick={() => setOpen(true)}>{primaryLabel}</Button>
      </div>
      <div className="toolbar">
        <Input aria-label="Search" placeholder="Search" value={search} onChange={(e) => setSearch(e.target.value)} />
      </div>
      {rows.length === 0 ? (
        <EmptyState title={`No ${title.toLowerCase()} yet.`} action={<Button onClick={() => setOpen(true)}>{primaryLabel}</Button>} />
      ) : (
        <DataTable
          rows={rows as Record<string, unknown>[]}
          columns={columns.map((c) =>
            c.key === "status" ? { ...c, render: (r) => <StatusBadge status={String(r.status || "")} /> } : c
          )}
          onRow={(r) => r.id && nav(`/${resource}/${String(r.id)}`)}
        />
      )}
      {open ? (
        <form className="card grid" onSubmit={submit} style={{ marginTop: 16 }}>
          <h2 className="h1">{primaryLabel}</h2>
          {createFields.map((f) => (
            <Input key={f.key} label={f.label} type={f.type || "text"} value={form[f.key] || ""} onChange={(e) => setForm({ ...form, [f.key]: e.target.value })} required />
          ))}
          {error ? <ErrorState message={error} /> : null}
          <div className="toolbar">
            <Button type="submit">Save</Button>
            <Button type="button" variant="secondary" onClick={() => setOpen(false)}>
              Cancel
            </Button>
          </div>
        </form>
      ) : null}
    </section>
  );
}
