import React from 'react';
import { Button } from 'react-bootstrap';

const Pagination = ({ page, onPageChange }) => {
  if (!page) return null;

  return (
    <div className="pagination">
      <Button
        variant="outline-primary"
        className="page-button"
        onClick={() => onPageChange(page.current - 1)}
        disabled={!page.has_previous}
      >
        Previous
      </Button>
      
      <span className="mx-2 d-flex align-items-center">
        Page {page.current} of {page.total_pages}
      </span>
      
      <Button
        variant="outline-primary"
        className="page-button"
        onClick={() => onPageChange(page.current + 1)}
        disabled={!page.has_next}
      >
        Next
      </Button>
    </div>
  );
};

export default Pagination; 