import React, { useEffect, useState } from 'react';
import { apiRequest } from '../api/client';
import { useAuth } from '../context/AuthContext';
import { CatalogoBundle } from '../types';
import { Modal } from '../components/Modal';
import { ConfirmModal, AlertBanner } from '../components/ConfirmModal';
import {
  Plus,
  Trash2,
  Power,
  PowerOff,
  Building2,
  GraduationCap,
  Landmark,
  PenTool,
  Target,
  FolderTree,
  FileSpreadsheet,
  Briefcase,
  Award,
  UserCheck,
  Tag
} from 'lucide-react';

type CatalogoKey =
  | 'iiee'
  | 'niveles'
  | 'areas'
  | 'firmas'
  | 'metas'
  | 'programas'
  | 'partidas'
  | 'cargos'
  | 'categorias'
  | 'situaciones'
  | 'subtipos';

type GrupoKey = 'institucional' | 'presupuesto' | 'personal';

export const CatalogosView: React.FC = () => {
  const { user } = useAuth();
  const [catalogos, setCatalogos] = useState<CatalogoBundle | null>(null);
  const [grupoActivo, setGrupoActivo] = useState<GrupoKey>('institucional');
  const [activeTab, setActiveTab] = useState<CatalogoKey>('iiee');
  const [loading, setLoading] = useState(true);

  // Banner de alerta con diseño
  const [banner, setBanner] = useState<{ type: 'success' | 'error' | 'warning'; message: string } | null>(null);

  // Modal Confirmación Eliminar
  const [deleteTarget, setDeleteTarget] = useState<{
    endpoint: string;
    id: number;
    nombre: string;
    etiqueta: string;
  } | null>(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  // Modal Crear
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalType, setModalType] = useState<CatalogoKey>('iiee');
  const [nombre, setNombre] = useState('');
  const [codigo, setCodigo] = useState('');
  const [descripcion, setDescripcion] = useState('');
  const [cargoFirmante, setCargoFirmante] = useState('');
  const [orden, setOrden] = useState(1);

  const isAdmin = user && user.rol === 'ADMINISTRADOR';

  const showNotification = (type: 'success' | 'error' | 'warning', message: string) => {
    setBanner({ type, message });
    setTimeout(() => {
      setBanner(null);
    }, 5000);
  };

  const loadData = async () => {
    setLoading(true);
    try {
      const data = await apiRequest<CatalogoBundle>('/api/catalogos/bundle');
      setCatalogos(data);
    } catch (err: any) {
      console.error('Error cargando catálogos:', err);
      showNotification('error', err.message || 'Error cargando los catálogos.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleOpenCreate = (type: CatalogoKey) => {
    setModalType(type);
    setNombre('');
    setCodigo('');
    setDescripcion('');
    setCargoFirmante('');
    setOrden(1);
    setIsModalOpen(true);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (modalType === 'iiee') {
        await apiRequest('/api/catalogos/instituciones', {
          method: 'POST',
          body: JSON.stringify({ nombre: nombre.trim(), codigo_modular: codigo.trim() || null }),
        });
        showNotification('success', `Institución "${nombre.trim()}" registrada con éxito.`);
      } else if (modalType === 'niveles') {
        await apiRequest('/api/catalogos/niveles', {
          method: 'POST',
          body: JSON.stringify({ nombre: nombre.trim() }),
        });
        showNotification('success', `Nivel educativo "${nombre.trim()}" registrado.`);
      } else if (modalType === 'areas') {
        await apiRequest('/api/catalogos/areas', {
          method: 'POST',
          body: JSON.stringify({ nombre: nombre.trim() }),
        });
        showNotification('success', `Área "${nombre.trim()}" registrada.`);
      } else if (modalType === 'firmas') {
        await apiRequest('/api/catalogos/firmas', {
          method: 'POST',
          body: JSON.stringify({
            nombre_firmante: nombre.trim(),
            cargo_firmante: cargoFirmante.trim(),
          }),
        });
        showNotification('success', `Firma autorizada registrada con éxito.`);
      } else if (modalType === 'metas') {
        await apiRequest('/api/catalogos/metas', {
          method: 'POST',
          body: JSON.stringify({ codigo: codigo.trim(), descripcion: descripcion.trim() || nombre.trim() }),
        });
        showNotification('success', `Meta presupuestal "${codigo.trim()}" registrada.`);
      } else if (modalType === 'programas') {
        await apiRequest('/api/catalogos/programas', {
          method: 'POST',
          body: JSON.stringify({ codigo: codigo.trim(), nombre: nombre.trim(), orden }),
        });
        showNotification('success', `Programa presupuestario "${codigo.trim()}" registrado.`);
      } else if (modalType === 'partidas') {
        await apiRequest('/api/catalogos/partidas', {
          method: 'POST',
          body: JSON.stringify({ codigo: codigo.trim(), descripcion: descripcion.trim() }),
        });
        showNotification('success', `Partida presupuestaria "${codigo.trim()}" registrada.`);
      } else if (modalType === 'cargos') {
        await apiRequest('/api/catalogos/cargos', {
          method: 'POST',
          body: JSON.stringify({ nombre: nombre.trim() }),
        });
        showNotification('success', `Cargo "${nombre.trim()}" registrado.`);
      } else if (modalType === 'categorias') {
        await apiRequest('/api/catalogos/categorias', {
          method: 'POST',
          body: JSON.stringify({ codigo: codigo.trim(), descripcion: descripcion.trim() }),
        });
        showNotification('success', `Categoría remunerativa "${codigo.trim()}" registrada.`);
      } else if (modalType === 'situaciones') {
        await apiRequest('/api/catalogos/situaciones', {
          method: 'POST',
          body: JSON.stringify({ nombre: nombre.trim() }),
        });
        showNotification('success', `Situación laboral "${nombre.trim()}" registrada.`);
      } else if (modalType === 'subtipos') {
        await apiRequest('/api/catalogos/subtipos', {
          method: 'POST',
          body: JSON.stringify({ nombre: nombre.trim() }),
        });
        showNotification('success', `Subtipo de trabajador "${nombre.trim()}" registrado.`);
      }

      setIsModalOpen(false);
      loadData();
    } catch (err: any) {
      showNotification('error', err.message || 'Error al guardar el elemento.');
    }
  };

  const handleToggleEstado = async (
    endpoint: string,
    id: number,
    nuevoEstado: boolean,
    nombreItem: string
  ) => {
    try {
      await apiRequest(`/api/catalogos/${endpoint}/${id}/estado`, {
        method: 'PATCH',
        body: JSON.stringify({ activo: nuevoEstado }),
      });
      showNotification(
        'success',
        `"${nombreItem}" fue ${nuevoEstado ? 'activado/a' : 'desactivado/a'} con éxito.`
      );
      loadData();
    } catch (err: any) {
      showNotification('error', err.message || 'No se pudo cambiar el estado.');
    }
  };

  const handleConfirmDelete = async () => {
    if (!deleteTarget) return;
    setDeleteLoading(true);
    try {
      const res = await apiRequest<{ ok: boolean; mensaje: string }>(
        `/api/catalogos/${deleteTarget.endpoint}/${deleteTarget.id}`,
        { method: 'DELETE' }
      );
      showNotification('success', res.mensaje || `"${deleteTarget.nombre}" fue eliminada definitivamente.`);
      setDeleteTarget(null);
      loadData();
    } catch (err: any) {
      showNotification('error', err.message || 'No se pudo eliminar el registro.');
      setDeleteTarget(null);
    } finally {
      setDeleteLoading(false);
    }
  };

  // Grupos y pestañas
  const tabsPorGrupo: Record<GrupoKey, { key: CatalogoKey; label: string; count: number; icon: any }[]> = {
    institucional: [
      { key: 'iiee', label: 'Instituciones Educativas', count: catalogos?.instituciones?.length || 0, icon: Building2 },
      { key: 'niveles', label: 'Niveles Educativos', count: catalogos?.niveles?.length || 0, icon: GraduationCap },
      { key: 'areas', label: 'Áreas de Sede', count: catalogos?.areas?.length || 0, icon: Landmark },
      { key: 'firmas', label: 'Firmas Autorizadas', count: catalogos?.firmas?.length || 0, icon: PenTool },
    ],
    presupuesto: [
      { key: 'metas', label: 'Metas Presupuestales', count: catalogos?.metas?.length || 0, icon: Target },
      { key: 'programas', label: 'Programas Presupuestarios', count: catalogos?.programas?.length || 0, icon: FolderTree },
      { key: 'partidas', label: 'Partidas Presupuestarias', count: catalogos?.partidas?.length || 0, icon: FileSpreadsheet },
    ],
    personal: [
      { key: 'cargos', label: 'Cargos', count: catalogos?.cargos?.length || 0, icon: Briefcase },
      { key: 'categorias', label: 'Categorías Remunerativas', count: catalogos?.categorias?.length || 0, icon: Award },
      { key: 'situaciones', label: 'Situaciones Laborales', count: catalogos?.situaciones?.length || 0, icon: UserCheck },
      { key: 'subtipos', label: 'Subtipos de Trabajador', count: catalogos?.subtipos?.length || 0, icon: Tag },
    ],
  };

  const getEtiquetaBotonAgregar = (tab: CatalogoKey) => {
    switch (tab) {
      case 'iiee': return 'Agregar Institución';
      case 'niveles': return 'Agregar Nivel';
      case 'areas': return 'Agregar Área';
      case 'firmas': return 'Agregar Firma';
      case 'metas': return 'Agregar Meta';
      case 'programas': return 'Agregar Programa';
      case 'partidas': return 'Agregar Partida';
      case 'cargos': return 'Agregar Cargo';
      case 'categorias': return 'Agregar Categoría';
      case 'situaciones': return 'Agregar Situación';
      case 'subtipos': return 'Agregar Subtipo';
    }
  };

  const getTituloModal = (type: CatalogoKey) => {
    switch (type) {
      case 'iiee': return 'Registrar Institución Educativa';
      case 'niveles': return 'Registrar Nivel Educativo';
      case 'areas': return 'Registrar Área de Sede Central';
      case 'firmas': return 'Registrar Firma Autorizada';
      case 'metas': return 'Registrar Meta Presupuestaria';
      case 'programas': return 'Registrar Programa Presupuestario';
      case 'partidas': return 'Registrar Partida Presupuestaria';
      case 'cargos': return 'Registrar Cargo';
      case 'categorias': return 'Registrar Categoría Remunerativa';
      case 'situaciones': return 'Registrar Situación Laboral';
      case 'subtipos': return 'Registrar Subtipo de Trabajador';
    }
  };

  return (
    <div className="page-container">
      {/* Banner de Notificación Estilizado */}
      {banner && (
        <AlertBanner
          type={banner.type}
          message={banner.message}
          onClose={() => setBanner(null)}
        />
      )}

      {/* Selector de Grupos Principales */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div style={{ display: 'flex', background: '#F1F5F9', padding: '0.25rem', borderRadius: 'var(--radius-lg)', border: '1px solid var(--border-card)' }}>
          <button
            onClick={() => {
              setGrupoActivo('institucional');
              setActiveTab('iiee');
            }}
            className={`btn btn-sm ${grupoActivo === 'institucional' ? 'btn-primary' : 'btn-ghost'}`}
          >
            🏫 Institucional
          </button>
          <button
            onClick={() => {
              setGrupoActivo('presupuesto');
              setActiveTab('metas');
            }}
            className={`btn btn-sm ${grupoActivo === 'presupuesto' ? 'btn-primary' : 'btn-ghost'}`}
          >
            📊 Presupuesto
          </button>
          <button
            onClick={() => {
              setGrupoActivo('personal');
              setActiveTab('cargos');
            }}
            className={`btn btn-sm ${grupoActivo === 'personal' ? 'btn-primary' : 'btn-ghost'}`}
          >
            👥 Parámetros de Personal
          </button>
        </div>

        {isAdmin && (
          <button
            onClick={() => handleOpenCreate(activeTab)}
            className="btn btn-primary"
          >
            <Plus size={16} />
            <span>{getEtiquetaBotonAgregar(activeTab)}</span>
          </button>
        )}
      </div>

      {/* Sub-Pestañas del Grupo Activo */}
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem', flexWrap: 'wrap' }}>
        {tabsPorGrupo[grupoActivo].map((t) => {
          const Icon = t.icon;
          const isSelected = activeTab === t.key;
          return (
            <button
              key={t.key}
              onClick={() => setActiveTab(t.key)}
              className={`btn btn-sm ${isSelected ? 'btn-secondary' : 'btn-ghost'}`}
              style={{
                borderColor: isSelected ? 'var(--teal-500)' : 'transparent',
                background: isSelected ? 'rgba(20, 184, 166, 0.1)' : 'transparent',
                color: isSelected ? 'var(--teal-400)' : 'var(--text-secondary)',
              }}
            >
              <Icon size={14} />
              <span>{t.label} ({t.count})</span>
            </button>
          );
        })}
      </div>

      {/* =====================================================================
          TABLAS DE CATÁLOGOS
          ===================================================================== */}

      {/* 1. Instituciones */}
      {activeTab === 'iiee' && (
        <div className="table-container">
          <table className="table">
            <thead>
              <tr>
                <th>Código Modular</th>
                <th>Nombre de la Institución Educativa</th>
                <th>Nivel</th>
                <th>Estado</th>
                {isAdmin && <th style={{ textAlign: 'right' }}>Acciones</th>}
              </tr>
            </thead>
            <tbody>
              {catalogos?.instituciones?.map((i) => (
                <tr key={i.id}>
                  <td className="mono-amount" style={{ fontWeight: 600, color: 'var(--teal-500)' }}>
                    {i.codigo_modular || 'S/C'}
                  </td>
                  <td style={{ fontWeight: 600 }}>{i.nombre}</td>
                  <td>
                    <span className="badge badge-indigo">{i.nivel_nombre || 'Sin nivel'}</span>
                  </td>
                  <td>
                    <span className={`badge ${i.activo ? 'badge-emerald' : 'badge-crimson'}`}>
                      {i.activo ? 'Activa' : 'Inactiva'}
                    </span>
                  </td>
                  {isAdmin && (
                    <td style={{ textAlign: 'right' }}>
                      <div style={{ display: 'inline-flex', gap: '0.4rem', alignItems: 'center' }}>
                        <button
                          onClick={() => handleToggleEstado('instituciones', i.id, !i.activo, i.nombre)}
                          className="btn btn-sm btn-secondary"
                          style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem' }}
                        >
                          {i.activo ? <PowerOff size={13} color="#f87171" /> : <Power size={13} color="#34d399" />}
                          <span>{i.activo ? 'Desactivar' : 'Activar'}</span>
                        </button>
                        <button
                          onClick={() => setDeleteTarget({
                            endpoint: 'instituciones',
                            id: i.id,
                            nombre: i.nombre,
                            etiqueta: 'la institución educativa',
                          })}
                          className="btn btn-sm btn-ghost"
                          style={{ color: '#ef4444', padding: '0.3rem 0.5rem' }}
                          title="Eliminar de forma definitiva"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* 2. Niveles */}
      {activeTab === 'niveles' && (
        <div className="table-container">
          <table className="table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Nombre del Nivel Educativo</th>
                <th>Estado</th>
                {isAdmin && <th style={{ textAlign: 'right' }}>Acciones</th>}
              </tr>
            </thead>
            <tbody>
              {catalogos?.niveles?.map((n) => (
                <tr key={n.id}>
                  <td className="mono-amount">#{n.id}</td>
                  <td style={{ fontWeight: 600 }}>{n.nombre}</td>
                  <td>
                    <span className={`badge ${n.activo ? 'badge-emerald' : 'badge-crimson'}`}>
                      {n.activo ? 'Activo' : 'Inactivo'}
                    </span>
                  </td>
                  {isAdmin && (
                    <td style={{ textAlign: 'right' }}>
                      <div style={{ display: 'inline-flex', gap: '0.4rem', alignItems: 'center' }}>
                        <button
                          onClick={() => handleToggleEstado('niveles', n.id, !n.activo, n.nombre)}
                          className="btn btn-sm btn-secondary"
                          style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem' }}
                        >
                          {n.activo ? <PowerOff size={13} color="#f87171" /> : <Power size={13} color="#34d399" />}
                          <span>{n.activo ? 'Desactivar' : 'Activar'}</span>
                        </button>
                        <button
                          onClick={() => setDeleteTarget({
                            endpoint: 'niveles',
                            id: n.id,
                            nombre: n.nombre,
                            etiqueta: 'el nivel educativo',
                          })}
                          className="btn btn-sm btn-ghost"
                          style={{ color: '#ef4444', padding: '0.3rem 0.5rem' }}
                          title="Eliminar de forma definitiva"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* 3. Áreas */}
      {activeTab === 'areas' && (
        <div className="table-container">
          <table className="table">
            <thead>
              <tr>
                <th>Nombre del Área de Sede Central</th>
                <th>Estado</th>
                {isAdmin && <th style={{ textAlign: 'right' }}>Acciones</th>}
              </tr>
            </thead>
            <tbody>
              {catalogos?.areas?.map((a) => (
                <tr key={a.id}>
                  <td style={{ fontWeight: 600 }}>{a.nombre}</td>
                  <td>
                    <span className={`badge ${a.activo ? 'badge-emerald' : 'badge-crimson'}`}>
                      {a.activo ? 'Activa' : 'Inactiva'}
                    </span>
                  </td>
                  {isAdmin && (
                    <td style={{ textAlign: 'right' }}>
                      <div style={{ display: 'inline-flex', gap: '0.4rem', alignItems: 'center' }}>
                        <button
                          onClick={() => handleToggleEstado('areas', a.id, !a.activo, a.nombre)}
                          className="btn btn-sm btn-secondary"
                          style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem' }}
                        >
                          {a.activo ? <PowerOff size={13} color="#f87171" /> : <Power size={13} color="#34d399" />}
                          <span>{a.activo ? 'Desactivar' : 'Activar'}</span>
                        </button>
                        <button
                          onClick={() => setDeleteTarget({
                            endpoint: 'areas',
                            id: a.id,
                            nombre: a.nombre,
                            etiqueta: 'el área de sede',
                          })}
                          className="btn btn-sm btn-ghost"
                          style={{ color: '#ef4444', padding: '0.3rem 0.5rem' }}
                          title="Eliminar de forma definitiva"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* 4. Firmas */}
      {activeTab === 'firmas' && (
        <div className="table-container">
          <table className="table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Nombre del Firmante</th>
                <th>Cargo Institucional</th>
                <th>Estado</th>
                {isAdmin && <th style={{ textAlign: 'right' }}>Acciones</th>}
              </tr>
            </thead>
            <tbody>
              {catalogos?.firmas?.map((f) => {
                const nombreFirmante = f.nombre_completo || f.nombre_firmante || `Firma #${f.id}`;
                return (
                  <tr key={f.id}>
                    <td className="mono-amount">#{f.id}</td>
                    <td style={{ fontWeight: 600 }}>{nombreFirmante}</td>
                    <td style={{ color: 'var(--text-secondary)' }}>{f.cargo || f.cargo_firmante}</td>
                    <td>
                      <span className={`badge ${f.activo ? 'badge-emerald' : 'badge-crimson'}`}>
                        {f.activo ? 'Activa' : 'Inactiva'}
                      </span>
                    </td>
                    {isAdmin && (
                      <td style={{ textAlign: 'right' }}>
                        <div style={{ display: 'inline-flex', gap: '0.4rem', alignItems: 'center' }}>
                          <button
                            onClick={() => handleToggleEstado('firmas', f.id, !f.activo, nombreFirmante)}
                            className="btn btn-sm btn-secondary"
                            style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem' }}
                          >
                            {f.activo ? <PowerOff size={13} color="#f87171" /> : <Power size={13} color="#34d399" />}
                            <span>{f.activo ? 'Desactivar' : 'Activar'}</span>
                          </button>
                          <button
                            onClick={() => setDeleteTarget({
                              endpoint: 'firmas',
                              id: f.id,
                              nombre: nombreFirmante,
                              etiqueta: 'la firma autorizada',
                            })}
                            className="btn btn-sm btn-ghost"
                            style={{ color: '#ef4444', padding: '0.3rem 0.5rem' }}
                            title="Eliminar de forma definitiva"
                          >
                            <Trash2 size={14} />
                          </button>
                        </div>
                      </td>
                    )}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* 5. Metas */}
      {activeTab === 'metas' && (
        <div className="table-container">
          <table className="table">
            <thead>
              <tr>
                <th>Código de Meta</th>
                <th>Descripción Presupuestaria</th>
                <th>Estado</th>
                {isAdmin && <th style={{ textAlign: 'right' }}>Acciones</th>}
              </tr>
            </thead>
            <tbody>
              {catalogos?.metas?.map((m) => (
                <tr key={m.id}>
                  <td className="mono-amount" style={{ fontWeight: 700, color: 'var(--indigo-500)' }}>{m.codigo}</td>
                  <td>{m.descripcion || 'Sin descripción'}</td>
                  <td>
                    <span className={`badge ${m.activo ? 'badge-emerald' : 'badge-crimson'}`}>
                      {m.activo ? 'Activa' : 'Inactiva'}
                    </span>
                  </td>
                  {isAdmin && (
                    <td style={{ textAlign: 'right' }}>
                      <div style={{ display: 'inline-flex', gap: '0.4rem', alignItems: 'center' }}>
                        <button
                          onClick={() => handleToggleEstado('metas', m.id, !m.activo, `Meta ${m.codigo}`)}
                          className="btn btn-sm btn-secondary"
                          style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem' }}
                        >
                          {m.activo ? <PowerOff size={13} color="#f87171" /> : <Power size={13} color="#34d399" />}
                          <span>{m.activo ? 'Desactivar' : 'Activar'}</span>
                        </button>
                        <button
                          onClick={() => setDeleteTarget({
                            endpoint: 'metas',
                            id: m.id,
                            nombre: `Meta ${m.codigo}`,
                            etiqueta: 'la meta presupuestaria',
                          })}
                          className="btn btn-sm btn-ghost"
                          style={{ color: '#ef4444', padding: '0.3rem 0.5rem' }}
                          title="Eliminar de forma definitiva"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* 6. Programas */}
      {activeTab === 'programas' && (
        <div className="table-container">
          <table className="table">
            <thead>
              <tr>
                <th>Código</th>
                <th>Nombre del Programa Presupuestario</th>
                <th>Orden</th>
                <th>Estado</th>
                {isAdmin && <th style={{ textAlign: 'right' }}>Acciones</th>}
              </tr>
            </thead>
            <tbody>
              {catalogos?.programas?.map((p) => (
                <tr key={p.id}>
                  <td className="mono-amount" style={{ fontWeight: 700, color: 'var(--teal-500)' }}>{p.codigo}</td>
                  <td style={{ fontWeight: 600 }}>{p.nombre}</td>
                  <td className="mono-amount">{p.orden}</td>
                  <td>
                    <span className={`badge ${p.activo ? 'badge-emerald' : 'badge-crimson'}`}>
                      {p.activo ? 'Activo' : 'Inactivo'}
                    </span>
                  </td>
                  {isAdmin && (
                    <td style={{ textAlign: 'right' }}>
                      <div style={{ display: 'inline-flex', gap: '0.4rem', alignItems: 'center' }}>
                        <button
                          onClick={() => handleToggleEstado('programas', p.id, !p.activo, p.nombre)}
                          className="btn btn-sm btn-secondary"
                          style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem' }}
                        >
                          {p.activo ? <PowerOff size={13} color="#f87171" /> : <Power size={13} color="#34d399" />}
                          <span>{p.activo ? 'Desactivar' : 'Activar'}</span>
                        </button>
                        <button
                          onClick={() => setDeleteTarget({
                            endpoint: 'programas',
                            id: p.id,
                            nombre: `Programa ${p.codigo} - ${p.nombre}`,
                            etiqueta: 'el programa presupuestario',
                          })}
                          className="btn btn-sm btn-ghost"
                          style={{ color: '#ef4444', padding: '0.3rem 0.5rem' }}
                          title="Eliminar de forma definitiva"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* 7. Partidas */}
      {activeTab === 'partidas' && (
        <div className="table-container">
          <table className="table">
            <thead>
              <tr>
                <th>Código de Partida</th>
                <th>Descripción Clasificadora</th>
                <th>Estado</th>
                {isAdmin && <th style={{ textAlign: 'right' }}>Acciones</th>}
              </tr>
            </thead>
            <tbody>
              {catalogos?.partidas?.map((pt) => (
                <tr key={pt.id}>
                  <td className="mono-amount" style={{ fontWeight: 700, color: 'var(--indigo-500)' }}>{pt.codigo}</td>
                  <td>{pt.descripcion}</td>
                  <td>
                    <span className={`badge ${pt.activo ? 'badge-emerald' : 'badge-crimson'}`}>
                      {pt.activo ? 'Activa' : 'Inactiva'}
                    </span>
                  </td>
                  {isAdmin && (
                    <td style={{ textAlign: 'right' }}>
                      <div style={{ display: 'inline-flex', gap: '0.4rem', alignItems: 'center' }}>
                        <button
                          onClick={() => handleToggleEstado('partidas', pt.id, !pt.activo, pt.codigo)}
                          className="btn btn-sm btn-secondary"
                          style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem' }}
                        >
                          {pt.activo ? <PowerOff size={13} color="#f87171" /> : <Power size={13} color="#34d399" />}
                          <span>{pt.activo ? 'Desactivar' : 'Activar'}</span>
                        </button>
                        <button
                          onClick={() => setDeleteTarget({
                            endpoint: 'partidas',
                            id: pt.id,
                            nombre: `Partida ${pt.codigo}`,
                            etiqueta: 'la partida presupuestaria',
                          })}
                          className="btn btn-sm btn-ghost"
                          style={{ color: '#ef4444', padding: '0.3rem 0.5rem' }}
                          title="Eliminar de forma definitiva"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* 8. Cargos */}
      {activeTab === 'cargos' && (
        <div className="table-container">
          <table className="table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Nombre del Cargo</th>
                <th>Estado</th>
                {isAdmin && <th style={{ textAlign: 'right' }}>Acciones</th>}
              </tr>
            </thead>
            <tbody>
              {catalogos?.cargos?.map((c) => (
                <tr key={c.id}>
                  <td className="mono-amount">#{c.id}</td>
                  <td style={{ fontWeight: 600 }}>{c.nombre}</td>
                  <td>
                    <span className={`badge ${c.activo ? 'badge-emerald' : 'badge-crimson'}`}>
                      {c.activo ? 'Activo' : 'Inactivo'}
                    </span>
                  </td>
                  {isAdmin && (
                    <td style={{ textAlign: 'right' }}>
                      <div style={{ display: 'inline-flex', gap: '0.4rem', alignItems: 'center' }}>
                        <button
                          onClick={() => handleToggleEstado('cargos', c.id, !c.activo, c.nombre)}
                          className="btn btn-sm btn-secondary"
                          style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem' }}
                        >
                          {c.activo ? <PowerOff size={13} color="#f87171" /> : <Power size={13} color="#34d399" />}
                          <span>{c.activo ? 'Desactivar' : 'Activar'}</span>
                        </button>
                        <button
                          onClick={() => setDeleteTarget({
                            endpoint: 'cargos',
                            id: c.id,
                            nombre: c.nombre,
                            etiqueta: 'el cargo',
                          })}
                          className="btn btn-sm btn-ghost"
                          style={{ color: '#ef4444', padding: '0.3rem 0.5rem' }}
                          title="Eliminar de forma definitiva"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* 9. Categorías */}
      {activeTab === 'categorias' && (
        <div className="table-container">
          <table className="table">
            <thead>
              <tr>
                <th>Código</th>
                <th>Descripción de Categoría</th>
                <th>Estado</th>
                {isAdmin && <th style={{ textAlign: 'right' }}>Acciones</th>}
              </tr>
            </thead>
            <tbody>
              {catalogos?.categorias?.map((cat) => (
                <tr key={cat.id}>
                  <td className="mono-amount" style={{ fontWeight: 700, color: 'var(--teal-500)' }}>{cat.codigo}</td>
                  <td style={{ fontWeight: 600 }}>{cat.descripcion}</td>
                  <td>
                    <span className={`badge ${cat.activo ? 'badge-emerald' : 'badge-crimson'}`}>
                      {cat.activo ? 'Activa' : 'Inactiva'}
                    </span>
                  </td>
                  {isAdmin && (
                    <td style={{ textAlign: 'right' }}>
                      <div style={{ display: 'inline-flex', gap: '0.4rem', alignItems: 'center' }}>
                        <button
                          onClick={() => handleToggleEstado('categorias', cat.id, !cat.activo, cat.codigo)}
                          className="btn btn-sm btn-secondary"
                          style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem' }}
                        >
                          {cat.activo ? <PowerOff size={13} color="#f87171" /> : <Power size={13} color="#34d399" />}
                          <span>{cat.activo ? 'Desactivar' : 'Activar'}</span>
                        </button>
                        <button
                          onClick={() => setDeleteTarget({
                            endpoint: 'categorias',
                            id: cat.id,
                            nombre: `Categoría ${cat.codigo}`,
                            etiqueta: 'la categoría remunerativa',
                          })}
                          className="btn btn-sm btn-ghost"
                          style={{ color: '#ef4444', padding: '0.3rem 0.5rem' }}
                          title="Eliminar de forma definitiva"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* 10. Situaciones */}
      {activeTab === 'situaciones' && (
        <div className="table-container">
          <table className="table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Situación Laboral</th>
                <th>Estado</th>
                {isAdmin && <th style={{ textAlign: 'right' }}>Acciones</th>}
              </tr>
            </thead>
            <tbody>
              {catalogos?.situaciones?.map((s) => (
                <tr key={s.id}>
                  <td className="mono-amount">#{s.id}</td>
                  <td style={{ fontWeight: 600 }}>{s.nombre}</td>
                  <td>
                    <span className={`badge ${s.activo ? 'badge-emerald' : 'badge-crimson'}`}>
                      {s.activo ? 'Activa' : 'Inactiva'}
                    </span>
                  </td>
                  {isAdmin && (
                    <td style={{ textAlign: 'right' }}>
                      <div style={{ display: 'inline-flex', gap: '0.4rem', alignItems: 'center' }}>
                        <button
                          onClick={() => handleToggleEstado('situaciones', s.id, !s.activo, s.nombre)}
                          className="btn btn-sm btn-secondary"
                          style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem' }}
                        >
                          {s.activo ? <PowerOff size={13} color="#f87171" /> : <Power size={13} color="#34d399" />}
                          <span>{s.activo ? 'Desactivar' : 'Activar'}</span>
                        </button>
                        <button
                          onClick={() => setDeleteTarget({
                            endpoint: 'situaciones',
                            id: s.id,
                            nombre: s.nombre,
                            etiqueta: 'la situación laboral',
                          })}
                          className="btn btn-sm btn-ghost"
                          style={{ color: '#ef4444', padding: '0.3rem 0.5rem' }}
                          title="Eliminar de forma definitiva"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* 11. Subtipos */}
      {activeTab === 'subtipos' && (
        <div className="table-container">
          <table className="table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Subtipo de Trabajador</th>
                <th>Estado</th>
                {isAdmin && <th style={{ textAlign: 'right' }}>Acciones</th>}
              </tr>
            </thead>
            <tbody>
              {catalogos?.subtipos?.map((sub) => (
                <tr key={sub.id}>
                  <td className="mono-amount">#{sub.id}</td>
                  <td style={{ fontWeight: 600 }}>{sub.nombre}</td>
                  <td>
                    <span className={`badge ${sub.activo ? 'badge-emerald' : 'badge-crimson'}`}>
                      {sub.activo ? 'Activo' : 'Inactivo'}
                    </span>
                  </td>
                  {isAdmin && (
                    <td style={{ textAlign: 'right' }}>
                      <div style={{ display: 'inline-flex', gap: '0.4rem', alignItems: 'center' }}>
                        <button
                          onClick={() => handleToggleEstado('subtipos', sub.id, !sub.activo, sub.nombre)}
                          className="btn btn-sm btn-secondary"
                          style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem' }}
                        >
                          {sub.activo ? <PowerOff size={13} color="#f87171" /> : <Power size={13} color="#34d399" />}
                          <span>{sub.activo ? 'Desactivar' : 'Activar'}</span>
                        </button>
                        <button
                          onClick={() => setDeleteTarget({
                            endpoint: 'subtipos',
                            id: sub.id,
                            nombre: sub.nombre,
                            etiqueta: 'el subtipo de trabajador',
                          })}
                          className="btn btn-sm btn-ghost"
                          style={{ color: '#ef4444', padding: '0.3rem 0.5rem' }}
                          title="Eliminar de forma definitiva"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Modal de Confirmación de Eliminación Estilizado */}
      <ConfirmModal
        isOpen={deleteTarget !== null}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleConfirmDelete}
        title="Confirmar Eliminación Definitiva"
        message={`¿Está seguro de que desea eliminar definitivamente ${deleteTarget?.etiqueta || 'el elemento'} "${deleteTarget?.nombre}"? Esta acción borrará el registro de la base de datos si no cuenta con planillas o personal vinculado.`}
        confirmText="Sí, Eliminar Definitivamente"
        cancelText="Cancelar"
        isDestructive={true}
        loading={deleteLoading}
      />

      {/* Modal Crear */}
      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title={getTituloModal(modalType)}>
        <form onSubmit={handleSave}>
          {modalType === 'iiee' ? (
            <>
              <div className="form-group">
                <label className="form-label">Nombre de la Institución Educativa *</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="Ej. I.E. San Pedro"
                  value={nombre}
                  onChange={(e) => setNombre(e.target.value)}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Código Modular</label>
                <input
                  type="text"
                  className="form-input mono-amount"
                  placeholder="Ej. 0345678"
                  value={codigo}
                  onChange={(e) => setCodigo(e.target.value)}
                />
              </div>
            </>
          ) : modalType === 'niveles' || modalType === 'cargos' || modalType === 'situaciones' || modalType === 'subtipos' || modalType === 'areas' ? (
            <div className="form-group">
              <label className="form-label">Nombre del Elemento *</label>
              <input
                type="text"
                className="form-input"
                placeholder={
                  modalType === 'niveles' ? 'Ej. INICIAL, PRIMARIA, SECUNDARIA' :
                  modalType === 'areas' ? 'Ej. Área de Gestión Pedagógica' :
                  modalType === 'cargos' ? 'Ej. Especialista Administrativo I' :
                  modalType === 'situaciones' ? 'Ej. NOMBRADO, CONTRATADO' :
                  'Ej. DOCENTE, ADMINISTRATIVO'
                }
                value={nombre}
                onChange={(e) => setNombre(e.target.value)}
                required
              />
            </div>
          ) : modalType === 'firmas' ? (
            <>
              <div className="form-group">
                <label className="form-label">Nombre Completo de la Autoridad *</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="Ej. Dr. Carlos Alberto Mendoza"
                  value={nombre}
                  onChange={(e) => setNombre(e.target.value)}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Cargo Institucional *</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="Ej. Director de UGEL Chepén"
                  value={cargoFirmante}
                  onChange={(e) => setCargoFirmante(e.target.value)}
                  required
                />
              </div>
            </>
          ) : modalType === 'metas' ? (
            <>
              <div className="form-group">
                <label className="form-label">Código de Meta *</label>
                <input
                  type="text"
                  className="form-input mono-amount"
                  placeholder="Ej. 0045"
                  value={codigo}
                  onChange={(e) => setCodigo(e.target.value)}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Descripción Presupuestaria *</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="Ej. Gestión Administrativa y de Personal"
                  value={descripcion}
                  onChange={(e) => setDescripcion(e.target.value)}
                  required
                />
              </div>
            </>
          ) : modalType === 'programas' ? (
            <>
              <div className="form-group">
                <label className="form-label">Código del Programa *</label>
                <input
                  type="text"
                  className="form-input mono-amount"
                  placeholder="Ej. 9001"
                  value={codigo}
                  onChange={(e) => setCodigo(e.target.value)}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Nombre del Programa *</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="Ej. Acciones Centrales"
                  value={nombre}
                  onChange={(e) => setNombre(e.target.value)}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Orden Jerárquico</label>
                <input
                  type="number"
                  min="0"
                  className="form-input"
                  value={orden}
                  onChange={(e) => setOrden(Number(e.target.value))}
                />
              </div>
            </>
          ) : modalType === 'partidas' ? (
            <>
              <div className="form-group">
                <label className="form-label">Código Clasificador de Partida *</label>
                <input
                  type="text"
                  className="form-input mono-amount"
                  placeholder="Ej. 2.1.11.21"
                  value={codigo}
                  onChange={(e) => setCodigo(e.target.value)}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Descripción de la Partida *</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="Ej. Asignación a Fondos de Asistencia y Estímulo"
                  value={descripcion}
                  onChange={(e) => setDescripcion(e.target.value)}
                  required
                />
              </div>
            </>
          ) : (
            <>
              <div className="form-group">
                <label className="form-label">Código de Categoría *</label>
                <input
                  type="text"
                  className="form-input mono-amount"
                  placeholder="Ej. F1, STA, SAC"
                  value={codigo}
                  onChange={(e) => setCodigo(e.target.value)}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Descripción de Categoría *</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="Ej. Funcionario 1"
                  value={descripcion}
                  onChange={(e) => setDescripcion(e.target.value)}
                  required
                />
              </div>
            </>
          )}

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem', marginTop: '1.5rem', borderTop: '1px solid var(--border-subtle)', paddingTop: '1rem' }}>
            <button type="button" onClick={() => setIsModalOpen(false)} className="btn btn-secondary">Cancelar</button>
            <button type="submit" className="btn btn-primary">Guardar Registro</button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
