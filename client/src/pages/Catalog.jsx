import { useEffect, useMemo, useState } from 'react';
import { Link, useSearchParams } from 'react-router';
import { api } from '../api';
import { useAuth } from '../auth';
import Icon from '../components/Icon';
import ProductCard from '../components/ProductCard';

const SORTS = {
  newest: { label: 'Newest first', fn: () => 0 },
  rating: { label: 'Customer rating', fn: (a, b) => (b.overall.avg_stars ?? -1) - (a.overall.avg_stars ?? -1) },
  reviews: { label: 'Most reviewed', fn: (a, b) => b.overall.count - a.overall.count },
  priceAsc: { label: 'Price: low to high', fn: (a, b) => (a.price ?? Infinity) - (b.price ?? Infinity) },
  priceDesc: { label: 'Price: high to low', fn: (a, b) => (b.price ?? -1) - (a.price ?? -1) },
};
const RATING_FILTERS = [4, 3, 2];

function Banner({ products }) {
  const images = products.slice(0, 3);
  return (
    <section className="banner">
      <div className="banner-copy">
        <span className="banner-kicker">A smarter way to read reviews</span>
        <h1>Know what buyers think of every part, not just the product.</h1>
        <p>
          We split each review into the parts it talks about, like the sole, the battery or the strap, and rate
          each one. Hover the dots on any product photo to see what people say about that part.
        </p>
        <a href="#products" className="btn btn-light">Start browsing <Icon name="right" size={16} /></a>
      </div>
      <div className="banner-art" aria-hidden="true">
        {images.map((p, i) => (
          <div key={p.id} className={`banner-tile t${i}`}>
            <img src={p.image_url} alt="" />
          </div>
        ))}
      </div>
    </section>
  );
}

function HowItWorks() {
  const steps = [
    { icon: 'pen', title: 'Write naturally', text: 'Shoppers write one normal review. No forms, no per-part sliders.' },
    { icon: 'split', title: 'We split it up', text: 'Each sentence is matched to the parts the seller marked on the product.' },
    { icon: 'target', title: 'Rated on the photo', text: 'Every part gets its own star rating, pinned right where it is on the product.' },
  ];
  return (
    <section className="how">
      {steps.map((s) => (
        <div key={s.title} className="how-step">
          <span className="how-icon"><Icon name={s.icon} size={22} /></span>
          <div>
            <strong>{s.title}</strong>
            <p>{s.text}</p>
          </div>
        </div>
      ))}
    </section>
  );
}

export default function Catalog() {
  const { user } = useAuth();
  const [params, setParams] = useSearchParams();
  const q = params.get('q') || '';
  const category = params.get('category') || '';
  const minRating = Number(params.get('rating') || 0);
  const sort = SORTS[params.get('sort')] ? params.get('sort') : 'newest';
  const [products, setProducts] = useState(null);
  const [error, setError] = useState('');
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [price, setPrice] = useState({ min: params.get('min') || '', max: params.get('max') || '' });

  useEffect(() => {
    const ctrl = new AbortController();
    setError('');
    setProducts(null);
    const qs = new URLSearchParams();
    if (q) qs.set('q', q);
    if (category) qs.set('category', category);
    api(`/api/products?${qs}`, { signal: ctrl.signal })
      .then((d) => setProducts(d.products))
      .catch((err) => err.name !== 'AbortError' && setError(err.message));
    return () => ctrl.abort();
  }, [q, category]);

  const update = (changes) => {
    const next = new URLSearchParams(params);
    Object.entries(changes).forEach(([k, v]) => (v ? next.set(k, v) : next.delete(k)));
    setParams(next, { replace: true });
  };

  const min = Number(params.get('min')) || 0;
  const max = Number(params.get('max')) || Infinity;
  const shown = useMemo(() => {
    if (!products) return [];
    return products
      .filter((p) => !minRating || (p.overall.avg_stars ?? 0) >= minRating)
      .filter((p) => p.price == null ? !params.get('min') && !params.get('max') : p.price >= min && p.price <= max)
      .slice()
      .sort(SORTS[sort].fn);
  }, [products, minRating, min, max, sort, params]);

  const categories = useMemo(() => {
    const counts = {};
    (products || []).forEach((p) => p.category && (counts[p.category] = (counts[p.category] || 0) + 1));
    return Object.entries(counts).sort();
  }, [products]);

  const isHome = !q && !category;
  const anyFilter = minRating || params.get('min') || params.get('max');
  const heading = q ? `Results for "${q}"` : category || 'All products';

  return (
    <div className="container">
      {isHome && products?.length > 0 && (
        <>
          <Banner products={products} />
          <HowItWorks />
        </>
      )}

      {!isHome && (
        <nav className="breadcrumb">
          <Link to="/">Home</Link> <Icon name="right" size={12} /> <span>{heading}</span>
        </nav>
      )}

      <div className="listing" id="products">
        <aside className={`filters ${filtersOpen ? 'open' : ''}`} aria-label="Filters">
          <div className="filters-head">
            <h2>Filters</h2>
            {anyFilter ? (
              <button type="button" className="link-btn" onClick={() => { update({ rating: '', min: '', max: '' }); setPrice({ min: '', max: '' }); }}>
                Clear all
              </button>
            ) : null}
          </div>

          {!q && (
            <div className="filter-group">
              <h3>Category</h3>
              <Link to="/" className={`filter-option ${!category ? 'on' : ''}`}>All categories</Link>
              {(category ? [[category, products?.length ?? 0]] : categories).map(([name, n]) => (
                <Link key={name} to={`/?category=${encodeURIComponent(name)}`} className={`filter-option ${category === name ? 'on' : ''}`}>
                  {name} <span className="muted">({n})</span>
                </Link>
              ))}
            </div>
          )}

          <div className="filter-group">
            <h3>Customer rating</h3>
            {RATING_FILTERS.map((r) => (
              <label key={r} className="check">
                <input type="radio" name="rating" checked={minRating === r} onChange={() => update({ rating: String(r) })} />
                <span>{r}★ &amp; above</span>
              </label>
            ))}
            {minRating > 0 && <button type="button" className="link-btn" onClick={() => update({ rating: '' })}>Any rating</button>}
          </div>

          <form
            className="filter-group"
            onSubmit={(e) => {
              e.preventDefault();
              update({ min: price.min, max: price.max });
            }}
          >
            <h3>Price</h3>
            <div className="price-range">
              <input type="number" min="0" placeholder="Min" value={price.min} onChange={(e) => setPrice({ ...price, min: e.target.value })} aria-label="Minimum price" />
              <span>to</span>
              <input type="number" min="0" placeholder="Max" value={price.max} onChange={(e) => setPrice({ ...price, max: e.target.value })} aria-label="Maximum price" />
              <button type="submit" className="btn btn-outline btn-sm">Go</button>
            </div>
          </form>
        </aside>

        <section className="results">
          <div className="results-head">
            <div>
              <h2>{heading}</h2>
              {products && <span className="muted small">Showing {shown.length} of {products.length} {products.length === 1 ? 'product' : 'products'}</span>}
            </div>
            <div className="results-tools">
              <button type="button" className="btn btn-outline btn-sm show-sm" onClick={() => setFiltersOpen(!filtersOpen)}>
                <Icon name="filter" size={16} /> Filters
              </button>
              <label className="sort">
                <span>Sort by</span>
                <select value={sort} onChange={(e) => update({ sort: e.target.value === 'newest' ? '' : e.target.value })}>
                  {Object.entries(SORTS).map(([k, s]) => <option key={k} value={k}>{s.label}</option>)}
                </select>
              </label>
            </div>
          </div>

          {error && <p className="error">{error}</p>}
          {!products && !error && (
            <div className="product-grid">
              {[0, 1, 2, 3].map((i) => <div key={i} className="product-card skeleton" />)}
            </div>
          )}
          {products && shown.length === 0 && (
            <div className="empty-state">
              <h3>{products.length ? 'No products match these filters' : q ? `Nothing matches "${q}"` : 'No products yet'}</h3>
              {products.length ? (
                <button type="button" className="btn btn-outline" onClick={() => update({ rating: '', min: '', max: '' })}>Clear filters</button>
              ) : user?.role === 'provider' ? (
                <Link className="btn" to="/seller/products/new">List your first product</Link>
              ) : (
                <p className="muted">Try a different search, or <Link to="/">browse all products</Link>.</p>
              )}
            </div>
          )}
          {shown.length > 0 && (
            <div className="product-grid">
              {shown.map((p) => <ProductCard key={p.id} product={p} />)}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
