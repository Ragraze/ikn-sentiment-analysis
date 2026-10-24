import assert from 'node:assert/strict';
import { IncomingMessage, ServerResponse } from 'node:http';
import { Duplex } from 'node:stream';

process.env.NODE_ENV = 'production';
const { default: next } = await import('next');

async function verifyRendering() {
  const app = next({ dev: false, dir: process.cwd(), hostname: 'localhost', port: 3000 });
  await app.prepare();

  async function render(url = '/') {
    const pathname = url.split('?')[0];
    const socket = new Duplex({ read() {}, write(chunk, encoding, callback) { callback(); } });
    socket.remoteAddress = '127.0.0.1';
    const request = new IncomingMessage(socket);
    request.url = url;
    request.method = 'GET';
    request.headers = { host: 'localhost:3000' };
    request.push(null);
    const response = new ServerResponse(request);
    response.assignSocket(socket);
    let body = '';
    const write = response.write.bind(response);
    const end = response.end.bind(response);
    response.write = (chunk, ...args) => { body += chunk.toString(); return write(chunk, ...args); };
    response.end = (chunk, ...args) => { if (chunk) body += chunk.toString(); return end(chunk, ...args); };
    await app.getRequestHandler()(request, response);
    assert.equal(response.statusCode, 200);
    assert.equal(response.getHeader('cache-control'), 'private, no-store');
    assert.equal(response.getHeader('x-frame-options'), 'DENY');
    const policy = response.getHeader('content-security-policy');
    const nonce = policy.match(/'nonce-([^']+)'/)[1];
    const scripts = [...body.matchAll(/<script\b[^>]*>/g)];
    assert.ok(scripts.length > 0, 'rendered page contains hydration scripts');
    for (const [tag] of scripts) assert.ok(tag.includes(`nonce="${nonce}"`), 'all scripts use the response nonce');
    assert.ok(body.includes('Analisis kalimat'));
    assert.ok(body.includes('Langsung ke konten'));
    assert.ok(body.includes('class="desktop-sidebar"'));
    assert.ok(body.includes('aria-controls="mobile-sidebar"'));
    assert.ok(body.includes('<dialog'));
    assert.ok(!body.includes('class="site-header"'));
    for (const route of ['/', '/analysis', '/dataset', '/topics', '/evaluation']) {
      assert.ok(body.includes(`href="${route}"`));
    }
    const activeLinks = [...body.matchAll(/<a\b[^>]*aria-current="page"[^>]*>/g)];
    assert.equal(activeLinks.length, 2, 'desktop and mobile sidebars each identify the current page');
    for (const [tag] of activeLinks) assert.ok(tag.includes(`href="${pathname}"`), `active destination matches ${pathname}`);
    const sections = { '/analysis': 'predict', '/dataset': 'dataset', '/topics': 'topics', '/evaluation': 'evaluation' };
    for (const [route, id] of Object.entries(sections)) {
      assert.equal(body.includes(`<section id="${id}"`), route === pathname, 'only the requested feature is rendered');
    }
    if (url === '/') {
      for (const title of ['Dashboard penelitian', 'Proporsi sentimen', 'Sebaran pada tiap bagian data', 'Topik menurut sentimen']) assert.ok(body.includes(title));
    }
    assert.equal([...body.matchAll(/<h1\b/g)].length, 1, 'each page has one main title');
    const redundantTitles = { '/analysis': 'Analisis sentimen &amp; topik', '/dataset': 'Dataset opini', '/topics': 'Peta topik percakapan', '/evaluation': 'Evaluasi klasifikasi' };
    if (redundantTitles[pathname]) assert.ok(!body.includes(`<h2>${redundantTitles[pathname]}</h2>`), 'feature cards do not repeat the page title');
    if (pathname === '/topics') {
      const selected = url.includes('source=notebook') ? 'notebook' : 'trained';
      assert.ok(body.includes(`<option value="${selected}" selected=""`), 'topic detail uses the selected report source');
    }
    if (pathname === '/analysis') {
      assert.ok(body.includes('aria-keyshortcuts="Control+Enter Meta+Enter"'));
      assert.ok(body.includes('Opini yang ingin dianalisis'));
      assert.ok(body.includes('Hasil analisis'));
      assert.ok(body.includes('Isian dan hasil terakhir tetap ada saat berpindah menu'));
    }
    if (pathname === '/dataset') {
      assert.ok(body.includes('dataset-search-help'));
      assert.ok(body.includes('Opini per halaman'));
      assert.ok(body.includes('aria-label="Halaman dataset"'));
    }
    if (pathname === '/evaluation') {
      assert.ok(body.includes('Cara membaca metrik evaluasi'));
      assert.ok(body.includes('Hasil notebook'));
      assert.ok(!body.includes('id="evaluation-source"'));
      assert.ok(!body.includes('Checkpoint aktif'));
    }
    socket.destroy();
    return nonce;
  }

  try {
    const first = await render();
    const second = await render();
    assert.notEqual(first, second);
    for (const route of ['/analysis', '/dataset', '/topics', '/evaluation']) await render(route);
    await render('/topics?source=notebook');
  } finally {
    await app.close();
  }
}

await verifyRendering();
console.log('PASS: five dashboard routes, active sidebar links, isolated page content, mobile dialog, production CSP nonces, and security headers.');
