'use client';

import { useEffect, useId, useState } from 'react';
import { ResourceState } from '@/components/resource-state';
import { SentimentBadge } from '@/components/sentiment-badge';
import { useResource } from '@/hooks/use-resource';
import { number } from '@/lib/format';
import { names, sentiments, splitNames } from '@/lib/sentiment';
import type { DatasetPage, DatasetRow, Sentiment, Split } from '@/lib/types';

function Opinion({ row }: { row: DatasetRow }) {
  const [expanded, setExpanded] = useState(false);
  const id = useId();
  const shortened = row.text.length > 180;
  return (
    <>
      <div id={id} className="opinion-text">{shortened && !expanded ? `${row.text.slice(0, 180)}…` : row.text}</div>
      {shortened && <button className="text-button" type="button" aria-expanded={expanded} aria-controls={id} onClick={() => setExpanded(value => !value)}>{expanded ? 'Ringkas teks' : 'Baca selengkapnya'}</button>}
    </>
  );
}

export function DatasetExplorer() {
  const [query, setQuery] = useState('');
  const [search, setSearch] = useState('');
  const [split, setSplit] = useState<'all' | Split>('all');
  const [label, setLabel] = useState<'all' | Sentiment>('all');
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(8);
  const pendingSearch = query.trim() !== search;
  const filtered = Boolean(query.trim() || split !== 'all' || label !== 'all');

  useEffect(() => {
    const nextSearch = query.trim();
    if (nextSearch === search) return;
    const timer = setTimeout(() => { setSearch(nextSearch); setPage(1); }, 300);
    return () => clearTimeout(timer);
  }, [query, search]);

  const params = new URLSearchParams({ q: search, split, label, page: String(page), page_size: String(pageSize) });
  const { data, loading, error, reload } = useResource<DatasetPage>(`/api/dataset?${params}`);
  const download = `/api/dataset/export?${new URLSearchParams({ q: search, split, label })}`;
  const start = (page - 1) * pageSize;
  const busy = loading || pendingSearch;
  const pages = Math.max(1, Math.ceil((data?.total || 0) / pageSize));

  function resetFilters() {
    setQuery('');
    setSearch('');
    setSplit('all');
    setLabel('all');
    setPage(1);
  }

  return (
    <section id="dataset" className="panel section-space dataset-workspace">
      <div className="feature-toolbar">
        <p>Ekspor CSV mengikuti pencarian dan filter yang diterapkan.</p>
        {busy || error || !data?.total ? <button className="button secondary" type="button" disabled>Ekspor CSV</button> : <a className="button secondary" href={download} download>Ekspor CSV</a>}
      </div>
      <div className="table-controls">
        <label className="search-field" htmlFor="opinion-search">Cari opini<input id="opinion-search" type="search" value={query} onChange={event => setQuery(event.target.value)} maxLength={200} placeholder="Kata atau potongan kalimat" aria-describedby="dataset-search-help" /></label>
        <label htmlFor="dataset-split">Bagian dataset<select id="dataset-split" value={split} onChange={event => { setSplit(event.target.value as 'all' | Split); setPage(1); }}><option value="all">Semua bagian</option>{Object.entries(splitNames).map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select></label>
        <label htmlFor="dataset-sentiment">Sentimen<select id="dataset-sentiment" value={label} onChange={event => { setLabel(event.target.value as 'all' | Sentiment); setPage(1); }}><option value="all">Semua sentimen</option>{sentiments.map(value => <option value={value} key={value}>{names[value]}</option>)}</select></label>
      </div>
      <div className="dataset-filter-summary">
        <div><p id="dataset-search-help">Pencarian diterapkan otomatis saat selesai mengetik.</p><p role="status">{pendingSearch ? 'Menerapkan pencarian…' : `${split === 'all' ? 'Semua bagian' : splitNames[split]} · ${label === 'all' ? 'Semua sentimen' : names[label]}${search ? ` · “${search}”` : ''}`}</p></div>
        {filtered && <button type="button" onClick={resetFilters}>Atur ulang filter</button>}
      </div>
      <div className="dataset-results" aria-busy={busy}>
        {busy || error ? <ResourceState loading={busy} error={error} onRetry={reload} /> : !data?.rows.length ? (
          <div className="dataset-empty"><ResourceState title={filtered ? 'Belum ada opini yang cocok' : 'Dataset belum memiliki opini'} message={filtered ? 'Coba kata yang lebih umum atau atur ulang filter untuk melihat seluruh opini.' : 'Tambahkan dataset penelitian untuk mulai menelusuri opini.'} />{filtered && <button type="button" onClick={resetFilters}>Tampilkan semua opini</button>}</div>
        ) : (
          <div className="dataset-table-wrap">
            <table className="dataset-table">
              <caption className="sr-only">Opini beserta label dan bagian dataset</caption>
              <thead><tr><th scope="col">No.</th><th scope="col">Teks opini</th><th scope="col">Sentimen</th><th scope="col">Bagian</th></tr></thead>
              <tbody>{data.rows.map((row, index) => (
                <tr key={row.id}><td data-label="No.">{number(start + index + 1)}</td><td><Opinion row={row} /></td><td data-label="Sentimen"><SentimentBadge label={row.label} /></td><td data-label="Bagian">{splitNames[row.split]}</td></tr>
              ))}</tbody>
            </table>
          </div>
        )}
      </div>
      <div className="table-footer">
        <div className="dataset-count"><span role="status">{busy ? 'Memuat opini…' : error ? 'Dataset belum tersedia' : data?.total ? `${number(start + 1)}–${number(Math.min(start + pageSize, data.total))} dari ${number(data.total)} opini` : '0 opini ditemukan'}</span><label htmlFor="dataset-page-size">Opini per halaman<select id="dataset-page-size" value={pageSize} onChange={event => { setPageSize(Number(event.target.value)); setPage(1); }}>{[8, 16, 32, 50].map(size => <option value={size} key={size}>{size}</option>)}</select></label></div>
        <nav className="pagination" aria-label="Halaman dataset">
          <button type="button" disabled={busy || Boolean(error) || page <= 1} onClick={() => setPage(value => value - 1)} aria-label="Halaman sebelumnya">Sebelumnya</button>
          <span aria-label={`Halaman ${page}`}>{page} / {busy ? '…' : pages}</span>
          <button type="button" disabled={busy || Boolean(error) || !data || start + pageSize >= data.total} onClick={() => setPage(value => value + 1)} aria-label="Halaman berikutnya">Berikutnya</button>
        </nav>
      </div>
    </section>
  );
}
