import React from 'react';
import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from 'lucide-react';

interface PaginationProps {
  currentPage: number;
  totalItems: number;
  pageSize: number;
  onPageChange: (page: number) => void;
  onPageSizeChange?: (pageSize: number) => void;
  pageSizeOptions?: number[];
  itemLabel?: string;
}

export const Pagination: React.FC<PaginationProps> = ({
  currentPage,
  totalItems,
  pageSize,
  onPageChange,
  onPageSizeChange,
  pageSizeOptions = [15, 25, 50, 100],
  itemLabel = 'registros',
}) => {
  const totalPages = Math.max(1, Math.ceil(totalItems / pageSize));
  const validPage = Math.min(Math.max(1, currentPage), totalPages);

  const startItem = totalItems === 0 ? 0 : (validPage - 1) * pageSize + 1;
  const endItem = Math.min(validPage * pageSize, totalItems);

  // Generar páginas a mostrar con elipsis inteligente
  const getPageNumbers = () => {
    const pages: (number | string)[] = [];
    if (totalPages <= 7) {
      for (let i = 1; i <= totalPages; i++) pages.push(i);
    } else {
      pages.push(1);
      if (validPage > 3) pages.push('...');
      const start = Math.max(2, validPage - 1);
      const end = Math.min(totalPages - 1, validPage + 1);
      for (let i = start; i <= end; i++) {
        if (!pages.includes(i)) pages.push(i);
      }
      if (validPage < totalPages - 2) pages.push('...');
      if (!pages.includes(totalPages)) pages.push(totalPages);
    }
    return pages;
  };

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      flexWrap: 'wrap',
      gap: '1rem',
      padding: '0.85rem 1.25rem',
      background: '#FFFFFF',
      borderTop: '1px solid #E2E8F0',
      borderRadius: '0 0 var(--radius-lg) var(--radius-lg)',
      fontSize: '0.825rem',
      color: '#475569',
    }}>
      {/* Información de rango */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <span>
          Mostrando <strong style={{ color: '#0F172A' }}>{startItem}</strong> - <strong style={{ color: '#0F172A' }}>{endItem}</strong> de <strong style={{ color: '#0F172A' }}>{totalItems}</strong> {itemLabel}
        </span>

        {/* Selector de tamaño de página */}
        {onPageSizeChange && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', marginLeft: '0.5rem' }}>
            <span style={{ color: '#64748B' }}>Filas por página:</span>
            <select
              className="form-select"
              value={pageSize}
              onChange={(e) => {
                onPageSizeChange(Number(e.target.value));
                onPageChange(1);
              }}
              style={{
                width: '72px',
                padding: '0.25rem 0.45rem',
                fontSize: '0.8rem',
                fontWeight: 600,
              }}
            >
              {pageSizeOptions.map((opt) => (
                <option key={opt} value={opt}>
                  {opt}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Controles de página */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
        {/* Primera página */}
        <button
          onClick={() => onPageChange(1)}
          disabled={validPage <= 1}
          className="btn btn-secondary btn-sm"
          style={{ padding: '0.35rem 0.5rem' }}
          title="Primera página"
        >
          <ChevronsLeft size={15} />
        </button>

        {/* Anterior */}
        <button
          onClick={() => onPageChange(validPage - 1)}
          disabled={validPage <= 1}
          className="btn btn-secondary btn-sm"
          style={{ padding: '0.35rem 0.5rem' }}
          title="Página anterior"
        >
          <ChevronLeft size={15} />
        </button>

        {/* Números de página */}
        {getPageNumbers().map((p, idx) => {
          if (p === '...') {
            return (
              <span key={`ellipsis-${idx}`} style={{ padding: '0 0.4rem', color: '#94A3B8' }}>
                ...
              </span>
            );
          }
          const isCurrent = p === validPage;
          return (
            <button
              key={p}
              onClick={() => onPageChange(p as number)}
              className={isCurrent ? 'btn btn-primary btn-sm' : 'btn btn-secondary btn-sm'}
              style={{
                minWidth: '32px',
                padding: '0.35rem 0.55rem',
                fontWeight: isCurrent ? 700 : 500,
              }}
            >
              {p}
            </button>
          );
        })}

        {/* Siguiente */}
        <button
          onClick={() => onPageChange(validPage + 1)}
          disabled={validPage >= totalPages}
          className="btn btn-secondary btn-sm"
          style={{ padding: '0.35rem 0.5rem' }}
          title="Página siguiente"
        >
          <ChevronRight size={15} />
        </button>

        {/* Última página */}
        <button
          onClick={() => onPageChange(totalPages)}
          disabled={validPage >= totalPages}
          className="btn btn-secondary btn-sm"
          style={{ padding: '0.35rem 0.5rem' }}
          title="Última página"
        >
          <ChevronsRight size={15} />
        </button>
      </div>
    </div>
  );
};
