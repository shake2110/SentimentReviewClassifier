import { formatDate } from './format';
import { RatingBadge } from './Stars';

/** Highlight each part snippet inside the full review text. */
function highlight(text, mentions, focus) {
  const ranges = [];
  for (const m of mentions) {
    for (const piece of m.snippet.split(' … ')) {
      const start = text.indexOf(piece);
      if (start >= 0) ranges.push({ start, end: start + piece.length, m });
    }
  }
  ranges.sort((a, b) => a.start - b.start);
  const out = [];
  let cursor = 0;
  for (const r of ranges) {
    if (r.start < cursor) continue;
    if (r.start > cursor) out.push(text.slice(cursor, r.start));
    const dim = focus && r.m.aspect_id !== focus;
    out.push(
      <mark key={`${r.start}-${r.m.aspect_id}`} className={`hl ${r.m.label} ${dim ? 'dim' : ''}`} title={`${r.m.aspect_name}: ${r.m.label}`}>
        {text.slice(r.start, r.end)}
      </mark>,
    );
    cursor = r.end;
  }
  out.push(text.slice(cursor));
  return out;
}

export default function ReviewList({ reviews, myReviewId, highlightPart }) {
  if (!reviews.length) {
    return <p className="muted empty-reviews">No reviews yet. Be the first to share what you think of each part.</p>;
  }
  return (
    <ul className="review-list">
      {reviews.map((r) => (
        <li key={r.id} className="review">
          <div className="review-top">
            <RatingBadge value={r.overall?.stars} size="sm" />
            {r.mentions.length > 0 && (
              <div className="review-tags">
                {r.mentions.map((m) => (
                  <span key={m.aspect_id} className={`tag ${m.label} ${highlightPart === m.aspect_id ? 'focus' : ''}`}>
                    {m.aspect_name} {m.stars.toFixed(1)}★
                  </span>
                ))}
              </div>
            )}
          </div>
          <p className="review-text">{highlight(r.text, r.mentions, highlightPart)}</p>
          <div className="review-meta">
            <span className="review-user">{r.user.name}</span>
            {r.id === myReviewId && <span className="you">Your review</span>}
            <span>{formatDate(r.created_at)}</span>
          </div>
        </li>
      ))}
    </ul>
  );
}
