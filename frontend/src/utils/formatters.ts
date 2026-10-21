export function formatNumber(val: number | null | undefined, decimals = 1, fallback = '—'): string {
  if (val === null || val === undefined || isNaN(val)) return fallback;
  return Number(val).toLocaleString('en-IN', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

export function formatPct(val: number | null | undefined, decimals = 1, fallback = '—'): string {
  if (val === null || val === undefined || isNaN(val)) return fallback;
  return `${Number(val).toFixed(decimals)}%`;
}

export function formatPValue(p: number): string {
  if (p < 0.001) return '< 0.001 (***)';
  if (p < 0.01) return `${p.toFixed(3)} (**)`;
  if (p < 0.05) return `${p.toFixed(3)} (*)`;
  return `${p.toFixed(3)} (ns)`;
}

export function formatDateLabel(isoString: string): string {
  try {
    const d = new Date(isoString);
    return d.toLocaleDateString('en-IN', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return isoString;
  }
}
