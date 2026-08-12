// src/pages/AnimeDetail.jsx
import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { useForm, Controller } from "react-hook-form";
import * as animesApi from "../api/animes";
import * as listApi from "../api/list";
import * as recApi from "../api/recommendations";
import ScoreBadge from "../components/ScoreBadge";
import AnimeCard from "../components/AnimeCard";
import Loading from "../components/Loading";
import { cleanHtml } from "../utils/stringUtils";
import "./AnimeDetail.css";

const STATUS_LABELS = {
  watching: "Assistindo",
  completed: "Completo",
  planned: "Planejado",
  dropped: "Abandonado",
};

export default function AnimeDetail() {
  const { id } = useParams(); // external_id
  const [anime, setAnime] = useState(null);
  const [similar, setSimilar] = useState([]);
  const [loadingSimilar, setLoadingSimilar] = useState(true);
  const [listEntry, setListEntry] = useState(null);
  const [isSaving, setIsSaving] = useState(false);
  const [isRemoving, setIsRemoving] = useState(false);

  const { control, watch, setValue, getValues } = useForm({
    defaultValues: {
      status: "planned",
      score: "",
    },
  });

  const formValues = watch();

  useEffect(() => {
    if (!listEntry) return;

    const { status, score } = formValues;

    const hasChanged =
      status !== listEntry.status ||
      (score !== "" ? Number(score) : null) !== listEntry.score;

    if (!hasChanged) return;

    const timer = setTimeout(() => {
      handleAutoSave();
    }, 500);

    return () => clearTimeout(timer);
  }, [formValues, listEntry]);

  useEffect(() => {
    setAnime(null);
    console.log("🔍 Buscando external_id:", id);

    animesApi.getAnimeByExternalId(id)
      .then((data) => {
        console.log("📦 Dados recebidos:", data);
        setAnime(data);

        if (data.is_in_list) {
          setListEntry({
            status: data.user_status,
            score: data.user_score,
            notes: data.user_notes,
          });
          setValue("status", data.user_status);
          setValue("score", data.user_score ?? "");
        } else {
          setListEntry(null);
          setValue("status", "planned");
          setValue("score", "");
        }
      })
      .catch((err) => {
        console.error("❌ Erro ao buscar anime:", err);
      });
  }, [id]);

  useEffect(() => {
    if (!anime) return;
    setLoadingSimilar(true);
    recApi
      .recommendByAnime(anime.external_id, { limit: 6 })
      .then((data) => setSimilar(data.recommendations || []))
      .catch(() => setSimilar([]))
      .finally(() => setLoadingSimilar(false));
  }, [anime]);

  async function handleAutoSave() {
    if (isSaving) return;

    setIsSaving(true);
    const { status, score } = getValues();

    try {
      const payload = {
        anime_id: Number(id),
        status,
        score: score === "" ? null : Number(score),
        notes: listEntry?.notes || "",
      };

      const updated = await listApi.updateListEntry(id, payload);
      setListEntry(updated);
    } catch (error) {
      console.error("Erro ao salvar:", error);
    } finally {
      setIsSaving(false);
    }
  }

  async function handleAdd() {
    if (isSaving) return;

    setIsSaving(true);
    const { status, score } = getValues();

    try {
      const payload = {
        anime_id: Number(id),
        status,
        score: score === "" ? null : Number(score),
      };

      const saved = await listApi.addToList(payload);
      setListEntry(saved);
    } catch (error) {
      console.error("Erro ao adicionar:", error);
    } finally {
      setIsSaving(false);
    }
  }

  async function handleRemove() {
    if (isRemoving) return;

    setIsRemoving(true);
    try {
      await listApi.removeFromList(anime.id);
      setListEntry(null);
      setValue("status", "planned");
      setValue("score", "");
    } catch (error) {
      console.error("Erro ao remover:", error);
    } finally {
      setIsRemoving(false);
    }
  }

  if (!anime) return <Loading label="Carregando anime" />;

  const isInList = listEntry !== null;
  const { status, score } = getValues();

  const hasChanges =
    isInList &&
    (status !== listEntry.status ||
      (score !== "" ? Number(score) : null) !== listEntry.score);

  return (
    <div>
      <section className="detail-hero">
        {anime.cover && (
          <div
            className="detail-hero__backdrop"
            style={{ backgroundImage: `url(${anime.cover})` }}
          />
        )}
        <div className="container detail-layout">
          {anime.cover && (
            <img className="detail-cover" src={anime.cover} alt="" />
          )}

          <div>
            <div className="detail-title-row">
              <h1>{anime.title_english || anime.title}</h1>
              {listEntry?.score != null && (
                <ScoreBadge score={listEntry.score} size="lg" />
              )}
            </div>

            <div className="detail-meta">
              {anime.year && <span className="mono">{anime.year}</span>}
              {anime.episodes && <span>{anime.episodes} episódios</span>}
              {anime.status && <span>{anime.status}</span>}
            </div>

            <div className="detail-genres">
              {(anime.genres || []).map((g) => (
                <span key={g}>{g}</span>
              ))}
            </div>

            {anime.synopsis && (
              <p className="detail-synopsis" style={{ whiteSpace: "pre-line" }}>
                {cleanHtml(anime.synopsis)}
              </p>
            )}

            <div className="detail-actions">
              <Controller
                name="status"
                control={control}
                render={({ field }) => (
                  <select
                    {...field}
                    disabled={!isInList && isSaving}
                  >
                    {Object.entries(STATUS_LABELS).map(([value, label]) => (
                      <option key={value} value={value}>
                        {label}
                      </option>
                    ))}
                  </select>
                )}
              />

              <div className="detail-score-input">
                <label htmlFor="score" className="eyebrow">Nota</label>
                <Controller
                  name="score"
                  control={control}
                  render={({ field }) => (
                    <input
                      {...field}
                      id="score"
                      type="number"
                      min="0"
                      max="10"
                      step="0.5"
                      placeholder="—"
                      disabled={!isInList && isSaving}
                    />
                  )}
                />
              </div>

              {!isInList ? (
                <button className="btn btn-primary" onClick={handleAdd} disabled={isSaving}>
                  {isSaving ? "Adicionando…" : "Adicionar à lista"}
                </button>
              ) : (
                <div className="detail-actions-buttons">
                  <button className="btn btn-danger" onClick={handleRemove} disabled={isRemoving}>
                    {isRemoving ? "Removendo…" : "Remover da lista"}
                  </button>
                  <div className="detail-auto-save-status">
                    {isSaving ? (
                      <span className="text-muted">💾 Salvando…</span>
                    ) : null}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </section>

      <section className="container" style={{ paddingBottom: "4rem" }}>
        <div className="section-heading">
          <div>
            <span className="eyebrow">Baseado em similaridade</span>
            <h2 style={{ fontSize: "1.6rem" }}>Se você curtiu isso</h2>
          </div>
        </div>

        {loadingSimilar ? (
          <Loading label="Calculando semelhanças" />
        ) : similar.length === 0 ? (
          <p style={{ color: "var(--ink-faint)" }}>
            Sem recomendações disponíveis para este título ainda.
          </p>
        ) : (
          <div className="grid">
            {similar.map((s) => (
              <AnimeCard
                key={s.id}
                anime={s}
                to={`/anime/${s.id}`}
              />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}