import { Link } from 'react-router';
import { formatPrice } from './format';
import { Rating } from './Stars';

export default function ProductCard({ product: p }) {
  return (
    <Link to={`/products/${p.id}`} className="product-card">
      <div className="pc-image">
        <img src={p.image_url} alt="" loading="lazy" />
        {p.aspect_count > 0 && <span className="pc-badge">{p.aspect_count} parts rated</span>}
      </div>
      <div className="pc-body">
        <span className="pc-seller">{p.provider.name}</span>
        <h3 className="pc-title">{p.name}</h3>
        <Rating summary={p.overall} size="sm" />
        {p.price != null && <div className="pc-price">{formatPrice(p.price)}</div>}
      </div>
    </Link>
  );
}
