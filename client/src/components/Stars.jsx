/** Five stars with fractional fill (value 1-5, or null for "no rating"). */
export default function Stars({ value, size = 'md' }) {
  const pct = value == null ? 0 : Math.max(0, Math.min(100, (value / 5) * 100));
  const label = value == null ? 'No rating yet' : `${value.toFixed(1)} out of 5 stars`;
  return (
    <span className={`stars stars-${size}`} role="img" aria-label={label} title={label}>
      <span className="stars-bg" aria-hidden="true">★★★★★</span>
      <span className="stars-fg" aria-hidden="true" style={{ width: `${pct}%` }}>★★★★★</span>
    </span>
  );
}

export const tone = (v) => (v == null ? 'none' : v >= 3.3 ? 'positive' : v <= 2.7 ? 'negative' : 'neutral');

/** Compact "4.2 ★" badge, coloured by score (marketplace style). */
export function RatingBadge({ value, size = 'md' }) {
  if (value == null) return <span className={`rating-badge none ${size}`}>New</span>;
  return (
    <span className={`rating-badge ${tone(value)} ${size}`} aria-label={`${value.toFixed(1)} out of 5`}>
      {value.toFixed(1)} <span aria-hidden="true">★</span>
    </span>
  );
}

export function Rating({ summary, size = 'md', showCount = true }) {
  const avg = summary?.avg_stars;
  const count = summary?.count ?? 0;
  return (
    <span className="rating">
      <RatingBadge value={avg} size={size} />
      {showCount && (
        <span className="rating-count">
          {count.toLocaleString()} {count === 1 ? 'rating' : 'ratings'}
        </span>
      )}
    </span>
  );
}
