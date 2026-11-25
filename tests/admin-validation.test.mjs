import test from "node:test";
import assert from "node:assert/strict";
import {
  isAllowedWebUrl,
  isInsideProject,
  isValidPort,
  isValidStartCommand
} from "../server/admin-validation.ts";

test("accepts only valid network ports", () => {
  assert.equal(isValidPort(1), true);
  assert.equal(isValidPort(65535), true);
  assert.equal(isValidPort(0), false);
  assert.equal(isValidPort(65536), false);
  assert.equal(isValidPort(5173.5), false);
  assert.equal(isValidPort("5173"), false);
});

test("validates startup commands and blocks empty or oversized entries", () => {
  assert.equal(isValidStartCommand(["npm.cmd", "run", "dev"]), true);
  assert.equal(isValidStartCommand([]), false);
  assert.equal(isValidStartCommand([" "]), false);
  assert.equal(isValidStartCommand(["node\0.exe"]), false);
  assert.equal(isValidStartCommand(["x".repeat(501)]), false);
});

test("allows only HTTP and HTTPS URLs", () => {
  assert.equal(isAllowedWebUrl("http://localhost:3000"), true);
  assert.equal(isAllowedWebUrl("https://example.com/path"), true);
  assert.equal(isAllowedWebUrl("javascript:alert(1)"), false);
  assert.equal(isAllowedWebUrl("not a URL"), false);
});

test("keeps configured working directories inside the project", () => {
  assert.equal(isInsideProject("C:\\portal\\storage\\projects\\abc", "."), true);
  assert.equal(isInsideProject("C:\\portal\\storage\\projects\\abc", "src"), true);
  assert.equal(isInsideProject("C:\\portal\\storage\\projects\\abc", "..\\other"), false);
  assert.equal(isInsideProject("C:\\portal\\storage\\projects\\abc", "D:\\other"), false);
});
