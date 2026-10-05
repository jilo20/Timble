import React, { useState } from "react";
import { Table, Badge } from "../../components/Common";
import { occupancyMatrix, hypotheticalCollision } from "./matrices";
function Matrix({ title, rows, columns, values, formula }) {
  return (
    <section className="panel padded">
      <h3>{title}</h3>
      <p className="formula compact">{formula}</p>
      <div className="table-scroll">
        <table className="matrix">
          <thead>
            <tr>
              <th>Index / entity</th>
              {columns.map((c, i) => (
                <th key={i}>{c}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={r}>
                <th>{r}</th>
                {values[i]?.map((value, j) => (
                  <td
                    className={
                      value === 1 || value === "MUST_TEACH"
                        ? "filled"
                        : value > 1
                          ? "violation"
                          : ""
                    }
                    key={j}
                  >
                    {value}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
export default function Demonstration({ run }) {
  const [day, setDay] = useState(1),
    [example, setExample] = useState(false);
  const s = run.scenario_snapshot;
  const entity = (kind, prefix) =>
    s[kind].map((x) => prefix + x.index + " · " + x.label);
  return (
    <>
      <div className="panel padded">
        <h2>From inputs to a feasible timetable</h2>
        <p>
          Pyomo defines the binary model. HiGHS minimizes total unused room
          capacity per meeting.
        </p>
        <div className="formula">
          x[o,m,f,r,d,p] ∈ {"{0,1}"}
          <br />
          min Σ (capacity[r] − students[o]) x[o,m,f,r,d,p]
        </div>
        <p>
          Missing faculty rules are ineligible. MUST_TEACH requires at least one
          offering, not every section. All displayed mathematical indices start
          at 1.
        </p>
      </div>
      <Matrix
        title="Faculty × Subject teaching rules"
        rows={entity("faculty", "F")}
        columns={entity("subjects", "S")}
        values={run.parameters.faculty_subject}
        formula="CANNOT ⇒ no candidate; MUST_TEACH ⇒ Σ y[o,f] ≥ 1"
      />
      <Matrix
        title="Offering × Block"
        rows={entity("offerings", "O")}
        columns={entity("blocks", "B")}
        values={run.parameters.offering_block}
        formula="A[o,b] = 1 when block b attends offering o"
      />
      <Matrix
        title="Offering × Room compatibility"
        rows={entity("offerings", "O")}
        columns={entity("rooms", "R")}
        values={run.parameters.room_compatibility}
        formula="Compatible ⇔ matching room type AND capacity[r] ≥ students[o]"
      />
      <div className="toolbar">
        <h2>Time occupancy</h2>
        <label>
          Day
          <select value={day} onChange={(e) => setDay(Number(e.target.value))}>
            {s.days.map((name, i) => (
              <option value={i + 1} key={name}>
                {name}
              </option>
            ))}
          </select>
        </label>
      </div>
      {[
        ["offering", "offerings", "O"],
        ["faculty", "faculty", "F"],
        ["room", "rooms", "R"],
        ["block", "blocks", "B"],
      ].map(([kind, entities, prefix]) => (
        <Matrix
          key={kind}
          title={kind + " × Time"}
          rows={entity(entities, prefix)}
          columns={s.periods
            .slice(0, -1)
            .map((time, i) => "P" + (i + 1) + " " + time)}
          values={occupancyMatrix(
            s[entities],
            run.validation.occupancy[kind],
            day,
            s.periods.length - 1,
          )}
          formula="For each entity and period: Σ starts covering that period ≤ 1"
        />
      ))}
      <section className="panel padded">
        <h2>Constraint validation</h2>
        <Badge>
          {run.validation.valid
            ? "All hard constraints satisfied"
            : "No valid complete assignment"}
        </Badge>
        <ul>
          {run.validation.violations.map((v, i) => (
            <li key={i}>{v}</li>
          ))}
        </ul>
        {run.assignments.length > 0 && (
          <>
            <button className="secondary" onClick={() => setExample(!example)}>
              Demonstrate a hypothetical collision
            </button>
            {example && (
              <>
                <p>
                  This hypothetical duplicate is not saved. It assigns the first
                  meeting twice to the same faculty and occupied periods.
                </p>
                <Table
                  rows={hypotheticalCollision(run.assignments[0])}
                  columns={[
                    { key: "index", title: "Faculty index" },
                    { key: "day", title: "Day index" },
                    { key: "period", title: "Period" },
                    { key: "count", title: "Occupancy (must be ≤ 1)" },
                  ]}
                />
                <p className="alert">
                  2 &gt; 1: the faculty collision constraint rejects this
                  assignment.
                </p>
              </>
            )}
          </>
        )}
      </section>
    </>
  );
}
