import React, { useState, useEffect } from "react";
import { ArrowRight, Calculator } from "lucide-react";
import { api, send } from "../../services/api";
import { Alert, Busy, Badge, Table, Modal } from "../../components/Common";
export default function Forecasts() {
  const [runs, setRuns] = useState([]),
    [programs, setPrograms] = useState([]),
    [program, setProgram] = useState(""),
    [year, setYear] = useState("2026-2027"),
    [capacity, setCapacity] = useState(30),
    [rate, setRate] = useState("0.05"),
    [selected, setSelected] = useState(null),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [detail, setDetail] = useState(null),
    [blockEditor, setBlockEditor] = useState(null),
    [blocks, setBlocks] = useState([]);
  const refresh = () => api("forecasts/").then(setRuns);
  useEffect(() => {
    Promise.all([
      refresh(),
      api("programs/").then(setPrograms),
      api("block-sections/").then(setBlocks),
    ]).catch((e) => setError(e.message));
  }, []);
  async function action(fn) {
    setBusy(true);
    setError("");
    try {
      await fn();
      await refresh();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <div className="page-heading">
        <div>
          <h1>
            <Calculator /> Forecast Generation
          </h1>
          <p>
            Trace historical demand through prerequisites to teaching sections.
          </p>
        </div>
        <span className="badge">CURRENT CURRICULUM</span>
      </div>
      <Alert>{error}</Alert>
      <section className="panel padded">
        <h2>Generate a forecast</h2>
        <form
          className="inline-form"
          onSubmit={(e) => {
            e.preventDefault();
            action(async () => {
              const run = await send("forecasts/", {
                academic_year: year,
                section_capacity: Number(capacity),
                failure_rate: rate,
                program_ids: program ? [Number(program)] : [],
              });
              setSelected(await api("forecasts/" + run.id + "/"));
            });
          }}
        >
          <label>
            Academic year
            <input
              value={year}
              onChange={(e) => setYear(e.target.value)}
              pattern="[0-9]{4}-[0-9]{4}"
              required
            />
          </label>
          <label>
            Program scope
            <select
              value={program}
              onChange={(e) => setProgram(e.target.value)}
            >
              <option value="">All active programs</option>
              {programs.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.program_code}
                </option>
              ))}
            </select>
          </label>
          <label>
            Section capacity
            <input
              type="number"
              min="1"
              required
              value={capacity}
              onChange={(e) => setCapacity(e.target.value)}
            />
          </label>
          <label>
            Forecast failure assumption (0–1)
            <input
              type="number"
              min="0"
              max="1"
              step="0.001"
              required
              value={rate}
              onChange={(e) => setRate(e.target.value)}
            />
          </label>
          <button disabled={busy}>
            Generate <ArrowRight size={16} />
          </button>
        </form>
      </section>
      <div className="split">
        <section className="panel padded run-list">
          <h2>Forecast runs</h2>
          {runs.map((r) => (
            <button
              className={
                "run-item " + (selected?.id === r.id ? "selected" : "")
              }
              key={r.id}
              onClick={() =>
                action(async () =>
                  setSelected(await api("forecasts/" + r.id + "/")),
                )
              }
            >
              <strong>
                #{r.id} · {r.academic_year}
              </strong>
              <Badge>{r.status}</Badge>
            </button>
          ))}
          {!runs.length && <p className="muted">No forecasts generated yet.</p>}
        </section>
        <section className="panel padded">
          {!selected ? (
            <p className="muted">Select a run to inspect its calculations.</p>
          ) : (
            <>
              <div className="toolbar">
                <h2>Forecast #{selected.id}</h2>
                {selected.status === "DRAFT" ? (
                  <button
                    disabled={busy}
                    onClick={() =>
                      action(async () =>
                        setSelected(
                          await send("forecasts/" + selected.id + "/", {}),
                        ),
                      )
                    }
                  >
                    Finalize & create offerings
                  </button>
                ) : (
                  <Badge>FINALIZED</Badge>
                )}
              </div>
              <Table
                rows={selected.results}
                columns={[
                  { key: "program", title: "Program" },
                  { key: "subject", title: "Subject" },
                  { key: "forecasted_students", title: "Students" },
                  { key: "required_sections", title: "Sections" },
                  {
                    key: "calculation",
                    title: "Computation",
                    render: (r) => (
                      <button
                        className="text-button"
                        onClick={() => setDetail(r)}
                      >
                        <Calculator size={15} />
                        Inspect
                      </button>
                    ),
                  },
                ]}
              />
              <h3>Shared-subject totals</h3>
              <p className="muted">
                SUM across programs. Sections retain each program’s provenance.
              </p>
              <div className="chips">
                {Object.entries(selected.shared_subject_totals).map(
                  ([subject, n]) => (
                    <span className="badge" key={subject}>
                      {subject}: {n}
                    </span>
                  ),
                )}
              </div>
              {selected.offerings.length > 0 && (
                <>
                  <h3>Course offerings · {selected.offerings.length}</h3>
                  <Table
                    rows={selected.offerings}
                    columns={[
                      { key: "id", title: "Offering" },
                      { key: "section_number", title: "Section" },
                      { key: "component_type", title: "Component" },
                      { key: "expected_students", title: "Students" },
                      { key: "duration_periods", title: "Duration" },
                      { key: "meetings_per_week", title: "Meetings" },
                      {
                        key: "blocks",
                        title: "Student blocks",
                        render: (o) => (
                          <button
                            className="text-button"
                            onClick={() =>
                              action(async () =>
                                setBlockEditor({
                                  id: o.id,
                                  ...(await api(
                                    "offerings/" + o.id + "/blocks/",
                                  )),
                                }),
                              )
                            }
                          >
                            Manage blocks
                          </button>
                        ),
                      },
                    ]}
                  />
                </>
              )}
            </>
          )}
        </section>
      </div>
      {busy && <Busy>Working…</Busy>}
      {detail && (
        <Modal
          title={detail.subject + " · Forecast computation"}
          onClose={() => setDetail(null)}
        >
          <p>Historical year: {detail.computation.historical_year}</p>
          <Table
            rows={detail.computation.evidence}
            columns={[
              { key: "subject", title: "Source subject" },
              { key: "source", title: "Enrollment" },
              { key: "rate", title: "Failing rate" },
              { key: "adjusted", title: "Adjusted enrollment" },
            ]}
          />
          <div className="formula">
            {detail.computation.formula}
            <br />
            {detail.source_enrollment} − {detail.failure_adjustment} →{" "}
            {detail.forecasted_students} students
            <br />
            ceil({detail.forecasted_students} /{" "}
            {detail.computation.section_capacity}) = {detail.required_sections}{" "}
            sections
          </div>
          <p>
            Method: {detail.forecast_method}. {detail.computation.rounding}.
          </p>
        </Modal>
      )}
      {blockEditor && (
        <Modal
          title={"Blocks attending offering #" + blockEditor.id}
          onClose={() => setBlockEditor(null)}
        >
          <p>
            Select all blocks attending this offering. Every selected block is
            protected from timetable conflicts.
          </p>
          {blocks
            .filter((b) => b.is_active)
            .map((b) => (
              <label className="check" key={b.id}>
                <input
                  type="checkbox"
                  checked={blockEditor.block_ids.includes(b.id)}
                  onChange={(e) =>
                    setBlockEditor({
                      ...blockEditor,
                      block_ids: e.target.checked
                        ? [...blockEditor.block_ids, b.id]
                        : blockEditor.block_ids.filter((id) => id !== b.id),
                    })
                  }
                />
                {programs.find((p) => p.id === b.program)?.program_code}-
                {b.year_level}
                {b.section_code}
              </label>
            ))}
          <button
            onClick={() =>
              action(async () => {
                await send(
                  "offerings/" + blockEditor.id + "/blocks/",
                  { block_ids: blockEditor.block_ids },
                  "PUT",
                );
                setBlockEditor(null);
              })
            }
          >
            Save block links
          </button>
        </Modal>
      )}
    </>
  );
}
