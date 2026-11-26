import { useEffect, useRef } from 'react';
import { labelOf } from './format';
import AspectPanel from './AspectPanel';

export default function HotspotViewer({ product, hotspots }) {
  const { openId, pinned, show, hide, toggle, close, keepOpen } = hotspots;
  const stageRef = useRef(null);
  const aspects = product.aspects || [];
  const open = aspects.find((a) => a.id === openId);

  // Esc or a click outside closes a pinned panel.
  useEffect(() => {
    if (!openId) return;
    const onKey = (e) => e.key === 'Escape' && close();
    const onDown = (e) => {
      if (stageRef.current && !stageRef.current.contains(e.target) && !e.target.closest?.('.parts-list')) close();
    };
    document.addEventListener('keydown', onKey);
    document.addEventListener('pointerdown', onDown);
    return () => {
      document.removeEventListener('keydown', onKey);
      document.removeEventListener('pointerdown', onDown);
    };
  }, [openId, close]);

  return (
    <div className="hotspot-stage" ref={stageRef}>
      <div className="hotspot-canvas">
        <img src={product.image_url} alt={product.name} className="hotspot-image" draggable="false" />
        {aspects.map((a) => (
          <button
            key={a.id}
            type="button"
            className={`hotspot-dot ${labelOf(a.summary)} ${openId === a.id ? 'active' : ''}`}
            style={{ left: `${a.x}%`, top: `${a.y}%` }}
            aria-label={`${a.name}: ${
              a.summary.count ? `${a.summary.avg_stars.toFixed(1)} stars from ${a.summary.count} reviews` : 'no reviews yet'
            }`}
            aria-expanded={openId === a.id}
            onMouseEnter={() => show(a.id)}
            onMouseLeave={hide}
            onFocus={() => show(a.id)}
            onBlur={hide}
            onClick={() => toggle(a.id)}
          >
            <span className="hotspot-label">{a.name}</span>
          </button>
        ))}
      </div>
      {open && (
        <AspectPanel
          key={open.id}
          aspect={open}
          pinned={pinned}
          onClose={close}
          onMouseEnter={keepOpen}
          onMouseLeave={hide}
        />
      )}
    </div>
  );
}
