import React, { useState } from "react";
import { Upload, Download, Package } from "lucide-react";
import { title, message } from "../../services/api";
import { Alert, Table } from "../../components/Common";

export default function Bulk({ schema }) {
  const [format, setFormat] = useState("bundle"),
    [kind, setKind] = useState("programs");
  const [file, setFile] = useState(null),
    [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  const bundled = format === "bundle";
  function reset() {
    setFile(null);
    setResult(null);
    setError("");
  }
  async function run(commit) {
    setBusy(true);
    setError("");
    const form = new FormData();
    form.append("file", file);
    form.append("commit", String(commit));
    try {
      const csrf = document.cookie
        .split("; ")
        .find((x) => x.startsWith("csrftoken="))
        ?.split("=")[1];
      const response = await fetch(
        bundled ? "/api/bulk-bundle/" : "/api/bulk/" + kind + "/",
        {
          method: "POST",
          body: form,
          headers: { "X-CSRFToken": csrf },
          credentials: "same-origin",
        },
      );
      const data = await response.json();
      if (typeof data.valid !== "boolean") {
        setResult(null);
        setError(message(data.errors || data.detail || "Import failed."));
      } else setResult(data);
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
          <p className="eyebrow">DATA WORKSPACE</p>
          <h1>Bulk management</h1>
          <p>
            Upload a dataset ZIP to validate and import all ten files together.
          </p>
        </div>
        <Package size={28} />
      </div>
      <Alert>{error}</Alert>
      <section className="panel padded">
        <div className="steps">
          <span>01 · Choose package</span>
          <span>02 · Review validation</span>
          <span>03 · Import together</span>
        </div>
        <div className="form-grid">
          <label>
            Import format
            <select
              disabled={busy}
              value={format}
              onChange={(e) => {
                setFormat(e.target.value);
                reset();
              }}
            >
              <option value="bundle">Dataset ZIP (all files)</option>
              <option value="csv">Single CSV</option>
            </select>
          </label>
          {bundled ? (
            <a className="button secondary" href="/api/bulk-bundle/">
              <Download size={17} />
              Download ZIP templates
            </a>
          ) : (
            <>
              <label>
                Dataset
                <select
                  disabled={busy}
                  value={kind}
                  onChange={(e) => {
                    setKind(e.target.value);
                    reset();
                  }}
                >
                  {Object.keys(schema).map((k) => (
                    <option key={k} value={k}>
                      {title(k)}
                    </option>
                  ))}
                </select>
              </label>
              <a className="button secondary" href={"/api/bulk/" + kind + "/"}>
                <Download size={17} />
                Download CSV template
              </a>
            </>
          )}
        </div>
        {bundled && (
          <>
            <p>
              The ZIP must contain all ten CSV templates at its root. Leave a
              file with just its header when there are no records. Timble
              resolves dependencies automatically; if any file fails, nothing in
              the package is saved.
            </p>
            <div className="actions">
              <a
                className="button secondary"
                href="/api/bulk-bundle/?package=datasets"
              >
                Download revised datasets
              </a>
              <a
                className="button secondary"
                href="/api/bulk-bundle/?package=demo"
              >
                Download demo ZIP
              </a>
            </div>
            <p className="muted">
              The revised package contains the verified subset of the legacy
              data. Unresolved curriculum and other missing academic records
              still require review. Demo data are synthetic.
            </p>
          </>
        )}
        <label className="upload">
          <Upload size={30} />
          <strong>
            {bundled ? "Choose a dataset ZIP" : "Choose a UTF-8 CSV file"}
          </strong>
          <span>
            {bundled
              ? "10 CSVs · One validation · One atomic import"
              : "Exact headers · Relationship checks · Atomic import"}
          </span>
          <input
            key={format + "-" + kind}
            disabled={busy}
            type="file"
            accept={
              bundled
                ? ".zip,application/zip,application/x-zip-compressed"
                : ".csv,text/csv"
            }
            onChange={(e) => {
              setFile(e.target.files[0]);
              setResult(null);
              setError("");
            }}
          />
        </label>
        <div className="actions">
          <button disabled={!file || busy} onClick={() => run(false)}>
            {busy
              ? "Checking…"
              : bundled
                ? "Validate package"
                : "Validate file"}
          </button>
          {result?.valid && !result.committed && (
            <button disabled={busy} onClick={() => run(true)}>
              {bundled ? "Import all datasets" : "Import validated file"}
            </button>
          )}
        </div>
      </section>
      {result && (
        <section className="panel padded">
          <h2>
            {result.committed
              ? "Import complete"
              : result.valid
                ? "Validation passed"
                : "Review required"}
          </h2>
          <p>
            {result.inserted ?? 0} inserted · {result.updated ?? 0} updated ·{" "}
            {result.skipped ?? 0} unchanged
            {!result.committed ? " (preview counts — nothing saved)" : ""}
          </p>
          {result.files?.length > 0 && (
            <Table
              rows={result.files}
              columns={[
                { key: "file", title: "File (dependency order)" },
                {
                  key: "valid",
                  title: "Validation",
                  render: (r) => (r.valid ? "Passed" : "Needs review"),
                },
                { key: "inserted", title: "Insert" },
                { key: "updated", title: "Update" },
                { key: "skipped", title: "Unchanged" },
              ]}
            />
          )}
          {result.errors?.length > 0 && (
            <Table
              rows={result.errors}
              columns={[
                ...(bundled ? [{ key: "file", title: "File" }] : []),
                { key: "row", title: "CSV row" },
                { key: "message", title: "Problem" },
              ]}
            />
          )}
        </section>
      )}
    </>
  );
}
