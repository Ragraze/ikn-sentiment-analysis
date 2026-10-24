import Link from 'next/link';
import { number } from '@/lib/format';
import { names } from '@/lib/sentiment';
import type { TopicAnalysis } from '@/lib/types';

export function TopicResult({ analysis }: { analysis: TopicAnalysis }) {
  const closest = analysis.topics[0];
  return (
    <section className="topic-result" aria-label="Hasil pemodelan topik">
      <div className="result-label"><h3>Topik kalimat</h3><span>Top2Vec</span></div>
      {analysis.matched && closest ? (
        <>
          <div className="topic-match-heading"><strong>Topik {closest.number + 1}</strong><span>Kelompok {names[analysis.sentiment].toLowerCase()}</span></div>
          <p className="topic-match-title">{closest.words.slice(0, 3).join(' · ')}</p>
          <ul className="keyword-list" aria-label="Kata kunci topik">{closest.words.map((word, index) => <li key={`${word}-${index}`}>{word}</li>)}</ul>
          <dl className="topic-match-meta"><div><dt>Kemiripan cosine</dt><dd>{closest.similarity.toFixed(4)}</dd></div>{closest.documents !== undefined && <div><dt>Opini dalam topik</dt><dd>{number(closest.documents)}</dd></div>}</dl>
          {analysis.topics.length > 1 && <details><summary>Topik pembanding ({analysis.topics.length - 1})</summary><div className="topic-alternatives">{analysis.topics.slice(1).map(topic => <div key={topic.number}><div><strong>Topik {topic.number + 1}</strong><p>{topic.words.slice(0, 5).join(', ')}</p></div><span>{topic.similarity.toFixed(4)}</span></div>)}</div></details>}
          <p className="section-note">Topik dipilih dari kelompok sentimen hasil IndoBERT. Kemiripan cosine berada pada rentang −1 sampai 1; angka lebih tinggi berarti lebih dekat, bukan probabilitas.</p>
        </>
      ) : (
        <div className="topic-unavailable"><h4>{analysis.available ? 'Belum ada topik yang cocok' : 'Analisis topik belum tersedia'}</h4><p>{analysis.message}</p><Link href="/topics">Lihat pemodelan topik</Link></div>
      )}
    </section>
  );
}
