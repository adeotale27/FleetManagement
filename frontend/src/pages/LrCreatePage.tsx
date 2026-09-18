import { useMutation, useQuery } from "@tanstack/react-query";
import { useSearchParams } from "react-router-dom";
import { useState } from "react";
import { api } from "../api/client";
import { Button, ErrorState, Input, Select, Skeleton } from "../components/ui/primitives";
import type { PageResult } from "../types";

export function LrCreatePage() {
  const [params] = useSearchParams();
  const [form, setForm] = useState<Record<string, string>>({ trip_id: params.get("trip") || "", freight_type: "NOT_PAID" });
  const [q, setQ] = useState("");
  const trips = useQuery({ queryKey: ["trips"], queryFn: () => api<PageResult<Record<string, string>>>("/trips") });
  const parties = useQuery({ queryKey: ["parties", q], queryFn: () => api<PageResult<Record<string, string>>>(`/parties?search=${encodeURIComponent(q)}`) });
  const [err, setErr] = useState<string | null>(null);
  const mutate = useMutation({
    mutationFn: () =>
      api("/lrs", {
        method: "POST",
        body: JSON.stringify({
          trip_id: form.trip_id,
          sender_id: form.sender_id,
          create_sender: !form.sender_id && Boolean(form.sender_name),
          sender_name: form.sender_name,
          sender_mobile: form.sender_mobile,
          receiver_name: form.receiver_name,
          articles: form.articles,
          weight: form.weight ? Number(form.weight) : 0,
          freight_amount: form.freight_amount ? Number(form.freight_amount) : 0,
          freight_type: form.freight_type,
          hsn_code: form.hsn_code,
          eway_bill_no: form.eway_bill_no,
        }),
      }),
    onError: (e: Error) => setErr(e.message),
  });
  if (trips.isLoading) return <Skeleton />;
  const trip = trips.data?.items.find((t) => t.id === form.trip_id);
  return (
    <form
      className="grid"
      onSubmit={(e) => {
        e.preventDefault();
        mutate.mutate();
      }}
    >
      <h1 className="h1">New LR</h1>
      <Select label="Trip" value={form.trip_id} onChange={(e) => setForm({ ...form, trip_id: e.target.value })}>
        <option value="">Select trip</option>
        {(trips.data?.items || []).map((t) => (
          <option key={t.id} value={t.id}>
            {t.trip_number} {t.origin_name} → {t.destination_name}
          </option>
        ))}
      </Select>
      {trip ? (
        <div className="card">
          Vehicle {trip.vehicle_number} · Driver {trip.driver_name} · {trip.origin_name} → {trip.destination_name}
        </div>
      ) : null}
      <Input label="Search sender" value={q} onChange={(e) => setQ(e.target.value)} />
      <Select label="Sender" value={form.sender_id || ""} onChange={(e) => setForm({ ...form, sender_id: e.target.value })}>
        <option value="">Create new below</option>
        {(parties.data?.items || []).map((p) => (
          <option key={p.id} value={p.id}>
            {p.name} · {p.mobile} · {p.city}
          </option>
        ))}
      </Select>
      {!form.sender_id ? (
        <>
          <Input label="New sender name" value={form.sender_name || ""} onChange={(e) => setForm({ ...form, sender_name: e.target.value })} />
          <Input label="Mobile" value={form.sender_mobile || ""} onChange={(e) => setForm({ ...form, sender_mobile: e.target.value })} />
        </>
      ) : null}
      <Input label="Receiver" value={form.receiver_name || ""} onChange={(e) => setForm({ ...form, receiver_name: e.target.value })} required />
      <Input label="Goods description" value={form.articles || ""} onChange={(e) => setForm({ ...form, articles: e.target.value })} />
      <Input label="Weight" type="number" value={form.weight || ""} onChange={(e) => setForm({ ...form, weight: e.target.value })} />
      <Input label="Freight amount" type="number" value={form.freight_amount || ""} onChange={(e) => setForm({ ...form, freight_amount: e.target.value })} />
      <Select label="Freight type" value={form.freight_type} onChange={(e) => setForm({ ...form, freight_type: e.target.value })}>
        <option value="PAID">Paid</option>
        <option value="NOT_PAID">Not paid</option>
      </Select>
      <details className="optional">
        <summary>Optional details</summary>
        <Input label="HSN" value={form.hsn_code || ""} onChange={(e) => setForm({ ...form, hsn_code: e.target.value })} />
        <Input label="E-way bill" value={form.eway_bill_no || ""} onChange={(e) => setForm({ ...form, eway_bill_no: e.target.value })} />
      </details>
      {err ? <ErrorState message={err} /> : null}
      {mutate.isSuccess ? <p>LR created.</p> : null}
      <Button type="submit">Generate LR</Button>
    </form>
  );
}
