export function MapPin({
  lat,
  lng,
  onChange,
}: {
  lat?: string;
  lng?: string;
  onChange: (lat: string, lng: string) => void;
}) {
  const la = lat || "21.1458";
  const ln = lng || "79.0882";
  return (
    <div className="grid">
      <label className="field">
        Latitude
        <input className="input" value={lat || ""} onChange={(e) => onChange(e.target.value, lng || "")} />
      </label>
      <label className="field">
        Longitude
        <input className="input" value={lng || ""} onChange={(e) => onChange(lat || "", e.target.value)} />
      </label>
      <iframe
        title="Map pin"
        style={{ width: "100%", height: 180, border: 0, borderRadius: 8 }}
        src={`https://www.openstreetmap.org/export/embed.html?bbox=${Number(ln) - 0.05}%2C${Number(la) - 0.05}%2C${Number(ln) + 0.05}%2C${Number(la) + 0.05}&layer=mapnik&marker=${la}%2C${ln}`}
      />
    </div>
  );
}
