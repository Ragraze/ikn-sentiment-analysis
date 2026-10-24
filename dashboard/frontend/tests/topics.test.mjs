import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { test } from 'node:test';
import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import ts from 'typescript';

const require = createRequire(import.meta.url);
const modules = new Map();
function loadComponent(path) {
  if (modules.has(path)) return modules.get(path).exports;
  const source = readFileSync(new URL(`../src/${path}`, import.meta.url), 'utf8');
  const compiled = ts.transpileModule(source, {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020, jsx: ts.JsxEmit.ReactJSX },
  }).outputText;
  const module = { exports: {} };
  modules.set(path, module);
  const resolve = name => name.startsWith('@/') ? loadComponent(`${name.slice(2)}.ts`) : require(name);
  new Function('require', 'module', 'exports', compiled)(resolve, module, module.exports);
  return module.exports;
}

const { TopicResult } = loadComponent('components/topic-result.tsx');
const { SentimentDonut, SplitDistribution } = loadComponent('components/dataset-charts.tsx');
const { analysisSessionReducer, initialAnalysisSession, sentenceError, formatAnalysisReport } = loadComponent('lib/analysis-session.ts');
const analysis = {
  model: 'Top2Vec', sentiment: 'negative', available: true, matched: true, state: 'ready',
  topics: [
    { number: 7, words: ['anggaran', 'pembangunan', 'ikn'], similarity: .75432, documents: 35 },
    { number: 2, words: ['hutan', 'lingkungan'], similarity: -.12345, documents: 90 },
  ],
};

test('topic results show actual topic IDs, keywords, counts, and signed cosine values', () => {
  const html = renderToStaticMarkup(createElement(TopicResult, { analysis }));
  assert.match(html, /Topik 8/);
  assert.match(html, /anggaran/);
  assert.match(html, /Kelompok negatif/);
  assert.match(html, /0\.7543/);
  assert.match(html, /35/);
  assert.match(html, /Topik pembanding \(1\)/);
  assert.match(html, /-0\.1235/);
  assert.match(html, /bukan probabilitas/);
  assert.ok(!html.includes('%'), 'cosine similarity is not rendered as a confidence percentage');
});

test('unavailable and unmatched topics have distinct states with a working destination', () => {
  for (const [available, heading] of [[false, 'Analisis topik belum tersedia'], [true, 'Belum ada topik yang cocok']]) {
    const html = renderToStaticMarkup(createElement(TopicResult, {
      analysis: { ...analysis, available, matched: false, topics: [], message: 'Coba kalimat IKN yang lebih lengkap.' },
    }));
    assert.ok(html.includes(heading));
    assert.match(html, /Coba kalimat IKN yang lebih lengkap/);
    assert.match(html, /href="\/topics"/);
    assert.ok(!html.includes('Kemiripan cosine'));
  }
});

test('corpus content is escaped and a single topic does not offer empty alternatives', () => {
  const html = renderToStaticMarkup(createElement(TopicResult, {
    analysis: { ...analysis, topics: [{ ...analysis.topics[0], words: ['<script>alert(1)</script>'] }] },
  }));
  assert.ok(!html.includes('<script>'));
  assert.match(html, /&lt;script&gt;/);
  assert.ok(!html.includes('Topik pembanding'));
});

test('sentiment charts expose counts and percentages in accessible text', () => {
  const html = renderToStaticMarkup(createElement(SentimentDonut, { counts: { positive: 2, neutral: 1, negative: 7 } }));
  assert.match(html, /role="img"/);
  assert.match(html, /Positif: 2 opini \(20,0%\)/);
  assert.match(html, /Netral: 1 opini \(10,0%\)/);
  assert.match(html, /Negatif: 7 opini \(70,0%\)/);
  assert.match(html, /<strong>10<\/strong>/);
});

test('charts handle empty and single-category data without invalid geometry', () => {
  const empty = renderToStaticMarkup(createElement(SentimentDonut, { counts: { positive: 0, neutral: 0, negative: 0 } }));
  assert.match(empty, /Belum ada opini/);
  assert.ok(!empty.includes('<svg'));
  const single = renderToStaticMarkup(createElement(SentimentDonut, { counts: { positive: 3, neutral: 0, negative: 0 } }));
  assert.match(single, /100,0%/);
  assert.equal([...single.matchAll(/<circle /g)].length, 1);
  assert.ok(!single.includes('NaN') && !single.includes('Infinity'));
});

test('dataset comparison charts provide a table with all three splits and sentiment counts', () => {
  const data = {
    train: { count: 18, counts: { positive: 3, neutral: 4, negative: 11 } },
    val: { count: 9, counts: { positive: 1, neutral: 2, negative: 6 } },
    test: { count: 7, counts: { positive: 1, neutral: 1, negative: 5 } },
  };
  const html = renderToStaticMarkup(createElement(SplitDistribution, { data }));
  assert.match(html, /Training: Negatif 11, Netral 4, Positif 3/);
  assert.match(html, /Validasi: Negatif 6, Netral 2, Positif 1/);
  assert.match(html, /Pengujian: Negatif 5, Netral 1, Positif 1/);
  assert.match(html, /Lihat angka pada grafik/);
  assert.match(html, /<caption/);
  assert.equal([...html.matchAll(/<td>/g)].length, 9);
});

const prediction = {
  label: 'negative', confidence: .8, scores: { negative: .8, neutral: .15, positive: .05 },
  normalized: 'anggaran bangun ikn', model: 'IndoBERT', base_model: 'fixture', topic_analysis: analysis,
};

test('clearing an opinion can restore the text and its matching result together', () => {
  const text = 'Anggaran pembangunan IKN.';
  let session = analysisSessionReducer(initialAnalysisSession, { type: 'edit', text });
  session = analysisSessionReducer(session, { type: 'result', text, result: prediction });
  assert.equal(session.result, prediction);
  session = analysisSessionReducer(session, { type: 'clear' });
  assert.equal(session.text, '');
  assert.equal(session.result, null);
  session = analysisSessionReducer(session, { type: 'restore' });
  assert.equal(session.text, text);
  assert.equal(session.result, prediction);
  assert.equal(session.undo, null);
});

test('editing an opinion discards its old result and rejects a late response for different text', () => {
  let session = analysisSessionReducer(initialAnalysisSession, { type: 'edit', text: 'Opini pertama IKN.' });
  session = analysisSessionReducer(session, { type: 'edit', text: 'Opini kedua IKN.' });
  session = analysisSessionReducer(session, { type: 'result', text: 'Opini pertama IKN.', result: prediction });
  assert.equal(session.text, 'Opini kedua IKN.');
  assert.equal(session.result, null);
  session = analysisSessionReducer(session, { type: 'result', text: 'Opini kedua IKN.', result: prediction });
  session = analysisSessionReducer(session, { type: 'edit', text: 'Opini berikutnya.' });
  assert.equal(session.result, null);
});

test('inline validation permits Indonesian text and line breaks while rejecting unsupported input', () => {
  for (const text of ['', '   ', '12345', 'IKN\u0000', 'a'.repeat(2001)]) assert.ok(sentenceError(text));
  assert.equal(sentenceError('Saya mendukung IKN.\nSemoga pembangunan bermanfaat.'), '');
  assert.equal(sentenceError('IKN\tNusantara'), '');
});

test('copied reports include the opinion, sentiment scores, and signed topic cosine', () => {
  const text = 'Anggaran pembangunan IKN.';
  const report = formatAnalysisReport(text, prediction);
  assert.ok(report.includes(text));
  assert.ok(report.includes('Negatif: 80,0%'));
  assert.ok(report.includes('Netral: 15,0%'));
  assert.ok(report.includes('Positif: 5,0%'));
  assert.ok(report.includes('Topik 8 (kelompok negatif)'));
  assert.ok(report.includes('Kemiripan cosine: 0.7543'));
  assert.ok(!report.includes('75,4%'));
  const unavailable = formatAnalysisReport(text, { ...prediction, topic_analysis: { ...analysis, matched: false, topics: [], message: 'Model topik belum tersedia.' } });
  assert.ok(unavailable.includes('Model topik belum tersedia.'));
  assert.ok(!unavailable.includes('Kemiripan cosine:'));
});
