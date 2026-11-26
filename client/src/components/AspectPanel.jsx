import { useState } from 'react';
import { formatDate } from './format';
import SentimentBar from './SentimentBar';
import Stars from './Stars';

const FILTERS = ['all', 'positive', 'neutral', 'negative'];

export default function AspectPanel({ aspect, pinned, onClose, onMouseEnter, onMouseLeave }) {
  const [filter, setFilter] = useState('all');
  const { summary, snippets } = aspect;
  const shown = filter === 'all' ? snippets : snippets.filter((s) => s.label === filter);

  // Open on the side of the dot with more room.
  const style = {};
  if (aspect.x > 50) style.right = `calc(${100 - aspect.x}% + 22px)`;
  else style.left = `calc(${aspect.x}% + 22px)`;
  if (aspect.y > 55) style.bottom = `max(0px, calc(${100 - aspect.y}% - 40px))`;
  else style.top = `max(0px, calc(${aspect.y}% - 40px))`;

  return (
    <section
      className="aspect-panel"
      style={style}
      role="dialog"
      aria-label={`Reviews about ${aspect.name}`}
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
    >
      <header className="aspect-panel-head">
        <div>
          <div className="eyebrow">Customer reviews</div>
          <h3>{aspect.name}</h3>
        </div>
        <button type="button" className="icon-btn" onClick={onClose} aria-label="Close">
          ×
        </button>
      </header>

      {summary.count === 0 ? (
        <p className="muted">No reviews mention the {aspect.name.toLowerCase()} yet.</p>
      ) : (
        <>
          <div className="aspect-score">
            <span className="aspect-score-num">{summary.avg_stars.toFixed(1)}</span>
            <div className="aspect-score-meta">
              <Stars value={summary.avg_stars} />
              <span className="muted small">Based on {summary.count} {summary.count === 1 ? 'review' : 'reviews'}</span>
            </div>
          </div>
          <SentimentBar summary={summary} />
          <div className="chips" role="tablist">
            {FILTERS.map((f) => (
              <button
                key={f}
                type="button"
                role="tab"
                aria-selected={filter === f}
                className={`chip ${filter === f ? 'on' : ''}`}
                onClick={() => setFilter(f)}
              >
                {f === 'all' ? `All ${summary.count}` : `${f[0].toUpperCase()}${f.slice(1)} ${summary[f]}`}
              </button>
            ))}
          </div>
          <ul className="snippets">
            {shown.map((s) => (
              <li key={s.review_id} className={`snippet ${s.label}`}>
                <div className="snippet-meta">
                  <Stars value={s.stars} size="sm" />
                  <span className="snippet-user">{s.user_name}</span>
                  <span className="muted">{formatDate(s.created_at)}</span>
                </div>
                <p>"{s.text}"</p>
              </li>
            ))}
            {shown.length === 0 && <li className="muted small">No {filter} comments.</li>}
          </ul>
        </>
      )}
      {!pinned && <div className="panel-hint">Click the dot to keep this open</div>}
    </section>
  );
}
