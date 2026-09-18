import { Link } from "react-router-dom";
import { Badge } from "../ui/primitives";

type Row = Record<string, unknown> & { id?: string };
type Col = { key: string; label: string; render?: (row: Row) => React.ReactNode };

export function DataTable({
  rows,
  columns,
  onRow,
}: {
  rows: Row[];
  columns: Col[];
  onRow?: (row: Row) => void;
}) {
  return (
    <>
      <div className="table-wrap">
        <table className="data">
          <thead>
            <tr>
              {columns.map((c) => (
                <th key={c.key}>{c.label}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, i) => (
              <tr key={row.id || i} onClick={() => onRow?.(row)} style={{ cursor: onRow ? "pointer" : "default" }}>
                {columns.map((c) => (
                  <td key={c.key}>{c.render ? c.render(row) : String(row[c.key] ?? "—")}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="grid" style={{ gap: 8, marginTop: 8 }}>
        {rows.map((row, i) => (
          <article className="mobile-card" key={row.id || i} onClick={() => onRow?.(row)}>
            {columns.slice(0, 4).map((c) => (
              <div key={c.key} style={{ marginBottom: 6 }}>
                <div className="muted">{c.label}</div>
                <div>{c.render ? c.render(row) : String(row[c.key] ?? "—")}</div>
              </div>
            ))}
          </article>
        ))}
      </div>
    </>
  );
}

export function StatusBadge({ status }: { status?: string }) {
  const tone = !status ? "info" : ["active", "available", "completed", "closed", "settled", "ok"].includes(status) ? "ok" : ["cancelled", "expired", "inactive"].includes(status) ? "bad" : "warn";
  return <Badge tone={tone}>{status || "—"}</Badge>;
}

export function DetailLink({ to, children }: { to: string; children: React.ReactNode }) {
  return <Link to={to}>{children}</Link>;
}
