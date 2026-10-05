import React, { useEffect, useState } from "react";
import { Plus, Search, Pencil, Trash2 } from "lucide-react";
import { api, send, label, title } from "../../services/api";
import { Alert, Busy, Modal, Table } from "../../components/Common";
export default function Catalog({ resource, schema }) {
  const [rows, setRows] = useState(null),
    [relations, setRelations] = useState({}),
    [error, setError] = useState(""),
    [query, setQuery] = useState(""),
    [editing, setEditing] = useState(null),
    [removing, setRemoving] = useState(null),
    [saving, setSaving] = useState(false);
  const fields = schema[resource] || [];
  async function refresh() {
    setRows(await api(resource + "/"));
  }
  useEffect(() => {
    let active = true;
    setRows(null);
    setError("");
    setQuery("");
    setEditing(null);
    Promise.all([
      api(resource + "/"),
      ...Array.from(new Set(fields.map((f) => f.relation).filter(Boolean))).map(
        async (r) => [r, await api(r + "/")],
      ),
    ])
      .then(([data, ...related]) => {
        if (active) {
          setRows(data);
          setRelations(Object.fromEntries(related));
        }
      })
      .catch((e) => active && setError(e.message));
    return () => {
      active = false;
    };
  }, [resource, schema]);
  async function save(e) {
    e.preventDefault();
    setSaving(true);
    setError("");
    try {
      const body = { ...editing };
      delete body.id;
      await send(
        resource + "/" + (editing.id ? editing.id + "/" : ""),
        body,
        editing.id ? "PUT" : "POST",
      );
      setEditing(null);
      await refresh();
    } catch (e) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  }
  const newRow = () =>
    Object.fromEntries(
      fields.map((f) => [
        f.name,
        f.type === "BooleanField"
          ? f.name === "is_active"
          : f.choices.length
            ? f.choices[0][0]
            : "",
      ]),
    );
  const columns = fields.map((f) => ({
    key: f.name,
    title: title(f.name),
    render: (r) =>
      f.relation
        ? label(
            (relations[f.relation] || []).find((x) => x.id === r[f.name]) || {
              id: r[f.name],
            },
          )
        : f.type === "BooleanField"
          ? r[f.name]
            ? "Yes"
            : "No"
          : String(r[f.name] ?? "—"),
  }));
  columns.push({
    key: "actions",
    title: "Actions",
    render: (r) => (
      <div className="row-actions">
        <button
          className="icon"
          aria-label={"Edit " + label(r)}
          onClick={() => {
            setError("");
            setEditing({ ...r });
          }}
        >
          <Pencil size={15} />
        </button>
        <button
          className="icon"
          aria-label={"Delete " + label(r)}
          onClick={() => setRemoving(r)}
        >
          <Trash2 size={15} />
        </button>
      </div>
    ),
  });
  return (
    <>
      <div className="page-heading">
        <div>
          <h2>{title(resource)}</h2>
          <p>Maintain the academic records used throughout Timble.</p>
        </div>
        <button
          onClick={() => {
            setError("");
            setEditing(newRow());
          }}
        >
          <Plus size={17} />
          Add record
        </button>
      </div>
      <Alert>{!editing && error}</Alert>
      <section className="panel">
        <div className="toolbar">
          <label className="search">
            <Search size={17} />
            <input
              aria-label="Search records"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search records…"
            />
          </label>
          <span className="muted">{rows?.length ?? 0} records</span>
        </div>
        {rows ? (
          <Table
            columns={columns}
            rows={rows.filter((r) =>
              Object.values(r)
                .join(" ")
                .toLowerCase()
                .includes(query.toLowerCase()),
            )}
          />
        ) : (
          <Busy />
        )}
      </section>
      {editing && (
        <Modal
          title={editing.id ? "Edit record" : "Add record"}
          onClose={() => setEditing(null)}
        >
          <form onSubmit={save}>
            <Alert>{error}</Alert>
            <div className="form-grid">
              {fields.map((f) => (
                <label key={f.name}>
                  {title(f.name)}
                  {f.type === "BooleanField" ? (
                    <input
                      type="checkbox"
                      checked={!!editing[f.name]}
                      onChange={(e) =>
                        setEditing({ ...editing, [f.name]: e.target.checked })
                      }
                    />
                  ) : f.relation || f.choices.length ? (
                    <select
                      required={f.required}
                      value={editing[f.name] ?? ""}
                      onChange={(e) =>
                        setEditing({
                          ...editing,
                          [f.name]: f.relation
                            ? Number(e.target.value)
                            : e.target.value,
                        })
                      }
                    >
                      <option value="">Select…</option>
                      {(f.relation
                        ? (relations[f.relation] || []).map((r) => [
                            r.id,
                            label(r),
                          ])
                        : f.choices
                      ).map(([value, text]) => (
                        <option key={value} value={value}>
                          {text}
                        </option>
                      ))}
                    </select>
                  ) : (
                    <input
                      required={f.required}
                      type={
                        /Integer|Decimal|Float/.test(f.type) ? "number" : "text"
                      }
                      step={f.type === "DecimalField" ? "0.000001" : undefined}
                      value={editing[f.name] ?? ""}
                      onChange={(e) =>
                        setEditing({ ...editing, [f.name]: e.target.value })
                      }
                    />
                  )}
                </label>
              ))}
            </div>
            <footer>
              <button
                type="button"
                className="secondary"
                onClick={() => setEditing(null)}
              >
                Cancel
              </button>
              <button disabled={saving}>
                {saving ? "Saving…" : "Save record"}
              </button>
            </footer>
          </form>
        </Modal>
      )}
      {removing && (
        <Modal title="Delete record" onClose={() => setRemoving(null)}>
          <p>
            Delete {label(removing)}? Referenced records must be deactivated
            instead.
          </p>
          <footer>
            <button className="secondary" onClick={() => setRemoving(null)}>
              Cancel
            </button>
            <button
              onClick={async () => {
                try {
                  await api(resource + "/" + removing.id + "/", {
                    method: "DELETE",
                  });
                  setRemoving(null);
                  await refresh();
                } catch (e) {
                  setRemoving(null);
                  setError(e.message);
                }
              }}
            >
              Delete record
            </button>
          </footer>
        </Modal>
      )}
    </>
  );
}
