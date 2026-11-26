import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { createBrowserRouter, RouterProvider } from 'react-router';
import { AuthProvider } from './auth';
import Layout from './components/Layout';
import RequireRole from './components/RequireRole';
import RouteError from './components/RouteError';
import Catalog from './pages/Catalog';
import Login from './pages/Login';
import NotFound from './pages/NotFound';
import PartEditor from './pages/PartEditor';
import ProductForm from './pages/ProductForm';
import ProductPage from './pages/ProductPage';
import ProviderDashboard from './pages/ProviderDashboard';
import Register from './pages/Register';
import '@fontsource-variable/inter';
import './styles.css';

const router = createBrowserRouter([
  {
    element: <Layout />,
    errorElement: <RouteError />,
    children: [
      { path: '/', element: <Catalog /> },
      { path: '/products/:id', element: <ProductPage /> },
      { path: '/login', element: <Login /> },
      { path: '/register', element: <Register /> },
      {
        path: '/seller',
        element: <RequireRole role="provider" />,
        children: [
          { index: true, element: <ProviderDashboard /> },
          { path: 'products/new', element: <ProductForm /> },
          { path: 'products/:id/edit', element: <ProductForm /> },
          { path: 'products/:id/parts', element: <PartEditor /> },
        ],
      },
      { path: '*', element: <NotFound /> },
    ],
  },
]);

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <AuthProvider>
      <RouterProvider router={router} />
    </AuthProvider>
  </StrictMode>,
);
