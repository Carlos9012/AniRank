import { useEffect, useState } from "react";
import * as recApi from "../api/recommendations";
import ScoreBadge from "../components/ScoreBadge";
import AnimeCard from "../components/AnimeCard";
import Loading from "../components/Loading";
import EmptyState from "../components/EmptyState";
import { Link } from "react-router-dom";
import "./ForYou.css";

export default function ForYou() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    recApi.getPersonalized(10).then(setData).finally(() => setLoading(false));
  }, []);

  if (loading) return <Loading label="Analisando suas notas" />;

  const hasData = data && data.recommendations && data.recommendations.length > 0;

  return (
    <div className="container">
      <div className="foryou-header">
        <span className="eyebrow">Personalizado</span>
        <h1>
          Pra <span>Você</span>
        </h1>

        {data && data.total_rated > 0 && (
          <div className="foryou-stats">
            <div className="foryou-stat">
              <span className="eyebrow">Animes avaliados</span>
              <strong>{data.total_rated}</strong>
            </div>
            <div className="foryou-stat">
              <span className="eyebrow">Sua média</span>
              <strong>{data.average_score?.toFixed(1)}</strong>
            </div>
          </div>
        )}
      </div>

      <div style={{ paddingTop: "2rem", paddingBottom: "4rem" }}>
        {!hasData ? (
          <EmptyState
            title="Ainda sem recomendações"
            description="Avalie alguns animes na sua lista para o AniRank aprender seu gosto."
            action={<Link className="btn btn-primary" to="/">Ir para o catálogo</Link>}
          />
        ) : (
          <div className="grid">
            {data.recommendations.map((r) => (
              <div key={r.id} className="reco-card">
                <AnimeCard
                  anime={r}
                  to={`/anime/${r.id}`}
                />
                <p className="reco-card__reason">{r.reason}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}