import React, { useState, useEffect } from "react";
import {
  LayoutDashboard,
  Upload,
  ChartNoAxesCombined,
  CalendarDays,
  LogOut,
  Menu,
} from "lucide-react";
import { api, send, title } from "../services/api";
import { Alert, Busy } from "../components/Common";
import Dashboard from "../features/dashboard/Dashboard";
import Catalog from "../features/master-data/Catalog";
import Bulk from "../features/bulk-management/Bulk";
import Forecasts from "../features/forecasting/Forecasts";
import Scheduling from "../features/scheduling/Scheduling";
export default function App() {
  const [session, setSession] = useState(null),
    [schema, setSchema] = useState({}),
    [page, setPage] = useState(location.hash.slice(1) || "dashboard"),
    [error, setError] = useState(""),
    [credentials, setCredentials] = useState({ username: "", password: "" }),
    [menu, setMenu] = useState(false);
  useEffect(() => {
    api("session/")
      .then(setSession)
      .catch((e) => setError(e.message));
  }, []);
  useEffect(() => {
    if (session?.authenticated)
      api("schema/")
        .then(setSchema)
        .catch((e) => setError(e.message));
  }, [session]);
  useEffect(() => {
    const fn = () => setPage(location.hash.slice(1) || "dashboard");
    window.addEventListener("hashchange", fn);
    return () => window.removeEventListener("hashchange", fn);
  }, []);
  const navigate = (p) => {
    location.hash = p;
    setPage(p);
    setMenu(false);
  };
  if (!session)
    return (
      <main className="login">
        <Alert>{error}</Alert>
        <Busy>Connecting to Timble…</Busy>
      </main>
    );
  if (!session.authenticated)
    return (
      <main className="login">
        <form
          className="panel padded"
          onSubmit={async (e) => {
            e.preventDefault();
            setError("");
            try {
              setSession(await send("session/", credentials));
            } catch (e) {
              setError(e.message);
            }
          }}
        >
          <div className="brand">
            <img src="/logo.svg" alt="" />
            <strong>TIMBLE</strong>
          </div>
          <p className="eyebrow">ACADEMIC PLANNING WORKSPACE</p>
          <h1>Welcome back.</h1>
          <p>Sign in to manage your institution’s academic plans.</p>
          <Alert>{error}</Alert>
          <label>
            Username
            <input
              autoComplete="username"
              required
              value={credentials.username}
              onChange={(e) =>
                setCredentials({ ...credentials, username: e.target.value })
              }
            />
          </label>
          <label>
            Password
            <input
              type="password"
              autoComplete="current-password"
              required
              value={credentials.password}
              onChange={(e) =>
                setCredentials({ ...credentials, password: e.target.value })
              }
            />
          </label>
          <button>Sign in</button>
        </form>
      </main>
    );
  const primary = [
    ["dashboard", "Overview", LayoutDashboard],
    ["bulk", "Bulk management", Upload],
    ["forecast", "Forecasting", ChartNoAxesCombined],
    ["schedule", "Scheduling studio", CalendarDays],
  ];
  return (
    <div className="shell">
      <aside className={menu ? "open" : ""}>
        <a className="brand" href="#dashboard">
          <img src="/logo.svg" alt="Timble logo" />
          <strong>
            TIMBLE<small>Academic planning</small>
          </strong>
        </a>
        <nav aria-label="Main navigation">
          <span className="nav-label">WORKSPACE</span>
          {primary.map(([p, label, Icon]) => (
            <button
              key={p}
              className={page === p ? "active" : ""}
              onClick={() => navigate(p)}
            >
              <Icon size={18} />
              {label}
            </button>
          ))}
          <span className="nav-label">MASTER DATA</span>
          {Object.keys(schema).map((p) => (
            <button
              key={p}
              className={page === p ? "active" : ""}
              onClick={() => navigate(p)}
            >
              <span className="nav-dot" />
              {title(p)}
            </button>
          ))}
        </nav>
        <div className="sidebar-foot">
          <span className="status-dot" />
          Timble V2 · Pyomo + HiGHS
        </div>
      </aside>
      <div className="workspace">
        <header className="topbar">
          <div>
            <button
              className="mobile icon"
              aria-label="Toggle navigation"
              onClick={() => setMenu(!menu)}
            >
              <Menu />
            </button>
            <span>Workspace</span>
            <span className="muted"> / </span>
            <strong>{title(page)}</strong>
          </div>
          <div className="user">
            <span className="avatar">
              {session.username.slice(0, 1).toUpperCase()}
            </span>
            {session.username}
            <button
              className="icon"
              aria-label="Sign out"
              onClick={async () => {
                try {
                  setSession(await api("session/", { method: "DELETE" }));
                } catch (e) {
                  setError(e.message);
                }
              }}
            >
              <LogOut size={17} />
            </button>
          </div>
        </header>
        <main className="content">
          <Alert>{error}</Alert>
          {page === "dashboard" ? (
            <Dashboard navigate={navigate} />
          ) : page === "bulk" ? (
            <Bulk schema={schema} />
          ) : page === "forecast" ? (
            <Forecasts />
          ) : page === "schedule" ? (
            <Scheduling />
          ) : schema[page] ? (
            <Catalog resource={page} schema={schema} />
          ) : (
            <Busy />
          )}
        </main>
        <footer className="app-footer">
          TIMBLE · Academic planning with mathematical clarity.
        </footer>
      </div>
    </div>
  );
}
