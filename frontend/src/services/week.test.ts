import { describe, expect, it } from "vitest";

import { nextWeekStart } from "./week";

describe("nextWeekStart", () => {
  it("advances to the next Monday across a month boundary", () => {
    expect(nextWeekStart("2026-10-26")).toBe("2026-11-02");
  });

  it("advances to the next Monday across a year boundary", () => {
    expect(nextWeekStart("2026-12-28")).toBe("2027-01-04");
  });
});
