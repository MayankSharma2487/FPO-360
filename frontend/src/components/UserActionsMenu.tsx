import React, { useState, useRef, useCallback } from 'react';
import { DropdownPortal } from './DropdownPortal';

interface UserActionsMenuProps {
  user: any;
  isActive: boolean;
  onEdit: (user: any) => void;
  onResetPassword: (id: number) => void;
  onToggleStatus: (id: number, currentActive: boolean) => void;
}

export const UserActionsMenu: React.FC<UserActionsMenuProps> = ({
  user, isActive, onEdit, onResetPassword, onToggleStatus
}) => {
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
        <button className="actions-menu-item" onClick={() => { onEdit(user); close(); }}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
          </svg>
          Edit User
        </button>

        <button className="actions-menu-item" onClick={() => { onResetPassword(user.id); close(); }}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
            <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
            <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
          </svg>
          Reset Password
        </button>

        <div className="actions-menu-divider" />

        <button
          className={`actions-menu-item ${isActive ? 'actions-menu-item--danger' : 'actions-menu-item--success'}`}
          onClick={() => { onToggleStatus(user.id, isActive); close(); }}
        >
          {isActive ? (
            <>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10"/><line x1="4.93" y1="4.93" x2="19.07" y2="19.07"/>
              </svg>
              Disable User
            </>
          ) : (
            <>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>
              </svg>
              Enable User
            </>
          )}
        </button>
      </DropdownPortal>
    </div>
  );
};