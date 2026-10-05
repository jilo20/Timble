export function message(error) {
  return typeof error === "string" ? error : JSON.stringify(error, null, 2);
}
export async function api(path, options = {}) {
  const csrf =
    document.cookie
      .split("; ")
      .find((x) => x.startsWith("csrftoken="))
      ?.split("=")[1] || "";
  const headers = {
    "X-CSRFToken": csrf,
    ...(options.body && !(options.body instanceof FormData)
      ? { "Content-Type": "application/json" }
      : {}),
    ...options.headers,
  };
  const response = await fetch("/api/" + path, {
    credentials: "same-origin",
    ...options,
    headers,
  });
  if (response.status === 204) return null;
  const data = await response.json();
  if (!response.ok)
    throw new Error(message(data.errors || data.detail || data));
  return data;
}
export const send = (path, data, method = "POST") =>
  api(path, { method, body: JSON.stringify(data) });
export const label = (row) =>
  row.program_code ||
  row.subject_code ||
  row.employee_code ||
  row.room_code ||
  row.alias ||
  row.section_code ||
  `#${row.id}`;
export const title = (value) =>
  value
    .replaceAll("-", " ")
    .replaceAll("_", " ")
    .replace(/\b\w/g, (x) => x.toUpperCase());
