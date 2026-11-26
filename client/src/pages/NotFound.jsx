import { Link } from 'react-router';

export default function NotFound() {
  return (
    <div className="container">
      <div className="empty-state">
        <h2>We couldn't find that page</h2>
        <Link to="/" className="btn">Continue shopping</Link>
      </div>
    </div>
  );
}
