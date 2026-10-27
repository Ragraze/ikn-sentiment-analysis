const numbers = new Intl.NumberFormat('id-ID');
const percentages = new Intl.NumberFormat('id-ID', { minimumFractionDigits: 1, maximumFractionDigits: 1 });

export const number = (value: number) => numbers.format(value);
export const percent = (value: number) => `${percentages.format(value * 100)}%`;
export const errorMessage = (error: unknown) =>
  error instanceof Error ? error.message : 'Permintaan gagal. Coba lagi.';
