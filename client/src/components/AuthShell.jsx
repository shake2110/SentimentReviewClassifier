import Icon from './Icon';

const POINTS = {
  consumer: [
    ['target', 'Read reviews part by part', 'Hover the dots on a product photo to see what buyers think of each part.'],
    ['pen', 'Write once, naturally', 'Just describe your experience. We work out which parts you mean.'],
    ['split', 'See how we read you', 'Preview exactly how your review will be split before you post it.'],
  ],
  provider: [
    ['store', 'List any product', 'Upload a photo, then click on it to mark the parts that matter.'],
    ['target', 'Part-level feedback', 'Find out exactly which part buyers love, and which one lets you down.'],
    ['check', 'Always up to date', 'Change your parts any time and existing reviews are re-analysed.'],
  ],
};

export default function AuthShell({ title, subtitle, audience = 'consumer', children }) {
  return (
    <div className="auth-shell">
      <aside className="auth-aside">
        <h2>{audience === 'provider' ? 'Sell smarter with part-level reviews' : 'Shop with the full picture'}</h2>
        <ul>
          {POINTS[audience].map(([icon, t, d]) => (
            <li key={t}>
              <span className="auth-icon"><Icon name={icon} size={20} /></span>
              <div><strong>{t}</strong><p>{d}</p></div>
            </li>
          ))}
        </ul>
      </aside>
      <div className="auth-main">
        <h1>{title}</h1>
        {subtitle && <p className="muted">{subtitle}</p>}
        {children}
      </div>
    </div>
  );
}
