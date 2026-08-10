import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import "./Auth.css";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ username: "", password: "" });
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(form);
      navigate("/");
    } catch (err) {
      setError(
        err.response?.status === 401
          ? "Usuário ou senha incorretos."
          : "Não foi possível entrar. Tente novamente."
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card card">
        <h1 className="auth-card__brand display">
          Ani<span>Rank</span>
        </h1>
        <p className="auth-card__tagline">Sua lista. Suas notas. Suas recomendações.</p>

        <form onSubmit={handleSubmit}>
          <div className="field">
            <label htmlFor="username">Usuário</label>
            <input
              id="username"
              value={form.username}
              onChange={(e) => setForm({ ...form, username: e.target.value })}
              autoComplete="username"
              required
            />
          </div>
          <div className="field">
            <label htmlFor="password">Senha</label>
            <input
              id="password"
              type="password"
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              autoComplete="current-password"
              required
            />
          </div>

          {error && <p className="error-text">{error}</p>}

          <button className="btn btn-primary" type="submit" disabled={submitting}>
            {submitting ? "Entrando…" : "Entrar"}
          </button>
        </form>

        <p className="auth-card__switch">
          Ainda não tem conta? <Link to="/register">Criar conta</Link>
        </p>
      </div>
    </div>
  );
}
