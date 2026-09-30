import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Clock, ShieldCheck, KeyRound, Menu } from 'lucide-react';

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

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setTime(now.toLocaleTimeString('es-PE', { hour: '2-digit', minute: '2-digit', second: '2-digit' }));
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  const titles: Record<string, string> = {
    dashboard: 'Panel Principal Institucional',
    planillas: 'Gestión Mensual de Planillas',
    personal: 'Maestro de Personal (II.EE. y Sede)',
    importaciones: 'Asistente de Importación de Descuentos',
    documentos: 'Centro de Emisión de Documentos Oficiales',
    catalogos: 'Catálogos y Parámetros Institucionales',
    reportes: 'Reportes Administrativos Obligatorios',
    auditoria: 'Auditoría Forense Inmutable',
    usuarios: 'Gestión de Cuentas y Accesos',
  };

  return (
    <header className="header">
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
        {onToggleSidebar && (
          <button
            onClick={onToggleSidebar}
            className="btn btn-ghost btn-sm"
            title={sidebarCollapsed ? 'Expandir menú lateral' : 'Plegar menú lateral'}
            style={{ padding: '0.45rem', color: '#475569', borderRadius: 'var(--radius-sm)' }}
          >
            <Menu size={20} />
          </button>
        )}
        <div>
          <h1 style={{ fontSize: '1.25rem', margin: 0, fontWeight: 700, color: '#0F172A' }}>
            {titles[currentTab] || 'Sistema de Planillas'}
          </h1>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '0.15rem' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>UGEL Chepén</span>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>•</span>
            <span style={{ fontSize: '0.75rem', color: '#059669', display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}>
              <ShieldCheck size={12} /> PostgreSQL 17 ACID
            </span>
          </div>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
        {/* Reloj Oficial */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--text-secondary)', fontSize: '0.825rem', fontFamily: 'var(--font-mono)' }}>
          <Clock size={15} style={{ color: 'var(--teal-500)' }} />
          <span>{time}</span>
        </div>

        {/* Botón Cambiar Contraseña */}
        <button
          onClick={onOpenPasswordModal}
          className="btn btn-secondary btn-sm"
          title="Cambiar contraseña de acceso"
        >
          <KeyRound size={14} />
          <span>Seguridad</span>
        </button>
      </div>
    </header>
  );
};
