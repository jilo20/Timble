import React, { useEffect, useState } from "react";
import {
  ArrowUpRight,
  BookOpen,
  Users,
  DoorOpen,
  GraduationCap,
} from "lucide-react";
import { api } from "../../services/api";
import { Alert } from "../../components/Common";
export default function Dashboard({ navigate }) {
  const [counts, setCounts] = useState({}),
    [error, setError] = useState("");
  useEffect(() => {
    Promise.all(
      ["programs", "subjects", "faculty", "rooms"].map(async (key) => [
        key,
        (await api(key + "/")).length,
      ]),
    )
      .then((x) => setCounts(Object.fromEntries(x)))
      .catch((e) => setError(e.message));
  }, []);
  return (
    <>
      <div className="page-heading">
        <div>
          <p className="eyebrow">ACADEMIC PLANNING, CONNECTED</p>
          <h1>A clear path to your next timetable.</h1>
          <p>
            Bring your curriculum, enrollment demand, and teaching resources
            together.
          </p>
        </div>
        <span className="version">TIMBLE / V2</span>
      </div>
      <Alert>{error}</Alert>
      <div className="stats">
        {[
          ["programs", GraduationCap],
          ["subjects", BookOpen],
          ["faculty", Users],
          ["rooms", DoorOpen],
        ].map(([key, Icon]) => (
          <article key={key}>
            <Icon size={21} />
            <strong>{counts[key] ?? "—"}</strong>
            <span>{key}</span>
          </article>
        ))}
      </div>
      <section className="hero">
        <div>
          <span className="eyebrow">YOUR PLANNING WORKFLOW</span>
          <h2>
            Good schedules start
            <br />
            with trusted data.
          </h2>
          <p>
            Follow each step from academic records to an optimized timetable,
            with the calculations visible along the way.
          </p>
          <button onClick={() => navigate("bulk")} className="light">
            Prepare your data <ArrowUpRight size={17} />
          </button>
        </div>
        <div className="workflow">
          {[
            [
              "01",
              "Master data",
              "Programs, curriculum, people & rooms",
              "programs",
            ],
            [
              "02",
              "Forecast demand",
              "Historical enrollment → course offerings",
              "forecast",
            ],
            [
              "03",
              "Build the timetable",
              "Pyomo model → HiGHS optimization",
              "schedule",
            ],
          ].map(([n, t, d, path]) => (
            <button key={n} onClick={() => navigate(path)}>
              <span>{n}</span>
              <div>
                <strong>{t}</strong>
                <small>{d}</small>
              </div>
              <ArrowUpRight size={18} />
            </button>
          ))}
        </div>
      </section>
      <div className="two-column">
        <section className="panel padded">
          <span className="eyebrow">EXPLAINABLE BY DESIGN</span>
          <h2>See the mathematics behind every assignment.</h2>
          <p>
            Inspect teaching rules, room compatibility, block relationships, and
            time occupancy. Every final assignment links back to its actual
            inputs.
          </p>
          <button className="secondary" onClick={() => navigate("schedule")}>
            Open scheduling studio <ArrowUpRight size={16} />
          </button>
        </section>
        <section className="panel padded">
          <span className="eyebrow">GETTING STARTED</span>
          <h2>One consistent source of academic data.</h2>
          <p>
            Upload the complete dataset ZIP. Timble checks every file, resolves
            dependencies, and saves the package only when all records are valid.
          </p>
          <button className="secondary" onClick={() => navigate("bulk")}>
            Open bulk management <ArrowUpRight size={16} />
          </button>
        </section>
      </div>
    </>
  );
}
