import React, { useEffect, useState } from 'react';
import { apiRequest } from '../api/client';
import { UserAccount } from '../types';
import { Modal } from '../components/Modal';
import { UserCog, Plus, Key, ShieldCheck, CheckCircle2 } from 'lucide-react';

export const UsuariosView: React.FC = () => {
  const [users, setUsers] = useState<UserAccount[]>([]);
  const [loading, setLoading] = useState(true);

  // Modales
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isResetOpen, setIsResetOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState<UserAccount | null>(null);

  // Forms
  const [createForm, setCreateForm] = useState({ username: '', nombre_completo: '', rol: 'PLANILLAS', password_temporal: '' });
  const [resetPass, setResetPass] = useState('');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const loadUsers = async () => {
    setLoading(true);
    try {
      const list = await apiRequest<UserAccount[]>('/api/users');
      setUsers(list);
    } catch (err: any) {
      setErrorMsg(err.message || 'Error al cargar usuarios.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadUsers();
  }, []);

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    if (createForm.password_temporal.length < 12) {
      setErrorMsg('La contraseña temporal debe tener al menos 12 caracteres.');
      return;
    }
    try {
      await apiRequest('/api/users', {
        method: 'POST',
        body: JSON.stringify(createForm),
      });
      setIsCreateOpen(false);
      setCreateForm({ username: '', nombre_completo: '', rol: 'PLANILLAS', password_temporal: '' });
      loadUsers();
    } catch (err: any) {
      setErrorMsg(err.message || 'Error al crear usuario.');
    }
  };

  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedUser) return;
    setErrorMsg(null);
    if (resetPass.length < 12) {
      setErrorMsg('La contraseña temporal debe tener al menos 12 caracteres.');
      return;
    }
    try {
      await apiRequest(`/api/users/${selectedUser.id}/reset-password`, {
        method: 'POST',
        body: JSON.stringify({
          password_temporal: resetPass,
          revision: selectedUser.revision,
        }),
      });
      setIsResetOpen(false);
      setResetPass('');
      loadUsers();
    } catch (err: any) {
      setErrorMsg(err.message || 'Error al restablecer contraseña.');
    }
  };

  return (
    <div className="page-container">
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h2 style={{ fontSize: '1.25rem', marginBottom: '0.25rem' }}>Gestión de Cuentas de Acceso</h2>
          <p style={{ fontSize: '0.85rem' }}>Administración de operadores y roles institucionales del sistema.</p>
        </div>

        <button onClick={() => setIsCreateOpen(true)} className="btn btn-primary">
          <Plus size={16} />
          <span>Crear Usuario</span>
        </button>
      </div>

      {errorMsg && (
        <div style={{ background: '#FEE2E2', border: '1px solid #FECACA', padding: '0.75rem', borderRadius: 'var(--radius-md)', color: '#B91C1C', marginBottom: '1.25rem', fontSize: '0.85rem' }}>
          {errorMsg}
        </div>
      )}

      {/* Tabla de Usuarios */}
      <div className="table-container">
        <table className="table">
          <thead>
            <tr>
              <th>Usuario</th>
              <th>Nombre Completo</th>
              <th>Rol Institucional</th>
              <th>Estado</th>
              <th>Cambio de Contraseña</th>
              <th style={{ textAlign: 'center' }}>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={6} style={{ textAlign: 'center', padding: '3rem' }}>Cargando usuarios...</td>
              </tr>
            ) : (
              users.map((u) => (
                <tr key={u.id}>
                  <td className="mono-amount" style={{ fontWeight: 700, color: 'var(--teal-500)' }}>{u.usuario}</td>
                  <td style={{ fontWeight: 600 }}>{u.nombre_completo}</td>
                  <td>
                    <span className={`badge ${
                      u.rol === 'ADMINISTRADOR' ? 'badge-teal' :
                      u.rol === 'PLANILLAS' ? 'badge-indigo' : 'badge-muted'
                    }`}>
                      {u.rol}
                    </span>
                  </td>
                  <td>
                    <span className={`badge ${u.activo ? 'badge-emerald' : 'badge-crimson'}`}>
                      {u.activo ? 'Activo' : 'Inactivo'}
                    </span>
                  </td>
                  <td>
                    <span className={`badge ${u.debe_cambiar_password ? 'badge-amber' : 'badge-emerald'}`}>
                      {u.debe_cambiar_password ? 'Pendiente' : 'Al día'}
                    </span>
                  </td>
                  <td style={{ textAlign: 'center' }}>
                    <button
                      onClick={() => {
                        setSelectedUser(u);
                        setResetPass('');
                        setErrorMsg(null);
                        setIsResetOpen(true);
                      }}
                      className="btn btn-ghost btn-sm"
                      title="Restablecer Contraseña"
                    >
                      <Key size={15} style={{ color: 'var(--amber-500)' }} />
                      <span>Restablecer</span>
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Modal Crear Usuario */}
      <Modal isOpen={isCreateOpen} onClose={() => setIsCreateOpen(false)} title="Crear Nueva Cuenta de Usuario">
        <form onSubmit={handleCreateUser}>
          <div className="form-group">
            <label className="form-label">Nombre de Usuario (Login) *</label>
            <input
              type="text"
              className="form-input"
              placeholder="Ej. mquispe"
              value={createForm.username}
              onChange={(e) => setCreateForm({ ...createForm, username: e.target.value })}
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label">Nombre Completo *</label>
            <input
              type="text"
              className="form-input"
              placeholder="Ej. Marco Antonio Quispe Ramos"
              value={createForm.nombre_completo}
              onChange={(e) => setCreateForm({ ...createForm, nombre_completo: e.target.value })}
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label">Rol Asignado *</label>
            <select
              className="form-select"
              value={createForm.rol}
              onChange={(e) => setCreateForm({ ...createForm, rol: e.target.value })}
            >
              <option value="PLANILLAS">PLANILLAS (Operador técnico completo)</option>
              <option value="CONSULTA">CONSULTA (Auditor / Solo lectura)</option>
              <option value="ADMINISTRADOR">ADMINISTRADOR (Acceso total institucional)</option>
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">Contraseña Temporal * (Mínimo 12 caracteres)</label>
            <input
              type="password"
              className="form-input"
              placeholder="••••••••••••"
              value={createForm.password_temporal}
              onChange={(e) => setCreateForm({ ...createForm, password_temporal: e.target.value })}
              required
            />
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              El usuario estará obligado a cambiarla en su primer inicio de sesión.
            </span>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem', marginTop: '1.5rem', borderTop: '1px solid var(--border-subtle)', paddingTop: '1rem' }}>
            <button type="button" onClick={() => setIsCreateOpen(false)} className="btn btn-secondary">Cancelar</button>
            <button type="submit" className="btn btn-primary">Registrar Cuenta</button>
          </div>
        </form>
      </Modal>

      {/* Modal Restablecer Contraseña */}
      <Modal isOpen={isResetOpen} onClose={() => setIsResetOpen(false)} title={`Restablecer Contraseña · ${selectedUser?.usuario}`}>
        <form onSubmit={handleResetPassword}>
          <p style={{ fontSize: '0.85rem', marginBottom: '1rem' }}>
            Ingresa una nueva contraseña temporal para <strong>{selectedUser?.nombre_completo}</strong>:
          </p>
          <div className="form-group">
            <label className="form-label">Nueva Contraseña Temporal *</label>
            <input
              type="password"
              className="form-input"
              placeholder="••••••••••••"
              value={resetPass}
              onChange={(e) => setResetPass(e.target.value)}
              required
            />
          </div>
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem', marginTop: '1.5rem', borderTop: '1px solid var(--border-subtle)', paddingTop: '1rem' }}>
            <button type="button" onClick={() => setIsResetOpen(false)} className="btn btn-secondary">Cancelar</button>
            <button type="submit" className="btn btn-primary">Guardar Nueva Contraseña</button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
