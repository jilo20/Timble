import React from "react";
import { it, expect, vi, afterEach } from "vitest";
import { render, screen, cleanup } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import Bulk from "./Bulk";
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});
it("requires preview before committing and displays row errors", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({
      ok: false,
      json: async () => ({
        valid: false,
        errors: [{ row: 3, message: "Unknown subject" }],
        inserted: 0,
        updated: 0,
        skipped: 0,
      }),
    }),
  );
  const user = userEvent.setup();
  render(<Bulk schema={{ programs: [] }} />);
  await user.selectOptions(screen.getByLabelText("Import format"), "csv");
  expect(
    screen.queryByRole("button", { name: "Import validated file" }),
  ).toBeNull();
  await user.upload(
    screen.getByLabelText(/Choose a UTF-8/),
    new File(["a,b\n1,2"], "data.csv", { type: "text/csv" }),
  );
  await user.click(screen.getByRole("button", { name: "Validate file" }));
  expect(await screen.findByText("Unknown subject")).toBeTruthy();
  expect(
    screen.queryByRole("button", { name: "Import validated file" }),
  ).toBeNull();
});

it("validates a complete ZIP before showing the atomic import action", async () => {
  const report = {
    valid: true,
    committed: false,
    inserted: 3,
    updated: 0,
    skipped: 0,
    errors: [],
    files: [
      {
        file: "programs.csv",
        valid: true,
        inserted: 1,
        updated: 0,
        skipped: 0,
      },
      {
        file: "subjects.csv",
        valid: true,
        inserted: 2,
        updated: 0,
        skipped: 0,
      },
    ],
  };
  const fetchMock = vi
    .fn()
    .mockResolvedValueOnce({ ok: true, json: async () => report })
    .mockResolvedValueOnce({
      ok: true,
      json: async () => ({ ...report, committed: true }),
    });
  vi.stubGlobal("fetch", fetchMock);
  const user = userEvent.setup();
  render(<Bulk schema={{ programs: [] }} />);
  expect(
    screen.queryByRole("button", { name: "Import all datasets" }),
  ).toBeNull();
  await user.upload(
    screen.getByLabelText(/Choose a dataset ZIP/),
    new File(["zip"], "datasets.zip", { type: "application/zip" }),
  );
  await user.click(screen.getByRole("button", { name: "Validate package" }));
  expect(await screen.findByText("subjects.csv")).toBeTruthy();
  expect(fetchMock.mock.calls[0][0]).toBe("/api/bulk-bundle/");
  expect(fetchMock.mock.calls[0][1].body.get("commit")).toBe("false");
  await user.click(screen.getByRole("button", { name: "Import all datasets" }));
  expect(await screen.findByText("Import complete")).toBeTruthy();
  expect(fetchMock.mock.calls[1][1].body.get("commit")).toBe("true");
});
it("shows filename and row errors and clears ZIP approval when the file changes", async () => {
  const fetchMock = vi
    .fn()
    .mockResolvedValueOnce({
      ok: true,
      json: async () => ({ valid: true, committed: false, errors: [] }),
    })
    .mockResolvedValueOnce({
      ok: false,
      json: async () => ({
        valid: false,
        committed: false,
        errors: [
          {
            file: "historical_enrollment.csv",
            row: 2,
            message: "Unknown subject",
          },
        ],
      }),
    });
  vi.stubGlobal("fetch", fetchMock);
  const user = userEvent.setup();
  render(<Bulk schema={{ programs: [] }} />);
  const upload = screen.getByLabelText(/Choose a dataset ZIP/);
  await user.upload(
    upload,
    new File(["zip"], "valid.zip", { type: "application/zip" }),
  );
  await user.click(screen.getByRole("button", { name: "Validate package" }));
  await screen.findByRole("button", { name: "Import all datasets" });
  await user.upload(
    upload,
    new File(["bad zip"], "invalid.zip", { type: "application/zip" }),
  );
  expect(
    screen.queryByRole("button", { name: "Import all datasets" }),
  ).toBeNull();
  await user.click(screen.getByRole("button", { name: "Validate package" }));
  expect(await screen.findByText("historical_enrollment.csv")).toBeTruthy();
  expect(screen.getByText("Unknown subject")).toBeTruthy();
  expect(
    screen.queryByRole("button", { name: "Import all datasets" }),
  ).toBeNull();
});
