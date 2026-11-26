import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Link, useParams } from 'react-router';
import { api } from '../api';
import { formatPrice } from '../components/format';
import HotspotViewer from '../components/HotspotViewer';
import Icon from '../components/Icon';
import ReviewComposer from '../components/ReviewComposer';
import ReviewList from '../components/ReviewList';
import Stars, { RatingBadge, tone } from '../components/Stars';
import useHotspots from '../components/useHotspots';

const SORTS = {
  newest: ['Most recent', (a, b) => new Date(b.created_at) - new Date(a.created_at)],
  high: ['Highest rated', (a, b) => b.overall.stars - a.overall.stars],
  low: ['Lowest rated', (a, b) => a.overall.stars - b.overall.stars],
};

function Histogram({ reviews }) {
  const counts = [5, 4, 3, 2, 1].map((s) => ({
    s,
    n: reviews.filter((r) => Math.min(5, Math.max(1, Math.round(r.overall?.stars ?? 3))) === s).length,
  }));
  const total = reviews.length || 1;
  return (
    <ul className="histogram">
      {counts.map(({ s, n }) => (
        <li key={s}>
          <span className="h-label">{s} ★</span>
          <span className="h-track"><span className={`h-fill s${s}`} style={{ width: `${(n / total) * 100}%` }} /></span>
          <span className="h-count">{n}</span>
        </li>
      ))}
    </ul>
  );
}

export default function ProductPage() {
  const { id } = useParams();
  const [product, setProduct] = useState(null);
  const [reviews, setReviews] = useState([]);
  const [error, setError] = useState('');
  const [sort, setSort] = useState('newest');
  const [partFilter, setPartFilter] = useState('');
  const [composing, setComposing] = useState(false);
  const hotspots = useHotspots();
  const reviewsRef = useRef(null);
  const mediaRef = useRef(null);

  const load = useCallback(async () => {
    try {
      const [p, r] = await Promise.all([api(`/api/products/${id}`), api(`/api/products/${id}/reviews`)]);
      setProduct(p.product);
      setReviews(r.reviews);
      setError('');
    } catch (err) {
      setError(err.message);
    }
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  const visible = useMemo(() => {
    const list = partFilter ? reviews.filter((r) => r.mentions.some((m) => m.aspect_id === partFilter)) : reviews;
    return list.slice().sort(SORTS[sort][1]);
  }, [reviews, partFilter, sort]);

  if (error) {
    return (
      <div className="container">
        <div className="empty-state">
          <h2>{error}</h2>
          <Link to="/" className="btn">Back to products</Link>
        </div>
      </div>
    );
  }
  if (!product) return <div className="container loading">Loading product…</div>;

  const aspects = product.aspects;
  const rated = aspects.filter((a) => a.summary.count > 0);
  const liked = rated.filter((a) => a.summary.avg_stars >= 3.3).sort((a, b) => b.summary.avg_stars - a.summary.avg_stars);
  const disliked = rated.filter((a) => a.summary.avg_stars <= 2.7).sort((a, b) => a.summary.avg_stars - b.summary.avg_stars);
  const myReview = reviews.find((r) => r.id === product.viewer.my_review_id) || null;
  const count = product.overall.count;

  const showPart = (aid) => {
    mediaRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' });
    hotspots.toggle(aid);
  };
  const filterByPart = (aid) => {
    setPartFilter(aid);
    reviewsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  return (
    <div className="container">
      <nav className="breadcrumb">
        <Link to="/">Home</Link> <Icon name="right" size={12} />
        {product.category && (
          <>
            <Link to={`/?category=${encodeURIComponent(product.category)}`}>{product.category}</Link> <Icon name="right" size={12} />
          </>
        )}
        <span>{product.name}</span>
      </nav>

      <div className="pdp">
        <section className="pdp-media" ref={mediaRef}>
          <HotspotViewer product={product} hotspots={hotspots} />
          <div className="media-legend">
            {aspects.length > 0 ? (
              <>
                <span><Icon name="dot" size={16} /> Hover or tap a dot to read reviews about that part</span>
                <span className="legend-keys">
                  <i className="dot positive" />Good <i className="dot neutral" />Mixed <i className="dot negative" />Poor <i className="dot none" />No reviews
                </span>
              </>
            ) : (
              <span>The seller hasn't marked any parts on this product yet.</span>
            )}
          </div>
        </section>

        <section className="pdp-info">
          <span className="pdp-seller">Sold by {product.provider.name}</span>
          <h1>{product.name}</h1>
          <div className="pdp-rating">
            <RatingBadge value={product.overall.avg_stars} />
            <a href="#reviews">{count.toLocaleString()} {count === 1 ? 'rating & review' : 'ratings & reviews'}</a>
          </div>

          {product.price != null && (
            <div className="pdp-price">
              <span className="price">{formatPrice(product.price)}</span>
              <span className="muted small">Inclusive of all taxes</span>
            </div>
          )}

          {(liked.length > 0 || disliked.length > 0) && (
            <div className="insights">
              {liked.length > 0 && (
                <div className="insight good">
                  <span className="insight-title"><Icon name="thumbUp" size={16} /> Customers like</span>
                  <div className="insight-chips">
                    {liked.slice(0, 4).map((a) => (
                      <button key={a.id} type="button" className="insight-chip" onClick={() => showPart(a.id)}>
                        {a.name} <b>{a.summary.avg_stars.toFixed(1)}★</b>
                      </button>
                    ))}
                  </div>
                </div>
              )}
              {disliked.length > 0 && (
                <div className="insight bad">
                  <span className="insight-title"><Icon name="thumbDown" size={16} /> Customers mention issues with</span>
                  <div className="insight-chips">
                    {disliked.slice(0, 4).map((a) => (
                      <button key={a.id} type="button" className="insight-chip" onClick={() => showPart(a.id)}>
                        {a.name} <b>{a.summary.avg_stars.toFixed(1)}★</b>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {aspects.length > 0 && (
            <div className="pdp-block">
              <h2>Ratings by part</h2>
              <ul className="parts-list">
                {aspects.map((a) => (
                  <li key={a.id}>
                    <button
                      type="button"
                      className={`part-row ${hotspots.openId === a.id ? 'active' : ''}`}
                      onMouseEnter={() => hotspots.show(a.id)}
                      onMouseLeave={hotspots.hide}
                      onClick={() => hotspots.toggle(a.id)}
                    >
                      <span className="part-name">{a.name}</span>
                      <span className="part-bar">
                        <span className={`part-fill ${tone(a.summary.avg_stars)}`} style={{ width: `${((a.summary.avg_stars ?? 0) / 5) * 100}%` }} />
                      </span>
                      <span className="part-score">{a.summary.avg_stars == null ? '-' : a.summary.avg_stars.toFixed(1)}</span>
                      <span className="part-count">({a.summary.count})</span>
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {product.description && (
            <div className="pdp-block">
              <h2>Product details</h2>
              <p className="description">{product.description}</p>
            </div>
          )}

          <div className="seller-box">
            <span className="seller-avatar"><Icon name="store" size={18} /></span>
            <div>
              <span className="muted small">Seller</span>
              <strong>{product.provider.name}</strong>
            </div>
          </div>

          {product.viewer.is_owner && (
            <div className="owner-actions">
              <Link className="btn btn-outline" to={`/seller/products/${product.id}/parts`}><Icon name="target" size={16} />Edit marked parts</Link>
              <Link className="btn btn-outline" to={`/seller/products/${product.id}/edit`}><Icon name="edit" size={16} />Edit details</Link>
            </div>
          )}
        </section>
      </div>

      <section className="reviews-section" id="reviews" ref={reviewsRef}>
        <h2 className="section-heading">Ratings &amp; Reviews</h2>
        <div className="ratings-overview">
          <div className="ro-summary">
            <div className="ro-big">
              {product.overall.avg_stars == null ? '-' : product.overall.avg_stars.toFixed(1)}
              <span>★</span>
            </div>
            <Stars value={product.overall.avg_stars} />
            <span className="muted small">{count.toLocaleString()} {count === 1 ? 'rating' : 'ratings'}</span>
          </div>
          <Histogram reviews={reviews} />
          <div className="ro-cta">
            <strong>Review this product</strong>
            <span className="muted small">Tell other shoppers what you think. We'll rate each part you mention.</span>
            {myReview ? (
              <a href="#your-review" className="btn btn-outline">See your review</a>
            ) : (
              <button type="button" className="btn btn-outline" onClick={() => setComposing(true)}>Write a review</button>
            )}
          </div>
        </div>

        {(composing || myReview) && (
          <div id="your-review">
            <ReviewComposer product={product} myReview={myReview} onChanged={load} onCancel={() => setComposing(false)} />
          </div>
        )}

        <div className="reviews-toolbar">
          <div className="part-filters" role="group" aria-label="Filter reviews by part">
            <button type="button" className={`chip ${!partFilter ? 'on' : ''}`} onClick={() => setPartFilter('')}>All reviews</button>
            {rated.map((a) => (
              <button key={a.id} type="button" className={`chip ${partFilter === a.id ? 'on' : ''}`} onClick={() => filterByPart(a.id)}>
                {a.name} ({a.summary.count})
              </button>
            ))}
          </div>
          <label className="sort">
            <span>Sort by</span>
            <select value={sort} onChange={(e) => setSort(e.target.value)}>
              {Object.entries(SORTS).map(([k, [label]]) => <option key={k} value={k}>{label}</option>)}
            </select>
          </label>
        </div>

        <ReviewList reviews={visible} myReviewId={product.viewer.my_review_id} highlightPart={partFilter} />
      </section>
    </div>
  );
}
