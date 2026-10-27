import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { test } from 'node:test';
import ts from 'typescript';
import config from '../next.config.mjs';

const source = await readFile(new URL('../src/lib/api.ts', import.meta.url), 'utf8');
const compiled = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2020 } }).outputText;
const { api } = await import(`data:text/javascript;base64,${Buffer.from(compiled).toString('base64')}`);

test('Next.js forwards all dashboard API routes to Flask', async () => {
  const rewrites = await config.rewrites();
  assert.deepEqual(rewrites, [{ source: '/api/:path*', destination: `${(process.env.FLASK_API_URL || 'http://127.0.0.1:5000').replace(/\/$/, '')}/api/:path*` }]);
});

test('prediction request keeps its method, JSON body, and abort signal', async t => {
  const controller = new AbortController();
  const payload = JSON.stringify({ text: 'Saya mendukung IKN.' });
  t.mock.method(globalThis, 'fetch', async (url, options) => {
    assert.equal(url, '/api/predict');
    assert.equal(options.method, 'POST');
    assert.equal(options.body, payload);
    assert.equal(options.signal.aborted, false);
    controller.abort();
    assert.equal(options.signal.aborted, true);
    assert.equal(options.cache, 'no-store');
    return Response.json({ label: 'positive' });
  });
  assert.deepEqual(await api('/api/predict', { method: 'POST', body: payload, signal: controller.signal }), { label: 'positive' });
});

test('missing checkpoint is shown as the actual backend error', async t => {
  t.mock.method(globalThis, 'fetch', async () => Response.json({ error: 'Checkpoint IndoBERT belum dipasang.' }, { status: 503 }));
  await assert.rejects(api('/api/predict'), /Checkpoint IndoBERT belum dipasang/);
});

test('an unreachable or non-JSON backend has an actionable message', async t => {
  t.mock.method(globalThis, 'fetch', async () => new Response('Bad gateway', { status: 502 }));
  await assert.rejects(api('/api/summary'), /backend berjalan di port 5000/);
});

test('API requests reject external destinations before making a request', async t => {
  const request = t.mock.method(globalThis, 'fetch', async () => { throw new Error('must not fetch'); });
  for (const url of ['https://other.example/api/summary', '//other.example/api/summary', '/api/\\other.example']) {
    await assert.rejects(api(url), /Alamat API tidak valid/);
  }
  assert.equal(request.mock.callCount(), 0);
});

test('API transport errors do not expose internal diagnostics', async t => {
  t.mock.method(globalThis, 'fetch', async () => { throw new Error('internal-network-secret'); });
  await assert.rejects(api('/api/summary'), error => !error.message.includes('internal-network-secret') && error.message.includes('Periksa koneksi'));
});

test('aborted API requests retain their cancellation behavior', async t => {
  const controller = new AbortController();
  controller.abort();
  const abort = new DOMException('Cancelled', 'AbortError');
  t.mock.method(globalThis, 'fetch', async () => { throw abort; });
  await assert.rejects(api('/api/summary', { signal: controller.signal }), error => error === abort);
});

test('invalid JSON shapes and error fields are handled without crashing', async t => {
  for (const data of [null, [], 'invalid']) {
    t.mock.method(globalThis, 'fetch', async () => Response.json(data));
    await assert.rejects(api('/api/summary'), /Format respons layanan tidak valid/);
  }
  t.mock.method(globalThis, 'fetch', async () => Response.json({ error: { internal: 'details' } }, { status: 500 }));
  await assert.rejects(api('/api/summary'), /HTTP 500/);
});

test('security headers disable framing, MIME sniffing, and unused device permissions', async () => {
  const [{ headers }] = await config.headers();
  const values = Object.fromEntries(headers.map(({ key, value }) => [key, value]));
  assert.equal(values['X-Frame-Options'], 'DENY');
  assert.equal(values['X-Content-Type-Options'], 'nosniff');
  assert.equal(values['Referrer-Policy'], 'no-referrer');
  assert.equal(values['Permissions-Policy'], 'camera=(), microphone=(), geolocation=()');
});

test('production CSP requires a nonce and does not allow arbitrary inline scripts', async () => {
  const source = await readFile(new URL('../src/lib/content-security-policy.ts', import.meta.url), 'utf8');
  const compiled = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2020 } }).outputText;
  const { contentSecurityPolicy } = await import(`data:text/javascript;base64,${Buffer.from(compiled).toString('base64')}`);
  const policy = contentSecurityPolicy('test-nonce', false);
  const scripts = policy.split('; ').find(value => value.startsWith('script-src'));
  assert.match(scripts, /'nonce-test-nonce'/);
  assert.match(scripts, /'strict-dynamic'/);
  assert.ok(!scripts.includes('unsafe-inline'));
  assert.ok(!scripts.includes('unsafe-eval'));
  assert.ok(policy.includes("frame-ancestors 'none'"));
  assert.ok(policy.includes("object-src 'none'"));
  assert.ok(policy.includes("connect-src 'self';"));
  assert.throws(() => contentSecurityPolicy("invalid'; script-src *", false));
});
