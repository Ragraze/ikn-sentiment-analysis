'use client';

import Link from 'next/link';
import { useState } from 'react';
import { PanelHeader } from '@/components/panel-header';
import { ResourceState } from '@/components/resource-state';
import { useResource } from '@/hooks/use-resource';
import { number } from '@/lib/format';
import { names, sentiments } from '@/lib/sentiment';
import type { TopicsResponse } from '@/lib/types';

export function TopicSummary() {
  const [source, setSource] = useState('trained');
  const { data, loading, error, reload } = useResource<TopicsResponse>(`/api/topics?source=${source}`);
  const total = data?.available ? sentiments.reduce((sum, label) => sum + (data.groups[label]?.topics.length || 0), 0) : 0;
  const maximum = data?.available ? Math.max(1, ...sentiments.map(label => data.groups[label]?.topics.length || 0)) : 1;

  return (
    <section className="panel" aria-label="Grafik topik per sentimen">
      <PanelHeader title="Topik menurut sentimen">
        <label className="field-label" htmlFor="overview-topic-source">Sumber topik</label>
        <select id="overview-topic-source" value={source} onChange={event => setSource(event.target.value)}><option value="trained">Training proyek</option><option value="notebook">Hasil notebook</option></select>
      </PanelHeader>
      {loading || error ? <ResourceState loading={loading} error={error} onRetry={reload} /> : !data?.available || !total ? (
        <ResourceState title="Topik belum tersedia" message="Pilih hasil notebook atau buka pemodelan topik untuk memeriksa ketersediaan laporan." />
      ) : (
        <div className="topic-summary-chart">
          <div className="topic-summary-total"><strong>{number(total)}</strong><span>topik ditemukan<span>{source === 'trained' ? 'Hasil training proyek' : 'Hasil notebook penelitian'}</span></span></div>
          {sentiments.map(label => {
            const count = data.groups[label]?.topics.length || 0;
            return <div className="topic-summary-row" key={label}><span>{names[label]}</span><div className="chart-track" aria-hidden="true"><div className={`chart-fill ${label}`} style={{ width: `${count / maximum * 100}%` }} /></div><strong>{number(count)} topik</strong></div>;
          })}
          <p className="section-note">Sumber: {data.source}. Kelompok sentimen berasal dari prediksi IndoBERT pada korpus pemodelan topik.</p>
        </div>
      )}
      <div className="panel-link-row"><Link href={`/topics?source=${source}`}>Lihat kata kunci &amp; coherence</Link></div>
    </section>
  );
}
