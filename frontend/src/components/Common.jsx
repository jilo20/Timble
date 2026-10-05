import React, { useEffect, useRef } from "react";
import { X, LoaderCircle } from "lucide-react";
export function Alert({ children }) {
  return children ? (
    <div className="alert" role="alert">
      {children}
    </div>
  ) : null;
}
export function Busy({ children = "Loading…" }) {
  return (
    <p className="busy">
      <LoaderCircle size={16} />
      {children}
    </p>
  );
}
export function Empty({ children }) {
  return <div className="empty">{children}</div>;
}
export function Modal({ title, children, onClose }) {
  const ref = useRef();
  useEffect(() => {
    const dialog = ref.current;
    dialog.showModal();
    return () => dialog.close();
  }, []);
  return (
    <dialog ref={ref} onCancel={onClose}>
      <header>
        <h2>{title}</h2>
        <button className="icon" aria-label="Close dialog" onClick={onClose}>
          <X />
        </button>
      </header>
      {children}
    </dialog>
  );
}
export function Table({ columns, rows }) {
  return (
    <div className="table-scroll">
      <table>
        <thead>
          <tr>
            {columns.map((c) => (
              <th key={c.key}>{c.title}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={r.id ?? i}>
              {columns.map((c) => (
                <td key={c.key}>
                  {c.render ? c.render(r) : String(r[c.key] ?? "—")}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {!rows.length && <Empty>No records yet.</Empty>}
    </div>
  );
}
export function Badge({ children }) {
  return (
    <span
      className={
        "badge " +
        (String(children).includes("ERROR") || children === "INFEASIBLE"
          ? "bad"
          : "")
      }
    >
      {children}
    </span>
  );
}
