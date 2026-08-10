import "./ScoreBadge.css";

export default function ScoreBadge({ score, size = "md" }) {
  if (score === null || score === undefined) return null;
  return (
    <div className={`score-badge score-badge--${size}`} aria-label={`Nota ${score}`}>
      <span className="score-badge__value mono">{Number(score).toFixed(1)}</span>
    </div>
  );
}
