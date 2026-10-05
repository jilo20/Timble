import React, { useState, useEffect } from "react";
import {
  ChevronRight,
  ChevronsLeft,
  ClipboardPenLine,
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
    [menu, setMenu] = useState(false),
    [sidebarOpen, setSidebarOpen] = useState(true),
    [collapsed, setCollapsed] = useState({});
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
  useEffect(() => {
    if (!menu) return;
    const close = (event) => {
      if (event.key === "Escape") setMenu(false);
    };
    window.addEventListener("keydown", close);
    return () => window.removeEventListener("keydown", close);
  }, [menu]);
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
            <strong>
              TIMBLE<small>University Timetabling</small>
            </strong>
          </div>
          <h1>Welcome back</h1>
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
  const isCatalog = Boolean(schema[page]);
  const modules = [
    [
      "data",
      "DATA MANAGEMENT",
      [
        ["dashboard", "Overview"],
        ["bulk", "Data Import"],
        ["programs", "Data Entry"],
      ],
    ],
    ["forecast", "FORECASTING", [["forecast", "Forecast Generation"]]],
    ["timetable", "TIMETABLING", [["schedule", "Generate Timetable"]]],
  ];
  return (
    <div className={"shell" + (sidebarOpen ? "" : " sidebar-collapsed")}>
      <a
        className="skip-link"
        href="#main-content"
        onClick={(e) => {
          e.preventDefault();
          document.getElementById("main-content").focus();
        }}
      >
        Skip to content
      </a>
      {menu && (
        <button
          className="nav-backdrop"
          aria-label="Close navigation"
          onClick={() => setMenu(false)}
        />
      )}
      <aside className={"sidebar" + (menu ? " open" : "")}>
        <div className="sidebar-brand">
          <a
            className="brand"
            href="#dashboard"
            onClick={() => navigate("dashboard")}
          >
            <img src="/logo.svg" alt="" />
            <strong>
              TIMBLE<small>University Timetabling</small>
            </strong>
          </a>
          <button
            className="sidebar-toggle"
            aria-label={
              sidebarOpen ? "Collapse navigation" : "Expand navigation"
            }
            aria-expanded={sidebarOpen}
            onClick={() => setSidebarOpen(!sidebarOpen)}
          >
            {sidebarOpen ? (
              <ChevronsLeft size={16} />
            ) : (
              <img src="/logo.svg" alt="" />
            )}
          </button>
        </div>
        <nav aria-label="Main navigation" className="main-nav">
          {modules.map(([id, label, links]) => {
            const active = links.some(
              ([p]) => page === p || (p === "programs" && isCatalog),
            );
            return (
              <div className="nav-module" key={id}>
                <button
                  className={"nav-label" + (active ? " current" : "")}
                  aria-expanded={!collapsed[id]}
                  aria-controls={"nav-" + id}
                  onClick={() =>
                    setCollapsed({ ...collapsed, [id]: !collapsed[id] })
                  }
                >
                  {label}
                  <ChevronRight
                    size={12}
                    className={!collapsed[id] ? "rotated" : ""}
                  />
                </button>
                <div id={"nav-" + id} hidden={Boolean(collapsed[id])}>
                  {links.map(([p, name]) => {
                    const selected =
                      page === p || (p === "programs" && isCatalog);
                    return (
                      <button
                        key={p}
                        className={selected ? "active" : ""}
                        aria-current={selected ? "page" : undefined}
                        onClick={() => navigate(p)}
                      >
                        {name}
                      </button>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </nav>
        <div className="sidebar-foot">
          <div className="user">
            <span className="avatar">
              {session.username.slice(0, 1).toUpperCase()}
            </span>
            <div className="user-details">
              <strong>{session.username}</strong>
              <small>University Office</small>
            </div>
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
              <LogOut size={16} />
            </button>
          </div>
        </div>
      </aside>
      <div className="workspace">
        <header className="mobile-header">
          <button
            className="icon"
            aria-label="Toggle navigation"
            aria-expanded={menu}
            onClick={() => {
              setSidebarOpen(true);
              setMenu(!menu);
            }}
          >
            <Menu size={21} />
          </button>
          <strong>TIMBLE</strong>
        </header>
        <main className="content" id="main-content" tabIndex={-1}>
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
            <>
              <div className="page-heading">
                <div>
                  <h1>
                    <ClipboardPenLine /> Data Entry
                  </h1>
                  <p>
                    Create and maintain scheduling inputs and academic master
                    data.
                  </p>
                </div>
              </div>
              <section className="panel data-entry">
                <nav className="entity-nav" aria-label="Data categories">
                  <span>Entities</span>
                  {Object.keys(schema).map((p) => (
                    <button
                      key={p}
                      className={page === p ? "active" : ""}
                      aria-current={page === p ? "page" : undefined}
                      onClick={() => navigate(p)}
                    >
                      {title(p)}
                    </button>
                  ))}
                </nav>
                <div className="entity-content">
                  <Catalog key={page} resource={page} schema={schema} />
                </div>
              </section>
            </>
          ) : (
            <Busy />
          )}
        </main>
      </div>
    </div>
  );
}
