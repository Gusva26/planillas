import React from 'react';
import { Modal } from './Modal';
import { AlertTriangle, AlertCircle, CheckCircle2 } from 'lucide-react';

interface ConfirmModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  isDestructive?: boolean;
  loading?: boolean;
}

export const ConfirmModal: React.FC<ConfirmModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmText = 'Confirmar',
  cancelText = 'Cancelar',
  isDestructive = true,
  loading = false,
}) => {
  return (
    <Modal isOpen={isOpen} onClose={onClose} title={title} maxWidth="480px">
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem', paddingTop: '0.25rem' }}>
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'flex-start' }}>
          <div
            style={{
              padding: '0.75rem',
              borderRadius: 'var(--radius-md)',
              background: isDestructive ? '#FEE2E2' : '#EFF6FF',
              border: `1px solid ${isDestructive ? '#FECACA' : '#BFDBFE'}`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
            }}
          >
            {isDestructive ? (
              <AlertTriangle size={24} color="#DC2626" />
            ) : (
              <AlertCircle size={24} color="#1D4ED8" />
            )}
          </div>
          <div>
            <p style={{ margin: 0, fontSize: '0.925rem', lineHeight: '1.5', color: '#334155' }}>
              {message}
            </p>
          </div>
        </div>

        <div
          style={{
            display: 'flex',
            justifyContent: 'flex-end',
            gap: '0.75rem',
            borderTop: '1px solid var(--border-subtle)',
            paddingTop: '1.25rem',
            marginTop: '0.5rem',
          }}
        >
          <button
            type="button"
            onClick={onClose}
            className="btn btn-secondary"
            disabled={loading}
          >
            {cancelText}
          </button>
          <button
            type="button"
            onClick={onConfirm}
            className={`btn ${isDestructive ? 'btn-danger' : 'btn-primary'}`}
            disabled={loading}
          >
            {loading ? 'Procesando...' : confirmText}
          </button>
        </div>
      </div>
    </Modal>
  );
};

interface AlertBannerProps {
  type: 'success' | 'error' | 'warning';
  message: string;
  onClose?: () => void;
}

export const AlertBanner: React.FC<AlertBannerProps> = ({ type, message, onClose }) => {
  const isErr = type === 'error';
  const isWarn = type === 'warning';
  const color = isErr ? '#DC2626' : isWarn ? '#D97706' : '#16A34A';
  const bg = isErr ? '#FEE2E2' : isWarn ? '#FEF3C7' : '#DCFCE7';
  const border = isErr ? '#FECACA' : isWarn ? '#FDE68A' : '#BBF7D0';

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0.85rem 1.25rem',
        borderRadius: 'var(--radius-md)',
        background: bg,
        border: `1px solid ${border}`,
        marginBottom: '1.25rem',
        animation: 'fadeIn 0.25s ease-out',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        {isErr ? (
          <AlertCircle size={18} color={color} />
        ) : isWarn ? (
          <AlertTriangle size={18} color={color} />
        ) : (
          <CheckCircle2 size={18} color={color} />
        )}
        <span style={{ fontSize: '0.875rem', fontWeight: 500, color: 'var(--text-primary)' }}>
          {message}
        </span>
      </div>
      {onClose && (
        <button
          onClick={onClose}
          className="btn btn-ghost btn-sm"
          style={{ padding: '0.2rem 0.5rem', color: 'var(--text-secondary)' }}
        >
          ×
        </button>
      )}
    </div>
  );
};
