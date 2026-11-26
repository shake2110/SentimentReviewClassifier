import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router';
import { useAuth } from '../auth';
import AuthShell from '../components/AuthShell';

const ROLES = [
  { value: 'consumer', title: "I'm shopping", text: 'Read and write reviews' },
  { value: 'provider', title: 'I sell products', text: 'List products and mark parts' },
];

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [form, setForm] = useState({
    name: '', email: '', password: '', role: location.state?.role === 'provider' ? 'provider' : 'consumer',
  });
  const [fields, setFields] = useState({});
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError('');
    setFields({});
    try {
      const user = await register(form);
      navigate(user.role === 'provider' ? '/seller' : location.state?.from || '/', { replace: true });
    } catch (err) {
      setError(err.message);
      setFields(err.fields || {});
      setBusy(false);
    }
  };

  return (
    <div className="container">
      <AuthShell title="Create your account" audience={form.role}>
        <form className="auth-form" onSubmit={submit}>
          <fieldset className="role-picker">
            <legend>Account type</legend>
            {ROLES.map((r) => (
              <label key={r.value} className={`role-option ${form.role === r.value ? 'on' : ''}`}>
                <input type="radio" name="role" value={r.value} checked={form.role === r.value} onChange={set('role')} />
                <strong>{r.title}</strong>
                <span>{r.text}</span>
              </label>
            ))}
          </fieldset>
          <label>
            {form.role === 'provider' ? 'Store name' : 'Your name'}
            <input value={form.name} onChange={set('name')} required maxLength={80} autoComplete="name" />
            {fields.name && <span className="field-error">{fields.name}</span>}
          </label>
          <label>
            Email address
            <input type="email" value={form.email} onChange={set('email')} required autoComplete="email" />
            {fields.email && <span className="field-error">{fields.email}</span>}
          </label>
          <label>
            Password
            <input type="password" value={form.password} onChange={set('password')} required minLength={8} autoComplete="new-password" />
            <span className={fields.password ? 'field-error' : 'hint-text'}>{fields.password || 'At least 8 characters'}</span>
          </label>
          {error && !Object.keys(fields).length && <p className="error">{error}</p>}
          <button className="btn btn-block btn-lg" disabled={busy}>{busy ? 'Creating account…' : 'Create account'}</button>
        </form>
        <p className="muted small center">
          Already have an account? <Link to="/login" state={location.state}>Sign in</Link>
        </p>
      </AuthShell>
    </div>
  );
}
