import React, { useEffect, useState } from 'react';
import { apiRequest } from '../api/client';
import { mensajeDeError } from '../api/errors';
import { Modal } from '../components/Modal';
import { Pagination } from '../components/Pagination';
import { CambioAuditoria, EventoAuditoria, PaginaAuditoria } from '../types';
import { ShieldAlert, Search, Eye, Filter, ShieldCheck, Clock, User, ArrowRight } from 'lucide-react';

export const AuditoriaView: React.FC = () => {
  const [eventos, setEventos] = useState<EventoAuditoria[]>([]);
  const [totalEventos, setTotalEventos] = useState(0);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [selectedEvento, setSelectedEvento] = useState<EventoAuditoria | null>(null);
  const [cambios, setCambios] = useState<CambioAuditoria[]>([]);
  const [loadingCambios, setLoadingCambios] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Filtros
  const [accionFiltro, setAccionFiltro] = useState('');
  const [entidadFiltro, setEntidadFiltro] = useState('');

  // Paginación en el servidor: el registro append-only no se descarga completo
  const [pagina, setPagina] = useState(1);
  const [tamano, setTamano] = useState(25);

  const loadEventos = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const params = new URLSearchParams({
        limite: String(tamano),
        desplazamiento: String((pagina - 1) * tamano),
      });
      if (accionFiltro) params.set('accion', accionFiltro);
      if (entidadFiltro) params.set('entidad', entidadFiltro);

      const data = await apiRequest<PaginaAuditoria>(`/api/auditoria?${params.toString()}`);
      setEventos(data.items);
      setTotalEventos(data.total);
    } catch (err) {
      setEventos([]);
      setTotalEventos(0);
      setErrorMsg(mensajeDeError(err, 'Error al cargar la auditoría.'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadEventos();
  }, [entidadFiltro, pagina, tamano]);

  const handleFiltrar = () => {
    if (pagina === 1) {
      loadEventos();
    } else {
      setPagina(1);
    }
  };

  const handleVerCambios = async (ev: EventoAuditoria) => {
    setSelectedEvento(ev);
    setIsModalOpen(true);
    setLoadingCambios(true);
    try {
      const data = await apiRequest<CambioAuditoria[]>(`/api/auditoria/${ev.id}/cambios`);
      setCambios(data);
    } catch (err) {
      setCambios([]);
      alert(mensajeDeError(err, 'Error al cargar cambios.'));
    } finally {
      setLoadingCambios(false);
    }
  };

  const getBadgeAccion = (accion: string) => {
    const act = (accion || '').toUpperCase();
    if (act.includes('INSERT') || act.includes('CREAR')) return 'badge-emerald';
    if (act.includes('UPDATE') || act.includes('EDIT')) return 'badge-indigo';
    if (act.includes('CERRAR')) return 'badge-amber';
    if (act.includes('REABRIR') || act.includes('DELETE') || act.includes('ELIMINAR')) return 'badge-crimson';
    return 'badge-muted';
  };

  return (
    <div className="page-container">
      {/* Encabezado */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '1rem',
        marginBottom: '1.5rem'
      }}>
        <div>
          <span style={{ fontSize: '0.725rem', fontWeight: 700, color: '#2563EB', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Control y Seguridad Forense
          </span>
          <h2 style={{ fontSize: '1.35rem', marginTop: '0.15rem', marginBottom: '0.2rem', color: '#0F172A', fontWeight: 800 }}>
            Auditoría Forense Inmutable
          </h2>
          <p style={{ fontSize: '0.85rem', color: '#64748B', margin: 0 }}>
            Trazabilidad rigurosa de todas las transacciones, modificaciones de haberes, cierres y aperturas.
          </p>
        </div>

        <div style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '0.45rem',
          padding: '0.4rem 0.85rem',
          borderRadius: 'var(--radius-full)',
          background: '#EFF6FF',
          border: '1px solid #DBEAFE',
          color: '#1D4ED8',
          fontSize: '0.75rem',
          fontWeight: 600
        }}>
          <ShieldCheck size={14} />
          <span>Bitácora Append-Only Certificada</span>
        </div>
      </div>

      {/* Barra de Filtros */}
      <div className="filter-toolbar">
        <div style={{ display: 'flex', gap: '0.85rem', flexWrap: 'wrap', alignItems: 'center' }}>
          <select
            className="form-select"
            value={entidadFiltro}
            onChange={(e) => {
              setEntidadFiltro(e.target.value);
              setPagina(1);
            }}
            style={{ width: '230px', fontWeight: 600 }}
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
            placeholder="Filtrar por acción (ej. CERRAR)..."
            value={accionFiltro}
            onChange={(e) => setAccionFiltro(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleFiltrar()}
            style={{ width: '240px' }}
          />

          <button onClick={handleFiltrar} className="btn btn-secondary btn-sm" style={{ padding: '0.55rem 1rem' }}>
            <Filter size={14} />
            <span>Filtrar</span>
          </button>
        </div>

        <span style={{ fontSize: '0.8rem', color: '#64748B' }}>
          <strong>{totalEventos.toLocaleString('es-PE')}</strong> eventos registrados con estos filtros
        </span>
      </div>

      {errorMsg && (
        <div className="alert alert-error" role="alert" style={{ marginBottom: '1rem' }}>
          {errorMsg}
        </div>
      )}

      {/* Tabla de Eventos */}
      <div className="table-container">
        <table className="table">
          <thead>
            <tr>
              <th style={{ width: '160px' }}>Fecha y Hora</th>
              <th>Operador</th>
              <th style={{ width: '130px' }}>Acción</th>
              <th>Entidad Auditada</th>
              <th style={{ width: '100px', textAlign: 'center' }}>Resultado</th>
              <th>Descripción del Evento</th>
              <th style={{ textAlign: 'center', width: '90px' }}>Diff</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={7} style={{ textAlign: 'center', padding: '3.5rem', color: '#64748B' }}>
                  Cargando registro de auditoría forense...
                </td>
              </tr>
            ) : eventos.length === 0 ? (
              <tr>
                <td colSpan={7} style={{ textAlign: 'center', padding: '3.5rem', color: '#64748B' }}>
                  No se registraron eventos con los filtros seleccionados.
                </td>
              </tr>
            ) : (
              eventos.map((ev) => (
                <tr key={ev.id}>
                  <td className="mono-amount" style={{ fontSize: '0.775rem', color: '#475569' }}>
                    {new Date(ev.fecha_hora).toLocaleString('es-PE')}
                  </td>
                  <td style={{ fontWeight: 600, color: '#0F172A' }}>
                    {ev.usuario_nombre || 'Sistema'}
                  </td>
                  <td>
                    <span className={`badge ${getBadgeAccion(ev.accion)}`}>
                      {ev.accion}
                    </span>
                  </td>
                  <td style={{ color: '#475569', fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>
                    {ev.entidad}
                  </td>
                  <td style={{ textAlign: 'center' }}>
                    <span className={`badge ${ev.resultado === 'EXITO' ? 'badge-emerald' : 'badge-crimson'}`}>
                      {ev.resultado}
                    </span>
                  </td>
                  <td style={{ fontSize: '0.8rem', maxWidth: '320px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', color: '#334155' }}>
                    {ev.descripcion || '—'}
                  </td>
                  <td style={{ textAlign: 'center' }}>
                    {ev.total_cambios > 0 ? (
                      <button 
                        onClick={() => handleVerCambios(ev)} 
                        className="btn btn-secondary btn-sm"
                        style={{ padding: '0.25rem 0.55rem', gap: '0.3rem', fontSize: '0.75rem' }}
                        title="Ver detalle de cambios antes/después"
                      >
                        <Eye size={13} style={{ color: '#1D4ED8' }} />
                        <span>{ev.total_cambios}</span>
                      </button>
                    ) : (
                      <span style={{ color: '#CBD5E1' }}>—</span>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
        <Pagination
          currentPage={pagina}
          totalItems={totalEventos}
          pageSize={tamano}
          onPageChange={setPagina}
          onPageSizeChange={setTamano}
          pageSizeOptions={[15, 25, 50, 100]}
          itemLabel="eventos"
        />
      </div>
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={`Inspección Forense de Cambios · Registro #${selectedEvento?.id}`}
        maxWidth="720px"
      >
        {loadingCambios ? (
          <div style={{ textAlign: 'center', padding: '2.5rem', color: '#64748B' }}>
            Extrayendo diferencias históricas...
          </div>
        ) : cambios.length === 0 ? (
          <p style={{ textAlign: 'center', color: '#64748B', padding: '1.5rem' }}>
            No hay cambios de campos específicos para este evento.
          </p>
        ) : (
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Campo Modificado</th>
                  <th>Valor Anterior</th>
                  <th>Valor Nuevo Registrado</th>
                </tr>
              </thead>
              <tbody>
                {cambios.map((c) => (
                  <tr key={c.id}>
                    <td style={{ fontWeight: 700, color: '#0F172A', fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>
                      {c.campo}
                    </td>
                    <td className="mono-amount" style={{ color: '#DC2626', background: '#FEF2F2' }}>
                      {c.valor_anterior || '(vacío)'}
                    </td>
                    <td className="mono-amount" style={{ color: '#059669', background: '#ECFDF5' }}>
                      {c.valor_nuevo || '(vacío)'}
                    </td>
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
