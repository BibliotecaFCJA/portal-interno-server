import test from "node:test";
import assert from "node:assert/strict";
import { isAdminTokenAuthorized } from "../server/auth.ts";

test("authorizes only an exact configured password", () => {
  assert.equal(isAdminTokenAuthorized("correct horse", "correct horse"), true);
  assert.equal(isAdminTokenAuthorized("wrong horse", "correct horse"), false);
  assert.equal(isAdminTokenAuthorized("correct horse ", "correct horse"), false);
});

test("rejects missing passwords and different-length tokens safely", () => {
  assert.equal(isAdminTokenAuthorized("", ""), false);
  assert.equal(isAdminTokenAuthorized("short", "longer password"), false);
});
