import { useEffect, useState, useCallback, useRef } from "react";
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

  const searchTimeout = useRef(null);

  const loadCatalog = useCallback((p) => {
    setLoading(true);
    animesApi
      .listAnimes({ skip: p * PAGE_SIZE, limit: PAGE_SIZE })
      .then(setCatalog)
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => loadCatalog(page), [page, loadCatalog]);

  useEffect(() => {
    if (searchTimeout.current) {
      clearTimeout(searchTimeout.current);
    }

    if (!query.trim()) {
      setSearchResults(null);
      setSearching(false);
      return;
    }

    setSearching(true);

    searchTimeout.current = setTimeout(async () => {
      try {
        const data = await animesApi.searchAnilist(query, 8);
        setSearchResults(data.results);
      } catch (error) {
        console.error("Erro na busca:", error);
        setSearchResults([]);
      } finally {
        setSearching(false);
      }
    }, 500);

    return () => clearTimeout(searchTimeout.current);
  }, [query]);

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

  function closePreview() {
    setPreview(null);
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

        <div className="catalog-search">
          <input
            placeholder="Buscar por título — ex: Naruto"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          {searching && <span className="search-spinner">⌛</span>}
        </div>

        {searchResults && (
          <div className="search-results">
            {searchResults.length === 0 ? (
              <p style={{ color: "var(--ink-faint)", fontSize: "0.85rem" }}>
                Nada encontrado no AniList para "{query}".
              </p>
            ) : (
              searchResults.map((r) => (
                <div
                  className="search-result search-result--clickable"
                  key={r.external_id}
                  role="button"
                  tabIndex={0}
                  onClick={() => navigate(`/anime/${r.external_id}`)}
                  onKeyDown={(e) => e.key === "Enter" && navigate(`/anime/${r.external_id}`)}
                >
                  {r.cover && <img src={r.cover} alt="" />}
                  <div className="search-result__info">
                    <strong>{r.title_english || r.title}</strong>
                    <span>
                      {r.year || "—"} · {(r.genres || []).slice(0, 3).join(", ")}
                    </span>
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
              ))
            )}
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
    </div>
  );
}