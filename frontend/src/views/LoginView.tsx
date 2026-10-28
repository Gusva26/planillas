import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { mensajeDeError } from '../api/errors';
import { Lock, User, ArrowRight, ShieldCheck, AlertCircle, Eye, EyeOff } from 'lucide-react';

export const LoginView: React.FC = () => {
  const { login } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(username, password);
    } catch (err) {
      setError(mensajeDeError(err, 'Credenciales no válidas o acceso restringido.'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '2rem 1.5rem',
      background: 'linear-gradient(135deg, #F8FAFC 0%, #EEF2F6 50%, #E2E8F0 100%)',
      position: 'relative',
    }}>
      {/* Elementos visuales decorativos institucionales de fondo */}
      <div style={{
        position: 'absolute',
        width: '450px',
        height: '450px',
        borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(37, 99, 235, 0.06) 0%, transparent 70%)',
        top: '10%',
        left: '15%',
        pointerEvents: 'none',
      }} />
      <div style={{
        position: 'absolute',
        width: '400px',
        height: '400px',
        borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(2, 132, 199, 0.05) 0%, transparent 70%)',
        bottom: '10%',
        right: '15%',
        pointerEvents: 'none',
      }} />

      <div className="card" style={{
        width: '100%',
        maxWidth: '450px',
        padding: '2.75rem 2.5rem',
        background: '#FFFFFF',
        boxShadow: '0 20px 30px -10px rgba(15, 23, 42, 0.1), 0 8px 12px -6px rgba(15, 23, 42, 0.05)',
        border: '1px solid #E2E8F0',
        borderRadius: 'var(--radius-xl)',
        position: 'relative',
        zIndex: 1,
      }}>
        {/* Brand Header */}
        <div style={{ textAlign: 'center', marginBottom: '2.25rem' }}>
          <div style={{
            width: 200,
            height: 200,
            borderRadius: 'var(--radius-xl)',
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            marginBottom: '1.25rem',
            background: '#FFFFFF',
            padding: '4px',
            border: '2px solid #E2E8F0',
            boxShadow: '0 4px 12px rgba(15, 23, 42, 0.08)',
          }}>
            <img
              src="/assets/logo_ugel.png"
              alt="UGEL Chepén"
              style={{ width: '100%', height: '100%', borderRadius: 'calc(var(--radius-xl) - 4px)', objectFit: 'cover' }}
            />
          </div>

          <div style={{
            display: 'inline-block',
            fontSize: '0.7rem',
            fontWeight: 800,
            letterSpacing: '0.08em',
            color: '#1D4ED8',
            textTransform: 'uppercase',
            background: '#EFF6FF',
            padding: '0.2rem 0.75rem',
            borderRadius: 'var(--radius-full)',
            marginBottom: '0.5rem',
            border: '1px solid #DBEAFE'
          }}>
            UGEL CHEPÉN · SUB-CAFAE
          </div>

          <h1 style={{ fontSize: '1.6rem', marginTop: '0.25rem', marginBottom: '0.35rem', color: '#0F172A', fontWeight: 800 }}>
            Sistema de Planillas
          </h1>
          <p style={{ fontSize: '0.85rem', color: '#64748B', margin: 0, lineHeight: 1.4 }}>
            Plataforma Integral de Emisión, Control y Archivos Bancarios
          </p>
        </div>

        {error && (
          <div style={{
            background: '#FEF2F2',
            border: '1px solid #FECACA',
            borderRadius: 'var(--radius-md)',
            padding: '0.85rem 1rem',
            marginBottom: '1.5rem',
            display: 'flex',
            alignItems: 'flex-start',
            gap: '0.65rem',
            color: '#991B1B',
            fontSize: '0.85rem',
          }}>
            <AlertCircle size={18} style={{ flexShrink: 0, marginTop: '2px', color: '#DC2626' }} />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label" htmlFor="login-username">
              Usuario Operador
            </label>
            <div style={{ position: 'relative' }}>
              <input
                id="login-username"
                type="text"
                className="form-input"
                placeholder="Ej. admin"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                autoComplete="username"
                style={{ paddingLeft: '2.6rem', height: '44px' }}
              />
              <User
                size={17}
                style={{ position: 'absolute', left: '0.95rem', top: '50%', transform: 'translateY(-50%)', color: '#94A3B8', pointerEvents: 'none' }}
              />
            </div>
          </div>

          <div className="form-group" style={{ marginBottom: '1.5rem' }}>
            <label className="form-label" htmlFor="login-password">
              Contraseña de Acceso
            </label>
            <div style={{ position: 'relative' }}>
              <input
                id="login-password"
                type={showPassword ? 'text' : 'password'}
                className="form-input"
                placeholder="••••••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="current-password"
                style={{ paddingLeft: '2.6rem', paddingRight: '2.75rem', height: '44px' }}
              />
              <Lock
                size={17}
                style={{ position: 'absolute', left: '0.95rem', top: '50%', transform: 'translateY(-50%)', color: '#94A3B8', pointerEvents: 'none' }}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="btn btn-ghost"
                style={{
                  position: 'absolute',
                  right: '0.4rem',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  padding: '0.4rem',
                  color: '#64748B',
                  borderRadius: 'var(--radius-sm)'
                }}
                title={showPassword ? 'Ocultar contraseña' : 'Ver contraseña'}
                aria-label={showPassword ? 'Ocultar contraseña' : 'Ver contraseña'}
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            style={{ width: '100%', height: '46px', fontSize: '0.95rem', fontWeight: 700 }}
            disabled={loading}
          >
            {loading ? (
              <span>Autenticando operador...</span>
            ) : (
              <>
                <span>Ingresar al Sistema</span>
                <ArrowRight size={17} />
              </>
            )}
          </button>
        </form>

        <div style={{ marginTop: '2.25rem', textAlign: 'center', borderTop: '1px solid var(--border-subtle)', paddingTop: '1.25rem' }}>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem', color: '#64748B', fontSize: '0.75rem', fontWeight: 500 }}>
            <ShieldCheck size={15} style={{ color: '#059669' }} />
            <span>Cifrado y hashing criptográfico Argon2id</span>
          </div>
        </div>
      </div>
    </div>
  );
};
