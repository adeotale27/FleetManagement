import { describe, expect, it } from "vitest";
import { can } from "./auth";

describe("permissions", () => {
  it("allows exact and wildcard", () => {
    expect(can(["trip:read"], "trip:read")).toBe(true);
    expect(can(["trip:read"], "trip:create")).toBe(false);
  });
});
