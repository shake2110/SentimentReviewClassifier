import Stars from './Stars';

/** Shows how one review was split into parts (used after submit and in previews). */
export default function Breakdown({ analysis, title = 'How we read your review' }) {
  if (!analysis) return null;
  const { mentions = [], general = [], overall } = analysis;
  return (
    <div className="breakdown">
      <div className="breakdown-head">
        <strong>{title}</strong>
        {overall && (
          <span className={`pill ${overall.label}`}>
            Overall {overall.label} · {overall.stars.toFixed(1)}★
          </span>
        )}
      </div>
      {mentions.length === 0 ? (
        <p className="muted small">
          This review does not mention any of the marked parts, so it only counts toward the overall rating.
        </p>
      ) : (
        <ul className="breakdown-list">
          {mentions.map((m) => (
            <li key={m.aspect_id}>
              <span className={`pill ${m.label}`}>{m.aspect_name}</span>
              <Stars value={m.stars} size="sm" />
              <span className="breakdown-snippet">"{m.snippet}"</span>
            </li>
          ))}
        </ul>
      )}
      {general.length > 0 && mentions.length > 0 && (
        <p className="muted small">General comments (overall rating only): {general.map((g) => `"${g.snippet}"`).join(', ')}</p>
      )}
    </div>
  );
}
