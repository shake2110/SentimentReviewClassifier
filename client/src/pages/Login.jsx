import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router';
import { useAuth } from '../auth';
import AuthShell from '../components/AuthShell';

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError('');
    try {
      const user = await login(email, password);
      navigate(location.state?.from || (user.role === 'provider' ? '/seller' : '/'), { replace: true });
    } catch (err) {
      setError(err.message);
      setBusy(false);
    }
  };

  return (
    <div className="container">
      <AuthShell title="Sign in" subtitle="Welcome back. Sign in to review products or manage your store.">
        <form className="auth-form" onSubmit={submit}>
          <label>
            Email address
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required autoComplete="email" autoFocus />
          </label>
          <label>
            Password
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required autoComplete="current-password" />
          </label>
          {error && <p className="error">{error}</p>}
          <button className="btn btn-block btn-lg" disabled={busy}>{busy ? 'Signing in…' : 'Sign in'}</button>
        </form>
        <div className="auth-divider"><span>New to AspectLens?</span></div>
        <Link to="/register" state={location.state} className="btn btn-outline btn-block">Create your account</Link>
      </AuthShell>
    </div>
  );
}
