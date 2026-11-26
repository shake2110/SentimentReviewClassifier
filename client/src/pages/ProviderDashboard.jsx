import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router';
import { api } from '../api';
import { useAuth } from '../auth';
import { formatPrice } from '../components/format';
import Icon from '../components/Icon';
import { RatingBadge } from '../components/Stars';

export default function ProviderDashboard() {
  const { user } = useAuth();
  const [products, setProducts] = useState(null);
  const [error, setError] = useState('');

  const load = useCallback(() => {
    api('/api/products?mine=1')
      .then((d) => setProducts(d.products))
      .catch((err) => setError(err.message));
  }, []);
  useEffect(load, [load]);

  const remove = async (p) => {
    if (!window.confirm(`Delete "${p.name}" and all ${p.overall.count} of its reviews? This cannot be undone.`)) return;
    try {
      await api(`/api/products/${p.id}`, { method: 'DELETE' });
      load();
    } catch (err) {
      setError(err.message);
    }
  };

  const totalReviews = products?.reduce((s, p) => s + p.overall.count, 0) ?? 0;
  const rated = products?.filter((p) => p.overall.avg_stars != null) ?? [];
  const avg = rated.length
    ? rated.reduce((s, p) => s + p.overall.avg_stars * p.overall.count, 0) / Math.max(1, totalReviews)
    : null;
  const unmarked = products?.filter((p) => p.aspect_count === 0).length ?? 0;

  return (
    <div className="container">
      <div className="page-head">
        <div>
          <span className="eyebrow">Seller dashboard</span>
          <h1>{user.name}</h1>
        </div>
        <Link to="/seller/products/new" className="btn"><Icon name="plus" size={18} />Add a product</Link>
      </div>

      {error && <p className="error">{error}</p>}

      {products && (
        <div className="stat-grid">
          <div className="stat"><span>Products listed</span><strong>{products.length}</strong></div>
          <div className="stat"><span>Total reviews</span><strong>{totalReviews}</strong></div>
          <div className="stat"><span>Average rating</span><strong>{avg == null ? '-' : `${avg.toFixed(1)} ★`}</strong></div>
          <div className={`stat ${unmarked ? 'warn' : ''}`}>
            <span>Products missing parts</span><strong>{unmarked}</strong>
          </div>
        </div>
      )}

      {!products && !error && <div className="loading">Loading…</div>}

      {products?.length === 0 && (
        <div className="empty-state card">
          <h2>List your first product</h2>
          <ol className="steps">
            <li><b>1</b>Upload a product photo and its details.</li>
            <li><b>2</b>Click on the photo to drop a dot on each part (sole, lace, battery…) and name it.</li>
            <li><b>3</b>Shoppers' reviews are automatically split and pinned to those parts.</li>
          </ol>
          <Link to="/seller/products/new" className="btn">Add a product</Link>
        </div>
      )}

      {products?.length > 0 && (
        <div className="card table-card">
          <div className="table-title">
            <h2>Your products</h2>
            <span className="muted small">{products.length} total</span>
          </div>
          <div className="table-scroll">
            <table className="table">
              <thead>
                <tr>
                  <th>Product</th>
                  <th>Price</th>
                  <th>Rating</th>
                  <th>Reviews</th>
                  <th>Parts</th>
                  <th aria-label="Actions" />
                </tr>
              </thead>
              <tbody>
                {products.map((p) => (
                  <tr key={p.id}>
                    <td>
                      <div className="cell-product">
                        <img src={p.image_url} alt="" />
                        <div>
                          <Link to={`/products/${p.id}`}>{p.name}</Link>
                          <span className="muted small">{p.category || 'Uncategorised'}</span>
                        </div>
                      </div>
                    </td>
                    <td>{p.price != null ? formatPrice(p.price) : <span className="muted">-</span>}</td>
                    <td><RatingBadge value={p.overall.avg_stars} size="sm" /></td>
                    <td>{p.overall.count}</td>
                    <td>
                      {p.aspect_count === 0 ? (
                        <span className="status warn">Not marked</span>
                      ) : (
                        <span className="status ok">{p.aspect_count} marked</span>
                      )}
                    </td>
                    <td>
                      <div className="row-actions">
                        <Link className="btn btn-sm" to={`/seller/products/${p.id}/parts`}><Icon name="target" size={15} />Parts</Link>
                        <Link className="icon-btn" to={`/seller/products/${p.id}/edit`} aria-label={`Edit ${p.name}`} title="Edit details"><Icon name="edit" size={18} /></Link>
                        <Link className="icon-btn" to={`/products/${p.id}`} aria-label={`View ${p.name}`} title="View product page"><Icon name="eye" size={18} /></Link>
                        <button type="button" className="icon-btn danger" onClick={() => remove(p)} aria-label={`Delete ${p.name}`} title="Delete"><Icon name="trash" size={18} /></button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
