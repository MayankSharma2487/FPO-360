// frontend/src/components/ui/ActionsMenu.tsx
import React, { useState, useRef, useEffect } from 'react';
import { Icons } from './icons';
import './../../styles/components/actions-menu.css';

interface ActionItemProps {
  icon?: keyof typeof Icons;
  label: string;
  onClick?: () => void;
  variant?: 'default' | 'danger' | 'success' | 'warning';
  disabled?: boolean;
}

interface ActionsMenuProps {
  children: React.ReactNode;
}

export const ActionItem: React.FC<ActionItemProps> = ({
  icon,
  label,
  onClick,
  variant = 'default',
  disabled = false,
}) => {
  const IconComponent = icon ? Icons[icon] : null;

  return (
    <button
      className={`
        actions-menu__item 
        ${variant === 'danger' ? 'actions-menu__danger' : ''}
        ${variant === 'success' ? 'actions-menu__success' : ''}
        ${variant === 'warning' ? 'actions-menu__warning' : ''}
        ${disabled ? 'actions-menu__disabled' : ''}
      `.trim()}
      onClick={disabled ? undefined : onClick}
      disabled={disabled}
      type="button"
    >
      {IconComponent && <IconComponent className="actions-menu__icon" />}
      <span className="actions-menu__label">{label}</span>
    </button>
  );
};

export const ActionsMenu: React.FC<ActionsMenuProps> = ({ children }) => {
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);

  const toggleMenu = () => setIsOpen(!isOpen);
  const closeMenu = () => setIsOpen(false);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        closeMenu();
      }
    };

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        closeMenu();
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      document.addEventListener('keydown', handleEscape);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleEscape);
    };
  }, [isOpen]);

  return (
    <div className="actions-menu" ref={menuRef}>
      <button
        ref={triggerRef}
        className="actions-menu__trigger"
        onClick={toggleMenu}
        aria-expanded={isOpen}
        aria-haspopup="true"
        type="button"
      >
        <Icons.MoreVertical size={18} />
      </button>

      {isOpen && (
        <div 
          className="actions-menu__dropdown" 
          role="menu"
          aria-orientation="vertical"
        >
          {children}
        </div>
      )}
    </div>
  );
};