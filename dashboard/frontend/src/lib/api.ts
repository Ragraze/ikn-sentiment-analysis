export async function api<T>(url: string, options?: RequestInit): Promise<T> {
  if (!url.startsWith('/api/') || url.includes('\\')) {
    throw new Error('Alamat API tidak valid.');
  }
  const deadline = AbortSignal.timeout(60_000);
  const signal = options?.signal ? AbortSignal.any([options.signal, deadline]) : deadline;
  let response: Response;
  try {
    response = await fetch(url, { ...options, signal, cache: 'no-store', credentials: 'same-origin', redirect: 'error' });
  } catch (error) {
    if (options?.signal?.aborted) throw error;
    if (deadline.aborted) throw new Error('Layanan belum merespons setelah satu menit. Coba lagi sebentar.');
    throw new Error('Layanan belum dapat dihubungi. Periksa koneksi, lalu coba lagi.');
  }
  let data;
  try {
    data = await response.json();
  } catch {
    throw new Error('Layanan belum mengirim data yang valid. Coba lagi setelah backend berjalan di port 5000.');
  }
  if (!data || typeof data !== 'object' || Array.isArray(data)) {
    throw new Error('Format respons layanan tidak valid. Coba lagi.');
  }
  if (!response.ok) throw new Error(typeof data.error === 'string' ? data.error : `Permintaan gagal (HTTP ${response.status}).`);
  return data as T;
}
