import test from "node:test";
import assert from "node:assert/strict";
import net from "node:net";
import { commandWithProjectPort, findAvailableProjectPort, setNodeServerPort, setPythonRunPort } from "../server/port-utils.ts";

function listen(server, port) {
  return new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(port, "127.0.0.1", resolve);
  });
}

function close(server) {
  return new Promise((resolve) => server.close(() => resolve()));
}

test("skips an OS-occupied preferred port and a catalog-reserved port", async (t) => {
  const server = net.createServer();
  await listen(server, 0);
  const occupied = server.address().port;
  t.after(() => close(server));
  assert.ok(occupied < 65535);

  const selected = await findAvailableProjectPort(occupied, [occupied + 1], [occupied, occupied + 2]);
  assert.equal(selected, occupied + 2);
});

test("passes the selected port to npm scripts and replaces existing server flags", () => {
  assert.deepEqual(commandWithProjectPort(["npm.cmd", "run", "dev"], 4312), [
    "npm.cmd", "run", "dev", "--", "--port", "4312"
  ]);
  assert.deepEqual(commandWithProjectPort(["npm.cmd", "run", "dev", "--", "--port", "3000", "--host"], 4312), [
    "npm.cmd", "run", "dev", "--", "--host", "--port", "4312"
  ]);
  assert.deepEqual(commandWithProjectPort(["python.exe", "-m", "uvicorn", "main:app", "--port", "8000"], 8001), [
    "python.exe", "-m", "uvicorn", "main:app", "--port", "8001"
  ]);
  assert.deepEqual(commandWithProjectPort(["python.exe", "manage.py", "runserver", "127.0.0.1:8000"], 8001), [
    "python.exe", "manage.py", "runserver", "127.0.0.1:8001"
  ]);
  assert.deepEqual(commandWithProjectPort(["python.exe", "-m", "http.server", "8000"], 8001), [
    "python.exe", "-m", "http.server", "8001"
  ]);
  assert.deepEqual(commandWithProjectPort(["php", "-S", "127.0.0.1:8000"], 8001), [
    "php", "-S", "127.0.0.1:8001"
  ]);
});

test("prefers an available detected port outside the framework fallback range", async () => {
  const server = net.createServer();
  await listen(server, 0);
  const preferred = server.address().port;
  await close(server);
  const selected = await findAvailableProjectPort(preferred, [], [preferred + 1, preferred + 2]);
  assert.equal(selected, preferred);
});

test("sets or inserts the Flask port without changing other run arguments", () => {
  assert.equal(setPythonRunPort('app.run(host="0.0.0.0", port=5000)', 8001), 'app.run(host="0.0.0.0", port=8001)');
  assert.equal(setPythonRunPort("app.run(debug=True)", 8001), "app.run(debug=True, port=8001)");
  assert.equal(setPythonRunPort("app.run()", 8001), "app.run(port=8001)");
});

test("rewrites common fixed ports in Node server files", () => {
  assert.equal(setNodeServerPort("const PORT = 3000; app.listen(PORT);", 4312), "const PORT = 4312; app.listen(PORT);");
  assert.equal(setNodeServerPort("server.listen(9000, '127.0.0.1');", 4312), "server.listen(4312, '127.0.0.1');");
});
