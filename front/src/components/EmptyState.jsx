import "./EmptyState.css";

export default function EmptyState({ title, description, action }) {
  return (
    <div className="empty-state">
      <div className="empty-state__mark" aria-hidden="true">無</div>
      <h3>{title}</h3>
      {description && <p>{description}</p>}
      {action}
    </div>
  );
}
