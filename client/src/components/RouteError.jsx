import { isRouteErrorResponse, Link, useRouteError } from 'react-router';

export default function RouteError() {
  const error = useRouteError();
  const message = isRouteErrorResponse(error) ? `${error.status} ${error.statusText}` : error?.message;
  return (
    <div className="container main">
      <div className="empty-state">
        <h2>Something went wrong</h2>
        <p className="muted">{message || 'Unexpected error.'}</p>
        <Link to="/" className="btn">Back to products</Link>
      </div>
    </div>
  );
}
