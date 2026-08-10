import { useState } from "react";
import * as recApi from "../api/recommendations";
import AnimeCard from "../components/AnimeCard";
import Loading from "../components/Loading";
import EmptyState from "../components/EmptyState";
import "./Discover.css";

const EXAMPLES = [
  "animes de ação com fantasia",
  "quero animes com arte visual dos anos 90",
  "algo como Code Geass, com protagonista inteligente",
];

export default function Discover() {
  const [description, setDescription] = useState("");
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [lastQuery, setLastQuery] = useState("");

  async function handleSubmit(e) {
    e.preventDefault();
    if (!description.trim()) return;
    setLoading(true);
    setLastQuery(description);
    try {
      const data = await recApi.recommendByDescription(description, 10);
      setResults(data.recommendations || []);
    } catch {
      setResults([]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="container">
      <section className="discover-hero">
        <span className="eyebrow">Busca por descrição</span>
        <h1 className="display" style={{ fontSize: "clamp(2.2rem, 5vw, 3.5rem)" }}>
          Descreva. <span>Descubra.</span>
        </h1>
        <p>
          Conte o que você quer assistir com suas próprias palavras — estética,
          tom, algo parecido com outro anime. Nós traduzimos isso em busca.
        </p>

        <form className="discover-form" onSubmit={handleSubmit}>
          <textarea
            placeholder="ex: quero um anime sombrio com protagonista anti-herói"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
          <button className="btn btn-primary" type="submit" disabled={loading}>
            {loading ? "…" : "Buscar"}
          </button>
        </form>

        <div className="discover-examples">
          {EXAMPLES.map((ex) => (
            <button key={ex} onClick={() => setDescription(ex)} type="button">
              {ex}
            </button>
          ))}
        </div>
      </section>

      <section style={{ paddingBottom: "4rem" }}>
        {loading ? (
          <Loading label="Interpretando seu pedido" />
        ) : results === null ? null : results.length === 0 ? (
          <EmptyState
            title="Nada encontrado"
            description={`Não achamos animes para "${lastQuery}". Tente descrever de outro jeito.`}
          />
        ) : (
          <div className="grid">
            {results.map((r) => (
              <AnimeCard
                key={r.id}
                anime={r}
                to={`/anime/${r.id}`}
              />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}