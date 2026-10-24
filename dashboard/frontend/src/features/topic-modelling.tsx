'use client';

import { useState } from 'react';
import Link from 'next/link';
import { ResourceState } from '@/components/resource-state';
import { useResource } from '@/hooks/use-resource';
import { number } from '@/lib/format';
import { names, sentiments } from '@/lib/sentiment';
import type { Sentiment, TopicsResponse } from '@/lib/types';

export function TopicModelling({ initialSource = 'trained' }: { initialSource?: 'trained' | 'notebook' }) {
  const [sentiment, setSentiment] = useState<Sentiment>('positive');
  const [source, setSource] = useState<string>(initialSource);
  const { data, loading, error, reload } = useResource<TopicsResponse>(`/api/topics?source=${source}`);
  const group = data?.groups?.[sentiment];

  return (
    <section id="topics" className="panel section-space topics-section">
      <div className="topic-source-toolbar">
        <label htmlFor="topic-source">Sumber topik<select id="topic-source" value={source} onChange={event => setSource(event.target.value)}><option value="notebook">Hasil notebook</option><option value="trained">Hasil training proyek</option></select></label>
      </div>
      <div className="topic-toolbar">
        <div className="segmented-control" role="group" aria-label="Sentimen untuk topik">
          {sentiments.map(label => <button key={label} type="button" aria-pressed={sentiment === label} onClick={() => setSentiment(label)}>{names[label]}</button>)}
        </div>
        {!loading && group && data?.available && <span className="muted">{number(group.topics.length)} topik{group.documents !== undefined && ` · ${number(group.documents)} opini`}</span>}
      </div>
      {loading || error ? <ResourceState loading={loading} error={error} onRetry={reload} /> : !data?.available ? (
        <ResourceState title="Hasil topik belum tersedia" message={data?.message || (source === 'trained' ? 'Pengelola perlu menjalankan pemodelan Top2Vec untuk menampilkan hasil training proyek.' : 'Output pemodelan topik pada notebook belum tersedia.')} />
      ) : (
        <div className="topic-layout">
          <div className="topic-list">
            {group?.topics.length ? group.topics.map(topic => (
              <article className="topic" key={topic.number}>
                <div className="topic-card-heading"><h3>Topik {topic.number + 1}</h3><span>{topic.documents !== undefined ? `${number(topic.documents)} opini` : names[sentiment]}</span></div>
                <p className="topic-name">{topic.words.slice(0, 3).join(' · ')}</p>
                {topic.word_scores ? <div className="keyword-chart" aria-label="Kemiripan kata terhadap topik">{topic.words.slice(0, 6).map((word, index) => <div key={`${word}-${index}`}><span>{word}</span><div className="chart-track" aria-hidden="true"><div className="keyword-fill" style={{ width: `${Math.max(0, Math.min(1, topic.word_scores?.[index] || 0)) * 100}%` }} /></div><strong>{topic.word_scores?.[index].toFixed(3)}</strong></div>)}</div> : <ul className="keyword-list" aria-label="Kata pembentuk topik">{topic.words.slice(3, 12).map((word, index) => <li key={`${word}-${index}`}>{word}</li>)}</ul>}
                <details><summary>Semua kata kunci{topic.word_scores ? ' & bobot' : ''}</summary>{topic.word_scores ? <dl className="word-weights">{topic.words.map((word, index) => <div key={`${word}-${index}`}><dt>{word}</dt><dd>{topic.word_scores?.[index].toFixed(4)}</dd></div>)}</dl> : <p className="topic-words">{topic.words.join(', ')}</p>}</details>
              </article>
            )) : <ResourceState title="Belum ada topik untuk sentimen ini" message="Pilih kategori sentimen lain." />}
          </div>
          <div className="coherence-section">
            <h3>Coherence per sentimen</h3>
            <p className="muted">Seberapa berkaitan kata-kata dalam topik? Skor c_v dihitung pada korpus setiap kategori.</p>
            {sentiments.map(label => {
              const score = data.groups[label]?.coherence;
              return (
                <div className="coherence-row" key={label}>
                  <div className="chart-label"><span>{names[label]}</span><strong>{score != null ? score.toFixed(4) : 'Belum tersedia'}</strong></div>
                  <div className="chart-track" aria-hidden="true"><div className={`chart-fill ${label}`} style={{ width: `${Math.max(0, Math.min(1, score || 0)) * 100}%` }} /></div>
                </div>
              );
            })}
            <div className="topic-explainer"><h3>Dari sentimen ke topik</h3><p>IndoBERT membaca sikap sebuah opini. Top2Vec mengelompokkan pembicaraannya, lalu mencari topik terdekat untuk kalimat baru.</p><Link href="/analysis">Coba analisis kalimat</Link><p className="section-note">Kata kunci membentuk ringkasan topik, bukan nama kategori yang ditentukan sebelumnya. Hasil notebook hanya menyimpan laporan; pencocokan kalimat memerlukan model Top2Vec proyek.</p></div>
          </div>
        </div>
      )}
      {data?.available && <p className="section-note panel-note">Sumber: {data.source}. {source === 'notebook' ? 'Hasil tersimpan dari eksekusi notebook penelitian.' : 'Hasil training Top2Vec proyek.'}</p>}
    </section>
  );
}
