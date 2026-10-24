'use client';

import { useEffect, useRef, useState } from 'react';
import type { FormEvent } from 'react';
import { SentimentBadge } from '@/components/sentiment-badge';
import { TopicResult } from '@/components/topic-result';
import { useAnalysisSession } from '@/hooks/use-analysis-session';
import { api } from '@/lib/api';
import { formatAnalysisReport, sentenceError } from '@/lib/analysis-session';
import { errorMessage, number, percent } from '@/lib/format';
import { names, sentiments } from '@/lib/sentiment';
import type { Health, Prediction } from '@/lib/types';

const examples = [
  { label: 'Dukungan', text: 'Saya mendukung pembangunan IKN untuk membuka peluang ekonomi baru.' },
  { label: 'Kritik', text: 'Pembangunan IKN hanya membuang anggaran dan merugikan rakyat.' },
  { label: 'Informasi', text: 'IKN terletak di Kalimantan Timur.' },
];

export function PredictionForm({ health, refreshHealth }: { health: Health | null; refreshHealth: () => void }) {
  const { session, dispatch } = useAnalysisSession();
  const { text, result } = session;
  const [inputError, setInputError] = useState('');
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [loading, setLoading] = useState(false);
  const [copying, setCopying] = useState(false);
  const [copyFeedback, setCopyFeedback] = useState('');
  const request = useRef<AbortController | null>(null);
  const actionVersion = useRef(0);
  const textarea = useRef<HTMLTextAreaElement>(null);
  const form = useRef<HTMLFormElement>(null);
  const resultHeading = useRef<HTMLHeadingElement>(null);
  const configured = health && (health.state === 'configured' || health.state === 'ready');

  useEffect(() => () => { request.current?.abort(); actionVersion.current += 1; }, []);
  useEffect(() => {
    if (result && form.current?.contains(document.activeElement)) resultHeading.current?.focus();
  }, [result]);

  function resetFeedback() {
    request.current?.abort();
    request.current = null;
    actionVersion.current += 1;
    setInputError('');
    setError('');
    setNotice('');
    setCopying(false);
    setCopyFeedback('');
    setLoading(false);
  }

  function edit(value: string) {
    resetFeedback();
    dispatch({ type: 'edit', text: value });
  }

  function clear() {
    resetFeedback();
    dispatch({ type: 'clear' });
    textarea.current?.focus();
  }

  function restore() {
    resetFeedback();
    dispatch({ type: 'restore' });
    setNotice('Kalimat dan hasil sebelumnya dipulihkan.');
    textarea.current?.focus();
  }

  function cancel() {
    resetFeedback();
    setNotice('Tampilan analisis dibatalkan. Kalimat tetap tersimpan di halaman ini.');
    textarea.current?.focus();
  }

  async function copyResult() {
    if (!result || copying) return;
    const version = actionVersion.current;
    setCopying(true);
    setCopyFeedback('');
    try {
      if (!navigator.clipboard?.writeText) throw new Error('Clipboard tidak tersedia.');
      await navigator.clipboard.writeText(formatAnalysisReport(text, result));
      if (version === actionVersion.current) setCopyFeedback('Hasil analisis disalin.');
    } catch {
      if (version === actionVersion.current) setCopyFeedback('Hasil belum tersalin. Izinkan akses clipboard atau pilih teks hasil untuk menyalinnya.');
    } finally {
      if (version === actionVersion.current) setCopying(false);
    }
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (loading || request.current) return;
    const validation = sentenceError(text);
    if (validation) {
      setInputError(validation);
      textarea.current?.focus();
      return;
    }
    if (!configured) {
      setError('Layanan analisis belum siap. Periksa layanan di bawah form, lalu coba lagi.');
      return;
    }
    const controller = new AbortController();
    request.current = controller;
    actionVersion.current += 1;
    const submittedText = text.trim();
    setLoading(true);
    setCopying(false);
    setCopyFeedback('');
    setInputError('');
    setError('');
    setNotice('');
    dispatch({ type: 'start' });
    try {
      const prediction = await api<Prediction>('/api/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: submittedText }),
        signal: controller.signal,
      });
      if (!controller.signal.aborted) {
        dispatch({ type: 'result', text: submittedText, result: prediction });
        setNotice(`Analisis selesai. Sentimen ${names[prediction.label].toLowerCase()}${prediction.topic_analysis?.matched ? ', topik ditemukan.' : '.'}`);
        refreshHealth();
      }
    } catch (error) {
      if (!controller.signal.aborted) setError(errorMessage(error));
    } finally {
      if (request.current === controller) request.current = null;
      if (!controller.signal.aborted) setLoading(false);
    }
  }

  return (
    <section id="predict" className="panel section-space prediction-section analysis-workspace">
      <div className="prediction-layout">
        <form ref={form} onSubmit={submit} noValidate>
          <div className="editor-intro"><h2>Opini yang ingin dianalisis</h2><p>Gunakan kalimat lengkap agar konteksnya terbaca.</p></div>
          <label htmlFor="sentence">Kalimat dalam bahasa Indonesia</label>
          <textarea ref={textarea} id="sentence" value={text} onChange={event => edit(event.target.value)} onBlur={() => { if (text.trim()) setInputError(sentenceError(text)); }} onKeyDown={event => {
            if (event.nativeEvent.isComposing) return;
            if ((event.metaKey || event.ctrlKey) && event.key === 'Enter') { event.preventDefault(); form.current?.requestSubmit(); }
            if (event.key === 'Escape' && loading) { event.preventDefault(); cancel(); }
          }} rows={7} maxLength={2000} placeholder="Tulis opini tentang IKN…" aria-describedby={`input-help${inputError ? ' sentence-error' : ''}`} aria-invalid={Boolean(inputError)} />
          <div className={`input-meta${text.length >= 1800 ? ' input-near-limit' : ''}`}><span id="input-help">Maksimal 2.000 karakter.</span><span>{number(text.length)} / 2.000</span></div>
          {inputError && <p className="field-error" id="sentence-error" role="alert">{inputError}</p>}
          <div className="example-buttons"><span>Pilih contoh untuk mengisi kolom:</span>{examples.map(example => <button type="button" key={example.label} onClick={() => { edit(example.text); textarea.current?.focus(); }}>{example.label}</button>)}</div>
          <div className="form-actions">
            <button className="button primary" type="submit" disabled={loading || !text.trim()} aria-keyshortcuts="Control+Enter Meta+Enter">{loading ? 'Menganalisis…' : 'Analisis kalimat'}</button>
            {loading ? <button type="button" onClick={cancel}>Batalkan</button> : <button type="button" disabled={!text && !result} onClick={clear}>Kosongkan</button>}
          </div>
          {session.undo && <div className="undo-feedback"><span>Kalimat dikosongkan.</span><button type="button" onClick={restore}>Urungkan</button></div>}
          {error && <p className="feature-error" role="alert">{error}</p>}
          <p className="editor-shortcut"><kbd>Ctrl</kbd> / <kbd>⌘</kbd> + <kbd>Enter</kbd> untuk analisis.</p>
          <p className="section-note editor-retention">Isian dan hasil terakhir tetap ada saat berpindah menu. Memuat ulang halaman akan mengosongkannya.</p>
        </form>
        <div className="result-panel" aria-label="Hasil analisis kalimat" aria-busy={loading}>
          <div className="analysis-result-toolbar"><h2 ref={resultHeading} tabIndex={-1}>Hasil analisis</h2>{result && <button type="button" onClick={copyResult} disabled={copying}>{copying ? 'Menyalin…' : 'Salin hasil'}</button>}</div>
          <p className="copy-feedback" role="status">{copyFeedback}</p>
          {result ? (
            <div className="prediction-result">
              <div className="result-label"><h3>Sentimen kalimat</h3><span>IndoBERT</span></div>
              <h3 className="prediction-title"><SentimentBadge label={result.label} /></h3>
              <p>Skor tertinggi <strong>{percent(result.confidence)}</strong></p>
              <div className="score-bars">
                {sentiments.map(label => <div className="score-row" key={label}><div className="chart-label"><span>{names[label]}</span><strong>{percent(result.scores[label])}</strong></div><div className="chart-track" aria-hidden="true"><div className={`chart-fill ${label}`} style={{ width: `${Math.max(0, Math.min(1, result.scores[label])) * 100}%` }} /></div></div>)}
              </div>
              <details><summary>Lihat teks setelah preprocessing</summary><p>{result.normalized}</p></details>
              {result.topic_analysis && <TopicResult analysis={result.topic_analysis} />}
              <p className="section-note">Model dapat keliru pada sarkasme dan konteks ambigu. Skor model bukan kepastian sentimen.</p>
            </div>
          ) : (
            <div className="prediction-empty">
              {loading ? <progress aria-label="Memproses analisis kalimat" /> : <div className="empty-analysis-mark" aria-hidden="true"><span /><span /><span /></div>}
              <h3>{loading ? 'Sedang membaca opini…' : 'Mulai dari satu opini'}</h3>
              <p>{loading ? 'Kalimat sedang diproses. Pemuatan model pertama dapat membutuhkan waktu lebih lama.' : 'Tulis kalimat di sebelah kiri atau pilih contoh. Sentimen, kata kunci, dan topik terdekat akan muncul di sini.'}</p>
              {!configured && !loading && <p className="section-note">Model belum tersambung. Periksa layanan analisis di bawah form ini.</p>}
            </div>
          )}
        </div>
      </div>
      <p className="analysis-announcement" role="status" aria-live="polite">{notice}</p>
    </section>
  );
}
