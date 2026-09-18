import { useMutation, useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { Button, ErrorState, Input, Select, Skeleton } from "../components/ui/primitives";
import type { PageResult } from "../types";

export function TripCreatePage() {
  const nav = useNavigate();
  const [kind, setKind] = useState<"indoor" | "outdoor">("indoor");
  const [form, setForm] = useState<Record<string, string>>({ journey_type: "one_way", vehicle_mode: "existing" });
  const [err, setErr] = useState<string | null>(null);
  const routes = useQuery({ queryKey: ["routes"], queryFn: () => api<PageResult<Record<string, string>>>("/routes") });
  const vehicles = useQuery({ queryKey: ["vehicles"], queryFn: () => api<PageResult<Record<string, string>>>("/vehicles?search=") });
  const drivers = useQuery({ queryKey: ["drivers"], queryFn: () => api<PageResult<Record<string, string>>>("/drivers") });
  const mutate = useMutation({
    mutationFn: () =>
      api("/trips", {
        method: "POST",
        body: JSON.stringify({
          trip_kind: kind,
          route_id: form.route_id,
          journey_type: form.journey_type,
          origin_name: form.origin_name,
          destination_name: form.destination_name,
          origin_lat: form.origin_lat,
          origin_lng: form.origin_lng,
          dest_lat: form.dest_lat,
          dest_lng: form.dest_lng,
          vehicle_mode: form.vehicle_mode,
          vehicle_id: form.vehicle_id,
          temp_vehicle_number: form.temp_vehicle_number,
          temp_vehicle_type: form.temp_vehicle_type,
          driver_id: form.driver_id,
          start_at: form.start_at,
          expected_return_at: form.expected_return_at,
          amount: form.amount ? Number(form.amount) : 0,
        }),
      }),
    onSuccess: () => nav("/trips"),
    onError: (e: Error) => setErr(e.message),
  });
  const selectedRoute = useMemo(() => routes.data?.items.find((r) => r.id === form.route_id), [routes.data, form.route_id]);
  if (routes.isLoading) return <Skeleton />;
  return (
    <form
      className="grid"
      onSubmit={(e) => {
        e.preventDefault();
        mutate.mutate();
      }}
    >
      <h1 className="h1">New trip</h1>
      <div className="toolbar">
        <Button type="button" variant={kind === "indoor" ? "primary" : "secondary"} onClick={() => setKind("indoor")}>
          Indoor trip
        </Button>
        <Button type="button" variant={kind === "outdoor" ? "primary" : "secondary"} onClick={() => setKind("outdoor")}>
          Outdoor trip
        </Button>
      </div>
      {kind === "indoor" ? (
        <Select label="Route" value={form.route_id || ""} onChange={(e) => setForm({ ...form, route_id: e.target.value })} required>
          <option value="">Select route</option>
          {(routes.data?.items || []).map((r) => (
            <option key={r.id} value={r.id}>
              {r.name}
            </option>
          ))}
        </Select>
      ) : (
        <>
          <Input label="Source" value={form.origin_name || ""} onChange={(e) => setForm({ ...form, origin_name: e.target.value })} required />
          <Input label="Destination" value={form.destination_name || ""} onChange={(e) => setForm({ ...form, destination_name: e.target.value })} required />
          <Input label="Source pin (lat,lng optional)" value={form.origin_lat || ""} onChange={(e) => setForm({ ...form, origin_lat: e.target.value })} />
        </>
      )}
      {selectedRoute ? (
        <p className="muted">
          {selectedRoute.origin_name} → {selectedRoute.destination_name}
        </p>
      ) : null}
      <Select label="Journey" value={form.journey_type} onChange={(e) => setForm({ ...form, journey_type: e.target.value })}>
        <option value="one_way">One way</option>
        <option value="round_trip">Round trip</option>
      </Select>
      <Input label="Start date & time" type="datetime-local" value={form.start_at || ""} onChange={(e) => setForm({ ...form, start_at: e.target.value })} required />
      {form.journey_type === "round_trip" ? (
        <Input label="Expected return" type="datetime-local" value={form.expected_return_at || ""} onChange={(e) => setForm({ ...form, expected_return_at: e.target.value })} required />
      ) : null}
      <Select label="Vehicle" value={form.vehicle_mode} onChange={(e) => setForm({ ...form, vehicle_mode: e.target.value })}>
        <option value="existing">Existing vehicle</option>
        <option value="temporary">Temporary vehicle</option>
      </Select>
      {form.vehicle_mode === "temporary" ? (
        <>
          <Input label="Temporary vehicle number" value={form.temp_vehicle_number || ""} onChange={(e) => setForm({ ...form, temp_vehicle_number: e.target.value })} required />
          <Input label="Type" value={form.temp_vehicle_type || "Truck"} onChange={(e) => setForm({ ...form, temp_vehicle_type: e.target.value })} />
        </>
      ) : (
        <Select label="Select vehicle" value={form.vehicle_id || ""} onChange={(e) => setForm({ ...form, vehicle_id: e.target.value })}>
          <option value="">Search / select</option>
          {(vehicles.data?.items || []).map((v) => (
            <option key={v.id} value={v.id}>
              {v.vehicle_number} ({v.status})
            </option>
          ))}
        </Select>
      )}
      <Select label="Driver" value={form.driver_id || ""} onChange={(e) => setForm({ ...form, driver_id: e.target.value })}>
        <option value="">Select driver</option>
        {(drivers.data?.items || []).map((d) => (
          <option key={d.id} value={d.id}>
            {d.name} {d.mobile}
          </option>
        ))}
      </Select>
      <details className="optional">
        <summary>Optional details</summary>
        <Input label="Trip amount" type="number" value={form.amount || ""} onChange={(e) => setForm({ ...form, amount: e.target.value })} />
      </details>
      {err ? <ErrorState message={err} /> : null}
      <Button type="submit" disabled={mutate.isPending}>
        Create trip
      </Button>
    </form>
  );
}
