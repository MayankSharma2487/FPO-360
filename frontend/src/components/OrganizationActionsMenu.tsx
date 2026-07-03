import React, { useState, useRef, useCallback } from 'react';
import { DropdownPortal } from './DropdownPortal';

interface OrganizationActionsMenuProps {
  org: any;
  onEdit: (org: any) => void;
}

export const OrganizationActionsMenu: React.FC<OrganizationActionsMenuProps> = ({ org, onEdit }) => {
  const [open, setOpen] = useState(false);
  const btnRef = useRef<HTMLButtonElement>(null);
  const close = useCallback(() => setOpen(false), []);

  return (
    <div style={{ display: 'inline-flex' }}>
      <button
        ref={btnRef}
        onClick={() => setOpen(o => !o)}
        aria-expanded={open}
        className="actions-menu-trigger"
        title="Actions"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
          <circle cx="12" cy="5" r="1.5"/><circle cx="12" cy="12" r="1.5"/><circle cx="12" cy="19" r="1.5"/>
        </svg>
      </button>

      <DropdownPortal triggerRef={btnRef} open={open} onClose={close}>
        <button className="actions-menu-item" onClick={() => { onEdit(org); close(); }}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
          </svg>
          Edit Organization
        </button>
      </DropdownPortal>
    </div>
  );
};