import { useState, useRef, useEffect, useCallback } from 'react';
import { createPortal } from 'react-dom';

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
  const triggerRef = useRef<HTMLButtonElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  
  // Explicitly type the state so TS knows it can be either a number or a string ('auto')
  const [coords, setCoords] = useState<{
    top: number | string;
    bottom: number | string;
    left: number | string;
    right: number | string;
  }>({ top: 0, left: 0, right: 'auto', bottom: 'auto' });

  // Calculate position dynamically
  const updatePosition = useCallback(() => {
    if (!triggerRef.current) return;
    const rect = triggerRef.current.getBoundingClientRect();
    
    const spaceBelow = window.innerHeight - rect.bottom;
    const spaceRight = window.innerWidth - rect.right;
    const menuWidth = 180; // matching CSS min-width
    const menuHeight = actions.length * 40 + 16; // approx height of menu

    let top: number | string = rect.bottom + 6;
    let bottom: number | string = 'auto';
    let left: number | string = rect.left;
    let right: number | string = 'auto';

    // If not enough space below, open upward
    if (spaceBelow < menuHeight && rect.top > menuHeight) {
      top = 'auto';
      bottom = window.innerHeight - rect.top + 6;
    }

    // If not enough space to the right, align to the left side
    if (spaceRight < menuWidth && rect.left > menuWidth) {
      left = 'auto';
      right = window.innerWidth - rect.right;
    }

    setCoords({ top, bottom, left, right });
  }, [actions.length]);

  // Recalculate on scroll and resize
  useEffect(() => {
    if (open) {
      updatePosition();
      window.addEventListener('resize', updatePosition);
      window.addEventListener('scroll', updatePosition, true); // true for capture phase to catch table scrolling
    }
    return () => {
      window.removeEventListener('resize', updatePosition);
      window.removeEventListener('scroll', updatePosition, true);
    };
  }, [open, updatePosition]);

  // Handle outside clicks
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Node;
      if (
        triggerRef.current && !triggerRef.current.contains(target) &&
        dropdownRef.current && !dropdownRef.current.contains(target)
      ) {
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
    <div className={`relative ${className}`}>
      <button
        ref={triggerRef}
        onClick={(e) => {
          e.stopPropagation();
          setOpen(!open);
        }}
        className="actions-menu-trigger"
        aria-expanded={open}
        aria-label="Actions"
      >
        ⋮
      </button>

      {open && createPortal(
        <div 
          ref={dropdownRef} 
          className="actions-menu-dropdown" 
          onKeyDown={handleKeyDown}
          style={{
            position: 'fixed',
            top: coords.top,
            bottom: coords.bottom,
            left: coords.left,
            right: coords.right,
            zIndex: 99999, // Ensure it is above all table headers/modals
            margin: 0
          }}
        >
          {actions.map((action, idx) => (
            <button
              key={idx}
              onClick={(e) => {
                e.stopPropagation();
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
        </div>,
        document.body
      )}
    </div>
  );
}