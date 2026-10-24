export function ResourceState({ loading, error, title, message, onRetry }: {
  loading?: boolean;
  error?: string;
  title?: string;
  message?: string;
  onRetry?: () => void;
}) {
  return (
    <div className={`resource-state${error ? ' has-error' : ''}`} role={error ? 'alert' : 'status'}>
      <h3>{loading ? 'Memuat data…' : error ? 'Data belum dapat dimuat' : title || 'Belum ada data'}</h3>
      <p>{loading ? 'Hasil akan tampil setelah data diterima.' : error || message}</p>
      {error && onRetry && <button type="button" onClick={onRetry}>Coba lagi</button>}
    </div>
  );
}
