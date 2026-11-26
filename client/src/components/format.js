const dateFmt = new Intl.DateTimeFormat(undefined, { day: 'numeric', month: 'short', year: 'numeric' });
export const formatDate = (iso) => dateFmt.format(new Date(iso));
export const formatPrice = (p) =>
  p == null ? '' : new Intl.NumberFormat(undefined, { style: 'currency', currency: import.meta.env.VITE_CURRENCY || 'INR' }).format(p);
export const labelOf = (summary) => summary?.label || 'none';
