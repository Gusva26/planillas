import React from 'react';
import { useAuth } from '../context/AuthContext';
import { 
  LayoutDashboard, 
  FileSpreadsheet, 
  Users, 
  UploadCloud, 
  FileText, 
  BookOpen, 
  BarChart3, 
  ShieldAlert, 
  UserCog, 
  LogOut,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';

interface SidebarProps {
  currentTab: string;
  onSelectTab: (tab: string) => void;
  collapsed: boolean;
  onToggleCollapse: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ 
  currentTab, 
  onSelectTab,
  collapsed,
  onToggleCollapse
}) => {
  const { user, logout } = useAuth();

  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, roles: ['ADMINISTRADOR', 'PLANILLAS', 'CONSULTA'] },
    { id: 'planillas', label: 'Planillas', icon: FileSpreadsheet, roles: ['ADMINISTRADOR', 'PLANILLAS', 'CONSULTA'] },
    { id: 'personal', label: 'Personal', icon: Users, roles: ['ADMINISTRADOR', 'PLANILLAS', 'CONSULTA'] },
    { id: 'importaciones', label: 'Importación', icon: UploadCloud, roles: ['ADMINISTRADOR', 'PLANILLAS'] },
    { id: 'documentos', label: 'Documentos', icon: FileText, roles: ['ADMINISTRADOR', 'PLANILLAS', 'CONSULTA'] },
    { id: 'catalogos', label: 'Catálogos', icon: BookOpen, roles: ['ADMINISTRADOR', 'PLANILLAS', 'CONSULTA'] },
    { id: 'reportes', label: 'Reportes', icon: BarChart3, roles: ['ADMINISTRADOR', 'PLANILLAS', 'CONSULTA'] },
    { id: 'auditoria', label: 'Auditoría', icon: ShieldAlert, roles: ['ADMINISTRADOR'] },
    { id: 'usuarios', label: 'Usuarios', icon: UserCog, roles: ['ADMINISTRADOR'] },
  ];

  const allowedItems = navItems.filter(item => user && item.roles.includes(user.rol));

  return (
    <aside className={`sidebar ${collapsed ? 'sidebar-collapsed' : ''}`}>
      {/* Brand Header */}
      {!collapsed ? (
        <div style={{ padding: '1.25rem 1rem', borderBottom: '1px solid var(--border-subtle)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', overflow: 'hidden' }}>
            <img 
              src="/assets/logo_ugel.png" 
              alt="UGEL Chepén" 
              style={{ 
                width: 38, 
                height: 38, 
                borderRadius: '50%', 
                objectFit: 'cover',
                border: '2px solid #E2E8F0',
                boxShadow: '0 1px 3px rgba(0, 0, 0, 0.08)',
                flexShrink: 0
              }} 
            />
            <div>
              <h2 style={{ fontSize: '0.975rem', margin: 0, lineHeight: 1.1, color: '#0F172A', whiteSpace: 'nowrap' }}>CAFAE UGEL</h2>
              <span style={{ fontSize: '0.7rem', color: '#1D4ED8', fontWeight: 700, letterSpacing: '0.05em', whiteSpace: 'nowrap' }}>
                SEDE CHEPÉN
              </span>
            </div>
          </div>
          <button
            onClick={onToggleCollapse}
            className="btn btn-ghost btn-sm"
            style={{ padding: '0.35rem', color: '#64748B', borderRadius: 'var(--radius-sm)' }}
            title="Plegar menú lateral"
          >
            <ChevronLeft size={18} />
          </button>
        </div>
      ) : (
        <div style={{ padding: '1rem 0.5rem', borderBottom: '1px solid var(--border-subtle)', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.5rem' }}>
          <img 
            src="/assets/logo_ugel.png" 
            alt="UGEL Chepén" 
            style={{ 
              width: 36, 
              height: 36, 
              borderRadius: '50%', 
              objectFit: 'cover',
              border: '2px solid #E2E8F0',
              boxShadow: '0 1px 3px rgba(0, 0, 0, 0.08)'
            }} 
          />
          <button
            onClick={onToggleCollapse}
            className="btn btn-ghost btn-sm"
            style={{ padding: '0.25rem', color: '#1D4ED8', borderRadius: 'var(--radius-sm)' }}
            title="Desplegar menú lateral"
          >
            <ChevronRight size={18} />
          </button>
        </div>
      )}

      {/* Nav List */}
      <nav style={{ flex: 1, padding: collapsed ? '0.75rem 0.35rem' : '1rem 0.75rem', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
        {allowedItems.map(item => {
          const Icon = item.icon;
          const isActive = currentTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onSelectTab(item.id)}
              title={collapsed ? item.label : undefined}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: collapsed ? 'center' : 'flex-start',
                gap: collapsed ? '0' : '0.75rem',
                padding: collapsed ? '0.75rem 0' : '0.75rem 1rem',
                borderRadius: 'var(--radius-md)',
                border: 'none',
                background: isActive ? '#EFF6FF' : 'transparent',
                color: isActive ? '#1D4ED8' : '#475569',
                fontWeight: isActive ? 600 : 500,
                fontSize: '0.875rem',
                cursor: 'pointer',
                textAlign: 'left',
                transition: 'all var(--transition-fast)',
                borderLeft: isActive ? '3px solid #1D4ED8' : '3px solid transparent',
                width: '100%',
              }}
              onMouseEnter={(e) => {
                if (!isActive) {
                  e.currentTarget.style.color = '#0F172A';
                  e.currentTarget.style.background = '#F1F5F9';
                }
              }}
              onMouseLeave={(e) => {
                if (!isActive) {
                  e.currentTarget.style.color = '#475569';
                  e.currentTarget.style.background = 'transparent';
                }
              }}
            >
              <Icon size={19} style={{ flexShrink: 0 }} />
              {!collapsed && <span style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{item.label}</span>}
            </button>
          );
        })}
      </nav>

      {/* User Card */}
      <div style={{ padding: collapsed ? '0.75rem 0.35rem' : '1.25rem', borderTop: '1px solid var(--border-subtle)', background: '#F8FAFC' }}>
        {!collapsed ? (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ overflow: 'hidden', maxWidth: '170px' }}>
              <div style={{ fontSize: '0.825rem', fontWeight: 600, color: '#0F172A', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>
                {user?.nombre || user?.username}
              </div>
              <span className={`badge ${user?.rol === 'ADMINISTRADOR' ? 'badge-indigo' : user?.rol === 'PLANILLAS' ? 'badge-teal' : 'badge-muted'}`} style={{ marginTop: '0.2rem', fontSize: '0.7rem', padding: '0.15rem 0.5rem' }}>
                {user?.rol}
              </span>
            </div>
            <button 
              onClick={logout} 
              title="Cerrar sesión"
              className="btn btn-ghost btn-sm" 
              style={{ padding: '0.45rem', borderRadius: 'var(--radius-sm)' }}
            >
              <LogOut size={16} />
            </button>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.5rem' }}>
            <div 
              style={{ width: 32, height: 32, borderRadius: '50%', background: '#EFF6FF', color: '#1D4ED8', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700, fontSize: '0.8rem' }}
              title={`${user?.nombre || user?.username} (${user?.rol})`}
            >
              {(user?.nombre || user?.username || 'U').substring(0, 1).toUpperCase()}
            </div>
            <button 
              onClick={logout} 
              title="Cerrar sesión"
              className="btn btn-ghost btn-sm" 
              style={{ padding: '0.4rem', borderRadius: 'var(--radius-sm)', color: '#DC2626' }}
            >
              <LogOut size={15} />
            </button>
          </div>
        )}
      </div>
    </aside>
  );
};
