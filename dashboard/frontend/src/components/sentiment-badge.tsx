import { names } from '@/lib/sentiment';
import type { Sentiment } from '@/lib/types';

export function SentimentBadge({ label }: { label: Sentiment }) {
  return <span className={`sentiment-badge ${label}`}>{names[label]}</span>;
}
