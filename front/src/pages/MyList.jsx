// src/pages/MyList.jsx
import { useEffect, useState } from "react";
import * as listApi from "../api/list";
import AnimeCard from "../components/AnimeCard";
import Loading from "../components/Loading";
import EmptyState from "../components/EmptyState";
import { Link } from "react-router-dom";
import "./MyList.css";

const TABS = [
  { value: "all", label: "Tudo" },
  { value: "watching", label: "Assistindo" },
  { value: "completed", label: "Completo" },
  { value: "planned", label: "Planejado" },
  { value: "dropped", label: "Abandonado" },
];

export default function MyList() {
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState("all");

  useEffect(() => {
    listApi.getMyList().then(setEntries).finally(() => setLoading(false));
  }, []);
  console.log("📦 Lista de animes recebida:", entries);
  const filtered = tab === "all" ? entries : entries.filter((e) => e.status === tab);

  return (
    <div className="container">
      <div className="mylist-header">
        <span className="eyebrow">Sua coleção</span>
        <h1>
          Minha <span>Lista</span>
        </h1>
      </div>

      <div className="status-tabs">
        {TABS.map((t) => (
          <button
            key={t.value}
            className={`status-tab ${tab === t.value ? "status-tab--active" : ""}`}
            onClick={() => setTab(t.value)}
          >
            {t.label} {t.value !== "all" && `(${entries.filter((e) => e.status === t.value).length})`}
          </button>
        ))}
      </div>

      {loading ? (
        <Loading label="Carregando sua lista" />
      ) : filtered.length === 0 ? (
        <EmptyState
          title="Nada por aqui ainda"
          description="Adicione animes do catálogo para começar a montar sua lista."
          action={<Link className="btn btn-primary" to="/">Ir para o catálogo</Link>}
        />
      ) : (
        <div className="grid" style={{ paddingBottom: "3rem" }}>
          {filtered.map((entry) => (
            <AnimeCard
              key={entry.id}
              anime={entry}
              score={entry.score}
              to={`/anime/${entry.external_id}`} 
            />
          ))}
        </div>
      )}
    </div>
  );
}