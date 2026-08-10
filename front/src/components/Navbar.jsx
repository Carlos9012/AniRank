import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import "./Navbar.css";

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login");
  }

  return (
    <header className="navbar">
      <div className="container navbar__inner">
        <NavLink to="/" className="navbar__brand display">
          Ani<span>Rank</span>
        </NavLink>

        {user && (
          <nav className="navbar__links">
            <NavLink to="/" end className={navClass}>Catálogo</NavLink>
            <NavLink to="/discover" className={navClass}>Descobrir</NavLink>
            <NavLink to="/for-you" className={navClass}>Pra Você</NavLink>
            <NavLink to="/my-list" className={navClass}>Minha Lista</NavLink>
          </nav>
        )}

        <div className="navbar__user">
          {user ? (
            <>
              <span className="navbar__username mono">@{user.username}</span>
              <button className="btn btn-ghost" onClick={handleLogout}>Sair</button>
            </>
          ) : (
            <NavLink to="/login" className="btn btn-primary">Entrar</NavLink>
          )}
        </div>
      </div>
    </header>
  );
}

function navClass({ isActive }) {
  return isActive ? "navbar__link navbar__link--active" : "navbar__link";
}
