import { Link } from "react-router-dom";
import ScoreBadge from "./ScoreBadge";
import "./AnimeCard.css";

export default function AnimeCard({ anime, score, statusLabel, to }) {
  const title = anime.title_english || anime.title || anime.anime_title;
  const cover = anime.cover || anime.anime_cover;
  const year = anime.year;
  const genres = anime.genres || [];

  const content = (
    <>
      <div className="anime-card__cover">
        {cover ? (
          <img src={cover} alt="" loading="lazy" />
        ) : (
          <div className="anime-card__cover-fallback" aria-hidden="true" />
        )}
        {score != null && (
          <div className="anime-card__badge">
            <ScoreBadge score={score} size="sm" />
          </div>
        )}
        {statusLabel && <span className="anime-card__status">{statusLabel}</span>}
      </div>
      <div className="anime-card__body">
        <h4 className="anime-card__title" title={title}>{title}</h4>
        <div className="anime-card__meta">
          {year && <span className="mono">{year}</span>}
          {genres.slice(0, 2).map((g) => (
            <span key={g} className="anime-card__genre">{g}</span>
          ))}
        </div>
      </div>
    </>
  );

  if (to) {
    return (
      <Link to={to} className="anime-card">
        {content}
      </Link>
    );
  }
  return <div className="anime-card">{content}</div>;
}