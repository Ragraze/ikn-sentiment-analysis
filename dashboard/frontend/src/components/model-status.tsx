'use client';

import Link from 'next/link';
import { useModelHealth } from '@/hooks/use-model-health';
import type { Health } from '@/lib/types';

const modelTitles: Record<Health['state'], string> = {
  missing_checkpoint: 'Checkpoint belum tersedia',
  configured: 'Checkpoint terpasang',
  ready: 'Siap digunakan',
  error: 'Model belum dapat dimuat',
};

export function ModelStatus({ showAction = true }: { showAction?: boolean }) {
  const health = useModelHealth();
  const topicGroups = health.data?.topics?.groups;
  const availableTopics = topicGroups ? Object.values(topicGroups).filter(group => group.available).length : 0;
  return (
    <section className="panel model-status" aria-label="Status layanan analisis" aria-busy={health.loading}>
      <div className="status-heading"><h2>Layanan analisis</h2><button type="button" disabled={health.loading} onClick={health.reload}>Periksa ulang</button></div>
      <dl className="model-status-list">
        <div><dt>IndoBERT<span>Klasifikasi sentimen</span></dt><dd>{health.loading ? 'Memeriksa…' : health.data ? modelTitles[health.data.state] : 'Belum tersambung'}</dd></div>
        <div><dt>Top2Vec<span>Pemodelan topik</span></dt><dd>{health.loading ? 'Memeriksa…' : !health.data ? 'Belum tersambung' : availableTopics === 3 ? '3 model terpasang' : availableTopics > 0 ? `${availableTopics} dari 3 model terpasang` : 'Model belum tersedia'}</dd></div>
      </dl>
      {health.error ? <p className="notice error" role="alert">{health.error}</p> : <p className="section-note">Model dimuat pada analisis pertama. Hasil sentimen tetap dapat dibaca saat model topik belum tersedia.</p>}
      {showAction && <Link href="/analysis" className="button status-action">Buka analisis kalimat</Link>}
    </section>
  );
}
