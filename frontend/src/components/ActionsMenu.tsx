import { useState, useRef, useEffect } from 'react';

interface MenuAction {
  label: string;
  icon?: React.ReactNode;
  onClick: () => void;
  variant?: 'default' | 'danger' | 'success';
}

interface Props {
  actions: MenuAction[];
  className?: string;
}

export function ActionsMenu({ actions, className = '' }: Props) {
  const [open, setOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    };

    if (open) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [open]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') setOpen(false);
  };

  return (
    <div className={`relative ${className}`} ref={menuRef}>
      <button
        onClick={() => setOpen(!open)}
        className="actions-menu-trigger"
        aria-expanded={open}
        aria-label="Actions"
      >
        ⋮
      </button>

      {open && (
        <div className="actions-menu-dropdown" onKeyDown={handleKeyDown}>
          {actions.map((action, idx) => (
            <button
              key={idx}
              onClick={() => {
                action.onClick();
                setOpen(false);
              }}
              className={`actions-menu-item ${
                action.variant === 'danger'
                  ? 'actions-menu-item--danger'
                  : action.variant === 'success'
                  ? 'actions-menu-item--success'
                  : ''
              }`}
            >
              {action.icon && <span className="flex-shrink-0">{action.icon}</span>}
              {action.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}