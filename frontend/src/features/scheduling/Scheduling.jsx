import React, { useEffect, useState } from "react";
import { Play, Info } from "lucide-react";
import { api, send } from "../../services/api";
import { Alert, Badge, Table, Modal, Busy } from "../../components/Common";
import Demonstration from "./Demonstration";
export default function Scheduling() {
  const [runs, setRuns] = useState([]),
    [forecasts, setForecasts] = useState([]),
    [forecast, setForecast] = useState(""),
    [selected, setSelected] = useState(null),
    [tab, setTab] = useState("Timetable"),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [explain, setExplain] = useState(null),
    [filter, setFilter] = useState("all");
  const refresh = () => api("schedules/").then(setRuns);
  useEffect(() => {
    Promise.all([
      refresh(),
      api("forecasts/").then((x) =>
        setForecasts(x.filter((r) => r.status === "FINALIZED")),
      ),
    ]).catch((e) => setError(e.message));
  }, []);
  useEffect(() => {
    if (!selected || !["QUEUED", "RUNNING"].includes(selected.status)) return;
    const timer = setInterval(() => {
      api("schedules/" + selected.id + "/")
        .then(setSelected)
        .catch((e) => setError(e.message));
      refresh().catch((e) => setError(e.message));
    }, 1500);
    return () => clearInterval(timer);
  }, [selected?.id, selected?.status]);
  async function generate(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const r = await send("schedules/", { forecast_id: Number(forecast) });
      setSelected(await api("schedules/" + r.id + "/"));
      await refresh();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  const s = selected?.scenario_snapshot;
  const columns = s
    ? [
        {
          key: "offering",
          title: "Offering",
          render: (a) => s.offerings[a.offering - 1].label,
        },
        {
          key: "faculty",
          title: "Faculty",
          render: (a) => s.faculty[a.faculty - 1].label,
        },
        {
          key: "room",
          title: "Room",
          render: (a) => s.rooms[a.room - 1].label,
        },
        { key: "day", title: "Day", render: (a) => s.days[a.day - 1] },
        {
          key: "start",
          title: "Time",
          render: (a) =>
            `${s.periods[a.start - 1]}–${s.periods[a.start + a.duration - 1]}`,
        },
        {
          key: "explain",
          title: "Computation",
          render: (a) => (
            <button
              className="text-button"
              onClick={() =>
                setExplain({
                  assignment: a,
                  ...selected.explanations[selected.assignments.indexOf(a)],
                })
              }
            >
              <Info size={15} />
              Explain
            </button>
          ),
        },
      ]
    : [];
  return (
    <>
      <div className="page-heading">
        <div>
          <p className="eyebrow">CONSTRAINT OPTIMIZATION</p>
          <h1>Scheduling studio</h1>
          <p>Build an explainable timetable from finalized course offerings.</p>
        </div>
        <Badge>PYOMO + HiGHS</Badge>
      </div>
      <Alert>{error}</Alert>
      <section className="panel padded">
        <form className="inline-form" onSubmit={generate}>
          <label>
            Finalized forecast
            <select
              required
              value={forecast}
              onChange={(e) => setForecast(e.target.value)}
            >
              <option value="">Choose forecast…</option>
              {forecasts.map((r) => (
                <option value={r.id} key={r.id}>
                  #{r.id} · {r.academic_year}
                </option>
              ))}
            </select>
          </label>
          <button disabled={busy || !forecast}>
            <Play size={16} />
            Generate schedule
          </button>
          <p className="muted">
            60-second solver limit · Exact room-waste objective
          </p>
        </form>
      </section>
      <div className="toolbar">
        <label>
          Schedule run
          <select
            value={selected?.id || ""}
            onChange={async (e) => {
              setError("");
              try {
                setSelected(await api("schedules/" + e.target.value + "/"));
              } catch (err) {
                setError(err.message);
              }
            }}
          >
            <option value="" disabled>
              Select a run…
            </option>
            {runs.map((r) => (
              <option key={r.id} value={r.id}>
                #{r.id} · {r.academic_year} · {r.status}
              </option>
            ))}
          </select>
        </label>
        {selected && <Badge>{selected.status}</Badge>}
      </div>
      {selected && (
        <>
          <div className="tabs">
            {["Timetable", "Solver progress", "Optimization computation"].map(
              (t) => (
                <button
                  className={tab === t ? "active" : ""}
                  key={t}
                  onClick={() => setTab(t)}
                >
                  {t}
                </button>
              ),
            )}
          </div>
          {["QUEUED", "RUNNING"].includes(selected.status) && (
            <Busy>
              HiGHS is solving. Terminal metrics appear when the solve finishes.
            </Busy>
          )}
          {selected.diagnostic && (
            <p className="muted">Solver: {selected.diagnostic}</p>
          )}
          {tab === "Timetable" && (
            <section className="panel padded">
              <div className="toolbar">
                <h2>Final timetable</h2>
                <label>
                  Day
                  <select
                    value={filter}
                    onChange={(e) => setFilter(e.target.value)}
                  >
                    <option value="all">All days</option>
                    {s.days.map((d, i) => (
                      <option key={d} value={i + 1}>
                        {d}
                      </option>
                    ))}
                  </select>
                </label>
              </div>
              <Table
                rows={selected.assignments.filter(
                  (a) => filter === "all" || a.day === Number(filter),
                )}
                columns={columns}
              />
              <p className="muted">
                Every multi-period meeting reserves all consecutive periods in
                its interval.
              </p>
            </section>
          )}
          {tab === "Solver progress" && (
            <section className="panel padded">
              <h2>Solver measurements</h2>
              <p>
                These are genuine terminal measurements from HiGHS. This
                integration records one terminal sample; it does not expose a
                live search trace.
              </p>
              <div className="stats">
                {[
                  ["objective_value", "Room capacity waste"],
                  ["best_bound", "Best bound"],
                  ["mip_gap", "MIP gap"],
                  ["nodes_explored", "Search nodes"],
                  ["elapsed_seconds", "Elapsed seconds"],
                ].map(([k, label]) => (
                  <article key={k}>
                    <span>{label}</span>
                    <strong>
                      {selected[k] == null
                        ? "Unavailable"
                        : Number(selected[k]).toLocaleString(undefined, {
                            maximumFractionDigits: 3,
                          })}
                    </strong>
                  </article>
                ))}
              </div>
              <Table
                rows={selected.metrics}
                columns={[
                  { key: "sequence_number", title: "Sample" },
                  {
                    key: "elapsed_seconds",
                    title: "Seconds",
                    render: (r) => Number(r.elapsed_seconds).toFixed(3),
                  },
                  { key: "objective_value", title: "Objective" },
                  { key: "best_bound", title: "Bound" },
                  { key: "mip_gap", title: "Gap" },
                  { key: "nodes_explored", title: "Nodes" },
                ]}
              />
            </section>
          )}
          {tab === "Optimization computation" && (
            <Demonstration run={selected} />
          )}
        </>
      )}
      {explain && (
        <Modal
          title="Why this assignment is valid"
          onClose={() => setExplain(null)}
        >
          <h3>{explain.offering.label}</h3>
          <p>
            {explain.offering.students} expected students ·{" "}
            {explain.offering.duration} consecutive periods
          </p>
          <h3>Faculty candidates</h3>
          <Table
            rows={explain.faculty_candidates}
            columns={[
              { key: "label", title: "Faculty" },
              { key: "rule", title: "Teaching rule" },
            ]}
          />
          <p>Chosen: {explain.chosen_faculty.label}</p>
          <h3>Room candidates</h3>
          <Table
            rows={explain.room_candidates}
            columns={[
              { key: "label", title: "Room" },
              { key: "capacity", title: "Seats" },
              { key: "reason", title: "Eligibility" },
            ]}
          />
          <div className="formula">
            {explain.chosen_room.label}: {explain.chosen_room.capacity} −{" "}
            {explain.offering.students} = {explain.waste} unused seats
            <br />
            Occupied periods:{" "}
            {explain.occupied_periods.map((p) => "P" + p).join(", ")}
          </div>
          <p>{explain.note}</p>
          <Badge>
            {selected.validation.valid
              ? "Faculty / room / block conflicts: none"
              : "See constraint validation"}
          </Badge>
        </Modal>
      )}
    </>
  );
}
