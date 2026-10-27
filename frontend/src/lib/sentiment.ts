import type { Sentiment, Split } from './types';

export const sentiments: Sentiment[] = ['negative', 'neutral', 'positive'];
export const names: Record<Sentiment, string> = {
  negative: 'Negatif',
  neutral: 'Netral',
  positive: 'Positif',
};
export const splitNames: Record<Split, string> = {
  train: 'Training',
  val: 'Validasi',
  test: 'Pengujian',
};
