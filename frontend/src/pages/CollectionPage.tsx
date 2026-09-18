import { useMutation, useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "../api/client";
import { Button, ErrorState, Input, Select, Skeleton } from "../components/ui/primitives";
import type { PageResult } from "../types";

export function CollectionPage() {
  const [q, setQ] = useState("");
  const [form, setForm] = useState<Record<string, string>>({ payment_mode: "Cash" });
  const parties = useQuery({ queryKey: ["parties", q], queryFn: () => api<PageResult<Record<string, string>>>(`/parties?search=${encodeURIComponent(q)}`) });
  const [err, setErr] = useState<string | null>(null);
  const [result, setResult] = useState<{ outstanding?: number; receipt_number?: string } | null>(null);
  const mutate = useMutation({
    mutationFn: () =>
      api<{ outstanding: number; receipt_number: string }>("/finance/collections", {
        method: "POST",
        body: JSON.stringify({
          party_id: form.party_id,
          amount: Number(form.amount),
          payment_mode: form.payment_mode,
          remarks: form.remarks,
          deewanji_id: form.deewanji_id,
        }),
      }),
    onSuccess: setResult,
    onError: (e: Error) => setErr(e.message),
  });
  if (parties.isLoading) return <Skeleton />;
  return (
    <form
      className="grid"
      onSubmit={(e) => {
        e.preventDefault();
        mutate.mutate();
      }}
    >
      <h1 className="h1">Record collection</h1>
      <Input label="Search party" value={q} onChange={(e) => setQ(e.target.value)} />
      <Select label="Party" value={form.party_id || ""} onChange={(e) => setForm({ ...form, party_id: e.target.value })} required>
        <option value="">Select</option>
        {(parties.data?.items || []).map((p) => (
          <option key={p.id} value={p.id}>
            {p.name} · {p.mobile}
          </option>
        ))}
      </Select>
      <Input label="Amount" type="number" value={form.amount || ""} onChange={(e) => setForm({ ...form, amount: e.target.value })} required />
      <Select label="Payment mode" value={form.payment_mode} onChange={(e) => setForm({ ...form, payment_mode: e.target.value })}>
        <option>Cash</option>
        <option>UPI</option>
        <option>Bank</option>
        <option>Cheque</option>
      </Select>
      <Input label="Remarks" value={form.remarks || ""} onChange={(e) => setForm({ ...form, remarks: e.target.value })} />
      {err ? <ErrorState message={err} /> : null}
      {result ? (
        <div className="card">
          Collection successful. Receipt {result.receipt_number}. Remaining outstanding {result.outstanding}.
        </div>
      ) : null}
      <Button type="submit">Save collection</Button>
    </form>
  );
}
