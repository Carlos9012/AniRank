export default function Loading({ label = "Carregando" }) {
  return (
    <div style={{ display: "flex", justifyContent: "center", padding: "3rem" }}>
      <span className="eyebrow">{label}…</span>
    </div>
  );
}
