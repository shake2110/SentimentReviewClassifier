import { useEffect, useRef, useState } from 'react';
import { Link, NavLink, Outlet, ScrollRestoration, useLocation, useNavigate, useSearchParams } from 'react-router';
import { api } from '../api';
import { useAuth } from '../auth';
import Icon from './Icon';

function Logo() {
  return (
    <Link to="/" className="logo" aria-label="AspectLens home">
      <span className="logo-mark" aria-hidden="true">
        <i className="d-pos" /><i className="d-neu" /><i className="d-neg" />
      </span>
      <span className="logo-text">Aspect<span>Lens</span></span>
    </Link>
  );
}

function SearchBar() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const location = useLocation();
  const [q, setQ] = useState(params.get('q') || '');
  useEffect(() => {
    if (location.pathname === '/') setQ(params.get('q') || '');
  }, [params, location.pathname]);

  const submit = (e) => {
    e.preventDefault();
    const next = new URLSearchParams();
    if (q.trim()) next.set('q', q.trim());
    navigate(`/?${next}`);
  };
  return (
    <form className="search-bar" role="search" onSubmit={submit}>
      <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search for products, brands and more" aria-label="Search products" />
      <button type="submit" aria-label="Search"><Icon name="search" /></button>
    </form>
  );
}

function AccountMenu() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const ref = useRef(null);
  const location = useLocation();

  useEffect(() => setOpen(false), [location.pathname]);
  useEffect(() => {
    if (!open) return undefined;
    const onDown = (e) => ref.current && !ref.current.contains(e.target) && setOpen(false);
    const onKey = (e) => e.key === 'Escape' && setOpen(false);
    document.addEventListener('pointerdown', onDown);
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('pointerdown', onDown);
      document.removeEventListener('keydown', onKey);
    };
  }, [open]);

  if (!user) {
    return (
      <Link to="/login" className="header-action">
        <Icon name="user" />
        <span><small>Hello, sign in</small>Account</span>
      </Link>
    );
  }
  return (
    <div className="account" ref={ref}>
      <button type="button" className="header-action" aria-expanded={open} onClick={() => setOpen(!open)}>
        <Icon name="user" />
        <span><small>Hello, {user.name.split(' ')[0]}</small><span className="ha-main">Account <Icon name="chevron" size={14} /></span></span>
      </button>
      {open && (
        <div className="menu" role="menu">
          <div className="menu-head">
            <strong>{user.name}</strong>
            <span className="muted small">{user.email}</span>
            <span className={`role-tag ${user.role}`}>{user.role === 'provider' ? 'Seller account' : 'Shopper account'}</span>
          </div>
          {user.role === 'provider' && (
            <>
              <Link role="menuitem" to="/seller"><Icon name="grid" size={18} />Seller dashboard</Link>
              <Link role="menuitem" to="/seller/products/new"><Icon name="plus" size={18} />Add a product</Link>
            </>
          )}
          <Link role="menuitem" to="/"><Icon name="search" size={18} />Browse products</Link>
          <button
            type="button"
            role="menuitem"
            onClick={() => {
              logout();
              navigate('/');
            }}
          >
            <Icon name="logout" size={18} />Sign out
          </button>
        </div>
      )}
    </div>
  );
}

function CategoryBar() {
  const [categories, setCategories] = useState([]);
  const [params] = useSearchParams();
  const location = useLocation();
  const active = location.pathname === '/' ? params.get('category') || '' : null;
  useEffect(() => {
    api('/api/categories').then((d) => setCategories(d.categories)).catch(() => {});
  }, [location.pathname]);

  return (
    <nav className="category-bar" aria-label="Categories">
      <div className="container category-inner">
        <Link to="/" className={active === '' ? 'on' : ''}>All products</Link>
        {categories.map((c) => (
          <Link key={c.name} to={`/?category=${encodeURIComponent(c.name)}`} className={active === c.name ? 'on' : ''}>
            {c.name}
          </Link>
        ))}
      </div>
    </nav>
  );
}

export default function Layout() {
  const { user } = useAuth();
  return (
    <div className="app">
      <div className="utility-bar">
        <div className="container utility-inner">
          <span>Reviews you can read part by part: hover the dots on any product.</span>
          <span className="utility-links">
            {user?.role === 'provider' ? (
              <NavLink to="/seller">Seller dashboard</NavLink>
            ) : (
              <Link to="/register" state={{ role: 'provider' }}>Sell on AspectLens</Link>
            )}
          </span>
        </div>
      </div>

      <header className="site-header">
        <div className="container header-main">
          <Logo />
          <SearchBar />
          <div className="header-actions">
            {user?.role === 'provider' && (
              <Link to="/seller" className="header-action hide-sm">
                <Icon name="store" />
                <span><small>Your store</small>Dashboard</span>
              </Link>
            )}
            <AccountMenu />
          </div>
        </div>
        <CategoryBar />
      </header>

      <main className="main">
        <Outlet />
      </main>

      <footer className="site-footer">
        <div className="container footer-grid">
          <div>
            <Logo />
            <p>
              Every review, broken down by product part. We read what shoppers write, work out which parts
              they are talking about, and rate each one separately.
            </p>
          </div>
          <div>
            <h4>Shop</h4>
            <Link to="/">All products</Link>
            <Link to="/login">Sign in</Link>
            <Link to="/register">Create an account</Link>
          </div>
          <div>
            <h4>Sell</h4>
            <Link to="/register" state={{ role: 'provider' }}>Become a seller</Link>
            <Link to="/seller">Seller dashboard</Link>
            <Link to="/seller/products/new">List a product</Link>
          </div>
          <div>
            <h4>How ratings work</h4>
            <p className="small">
              Each review is split into clauses, matched to the parts the seller marked, and scored 1-5 by a
              sentiment model. Part ratings are the average across all reviews that mention that part.
            </p>
          </div>
        </div>
        <div className="container footer-bottom">© {new Date().getFullYear()} AspectLens</div>
      </footer>
      <ScrollRestoration />
    </div>
  );
}
