import { useEffect, useRef, useState } from 'react';
import { Link, useBlocker, useParams } from 'react-router';
import { api } from '../api';
import Breakdown from '../components/Breakdown';
import Icon from '../components/Icon';
import { Rating } from '../components/Stars';

const clamp = (v) => Math.max(0, Math.min(100, Math.round(v * 100) / 100));
let tempId = 0;

const fromProduct = (product) =>
  product.aspects.map((a) => ({
    key: a.id,
    id: a.id,
    name: a.name,
    keywords: a.keywords.join(', '),
    x: a.x,
    y: a.y,
    summary: a.summary,
  }));

export default function PartEditor() {
  const { id } = useParams();
  const [product, setProduct] = useState(null);
  const [parts, setParts] = useState([]);
  const [selected, setSelected] = useState(null);
  const [dirty, setDirty] = useState(false);
  const [saving, setSaving] = useState(false);
  const [notice, setNotice] = useState('');
  const [error, setError] = useState('');
  const [sample, setSample] = useState('');
  const [sampleResult, setSampleResult] = useState(null);
  const canvasRef = useRef(null);
  const drag = useRef(null);
  const nameInputs = useRef({});
  const focusNext = useRef(null);

  useEffect(() => {
    api(`/api/products/${id}`)
      .then(({ product: p }) => {
        if (!p.viewer.is_owner) throw new Error('You can only mark parts on your own products.');
        setProduct(p);
        setParts(fromProduct(p));
      })
      .catch((err) => setError(err.message));
  }, [id]);

  // Warn before leaving with unsaved changes (in-app navigation and tab close).
  const blocker = useBlocker(({ currentLocation, nextLocation }) => dirty && currentLocation.pathname !== nextLocation.pathname);
  useEffect(() => {
    if (blocker.state !== 'blocked') return;
    if (window.confirm('You have unsaved part changes. Leave without saving?')) blocker.proceed();
    else blocker.reset();
  }, [blocker]);
  useEffect(() => {
    if (!dirty) return undefined;
    const onUnload = (e) => {
      e.preventDefault();
      e.returnValue = '';
    };
    window.addEventListener('beforeunload', onUnload);
    return () => window.removeEventListener('beforeunload', onUnload);
  }, [dirty]);

  useEffect(() => {
    if (focusNext.current && nameInputs.current[focusNext.current]) {
      nameInputs.current[focusNext.current].focus();
      focusNext.current = null;
    }
  });

  const change = (updater) => {
    setParts(updater);
    setDirty(true);
    setNotice('');
  };
  const update = (key, patch) => change((ps) => ps.map((p) => (p.key === key ? { ...p, ...patch } : p)));
  const remove = (key) => {
    change((ps) => ps.filter((p) => p.key !== key));
    if (selected === key) setSelected(null);
  };

  const pointToPct = (e) => {
    const r = canvasRef.current.getBoundingClientRect();
    return { x: clamp(((e.clientX - r.left) / r.width) * 100), y: clamp(((e.clientY - r.top) / r.height) * 100) };
  };

  const addAt = (e) => {
    if (e.target.closest('.editor-dot')) return;
    if (parts.length >= 20) {
      setError('A product can have at most 20 marked parts.');
      return;
    }
    const key = `new-${++tempId}`;
    change((ps) => [...ps, { key, id: undefined, name: '', keywords: '', ...pointToPct(e), summary: null }]);
    setSelected(key);
    focusNext.current = key;
  };

  const onDotDown = (e, key) => {
    e.preventDefault();
    e.currentTarget.setPointerCapture(e.pointerId);
    drag.current = { key, sx: e.clientX, sy: e.clientY, moved: false };
    setSelected(key);
  };
  const onDotMove = (e) => {
    const d = drag.current;
    if (!d) return;
    if (!d.moved && Math.hypot(e.clientX - d.sx, e.clientY - d.sy) < 3) return;
    d.moved = true;
    update(d.key, pointToPct(e));
  };
  const onDotUp = () => {
    const d = drag.current;
    drag.current = null;
    if (d && !d.moved) {
      focusNext.current = d.key;
      setSelected(d.key);
    }
  };
  const onDotKey = (e, part) => {
    const step = e.shiftKey ? 2 : 0.5;
    const moves = { ArrowLeft: [-step, 0], ArrowRight: [step, 0], ArrowUp: [0, -step], ArrowDown: [0, step] };
    if (moves[e.key]) {
      e.preventDefault();
      const [dx, dy] = moves[e.key];
      update(part.key, { x: clamp(part.x + dx), y: clamp(part.y + dy) });
    } else if (e.key === 'Delete' || e.key === 'Backspace') {
      e.preventDefault();
      remove(part.key);
    }
  };

  const save = async () => {
    setError('');
    const names = parts.map((p) => p.name.trim().toLowerCase());
    const blank = parts.find((p) => !p.name.trim());
    if (blank) {
      setSelected(blank.key);
      focusNext.current = blank.key;
      setError('Every dot needs a part name.');
      return;
    }
    const dup = names.find((n, i) => names.indexOf(n) !== i);
    if (dup) {
      setError(`Two parts are both called "${dup}". Part names must be unique.`);
      return;
    }
    setSaving(true);
    try {
      const res = await api(`/api/products/${id}/aspects`, {
        method: 'PUT',
        body: {
          aspects: parts.map((p) => ({
            id: p.id,
            name: p.name.trim(),
            keywords: p.keywords.split(',').map((k) => k.trim()).filter(Boolean),
            x: p.x,
            y: p.y,
          })),
        },
      });
      setProduct(res.product);
      setParts(fromProduct(res.product));
      setSelected(null);
      setDirty(false);
      setSampleResult(null);
      const n = res.reanalyzed_reviews;
      setNotice(`Saved ${res.product.aspects.length} parts.${n ? ` Re-analysed ${n} existing review${n === 1 ? '' : 's'} against them.` : ''}`);
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  const testSample = async () => {
    setError('');
    try {
      const d = await api(`/api/products/${id}/analyze`, { method: 'POST', body: { text: sample } });
      setSampleResult(d.analysis);
    } catch (err) {
      setError(err.message);
    }
  };

  if (error && !product) {
    return (
      <div className="container"><div className="empty-state">
        <h2>{error}</h2>
        <Link to="/seller" className="btn">Back to dashboard</Link>
      </div></div>
    );
  }
  if (!product) return <div className="container loading">Loading…</div>;

  return (
    <div className="container">
      <nav className="breadcrumb">
        <Link to="/seller">Seller dashboard</Link> <Icon name="right" size={12} /> <span>{product.name}</span>
      </nav>
      <div className="page-head">
        <div>
          <h1>Mark the parts</h1>
          <p className="muted">
            Click anywhere on the photo to drop a dot, then name that part. Drag a dot to move it (or focus it and use the arrow keys).
            Reviews that mention a part, or a word meaning the same thing, get pinned to its dot.
          </p>
        </div>
        <div className="row gap">
          <Link to={`/products/${product.id}`} className="btn btn-outline"><Icon name="eye" size={16} />View as shopper</Link>
          <button type="button" className="btn" onClick={save} disabled={!dirty || saving}>
            {saving ? 'Saving & re-analysing…' : dirty ? 'Save parts' : 'Saved'}
          </button>
        </div>
      </div>

      {notice && <p className="notice">{notice}</p>}
      {error && <p className="error">{error}</p>}

      <div className="editor-layout">
        <div className="editor-canvas-wrap">
          <div className="hotspot-canvas editor-canvas" ref={canvasRef} onClick={addAt}>
            <img src={product.image_url} alt={product.name} className="hotspot-image" draggable="false" />
            {parts.map((p, i) => (
              <button
                key={p.key}
                type="button"
                className={`editor-dot ${selected === p.key ? 'selected' : ''} ${p.name.trim() ? '' : 'unnamed'}`}
                style={{ left: `${p.x}%`, top: `${p.y}%` }}
                aria-label={`${p.name || 'Unnamed part'} at ${Math.round(p.x)}%, ${Math.round(p.y)}%`}
                onPointerDown={(e) => onDotDown(e, p.key)}
                onPointerMove={onDotMove}
                onPointerUp={onDotUp}
                onKeyDown={(e) => onDotKey(e, p)}
                onFocus={() => setSelected(p.key)}
              >
                {i + 1}
                {p.name && <span className="hotspot-label">{p.name}</span>}
              </button>
            ))}
          </div>
          {parts.length === 0 && <p className="hint center">No parts yet. Click on the photo to add the first one.</p>}
        </div>

        <aside className="editor-side">
          <h2 className="section-title">Parts ({parts.length}/20)</h2>
          {parts.length === 0 && <p className="muted small">Each dot you add shows up here.</p>}
          <ol className="editor-parts">
            {parts.map((p, i) => (
              <li key={p.key} className={`card editor-part ${selected === p.key ? 'selected' : ''}`} onClick={() => setSelected(p.key)}>
                <div className="editor-part-head">
                  <span className="editor-num">{i + 1}</span>
                  <input
                    ref={(el) => (nameInputs.current[p.key] = el)}
                    value={p.name}
                    maxLength={40}
                    placeholder="Part name, e.g. Sole"
                    aria-label={`Name of part ${i + 1}`}
                    onChange={(e) => update(p.key, { name: e.target.value })}
                  />
                  <button type="button" className="icon-btn" aria-label={`Remove ${p.name || 'part'}`} onClick={(e) => { e.stopPropagation(); remove(p.key); }}>
                    ×
                  </button>
                </div>
                <label className="small">
                  Other words shoppers might use <span className="muted">(optional, comma-separated)</span>
                  <input
                    value={p.keywords}
                    placeholder="e.g. grip, outsole, tread"
                    onChange={(e) => update(p.key, { keywords: e.target.value })}
                  />
                </label>
                {p.summary && p.summary.count > 0 && <Rating summary={p.summary} size="sm" />}
              </li>
            ))}
          </ol>

          <div className="card tester">
            <h3>Try a sample review</h3>
            <p className="muted small">See how a review would be split across your saved parts.</p>
            <textarea rows={3} value={sample} onChange={(e) => setSample(e.target.value)} placeholder="The grip is great but the laces came undone constantly." />
            <button type="button" className="btn btn-outline" onClick={testSample} disabled={sample.trim().length < 10 || dirty}>
              Test
            </button>
            {dirty && <span className="muted small"> Save your parts first.</span>}
            <Breakdown analysis={sampleResult} title="Result" />
          </div>
        </aside>
      </div>
    </div>
  );
}
