import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import "./Auth.css";

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: "", username: "", password: "" });
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await register(form);
      navigate("/");
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(typeof detail === "string" ? detail : "Não foi possível criar a conta.");
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
        <p className="auth-card__tagline">Crie sua conta para começar a trackear.</p>

        <form onSubmit={handleSubmit}>
          <div className="field">
            <label htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              autoComplete="email"
              required
            />
          </div>
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
              autoComplete="new-password"
              required
            />
          </div>

          {error && <p className="error-text">{error}</p>}

          <button className="btn btn-primary" type="submit" disabled={submitting}>
            {submitting ? "Criando…" : "Criar conta"}
          </button>
        </form>

        <p className="auth-card__switch">
          Já tem conta? <Link to="/login">Entrar</Link>
        </p>
      </div>
    </div>
  );
}
