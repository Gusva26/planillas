import React, { useEffect, useState } from 'react';
import { apiRequest } from '../api/client';
import { mensajeDeError } from '../api/errors';
import { UserAccount } from '../types';
import { Modal } from '../components/Modal';
import { UserCog, Plus, Key, ShieldCheck, CheckCircle2, User, Lock, AlertCircle } from 'lucide-react';

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
    } catch (err) {
      setErrorMsg(mensajeDeError(err, 'Error al cargar usuarios.'));
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
    } catch (err) {
      setErrorMsg(mensajeDeError(err, 'Error al crear usuario.'));
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
    } catch (err) {
      setErrorMsg(mensajeDeError(err, 'Error al restablecer contraseña.'));
    }
  };

  return (
    <div className="page-container">
      {/* Encabezado */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: '1.75rem',
        flexWrap: 'wrap',
        gap: '1rem'
      }}>
        <div>
          <span style={{ fontSize: '0.725rem', fontWeight: 700, color: '#2563EB', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Seguridad y Accesos
          </span>
          <h2 style={{ fontSize: '1.35rem', marginTop: '0.15rem', marginBottom: '0.2rem', color: '#0F172A', fontWeight: 800 }}>
            Gestión de Cuentas y Operadores
          </h2>
          <p style={{ fontSize: '0.85rem', color: '#64748B', margin: 0 }}>
            Administración de credenciales con cifrado Argon2id, roles institucionales y políticas de contraseña.
          </p>
        </div>

        <button 
          onClick={() => {
            setErrorMsg(null);
            setIsCreateOpen(true);
          }} 
          className="btn btn-primary"
          style={{ fontWeight: 700 }}
        >
          <Plus size={16} />
          <span>Crear Nuevo Operador</span>
        </button>
      </div>

      {errorMsg && (
        <div style={{
          background: '#FEF2F2',
          border: '1.5px solid #FECACA',
          padding: '0.85rem 1.25rem',
          borderRadius: 'var(--radius-md)',
          color: '#991B1B',
          marginBottom: '1.5rem',
          fontSize: '0.85rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem'
        }}>
          <AlertCircle size={17} style={{ color: '#DC2626' }} />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Tabla de Usuarios */}
      <div className="table-container">
        <table className="table">
          <thead>
            <tr>
              <th style={{ width: '120px' }}>Cuenta (Login)</th>
              <th>Nombre Completo del Operador</th>
              <th style={{ width: '160px' }}>Rol Institucional</th>
              <th style={{ width: '100px', textAlign: 'center' }}>Estado</th>
              <th style={{ width: '160px', textAlign: 'center' }}>Política de Clave</th>
              <th style={{ textAlign: 'center', width: '140px' }}>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={6} style={{ textAlign: 'center', padding: '3.5rem', color: '#64748B' }}>
                  Cargando directorio de operadores...
                </td>
              </tr>
            ) : (
              users.map((u) => (
                <tr key={u.id}>
                  <td className="mono-amount" style={{ fontWeight: 700, color: '#1D4ED8' }}>
                    {u.usuario}
                  </td>
                  <td>
                    <div style={{ fontWeight: 700, color: '#0F172A' }}>{u.nombre_completo}</div>
                  </td>
                  <td>
                    <span className={`badge ${
                      u.rol === 'ADMINISTRADOR' ? 'badge-indigo' :
                      u.rol === 'PLANILLAS' ? 'badge-teal' : 'badge-muted'
                    }`}>
                      {u.rol}
                    </span>
                  </td>
                  <td style={{ textAlign: 'center' }}>
                    <span className={`badge ${u.activo ? 'badge-emerald' : 'badge-crimson'}`}>
                      {u.activo ? 'Activo' : 'Inactivo'}
                    </span>
                  </td>
                  <td style={{ textAlign: 'center' }}>
                    <span className={`badge ${u.debe_cambiar_password ? 'badge-amber' : 'badge-emerald'}`}>
                      {u.debe_cambiar_password ? 'Cambio Pendiente' : 'Actualizada'}
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
                      className="btn btn-secondary btn-sm"
                      style={{ padding: '0.3rem 0.65rem' }}
                      title="Restablecer Contraseña temporal"
                    >
                      <Key size={13} style={{ color: '#D97706' }} />
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
      <Modal isOpen={isCreateOpen} onClose={() => setIsCreateOpen(false)} title="Crear Nueva Cuenta de Operador">
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
            <label className="form-label">Nombre Completo del Servidor *</label>
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
            <label className="form-label">Rol Institucional *</label>
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
            <span style={{ fontSize: '0.75rem', color: '#64748B', marginTop: '2px' }}>
              El usuario estará forzado a cambiarla obligatoriamente en su primer ingreso.
            </span>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1.5rem', borderTop: '1px solid var(--border-subtle)', paddingTop: '1.25rem' }}>
            <button type="button" onClick={() => setIsCreateOpen(false)} className="btn btn-secondary">Cancelar</button>
            <button type="submit" className="btn btn-primary">Registrar Cuenta</button>
          </div>
        </form>
      </Modal>

      {/* Modal Restablecer Contraseña */}
      <Modal isOpen={isResetOpen} onClose={() => setIsResetOpen(false)} title={`Restablecer Contraseña · ${selectedUser?.usuario}`}>
        <form onSubmit={handleResetPassword}>
          <p style={{ fontSize: '0.85rem', color: '#475569', marginBottom: '1.25rem' }}>
            Ingresa una nueva contraseña temporal para el operador <strong>{selectedUser?.nombre_completo}</strong>:
          </p>
          <div className="form-group">
            <label className="form-label">Nueva Contraseña Temporal * (mínimo 12 caracteres)</label>
            <input
              type="password"
              className="form-input"
              placeholder="••••••••••••"
              value={resetPass}
              onChange={(e) => setResetPass(e.target.value)}
              required
            />
          </div>
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1.5rem', borderTop: '1px solid var(--border-subtle)', paddingTop: '1.25rem' }}>
            <button type="button" onClick={() => setIsResetOpen(false)} className="btn btn-secondary">Cancelar</button>
            <button type="submit" className="btn btn-primary">Guardar Nueva Clave</button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
