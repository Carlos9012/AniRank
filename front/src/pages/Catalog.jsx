import { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import * as animesApi from "../api/animes";
import AnimeCard from "../components/AnimeCard";
import Loading from "../components/Loading";
import EmptyState from "../components/EmptyState";
import "./Catalog.css";

const PAGE_SIZE = 18;

export default function Catalog() {
  const [catalog, setCatalog] = useState({ results: [], total: 0 });
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(0);

  const [query, setQuery] = useState("");
  const [searchResults, setSearchResults] = useState(null);
  const [searching, setSearching] = useState(false);
  const [importingId, setImportingId] = useState(null);
  const [preview, setPreview] = useState(null);
  const navigate = useNavigate();

  const loadCatalog = useCallback((p) => {
    setLoading(true);
    animesApi
      .listAnimes({ skip: p * PAGE_SIZE, limit: PAGE_SIZE })
      .then(setCatalog)
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => loadCatalog(page), [page, loadCatalog]);

  async function handleSearch(e) {
    e.preventDefault();
    if (!query.trim()) return;
    setSearching(true);
    try {
      const data = await animesApi.searchAnilist(query, 8);
      setSearchResults(data.results);
    } finally {
      setSearching(false);
    }
  }

  async function handleCardClick(result) {
    setPreview({ loading: true, data: null, error: null, base: result });
    try {
      const data = await animesApi.searchAnilist(result.title, 5);
      const exact =
        data.results.find((r) => r.external_id === result.external_id) || data.results[0];
      setPreview({ loading: false, data: exact || result, error: null, base: result });
    } catch {
      setPreview({ loading: false, data: null, error: "Não foi possível buscar no AniList agora.", base: result });
    }
  }

  function closePreview() {
    setPreview(null);
  }

  async function handleImport(externalId) {
    setImportingId(externalId);
    try {
      await animesApi.importAnime(externalId);
      setSearchResults(null);
      setQuery("");
      loadCatalog(0);
      setPage(0);
    } finally {
      setImportingId(null);
    }
  }

  const totalPages = Math.ceil(catalog.total / PAGE_SIZE);

  return (
    <div>
      <section className="catalog-hero container">
        <span className="eyebrow">Catálogo</span>
        <h1>
          Encontre seu <span>próximo</span> obcecante
        </h1>
        <p>
          Busque qualquer anime no AniList e traga para o seu catálogo, ou
          explore o que a comunidade já importou.
        </p>

        <form className="catalog-search" onSubmit={handleSearch}>
          <input
            placeholder="Buscar por título — ex: Naruto"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <button className="btn btn-primary" type="submit" disabled={searching}>
            {searching ? "…" : "Buscar"}
          </button>
        </form>

        {searchResults && (
          <div className="search-results">
            {searchResults.length === 0 && (
              <p style={{ color: "var(--ink-faint)", fontSize: "0.85rem" }}>
                Nada encontrado no AniList para "{query}".
              </p>
            )}
            {searchResults.map((r) => (
              <div
                className="search-result search-result--clickable"
                key={r.external_id}
                role="button"
                tabIndex={0}
                onClick={() => handleCardClick(r)}
                onKeyDown={(e) => e.key === "Enter" && handleCardClick(r)}
              >
                {r.cover && <img src={r.cover} alt="" />}
                <div className="search-result__info">
                  <strong>{r.title_english || r.title}</strong>
                  <span>{r.year || "—"} · {(r.genres || []).slice(0, 3).join(", ")}</span>
                </div>
                <button
                  className="btn btn-ghost"
                  disabled={r.already_in_db || importingId === r.external_id}
                  onClick={(e) => {
                    e.stopPropagation();
                    handleImport(r.external_id);
                  }}
                >
                  {r.already_in_db
                    ? "Já no catálogo"
                    : importingId === r.external_id
                    ? "Importando…"
                    : "Importar"}
                </button>
              </div>
            ))}
          </div>
        )}
      </section>

      <div className="container">
        <div className="section-heading">
          <div>
            <span className="eyebrow">{catalog.total} no total</span>
            <h2 style={{ fontSize: "1.6rem" }}>Catálogo interno</h2>
          </div>
        </div>

        {loading ? (
          <Loading label="Carregando catálogo" />
        ) : catalog.results.length === 0 ? (
          <EmptyState
            title="Catálogo vazio"
            description="Busque um anime acima e importe para começar a preencher o catálogo."
          />
        ) : (
          <>
            <div className="grid">
              {catalog.results.map((anime) => (
                <AnimeCard
                  key={anime.id}
                  anime={anime}
                  to={`/anime/${anime.external_id}`}
                />
              ))}
            </div>

            {totalPages > 1 && (
              <div className="pagination">
                <button
                  className="btn btn-ghost"
                  disabled={page === 0}
                  onClick={() => setPage((p) => p - 1)}
                >
                  ← Anterior
                </button>
                <span className="mono" style={{ alignSelf: "center", color: "var(--ink-faint)" }}>
                  {page + 1} / {totalPages}
                </span>
                <button
                  className="btn btn-ghost"
                  disabled={page + 1 >= totalPages}
                  onClick={() => setPage((p) => p + 1)}
                >
                  Próxima →
                </button>
              </div>
            )}
          </>
        )}
      </div>

      {preview && (
        <div className="preview-backdrop" onClick={closePreview}>
          <div className="preview-modal card" onClick={(e) => e.stopPropagation()}>
            <button className="preview-modal__close" onClick={closePreview} aria-label="Fechar">
              ×
            </button>

            {preview.loading ? (
              <Loading label="Buscando no AniList" />
            ) : preview.error ? (
              <p className="error-text">{preview.error}</p>
            ) : (
              <div className="preview-modal__body">
                {preview.data.cover && <img src={preview.data.cover} alt="" />}
                <div>
                  <h3 style={{ textTransform: "none", letterSpacing: 0, fontSize: "1.3rem" }}>
                    {preview.data.title_english || preview.data.title}
                  </h3>
                  <p className="mono" style={{ color: "var(--ink-faint)", marginTop: "0.4rem" }}>
                    {preview.data.year || "—"} · {preview.data.episodes ?? "?"} ep · {preview.data.status}
                  </p>
                  <div className="detail-genres" style={{ marginTop: "0.8rem" }}>
                    {(preview.data.genres || []).map((g) => <span key={g}>{g}</span>)}
                  </div>
                  <button
                    className="btn btn-primary"
                    style={{ marginTop: "1.25rem" }}
                    disabled={preview.data.already_in_db || importingId === preview.data.external_id}
                    onClick={() => handleImport(preview.data.external_id)}
                  >
                    {preview.data.already_in_db ? "Já no catálogo" : "Importar para o catálogo"}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}