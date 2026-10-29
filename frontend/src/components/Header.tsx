import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Clock, ShieldCheck, KeyRound, Menu, Calendar } from 'lucide-react';

interface HeaderProps {
  currentTab: string;
  onOpenPasswordModal: () => void;
  onToggleSidebar?: () => void;
  sidebarCollapsed?: boolean;
}

export const Header: React.FC<HeaderProps> = ({ 
  currentTab, 
  onOpenPasswordModal,
  onToggleSidebar,
  sidebarCollapsed
}) => {
  const { user } = useAuth();
  const [time, setTime] = useState<string>('');
  const [dateStr, setDateStr] = useState<string>('');

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setTime(now.toLocaleTimeString('es-PE', { hour: '2-digit', minute: '2-digit', second: '2-digit' }));
      setDateStr(now.toLocaleDateString('es-PE', { weekday: 'short', day: '2-digit', month: 'short', year: 'numeric' }));
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  const meta: Record<string, { title: string; category: string; description: string }> = {
    dashboard: { 
      title: 'Panel Principal Institucional', 
      category: 'Resumen Ejecutivo', 
      description: 'Métricas clave, nómina activa y alertas de control' 
    },
    planillas: { 
      title: 'Gestión Mensual de Planillas', 
      category: 'Planillas', 
      description: 'Cálculo reactivo, edición en cuadrícula y cierre mensual' 
    },
    personal: { 
      title: 'Maestro de Personal', 
      category: 'Recursos Humanos', 
      description: 'Directorio unificado de servidores II.EE. y Sede' 
    },
    importaciones: { 
      title: 'Asistente de Importaciones', 
      category: 'Carga Masiva', 
      description: 'Carga asistida de descuentos bancarios e institucionales' 
    },
    documentos: { 
      title: 'Emisión de Documentos Oficiales', 
      category: 'Expedición', 
      description: 'Boletas de pago, resúmenes y archivos bancarios BN' 
    },
    catalogos: { 
      title: 'Catálogos y Estructuras', 
      category: 'Configuración', 
      description: 'II.EE., programas presupuestales, cargos y firmantes' 
    },
    reportes: { 
      title: 'Reportes y Consolidados', 
      category: 'Informes', 
      description: 'Nóminas analíticas, padrones y comparativas intermensuales' 
    },
    auditoria: { 
      title: 'Auditoría Forense Inmutable', 
      category: 'Seguridad', 
      description: 'Trazabilidad estricta y registro de cambios append-only' 
    },
    usuarios: { 
      title: 'Control de Usuarios y Accesos', 
      category: 'Seguridad', 
      description: 'Operadores del sistema, credenciales y privilegios' 
    },
  };

  const currentMeta = meta[currentTab] || {
    title: 'Sistema de Planillas',
    category: 'Módulo',
    description: 'UGEL Chepén'
  };

  return (
    <header className="header">
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        {onToggleSidebar && (
          <button
            onClick={onToggleSidebar}
            className="btn btn-ghost btn-sm"
            title={sidebarCollapsed ? 'Expandir menú lateral' : 'Plegar menú lateral'}
            aria-label={sidebarCollapsed ? 'Expandir menú lateral' : 'Plegar menú lateral'}
            style={{ padding: '0.45rem', color: '#475569', borderRadius: 'var(--radius-md)' }}
          >
            <Menu size={20} />
          </button>
        )}
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '2px' }}>
            <span style={{ fontSize: '0.725rem', fontWeight: 600, color: '#2563EB', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              {currentMeta.category}
            </span>
            <span style={{ color: '#CBD5E1', fontSize: '0.75rem' }}>/</span>
            <span style={{ fontSize: '0.75rem', color: '#64748B' }}>
              UGEL Chepén
            </span>
          </div>
          <h1 style={{ fontSize: '1.25rem', margin: 0, fontWeight: 700, color: '#0F172A', letterSpacing: '-0.02em' }}>
            {currentMeta.title}
          </h1>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
        {/* Estado del Sistema */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          padding: '0.35rem 0.75rem',
          borderRadius: 'var(--radius-full)',
          background: '#F1F5F9',
          border: '1px solid #E2E8F0',
          fontSize: '0.75rem',
          fontWeight: 600,
          color: '#334155'
        }}>
          <span style={{
            width: 7,
            height: 7,
            borderRadius: '50%',
            background: '#10B981',
            boxShadow: '0 0 0 2px rgba(16, 185, 129, 0.2)'
          }} />
          <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
            <ShieldCheck size={13} style={{ color: '#059669' }} />
            PostgreSQL ACID
          </span>
        </div>

        {/* Reloj y Fecha Oficial */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem',
          color: '#475569',
          fontSize: '0.8rem',
          borderLeft: '1px solid #E2E8F0',
          paddingLeft: '1rem'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
            <Calendar size={14} style={{ color: '#64748B' }} />
            <span style={{ textTransform: 'capitalize' }}>{dateStr}</span>
          </div>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.35rem',
            fontFamily: 'var(--font-mono)',
            fontWeight: 600,
            color: '#0F172A',
            background: '#F8FAFC',
            padding: '0.2rem 0.5rem',
            borderRadius: 'var(--radius-sm)',
            border: '1px solid #E2E8F0'
          }}>
            <Clock size={13} style={{ color: '#2563EB' }} />
            <span>{time}</span>
          </div>
        </div>

        {/* Botón Seguridad */}
        <button
          onClick={onOpenPasswordModal}
          className="btn btn-secondary btn-sm"
          title="Cambiar contraseña de acceso institucional"
          aria-label="Seguridad y contraseña"
          style={{ gap: '0.4rem' }}
        >
          <KeyRound size={14} style={{ color: '#2563EB' }} />
          <span>Seguridad</span>
        </button>
      </div>
    </header>
  );
};
