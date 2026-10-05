import React, { useEffect, useState } from "react";
import {
  ArrowUpRight,
  BookOpen,
  Users,
  DoorOpen,
  GraduationCap,
  LayoutDashboard,
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
          <h1>
            <LayoutDashboard /> Overview
          </h1>
          <p>
            Manage academic data, forecast enrollment, and generate university
            timetables.
          </p>
        </div>
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
      <section className="panel padded">
        <h2>Academic planning workflow</h2>
        <p>
          Prepare your records, review enrollment demand, then build a
          timetable.
        </p>
        <div className="workflow">
          {[
            [
              "01",
              "Data Management",
              "Maintain programs, curriculum, faculty, and rooms.",
              "programs",
            ],
            [
              "02",
              "Forecasting",
              "Turn historical enrollment into course offerings.",
              "forecast",
            ],
            [
              "03",
              "Timetabling",
              "Generate schedules and review every assignment.",
              "schedule",
            ],
          ].map(([n, t, d, path]) => (
            <button key={n} onClick={() => navigate(path)}>
              <span>{n}</span>
              <div>
                <strong>{t}</strong>
                <small>{d}</small>
              </div>
              <ArrowUpRight size={17} />
            </button>
          ))}
        </div>
      </section>
      <div className="two-column">
        <section className="panel padded">
          <h2>Import academic data</h2>
          <p>
            Upload all ten datasets in one ZIP package. Review validation
            results before saving the records.
          </p>
          <button className="secondary" onClick={() => navigate("bulk")}>
            Open Data Import <ArrowUpRight size={16} />
          </button>
        </section>
        <section className="panel padded">
          <h2>Review timetable computations</h2>
          <p>
            Inspect teaching rules, room compatibility, block relationships, and
            the calculations behind each assignment.
          </p>
          <button className="secondary" onClick={() => navigate("schedule")}>
            Open Generate Timetable <ArrowUpRight size={16} />
          </button>
        </section>
      </div>
    </>
  );
}
