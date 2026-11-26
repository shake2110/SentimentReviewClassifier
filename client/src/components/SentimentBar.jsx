export default function SentimentBar({ summary }) {
  const { positive = 0, neutral = 0, negative = 0 } = summary || {};
  const total = positive + neutral + negative;
  if (!total) return null;
  const seg = (n) => `${(n / total) * 100}%`;
  return (
    <div className="sentiment">
      <div className="sentiment-bar" aria-hidden="true">
        <span className="seg pos" style={{ width: seg(positive) }} />
        <span className="seg neu" style={{ width: seg(neutral) }} />
        <span className="seg neg" style={{ width: seg(negative) }} />
      </div>
      <div className="sentiment-legend">
        <span><i className="dot pos" />{positive} positive</span>
        <span><i className="dot neu" />{neutral} neutral</span>
        <span><i className="dot neg" />{negative} negative</span>
      </div>
    </div>
  );
}
