// frontend/src/components/ui/EmptyState.tsx
import React from 'react';
import { Icons, type IconName } from './icons';
import './../../styles/components/empty-state.css';

interface EmptyStateProps {
  icon?: IconName;
  title: string;
  description?: string;
  primaryAction?: React.ReactNode;
  secondaryAction?: React.ReactNode;
  illustration?: React.ReactNode;
  variant?: 'default' | 'search' | 'table' | 'permission' | 'error';
  children?: React.ReactNode;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon = 'Package',
  title,
  description,
  primaryAction,
  secondaryAction,
  illustration,
  variant = 'default',
  children,
}) => {
  const IconComponent = Icons[icon as keyof typeof Icons];

  return (
    <div className={`empty-state empty-state--${variant}`}>
      {illustration ? (
        <div className="empty-illustration">{illustration}</div>
      ) : (
        IconComponent && <IconComponent className="empty-icon" />
      )}
      
      <div className="empty-title">{title}</div>
      
      {description && <div className="empty-description">{description}</div>}
      
      {children && <div className="empty-children">{children}</div>}

      {(primaryAction || secondaryAction) && (
        <div className="empty-actions">
          {primaryAction}
          {secondaryAction}
        </div>
      )}
    </div>
  );
};