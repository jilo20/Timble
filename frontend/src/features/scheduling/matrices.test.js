import { describe, it, expect } from "vitest";
import { occupancyMatrix, hypotheticalCollision } from "./matrices";
describe("mathematical occupancy", () => {
  it("uses 1-based periods and filters the selected day", () => {
    expect(
      occupancyMatrix(
        [{ index: 1 }],
        [
          { index: 1, day: 1, period: 2, count: 1 },
          { index: 1, day: 2, period: 1, count: 1 },
        ],
        1,
        3,
      ),
    ).toEqual([[0, 1, 0]]);
  });
  it("demonstrates every occupied period without mutating the assignment", () => {
    const a = { faculty: 2, day: 1, start: 2, duration: 3 };
    expect(hypotheticalCollision(a)).toEqual([
      { index: 2, day: 1, period: 2, count: 2 },
      { index: 2, day: 1, period: 3, count: 2 },
      { index: 2, day: 1, period: 4, count: 2 },
    ]);
    expect(a.duration).toBe(3);
  });
});
