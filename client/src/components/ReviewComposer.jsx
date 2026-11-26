import { useEffect, useState } from 'react';
import { Link } from 'react-router';
import { api } from '../api';
import { useAuth } from '../auth';
import Breakdown from './Breakdown';

const MIN = 10;
const MAX = 3000;

/** Write / edit / delete the signed-in shopper's review of one product. */
export default function ReviewComposer({ product, myReview, onChanged, onCancel }) {
  const { user } = useAuth();
  const [text, setText] = useState(myReview?.text || '');
  const [editing, setEditing] = useState(!myReview);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);
  const [preview, setPreview] = useState(null);

  useEffect(() => {
    setText(myReview?.text || '');
    setEditing(!myReview);
  }, [myReview?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  if (!user) {
    return (
      <div className="composer">
        <h3>Share your experience</h3>
        <p className="muted">
          <Link to="/login" state={{ from: `/products/${product.id}` }}>Log in</Link> or{' '}
          <Link to="/register">create a shopper account</Link> to review this product.
        </p>
      </div>
    );
  }
  if (user.role !== 'consumer') {
    return (
      <div className="composer">
        <h3>Reviews</h3>
        <p className="muted">Seller accounts can't post reviews. Sign in as a shopper to write one.</p>
      </div>
    );
  }

  const length = text.trim().length;
  const valid = length >= MIN && length <= MAX;

  const run = async (fn) => {
    setBusy(true);
    setError('');
    try {
      await fn();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const doPreview = () =>
    run(async () => {
      const d = await api(`/api/products/${product.id}/analyze`, { method: 'POST', body: { text } });
      setPreview(d.analysis);
    });

  const submit = (e) => {
    e.preventDefault();
    run(async () => {
      const d = myReview
        ? await api(`/api/reviews/${myReview.id}`, { method: 'PUT', body: { text } })
        : await api(`/api/products/${product.id}/reviews`, { method: 'POST', body: { text } });
      setResult(d.review);
      setPreview(null);
      setEditing(false);
      onChanged();
    });
  };

  const remove = () => {
    if (!window.confirm('Delete your review? This cannot be undone.')) return;
    run(async () => {
      await api(`/api/reviews/${myReview.id}`, { method: 'DELETE' });
      setResult(null);
      setText('');
      onChanged();
    });
  };

  if (myReview && !editing) {
    return (
      <div className="composer">
        <div className="composer-head">
          <h3>Your review</h3>
          <div className="row gap">
            <button type="button" className="btn btn-outline" onClick={() => setEditing(true)} disabled={busy}>Edit</button>
            <button type="button" className="btn btn-danger" onClick={remove} disabled={busy}>Delete</button>
          </div>
        </div>
        <p className="review-text">{myReview.text}</p>
        <Breakdown analysis={result || myReview} title={result ? 'Saved! Here is how we read it' : 'How we read your review'} />
        {error && <p className="error">{error}</p>}
      </div>
    );
  }

  return (
    <form className="composer" onSubmit={submit}>
      <h3>{myReview ? 'Edit your review' : 'Write a review'}</h3>
      <p className="muted small">
        Just write naturally. We'll work out which parts of the product you're talking about
        {product.aspects?.length ? ` (${product.aspects.map((a) => a.name).join(', ')})` : ''} and how you feel about each one.
      </p>
      <textarea
        value={text}
        onChange={(e) => {
          setText(e.target.value);
          setPreview(null);
        }}
        rows={5}
        maxLength={MAX}
        placeholder="e.g. The leather quality is very good but the lace quality is not so good."
        aria-label="Your review"
      />
      <div className="composer-foot">
        <span className={`muted small ${length > 0 && length < MIN ? 'warn' : ''}`}>
          {length < MIN ? `${MIN - length} more characters needed` : `${length}/${MAX}`}
        </span>
        <div className="row gap">
          <button
            type="button"
            className="btn btn-text"
            onClick={() => (myReview ? setEditing(false) : onCancel?.())}
            disabled={busy}
          >
            Cancel
          </button>
          <button type="button" className="btn btn-outline" onClick={doPreview} disabled={!valid || busy}>Preview breakdown</button>
          <button type="submit" className="btn" disabled={!valid || busy}>
            {busy ? 'Analysing…' : myReview ? 'Save changes' : 'Post review'}
          </button>
        </div>
      </div>
      {preview && <Breakdown analysis={preview} title="Preview (not posted yet)" />}
      {error && <p className="error">{error}</p>}
    </form>
  );
}
