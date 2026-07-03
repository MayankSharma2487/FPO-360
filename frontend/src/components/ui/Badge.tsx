// frontend/src/components/ui/Badge.tsx
import React from 'react';
import { Icons, type IconName } from './icons';
import './../../styles/components/badge.css';

export type BadgeVariant = 'primary' | 'success' | 'warning' | 'danger' | 'info' | 'neutral';
export type BadgeSize = 'sm' | 'md' | 'lg';

interface BadgeProps {
  variant?: BadgeVariant;
  size?: BadgeSize;
  icon?: IconName;
  children: React.ReactNode;
  className?: string;
  rounded?: boolean;
  outline?: boolean;
}

export const Badge: React.FC<BadgeProps> = ({
  variant = 'neutral',
  size = 'md',
  icon,
  children,
  className = '',
  rounded = false,
  outline = false,
}) => {
  const IconComponent = icon ? Icons[icon] : null;

  return (
    <span
      className={`
        badge 
        badge--${variant} 
        badge--${size} 
        ${rounded ? 'badge--rounded' : ''} 
        ${outline ? 'badge--outline' : ''} 
        ${className}
      `.trim()}
    >
      {IconComponent && <IconComponent className="badge-icon" />}
      <span className="badge-content">{children}</span>
    </span>
  );
};