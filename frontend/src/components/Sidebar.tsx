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
  ChevronRight,
  ShieldCheck
} from 'lucide-react';

interface SidebarProps {
  currentTab: string;
  onSelectTab: (tab: string) => void;
  collapsed: boolean;
  onToggleCollapse: () => void;
}

interface NavItem {
  id: string;
  label: string;
  icon: React.ElementType;
  roles: string[];
  section?: string;
}

export const Sidebar: React.FC<SidebarProps> = ({ 
  currentTab, 
  onSelectTab,
  collapsed,
  onToggleCollapse
}) => {
  const { user, logout } = useAuth();

  const navItems: NavItem[] = [
    // Operaciones
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, roles: ['ADMINISTRADOR', 'PLANILLAS', 'CONSULTA'], section: 'OPERACIONES' },
    { id: 'planillas', label: 'Planillas', icon: FileSpreadsheet, roles: ['ADMINISTRADOR', 'PLANILLAS', 'CONSULTA'] },
    { id: 'personal', label: 'Personal', icon: Users, roles: ['ADMINISTRADOR', 'PLANILLAS', 'CONSULTA'] },
    { id: 'importaciones', label: 'Importación', icon: UploadCloud, roles: ['ADMINISTRADOR', 'PLANILLAS'] },
    // Documentos y Análisis
    { id: 'documentos', label: 'Documentos', icon: FileText, roles: ['ADMINISTRADOR', 'PLANILLAS', 'CONSULTA'], section: 'DOCUMENTOS Y GESTIÓN' },
    { id: 'reportes', label: 'Reportes', icon: BarChart3, roles: ['ADMINISTRADOR', 'PLANILLAS', 'CONSULTA'] },
    // Configuración & Seguridad
    { id: 'catalogos', label: 'Catálogos', icon: BookOpen, roles: ['ADMINISTRADOR', 'PLANILLAS', 'CONSULTA'], section: 'SISTEMA Y CONTROL' },
    { id: 'auditoria', label: 'Auditoría', icon: ShieldAlert, roles: ['ADMINISTRADOR'] },
    { id: 'usuarios', label: 'Usuarios', icon: UserCog, roles: ['ADMINISTRADOR'] },
  ];

  const allowedItems = navItems.filter(item => user && item.roles.includes(user.rol));

  const roleBadgeClass = user?.rol === 'ADMINISTRADOR' 
    ? 'badge-indigo' 
    : user?.rol === 'PLANILLAS' 
      ? 'badge-teal' 
      : 'badge-muted';

  return (
    <aside className={`sidebar ${collapsed ? 'sidebar-collapsed' : ''}`}>
      {/* Brand Header */}
      {!collapsed ? (
        <div style={{
          padding: '1.25rem 1.15rem',
          borderBottom: '1px solid var(--border-subtle)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: '#FFFFFF'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem', overflow: 'hidden' }}>
            <div style={{
              width: 40,
              height: 40,
              borderRadius: '10px',
              border: '1.5px solid #E2E8F0',
              overflow: 'hidden',
              flexShrink: 0,
              background: '#FFFFFF',
              boxShadow: '0 2px 4px rgba(15, 23, 42, 0.05)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <img 
                src="/assets/logo_ugel.png" 
                alt="UGEL Chepén" 
                style={{ width: '100%', height: '100%', objectFit: 'cover' }} 
              />
            </div>
            <div style={{ overflow: 'hidden' }}>
              <div style={{ fontSize: '0.95rem', fontWeight: 800, color: '#0F172A', letterSpacing: '-0.02em', lineHeight: 1.1 }}>
                CAFAE UGEL
              </div>
              <div style={{ fontSize: '0.7rem', color: '#2563EB', fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', marginTop: '2px' }}>
                Sede Chepén
              </div>
            </div>
          </div>
          <button
            onClick={onToggleCollapse}
            className="btn btn-ghost btn-sm"
            style={{ padding: '0.35rem', color: '#64748B', borderRadius: 'var(--radius-sm)' }}
            title="Plegar menú lateral"
            aria-label="Plegar menú lateral"
          >
            <ChevronLeft size={18} />
          </button>
        </div>
      ) : (
        <div style={{
          padding: '1.15rem 0.5rem',
          borderBottom: '1px solid var(--border-subtle)',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: '0.75rem',
          background: '#FFFFFF'
        }}>
          <div style={{
            width: 36,
            height: 36,
            borderRadius: '10px',
            border: '1.5px solid #E2E8F0',
            overflow: 'hidden',
            background: '#FFFFFF',
            boxShadow: '0 2px 4px rgba(15, 23, 42, 0.05)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <img 
              src="/assets/logo_ugel.png" 
              alt="UGEL Chepén" 
              style={{ width: '100%', height: '100%', objectFit: 'cover' }} 
            />
          </div>
          <button
            onClick={onToggleCollapse}
            className="btn btn-ghost btn-sm"
            style={{ padding: '0.3rem', color: '#2563EB', borderRadius: 'var(--radius-sm)' }}
            title="Desplegar menú lateral"
            aria-label="Desplegar menú lateral"
          >
            <ChevronRight size={18} />
          </button>
        </div>
      )}

      {/* Navigation List */}
      <nav style={{
        flex: 1,
        padding: collapsed ? '0.85rem 0.45rem' : '1rem 0.85rem',
        display: 'flex',
        flexDirection: 'column',
        gap: '0.2rem',
        overflowY: 'auto'
      }}>
        {allowedItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentTab === item.id;

          return (
            <React.Fragment key={item.id}>
              {/* Sección encabezado solo en modo expandido */}
              {!collapsed && item.section && (
                <div style={{
                  fontSize: '0.65rem',
                  fontWeight: 700,
                  color: '#94A3B8',
                  letterSpacing: '0.08em',
                  padding: '0.85rem 0.75rem 0.35rem',
                  textTransform: 'uppercase'
                }}>
                  {item.section}
                </div>
              )}

              <button
                onClick={() => onSelectTab(item.id)}
                title={collapsed ? item.label : undefined}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: collapsed ? 'center' : 'flex-start',
                  gap: collapsed ? '0' : '0.85rem',
                  padding: collapsed ? '0.7rem 0' : '0.65rem 0.85rem',
                  borderRadius: 'var(--radius-md)',
                  border: 'none',
                  background: isActive ? '#EFF6FF' : 'transparent',
                  color: isActive ? '#1D4ED8' : '#475569',
                  fontWeight: isActive ? 600 : 500,
                  fontSize: '0.85rem',
                  cursor: 'pointer',
                  textAlign: 'left',
                  transition: 'all var(--transition-fast)',
                  position: 'relative',
                  width: '100%',
                }}
                onMouseEnter={(e) => {
                  if (!isActive) {
                    e.currentTarget.style.color = '#0F172A';
                    e.currentTarget.style.background = '#F8FAFC';
                  }
                }}
                onMouseLeave={(e) => {
                  if (!isActive) {
                    e.currentTarget.style.color = '#475569';
                    e.currentTarget.style.background = 'transparent';
                  }
                }}
              >
                {isActive && (
                  <span style={{
                    position: 'absolute',
                    left: 0,
                    top: '15%',
                    bottom: '15%',
                    width: '3.5px',
                    borderRadius: '0 4px 4px 0',
                    background: '#1D4ED8',
                  }} />
                )}
                <Icon 
                  size={18} 
                  strokeWidth={isActive ? 2.2 : 1.8}
                  style={{ 
                    flexShrink: 0, 
                    color: isActive ? '#1D4ED8' : '#64748B',
                    transition: 'color var(--transition-fast)'
                  }} 
                />
                {!collapsed && (
                  <span style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {item.label}
                  </span>
                )}
              </button>
            </React.Fragment>
          );
        })}
      </nav>

      {/* User Status & Profile Footer */}
      <div style={{
        padding: collapsed ? '0.85rem 0.45rem' : '1.15rem',
        borderTop: '1px solid var(--border-subtle)',
        background: '#FAFCFE'
      }}>
        {!collapsed ? (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '0.75rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', overflow: 'hidden' }}>
              <div style={{
                width: 36,
                height: 36,
                borderRadius: 'var(--radius-full)',
                background: '#DBEAFE',
                color: '#1D4ED8',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontWeight: 700,
                fontSize: '0.85rem',
                flexShrink: 0,
                border: '1.5px solid #BFDBFE'
              }}>
                {(user?.nombre || user?.username || 'U').substring(0, 1).toUpperCase()}
              </div>
              <div style={{ overflow: 'hidden' }}>
                <div style={{
                  fontSize: '0.825rem',
                  fontWeight: 600,
                  color: '#0F172A',
                  textOverflow: 'ellipsis',
                  overflow: 'hidden',
                  whiteSpace: 'nowrap'
                }}>
                  {user?.nombre || user?.username}
                </div>
                <div style={{ marginTop: '0.15rem' }}>
                  <span className={`badge ${roleBadgeClass}`} style={{ fontSize: '0.65rem', padding: '0.1rem 0.45rem' }}>
                    {user?.rol}
                  </span>
                </div>
              </div>
            </div>
            <button 
              onClick={logout} 
              title="Cerrar sesión segura"
              aria-label="Cerrar sesión segura"
              className="btn btn-ghost btn-sm" 
              style={{ padding: '0.45rem', borderRadius: 'var(--radius-md)', color: '#DC2626' }}
            >
              <LogOut size={16} />
            </button>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.65rem' }}>
            <div 
              style={{
                width: 34,
                height: 34,
                borderRadius: 'var(--radius-full)',
                background: '#DBEAFE',
                color: '#1D4ED8',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontWeight: 700,
                fontSize: '0.825rem',
                border: '1.5px solid #BFDBFE'
              }}
              title={`${user?.nombre || user?.username} (${user?.rol})`}
            >
              {(user?.nombre || user?.username || 'U').substring(0, 1).toUpperCase()}
            </div>
            <button 
              onClick={logout} 
              title="Cerrar sesión segura"
              aria-label="Cerrar sesión segura"
              className="btn btn-ghost btn-sm" 
              style={{ padding: '0.35rem', borderRadius: 'var(--radius-sm)', color: '#DC2626' }}
            >
              <LogOut size={16} />
            </button>
          </div>
        )}
      </div>
    </aside>
  );
};
