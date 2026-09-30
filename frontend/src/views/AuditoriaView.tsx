import React, { useEffect, useState } from 'react';
import { apiRequest } from '../api/client';
import { Modal } from '../components/Modal';
import { ShieldAlert, Search, Eye, Filter } from 'lucide-react';

export const AuditoriaView: React.FC = () => {
  const [eventos, setEventos] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedEvento, setSelectedEvento] = useState<any | null>(null);
  const [cambios, setCambios] = useState<any[]>([]);
  const [loadingCambios, setLoadingCambios] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Filtros
  const [accionFiltro, setAccionFiltro] = useState('');
  const [entidadFiltro, setEntidadFiltro] = useState('');

  const loadEventos = async () => {
    setLoading(true);
    try {
      let query = '/api/auditoria?limite=150';
      if (accionFiltro) query += `&accion=${encodeURIComponent(accionFiltro)}`;
      if (entidadFiltro) query += `&entidad=${encodeURIComponent(entidadFiltro)}`;
      const list = await apiRequest<any[]>(query);
      setEventos(list);
    } catch (err) {
      console.error('Error cargando auditoría:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadEventos();
  }, [entidadFiltro]);

  const handleVerCambios = async (ev: any) => {
    setSelectedEvento(ev);
    setIsModalOpen(true);
    setLoadingCambios(true);
    try {
      const data = await apiRequest(`/api/auditoria/${ev.id}/cambios`);
      setCambios(data);
    } catch (err: any) {
      alert(err.message || 'Error al cargar cambios.');
    } finally {
      setLoadingCambios(false);
    }
  };

  return (
    <div className="page-container">
      {/* Barra de Filtros */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
          <select
            className="form-select"
            value={entidadFiltro}
            onChange={(e) => setEntidadFiltro(e.target.value)}
            style={{ width: '220px' }}
          >
            <option value="">-- Todas las Entidades --</option>
            <option value="planilla_versiones">Planilla Versiones</option>
            <option value="planilla_detalle">Planilla Detalle</option>
            <option value="planilla_descuentos">Descuentos</option>
            <option value="trabajadores">Trabajadores</option>
            <option value="importaciones">Importaciones</option>
            <option value="usuarios">Usuarios</option>
          </select>

          <input
            type="text"
            className="form-input"
            placeholder="Filtrar por acción..."
            value={accionFiltro}
            onChange={(e) => setAccionFiltro(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && loadEventos()}
            style={{ width: '220px' }}
          />

          <button onClick={loadEventos} className="btn btn-secondary">Filtrar</button>
        </div>

        <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
          Registro forense inmutable append-only
        </span>
      </div>

      {/* Tabla de Eventos */}
      <div className="table-container">
        <table className="table">
          <thead>
            <tr>
              <th>Fecha y Hora</th>
              <th>Usuario</th>
              <th>Acción</th>
              <th>Entidad</th>
              <th>Resultado</th>
              <th>Descripción</th>
              <th style={{ textAlign: 'center' }}>Cambios</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={7} style={{ textAlign: 'center', padding: '3rem' }}>Cargando registro forense...</td>
              </tr>
            ) : eventos.length === 0 ? (
              <tr>
                <td colSpan={7} style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
                  No se registraron eventos con los filtros seleccionados.
                </td>
              </tr>
            ) : (
              eventos.map((ev) => (
                <tr key={ev.id}>
                  <td className="mono-amount" style={{ fontSize: '0.775rem' }}>
                    {new Date(ev.fecha_hora).toLocaleString('es-PE')}
                  </td>
                  <td style={{ fontWeight: 600 }}>{ev.usuario_nombre || 'Sistema'}</td>
                  <td>
                    <span className="badge badge-indigo">{ev.accion}</span>
                  </td>
                  <td>{ev.entidad}</td>
                  <td>
                    <span className={`badge ${ev.resultado === 'EXITO' ? 'badge-emerald' : 'badge-crimson'}`}>
                      {ev.resultado}
                    </span>
                  </td>
                  <td style={{ fontSize: '0.8rem', maxWidth: '300px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {ev.descripcion || '—'}
                  </td>
                  <td style={{ textAlign: 'center' }}>
                    {ev.total_cambios > 0 ? (
                      <button onClick={() => handleVerCambios(ev)} className="btn btn-ghost btn-sm" title="Ver detalle de cambios">
                        <Eye size={15} style={{ color: 'var(--teal-500)' }} />
                        <span>{ev.total_cambios}</span>
                      </button>
                    ) : (
                      <span style={{ color: 'var(--text-muted)' }}>—</span>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Modal Ver Cambios Antes / Después */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={`Detalle de Cambios Forenses · Evento #${selectedEvento?.id}`}
        maxWidth="700px"
      >
        {loadingCambios ? (
          <div style={{ textAlign: 'center', padding: '2rem' }}>Cargando diferencias...</div>
        ) : cambios.length === 0 ? (
          <p style={{ textAlign: 'center', color: 'var(--text-muted)' }}>No hay cambios de campos específicos registrados.</p>
        ) : (
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Campo</th>
                  <th>Valor Anterior</th>
                  <th>Valor Nuevo</th>
                </tr>
              </thead>
              <tbody>
                {cambios.map((c) => (
                  <tr key={c.id}>
                    <td style={{ fontWeight: 600 }}>{c.campo}</td>
                    <td className="mono-amount" style={{ color: '#F87171' }}>{c.valor_anterior || '—'}</td>
                    <td className="mono-amount" style={{ color: '#34D399' }}>{c.valor_nuevo || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Modal>
    </div>
  );
};
