'use client';

import type { CSSProperties } from 'react';
import { ResourceState } from '@/components/resource-state';
import { SentimentBadge } from '@/components/sentiment-badge';
import { useResource } from '@/hooks/use-resource';
import { number, percent } from '@/lib/format';
import { names } from '@/lib/sentiment';
import type { Evaluation } from '@/lib/types';

export function EvaluationPanel() {
  const { data: report, loading, error, reload } = useResource<Evaluation>('/api/evaluation?source=notebook');

  return (
    <section id="evaluation" className="panel section-space evaluation-workspace">
      <div className="evaluation-source-context"><strong>Hasil notebook</strong><p>Metrik dihitung dari CSV prediksi yang tersimpan pada penelitian.</p></div>
      {loading || error ? <ResourceState loading={loading} error={error} onRetry={reload} /> : !report?.available ? (
        <ResourceState title="Evaluasi belum tersedia" message={report?.message || 'File prediksi hasil notebook belum tersedia. Periksa dataset penelitian.'} />
      ) : (
        <>
          <dl className="evaluation-stats">
            <div><dt>Akurasi</dt><dd>{percent(report.accuracy || 0)}</dd><span>Proporsi prediksi yang benar</span></div>
            <div><dt>Macro F1</dt><dd>{(report.macro_f1 || 0).toLocaleString('id-ID', { minimumFractionDigits: 3, maximumFractionDigits: 3 })}</dd><span>Rata-rata F1 ketiga sentimen</span></div>
            <div><dt>Data uji</dt><dd>{number(report.count || 0)}</dd><span>Opini pada evaluasi notebook</span></div>
          </dl>
          <div className="evaluation-grid">
            <div className="matrix-wrap">
              <h3>Confusion matrix</h3>
              <p className="muted">Baris: label aktual. Kolom: prediksi model.</p>
              <div className="table-scroll" tabIndex={0} role="region" aria-label="Confusion matrix yang dapat digulir">
                <table className="matrix">
                  <caption className="sr-only">Jumlah prediksi untuk setiap pasangan label aktual dan prediksi</caption>
                  <thead><tr><th scope="col">Aktual / Prediksi</th>{report.labels?.map(label => <th scope="col" key={label}>{names[label]}</th>)}</tr></thead>
                  <tbody>{report.confusion?.map((row, index) => {
                    const total = row.reduce((sum, count) => sum + count, 0);
                    return <tr key={index}><th scope="row">{report.labels ? names[report.labels[index]] : ''}</th>{row.map((count, column) => <td className={index === column ? 'correct' : ''} key={column} style={{ '--cell-strength': `${total ? 4 + count / total * 23 : 0}%` } as CSSProperties}>{number(count)}</td>)}</tr>;
                  })}</tbody>
                </table>
              </div>
              <p className="matrix-key"><span aria-hidden="true" />Diagonal hijau: prediksi sesuai label aktual.</p>
            </div>
            <div className="class-metrics">
              <h3>Metrik per sentimen</h3>
              <div className="table-scroll" tabIndex={0} role="region" aria-label="Metrik per sentimen yang dapat digulir">
                <table>
                  <caption className="sr-only">Precision, recall, F1, dan jumlah data untuk setiap kategori</caption>
                  <thead><tr><th scope="col">Sentimen</th><th scope="col">Precision</th><th scope="col">Recall</th><th scope="col">F1</th><th scope="col">Jumlah</th></tr></thead>
                  <tbody>{report.per_class?.map(row => <tr key={row.label}><th scope="row"><SentimentBadge label={row.label} /></th><td>{percent(row.precision)}</td><td>{percent(row.recall)}</td><td>{percent(row.f1)}</td><td>{number(row.support)}</td></tr>)}</tbody>
                </table>
              </div>
            </div>
          </div>
        </>
      )}
      <details className="evaluation-reading-guide"><summary>Cara membaca metrik evaluasi</summary><dl><div><dt>Akurasi</dt><dd>Proporsi seluruh opini yang sentimennya diklasifikasikan dengan benar.</dd></div><div><dt>Precision</dt><dd>Dari opini yang diprediksi sebagai suatu sentimen, berapa yang labelnya memang sesuai.</dd></div><div><dt>Recall</dt><dd>Dari opini yang memiliki suatu label sentimen, berapa yang berhasil ditemukan model.</dd></div><div><dt>F1 dan Macro F1</dt><dd>F1 merangkum precision dan recall. Macro F1 merata-ratakan F1 ketiga kelas dengan bobot yang sama.</dd></div><div><dt>Jumlah data</dt><dd>Jumlah opini berlabel pada tiap kelas. Ketimpangan jumlah kelas perlu diperhatikan saat membandingkan akurasi dan Macro F1.</dd></div></dl></details>
      <p className="section-note panel-note">Sumber: {report?.source_file || 'CSV prediksi hasil notebook'}.</p>
    </section>
  );
}
