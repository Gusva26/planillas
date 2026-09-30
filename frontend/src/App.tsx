import React, { useState } from 'react';
import { useAuth } from './context/AuthContext';
import { apiRequest } from './api/client';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { Modal } from './components/Modal';
import { LoginView } from './views/LoginView';
import { DashboardView } from './views/DashboardView';
import { PlanillasView } from './views/PlanillasView';
import { TrabajadoresView } from './views/TrabajadoresView';
import { ImportacionesView } from './views/ImportacionesView';
import { DocumentosView } from './views/DocumentosView';
import { CatalogosView } from './views/CatalogosView';
import { ReportesView } from './views/ReportesView';
import { AuditoriaView } from './views/AuditoriaView';
import { UsuariosView } from './views/UsuariosView';
import { KeyRound, ShieldAlert } from 'lucide-react';

export const AppContent: React.FC = () => {
  const { user, loading, logout, reloadUser } = useAuth();
  const [currentTab, setCurrentTab] = useState<string>('dashboard');
  const [sidebarCollapsed, setSidebarCollapsed] = useState<boolean>(() => {
    return localStorage.getItem('cafae_sidebar_collapsed') === 'true';
  });

  const handleToggleSidebar = () => {
    setSidebarCollapsed((prev) => {
      const next = !prev;
      localStorage.setItem('cafae_sidebar_collapsed', String(next));
      return next;
    });
  };

  // Modal Cambiar Contraseña
  const [isPassModalOpen, setIsPassModalOpen] = useState(false);
  const [currentPass, setCurrentPass] = useState('');
  const [newPass, setNewPass] = useState('');
  const [repeatPass, setRepeatPass] = useState('');
  const [passError, setPassError] = useState<string | null>(null);
  const [passSaving, setPassSaving] = useState(false);

  if (loading) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--bg-app)' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{
            width: 48,
            height: 48,
            border: '3px solid rgba(20, 184, 166, 0.2)',
            borderTopColor: 'var(--teal-500)',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
            margin: '0 auto 1rem',
          }} />
          <style>{`@keyframes spin { 100% { transform: rotate(360deg); } }`}</style>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Cargando sistema CAFAE UGEL Chepén...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return <LoginView />;
  }

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setPassError(null);
    if (newPass !== repeatPass) {
      setPassError('Las nuevas contraseñas no coinciden.');
      return;
    }
    if (newPass.length < 12) {
      setPassError('La nueva contraseña debe tener al menos 12 caracteres.');
      return;
    }
    setPassSaving(true);
    try {
      await apiRequest('/api/auth/change-password', {
        method: 'POST',
        body: JSON.stringify({
          current_password: currentPass,
          new_password: newPass,
          repeat_password: repeatPass,
        }),
      });
      setIsPassModalOpen(false);
      setCurrentPass('');
      setNewPass('');
      setRepeatPass('');
      alert('Contraseña actualizada con éxito. Inicia sesión nuevamente.');
      await logout();
    } catch (err: any) {
      setPassError(err.message || 'Error al cambiar contraseña.');
    } finally {
      setPassSaving(false);
    }
  };

  return (
    <div className="app-layout">
      {/* Sidebar de Navegación Plegable */}
      <Sidebar 
        currentTab={currentTab} 
        onSelectTab={setCurrentTab}
        collapsed={sidebarCollapsed}
        onToggleCollapse={handleToggleSidebar}
      />

      {/* Contenido Principal */}
      <div className="main-content">
        <Header 
          currentTab={currentTab} 
          onOpenPasswordModal={() => setIsPassModalOpen(true)}
          onToggleSidebar={handleToggleSidebar}
          sidebarCollapsed={sidebarCollapsed}
        />

        {/* Modal Obligatorio si debe cambiar contraseña */}
        {user.debe_cambiar_password && (
          <div style={{
            background: '#FEF3C7',
            borderBottom: '1px solid #FDE68A',
            padding: '0.75rem 2rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#92400E', fontSize: '0.85rem', fontWeight: 500 }}>
              <ShieldAlert size={16} />
              <span>Tu cuenta utiliza una contraseña temporal. Por seguridad, cámbiala antes de continuar.</span>
            </div>
            <button onClick={() => setIsPassModalOpen(true)} className="btn btn-sm btn-primary">
              Cambiar Contraseña Ahora
            </button>
          </div>
        )}

        <main style={{ flex: 1 }}>
          {currentTab === 'dashboard' && <DashboardView onNavigate={setCurrentTab} />}
          {currentTab === 'planillas' && <PlanillasView />}
          {currentTab === 'personal' && <TrabajadoresView />}
          {currentTab === 'importaciones' && <ImportacionesView />}
          {currentTab === 'documentos' && <DocumentosView />}
          {currentTab === 'catalogos' && <CatalogosView />}
          {currentTab === 'reportes' && <ReportesView />}
          {currentTab === 'auditoria' && <AuditoriaView />}
          {currentTab === 'usuarios' && <UsuariosView />}
        </main>
      </div>

      {/* Modal Cambiar Contraseña */}
      <Modal isOpen={isPassModalOpen} onClose={() => setIsPassModalOpen(false)} title="Actualizar Contraseña de Acceso">
        {passError && (
          <div style={{ background: '#FEE2E2', border: '1px solid #FECACA', padding: '0.75rem', borderRadius: 'var(--radius-md)', color: '#B91C1C', marginBottom: '1rem', fontSize: '0.85rem' }}>
            {passError}
          </div>
        )}
        <form onSubmit={handleChangePassword}>
          <div className="form-group">
            <label className="form-label">Contraseña Actual</label>
            <input
              type="password"
              className="form-input"
              value={currentPass}
              onChange={(e) => setCurrentPass(e.target.value)}
              required
            />
          </div>
          <div className="form-group">
            <label className="form-label">Nueva Contraseña (mínimo 12 caracteres)</label>
            <input
              type="password"
              className="form-input"
              value={newPass}
              onChange={(e) => setNewPass(e.target.value)}
              required
            />
          </div>
          <div className="form-group">
            <label className="form-label">Confirmar Nueva Contraseña</label>
            <input
              type="password"
              className="form-input"
              value={repeatPass}
              onChange={(e) => setRepeatPass(e.target.value)}
              required
            />
          </div>
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem', marginTop: '1.5rem', borderTop: '1px solid var(--border-subtle)', paddingTop: '1rem' }}>
            <button type="button" onClick={() => setIsPassModalOpen(false)} className="btn btn-secondary">Cancelar</button>
            <button type="submit" className="btn btn-primary" disabled={passSaving}>
              {passSaving ? 'Guardando...' : 'Actualizar Contraseña'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
