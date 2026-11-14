import { ChevronLeft, ChevronRight } from "lucide-react";
import Button from "./Button.jsx";

const PAGE_SIZE_OPTIONS = [10, 20, 50, 100];

export default function Pagination({
  page = 1,
  pageSize = 10,
  totalItems = 0,
  onPageChange,
  onPageSizeChange,
}) {
  if (totalItems <= 0) return null;

  const totalPages = Math.max(1, Math.ceil(totalItems / pageSize));
  const start = (page - 1) * pageSize + 1;
  const end = Math.min(totalItems, page * pageSize);

  return (
    <div className="pagination-bar">
      <div className="pagination-info">
        <span>
          Mostrando <strong>{start}</strong>–<strong>{end}</strong> de{" "}
          <strong>{totalItems}</strong> itens
        </span>
        <label className="pagination-size-label">
          <span>Itens por página:</span>
          <select
            className="pagination-size-select"
            value={pageSize}
            onChange={(e) => onPageSizeChange(Number(e.target.value))}
            aria-label="Itens por página"
          >
            {PAGE_SIZE_OPTIONS.map((opt) => (
              <option key={opt} value={opt}>
                {opt}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="pagination-controls">
        <Button
          secondary
          small
          icon={ChevronLeft}
          disabled={page <= 1}
          onClick={() => onPageChange(page - 1)}
          aria-label="Página anterior"
        >
          Anterior
        </Button>
        <span className="pagination-page-indicator">
          Página {page} de {totalPages}
        </span>
        <Button
          secondary
          small
          icon={ChevronRight}
          disabled={page >= totalPages}
          onClick={() => onPageChange(page + 1)}
          aria-label="Próxima página"
        >
          Próxima
        </Button>
      </div>
    </div>
  );
}
