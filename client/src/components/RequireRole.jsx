import { Navigate, Outlet, useLocation } from 'react-router';
import { useAuth } from '../auth';

export default function RequireRole({ role }) {
  const { user } = useAuth();
  const location = useLocation();
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  if (role && user.role !== role) {
    return (
      <div className="container"><div className="empty-state">
        <h2>Seller accounts only</h2>
        <p>You are signed in as a shopper. Create a seller account to list products and mark their parts.</p>
      </div></div>
    );
  }
  return <Outlet />;
}
