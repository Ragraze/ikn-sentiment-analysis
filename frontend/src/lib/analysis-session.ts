import { percent } from '@/lib/format';
import { names, sentiments } from '@/lib/sentiment';
import type { Prediction } from '@/lib/types';

export type AnalysisSnapshot = { text: string; result: Prediction | null };
export type AnalysisSession = AnalysisSnapshot & { undo: AnalysisSnapshot | null };
export const initialAnalysisSession: AnalysisSession = { text: '', result: null, undo: null };
type AnalysisAction =
  | { type: 'edit'; text: string }
  | { type: 'start' }
  | { type: 'result'; text: string; result: Prediction }
  | { type: 'clear' }
  | { type: 'restore' };

export function analysisSessionReducer(state: AnalysisSession, action: AnalysisAction): AnalysisSession {
  switch (action.type) {
    case 'edit':
      return { text: action.text, result: null, undo: null };
    case 'start':
      return { ...state, result: null, undo: null };
    case 'result':
      return action.text === state.text.trim() ? { ...state, result: action.result, undo: null } : state;
    case 'clear':
      return state.text || state.result ? { text: '', result: null, undo: { text: state.text, result: state.result } } : state;
    case 'restore':
      return state.undo ? { ...state.undo, undo: null } : state;
  }
}

export function sentenceError(text: string): string {
  if (!text.trim()) return 'Tulis opini tentang IKN sebelum menganalisis.';
  if (!/\p{L}/u.test(text)) return 'Kalimat perlu mengandung huruf. Tambahkan opini dalam bahasa Indonesia.';
  if (text.length > 2000) return 'Kalimat terlalu panjang. Ringkas menjadi maksimal 2.000 karakter.';
  if (/[\u0000-\u0008\u000b\u000c\u000e-\u001f]/u.test(text)) return 'Hapus karakter kontrol dari teks, lalu coba lagi.';
  return '';
}

export function formatAnalysisReport(text: string, result: Prediction): string {
  const lines = ['Analisis opini IKN', '', `Kalimat: ${text.trim()}`, `Sentimen: ${names[result.label]}`,
    `Skor sentimen: ${percent(result.confidence)}`, ...sentiments.map(label => `${names[label]}: ${percent(result.scores[label])}`)];
  const analysis = result.topic_analysis;
  const topic = analysis?.matched ? analysis.topics[0] : undefined;
  if (topic) {
    lines.push('', `Topik ${topic.number + 1} (kelompok ${names[analysis.sentiment].toLowerCase()})`,
      `Kata kunci: ${topic.words.join(', ')}`, `Kemiripan cosine: ${topic.similarity.toFixed(4)}`);
  } else {
    lines.push('', `Topik: ${analysis?.message || 'Belum tersedia.'}`);
  }
  lines.push('', 'Skor model bukan kepastian. Kemiripan cosine topik bukan probabilitas sentimen.');
  return lines.join('\n');
}
