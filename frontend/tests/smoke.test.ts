import { describe, expect, it } from "vitest";

describe("test harness", () => {
  it("runs a basic assertion so CI detects tests", () => {
    expect(true).toBe(true);
  });
});
