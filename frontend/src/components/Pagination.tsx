import type { PaginationMeta } from '../api/types'

interface PaginationProps {
  meta: PaginationMeta
  onPageChange: (page: number) => void
  disabled?: boolean
}

export function Pagination({ meta, onPageChange, disabled }: PaginationProps) {
  const { current_page, total_pages, total_records, page_size } = meta

  if (total_records === 0) return null

  return (
    <div className="pagination">
      <p className="pagination__info muted">
        Page {current_page} of {total_pages} ({total_records} total, {page_size} per page)
      </p>
      <div className="pagination__actions">
        <button
          type="button"
          className="btn btn--ghost btn--small"
          disabled={disabled || current_page <= 1}
          onClick={() => onPageChange(current_page - 1)}
        >
          Previous
        </button>
        <button
          type="button"
          className="btn btn--ghost btn--small"
          disabled={disabled || current_page >= total_pages}
          onClick={() => onPageChange(current_page + 1)}
        >
          Next
        </button>
      </div>
    </div>
  )
}
