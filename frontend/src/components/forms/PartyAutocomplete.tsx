import { useEffect, useState } from "react";
import { api } from "../../api/client";

type PartyHit = { id: string; name: string; mobile?: string; city?: string; outstanding?: number };

export function PartyAutocomplete({
  onSelect,
}: {
  onSelect: (party: PartyHit | null, createName?: string) => void;
}) {
  const [q, setQ] = useState("");
  const [items, setItems] = useState<PartyHit[]>([]);
  useEffect(() => {
    if (q.length < 2) {
      setItems([]);
      return;
    }
    const t = setTimeout(() => {
      api<{ items: PartyHit[] }>(`/parties/autocomplete?q=${encodeURIComponent(q)}`)
        .then((d: { items: PartyHit[] }) => setItems(d.items || []))
        .catch(() => setItems([]));
    }, 200);
    return () => clearTimeout(t);
  }, [q]);
  return (
    <div className="field">
      <label>Sender</label>
      <input className="input" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Type name or mobile" aria-autocomplete="list" />
      {items.length > 0 ? (
        <div className="panel" style={{ padding: 0 }}>
          {items.map((p) => (
            <button
              type="button"
              key={p.id}
              className="btn ghost"
              style={{ width: "100%", justifyContent: "flex-start" }}
              onClick={() => {
                onSelect(p);
                setQ(`${p.name} · ${p.mobile || ""}`);
                setItems([]);
              }}
            >
              {p.name} · {p.mobile} · {p.city} · outstanding {p.outstanding ?? 0}
            </button>
          ))}
        </div>
      ) : null}
      {q.length > 2 && items.length === 0 ? (
        <button type="button" className="btn secondary" onClick={() => onSelect(null, q)}>
          Create new party “{q}”
        </button>
      ) : null}
    </div>
  );
}
