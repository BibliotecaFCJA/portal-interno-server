import test from "node:test";
import assert from "node:assert/strict";
import path from "node:path";
import os from "node:os";
import {
  exceedsUploadLimits,
  getUploadTarget,
  MAX_UPLOAD_BYTES,
  MAX_UPLOAD_FILES,
  shouldSkipUploadFile
} from "../server/upload-policy.ts";

const projectDir = path.join(os.tmpdir(), "portal-upload-test", "project");

test("accepts normal files and removes the selected folder prefix", () => {
  assert.equal(
    getUploadTarget(projectDir, "Portal/app/main.py", "Portal"),
    path.join(projectDir, "app", "main.py")
  );
  assert.equal(getUploadTarget(projectDir, "package.json"), path.join(projectDir, "package.json"));
});

test("rejects traversal and absolute upload paths", () => {
  assert.equal(getUploadTarget(projectDir, "../outside.txt"), null);
  assert.equal(getUploadTarget(projectDir, "folder/../../outside.txt"), null);
  assert.equal(getUploadTarget(projectDir, "Portal/../../outside.txt", "Portal"), null);
  assert.equal(getUploadTarget(projectDir, path.resolve(os.tmpdir(), "outside.txt")), null);
});

test("skips secrets, certificates and generated dependency folders but includes databases", () => {
  for (const file of [
    ".env",
    "config/.env.local",
    "certs/private.pem",
    "node_modules/pkg/index.js",
    ".NEXT/cache/file"
  ]) {
    assert.equal(shouldSkipUploadFile(file), true, file);
    assert.equal(getUploadTarget(projectDir, file), null, file);
  }
  assert.equal(shouldSkipUploadFile("src/.env.example.ts"), true);
  for (const file of ["data/app.db", "data/app.sqlite", "data/app.sqlite3", "data/app.db3", "data/app.mdb"]) {
    assert.equal(shouldSkipUploadFile(file), false, file);
    assert.equal(getUploadTarget(projectDir, file), path.join(projectDir, file.replaceAll("/", path.sep)));
  }
});

test("enforces file-count and total-size limits at the boundary", () => {
  assert.equal(exceedsUploadLimits(MAX_UPLOAD_FILES - 1, 0, 1), false);
  assert.equal(exceedsUploadLimits(MAX_UPLOAD_FILES, 0, 1), true);
  assert.equal(exceedsUploadLimits(0, MAX_UPLOAD_BYTES - 1, 1), false);
  assert.equal(exceedsUploadLimits(0, MAX_UPLOAD_BYTES, 1), true);
});
