'use client';

import Link from 'next/link';
import { useState } from 'react';
import { SentimentDonut, SplitDistribution } from '@/components/dataset-charts';
import { ModelStatus } from '@/components/model-status';
import { PanelHeader } from '@/components/panel-header';
import { ResourceState } from '@/components/resource-state';
import { TopicSummary } from '@/features/topic-summary';
import { useResource } from '@/hooks/use-resource';
import { number, percent } from '@/lib/format';
import { sentiments, splitNames } from '@/lib/sentiment';
import type { Split, Summary } from '@/lib/types';

export function Overview() {
  const { data, loading, error, reload } = useResource<Summary>('/api/summary');
  const [split, setSplit] = useState<'all' | Split>('all');
  const selected = data && (split === 'all' ? { count: data.total, counts: data.counts } : data.splits[split]);
  const selectedCount = selected ? sentiments.reduce((sum, label) => sum + selected.counts[label], 0) : 0;

  return (
    <>
      <dl className="summary-strip" aria-label="Ringkasan dataset" aria-busy={loading}>
        <div className="summary-total"><dt>Total opini</dt><dd>{data ? number(data.total) : loading ? '…' : 'Belum tersedia'}</dd><span>Dataset penelitian IKN</span></div>
        {(['train', 'val', 'test'] as Split[]).map(key => (
          <div key={key}><dt>Data {splitNames[key].toLowerCase()}</dt><dd>{data ? number(data.splits[key].count) : loading ? '…' : 'Belum tersedia'}</dd><span>{data && data.total > 0 ? `${percent(data.splits[key].count / data.total)} dari seluruh opini` : 'Pembagian dataset'}</span></div>
        ))}
      </dl>
      <div className="overview-charts">
        <section className="panel" aria-label="Grafik proporsi sentimen">
          <PanelHeader title="Proporsi sentimen" description="Bagaimana komposisi label opini dalam dataset?">
            <label className="field-label" htmlFor="distribution-split">Bagian dataset</label>
            <select id="distribution-split" value={split} onChange={event => setSplit(event.target.value as 'all' | Split)}>
              <option value="all">Semua data</option>
              {Object.entries(splitNames).map(([value, label]) => <option value={value} key={value}>{label}</option>)}
            </select>
          </PanelHeader>
          {loading || error || !selected ? <ResourceState loading={loading} error={error} onRetry={reload} title="Dataset belum tersedia" message="Tambahkan data penelitian untuk melihat distribusi." /> : selectedCount === 0 ? <ResourceState title="Bagian ini belum memiliki opini" message="Pilih bagian dataset lain." /> : (
            <>
              <SentimentDonut counts={selected.counts} />
              <p className="chart-caption">{number(selectedCount)} opini · {split === 'all' ? 'Semua bagian dataset' : splitNames[split]}. Menggunakan label asli penelitian.</p>
            </>
          )}
        </section>
        <section className="panel" aria-label="Grafik sentimen per bagian dataset">
          <PanelHeader title="Sebaran pada tiap bagian data" description="Bandingkan jumlah opini per sentimen pada training, validasi, dan pengujian." />
          {loading || error || !data ? <ResourceState loading={loading} error={error} onRetry={reload} title="Dataset belum tersedia" message="Data penelitian diperlukan untuk membuat perbandingan." /> : <SplitDistribution data={data.splits} />}
        </section>
      </div>
      <div className="overview-secondary">
        <TopicSummary />
        <ModelStatus />
      </div>
      <div className="research-note"><div><h2>Tentang data ini</h2><p>Grafik sentimen memakai label asli dataset. Grafik topik memakai hasil pengelompokan opini berdasarkan prediksi IndoBERT, sehingga sumber dan jumlah dokumennya berbeda.</p></div><Link href="/dataset">Telusuri dataset</Link></div>
    </>
  );
}
