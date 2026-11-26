import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router';
import { api } from '../api';
import Icon from '../components/Icon';

const EMPTY = { name: '', category: '', price: '', description: '' };

export default function ProductForm() {
  const { id } = useParams();
  const editing = Boolean(id);
  const navigate = useNavigate();
  const [form, setForm] = useState(EMPTY);
  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState('');
  const [existingImage, setExistingImage] = useState('');
  const [fields, setFields] = useState({});
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(editing);

  useEffect(() => {
    if (!editing) return;
    api(`/api/products/${id}`)
      .then(({ product }) => {
        if (!product.viewer.is_owner) throw new Error('You can only edit your own products.');
        setForm({
          name: product.name,
          category: product.category,
          price: product.price ?? '',
          description: product.description,
        });
        setExistingImage(product.image_url);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [editing, id]);

  useEffect(() => {
    if (!file) return undefined;
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    if (!editing && !file) {
      setFields({ image: 'Choose a product photo.' });
      return;
    }
    setBusy(true);
    setError('');
    setFields({});
    const data = new FormData();
    Object.entries(form).forEach(([k, v]) => data.append(k, v));
    if (file) data.append('image', file);
    try {
      const res = editing
        ? await api(`/api/products/${id}`, { method: 'PATCH', form: data })
        : await api('/api/products', { method: 'POST', form: data });
      navigate(editing ? '/seller' : `/seller/products/${res.product.id}/parts`);
    } catch (err) {
      setError(err.message);
      setFields(err.fields || {});
      setBusy(false);
    }
  };

  if (loading) return <div className="container loading">Loading…</div>;

  const shownImage = previewUrl || existingImage;

  return (
    <div className="container">
    <nav className="breadcrumb">
      <Link to="/seller">Seller dashboard</Link> <Icon name="right" size={12} /> <span>{editing ? 'Edit product' : 'Add a product'}</span>
    </nav>
    {!editing && (
      <ol className="stepper">
        <li className="on"><b>1</b>Product details</li>
        <li><b>2</b>Mark the parts</li>
      </ol>
    )}
    <form className="card form-card" onSubmit={submit}>
      <h1>{editing ? 'Edit product' : 'Product details'}</h1>

      <div className="form-grid">
        <div className="form-fields">
          <label>
            Product name
            <input value={form.name} onChange={set('name')} required maxLength={120} placeholder="e.g. Trailblazer Leather Sneaker" />
            {fields.name && <span className="field-error">{fields.name}</span>}
          </label>
          <div className="row gap">
            <label className="grow">
              Category
              <input value={form.category} onChange={set('category')} maxLength={60} placeholder="Footwear" />
            </label>
            <label className="grow">
              Price (optional)
              <input type="number" min="0" step="0.01" value={form.price} onChange={set('price')} />
              {fields.price && <span className="field-error">{fields.price}</span>}
            </label>
          </div>
          <label>
            Description
            <textarea value={form.description} onChange={set('description')} rows={5} maxLength={4000} />
            {fields.description && <span className="field-error">{fields.description}</span>}
          </label>
        </div>

        <div className="form-image">
          <span className="label-text">Product photo</span>
          <label className={`dropzone ${shownImage ? 'has-image' : ''}`}>
            {shownImage ? (
              <img src={shownImage} alt="Preview" />
            ) : (
              <span className="dz-empty"><Icon name="upload" size={28} /><strong>Upload product photo</strong>JPG, PNG or WEBP, up to 8 MB</span>
            )}
            <input type="file" accept="image/jpeg,image/png,image/webp" onChange={(e) => setFile(e.target.files?.[0] || null)} />
          </label>
          {fields.image && <span className="field-error">{fields.image}</span>}
          <p className="muted small">
            Use a clear photo where every part you want rated is visible.
            {editing && ' Replacing the photo keeps marked parts at the same relative positions, so re-check them.'}
          </p>
        </div>
      </div>

      {error && !Object.keys(fields).length && <p className="error">{error}</p>}
      <div className="form-actions">
        <Link to="/seller" className="btn btn-text">Cancel</Link>
        <button className="btn" disabled={busy}>
          {busy ? 'Saving…' : editing ? 'Save changes' : 'Continue to mark parts →'}
        </button>
      </div>
    </form>
    </div>
  );
}
