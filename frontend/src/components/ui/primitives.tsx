import type { ButtonHTMLAttributes, InputHTMLAttributes, ReactNode } from "react";

export function Button({ variant = "primary", ...props }: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary" | "secondary" | "danger" | "ghost" }) {
  return <button {...props} className={`btn ${variant === "primary" ? "" : variant} ${props.className || ""}`} />;
}

export function Input(props: InputHTMLAttributes<HTMLInputElement> & { label?: string }) {
  const { label, id, ...rest } = props;
  return (
    <div className="field">
      {label ? <label htmlFor={id}>{label}</label> : null}
      <input id={id} className="input" {...rest} />
    </div>
  );
}

export function Select({ label, id, children, ...rest }: InputHTMLAttributes<HTMLSelectElement> & { label?: string; children: ReactNode }) {
  return (
    <div className="field">
      {label ? <label htmlFor={id}>{label}</label> : null}
      <select id={id} className="input" {...rest}>
        {children}
      </select>
    </div>
  );
}

export function Badge({ children, tone = "info" }: { children: ReactNode; tone?: "ok" | "warn" | "bad" | "info" }) {
  return <span className={`badge ${tone}`}>{children}</span>;
}

export function StatCard({ label, value, onClick }: { label: string; value: string | number; onClick?: () => void }) {
  return (
    <button type="button" className="card" onClick={onClick} style={{ textAlign: "left", cursor: onClick ? "pointer" : "default" }}>
      <div className="stat-label">{label}</div>
      <div className="stat-value">{value}</div>
    </button>
  );
}

export function EmptyState({ title, action }: { title: string; action?: ReactNode }) {
  return (
    <div className="state">
      <p>{title}</p>
      {action}
    </div>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="state">
      <p>{message}</p>
      {onRetry ? (
        <Button type="button" onClick={onRetry}>
          Retry
        </Button>
      ) : null}
    </div>
  );
}

export function Skeleton() {
  return <div className="card state">Loading…</div>;
}

export function PermissionDenied() {
  return <div className="state">You do not have permission to view this page.</div>;
}

export function Modal({ title, children, onClose }: { title: string; children: ReactNode; onClose: () => void }) {
  return (
    <div className="drawer" role="dialog" aria-modal="true" aria-label={title} onClick={onClose}>
      <div className="panel" onClick={(e) => e.stopPropagation()}>
        <div className="page-header">
          <h2 className="h1">{title}</h2>
          <Button variant="ghost" onClick={onClose} aria-label="Close">
            Close
          </Button>
        </div>
        {children}
      </div>
    </div>
  );
}
