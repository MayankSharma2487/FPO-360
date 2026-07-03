// frontend/src/components/ui/Alert.tsx
import React from 'react';
import { Icons, type IconName } from './icons';
import './../../styles/components/alert.css';

interface AlertProps {
  variant?: 'success' | 'warning' | 'danger' | 'info';
  title?: string;
  description?: string;
  icon?: IconName;
  dismissible?: boolean;
  onDismiss?: () => void;
  children?: React.ReactNode;
  className?: string;
}

export const Alert: React.FC<AlertProps> = ({
  variant = 'info',
  title,
  description,
  icon,
  dismissible = false,
  onDismiss,
  children,
  className = '',
}) => {
  const getIcon = () => {
    if (icon) return Icons[icon];
    switch (variant) {
      case 'success': return Icons.Success;
      case 'warning': return Icons.Warning;
      case 'danger': return Icons.Error;
      default: return Icons.Info;
    }
  };

  const IconComponent = getIcon();

  return (
    <div className={`alert alert--${variant} ${className}`.trim()}>
      <div className="alert-icon">
        <IconComponent />
      </div>
      
      <div className="alert-content">
        {title && <div className="alert-title">{title}</div>}
        {description && <div className="alert-description">{description}</div>}
        {children && <div className="alert-children">{children}</div>}
      </div>

      {dismissible && onDismiss && (
        <button className="alert-close" onClick={onDismiss} aria-label="Dismiss">
          <Icons.Close />
        </button>
      )}
    </div>
  );
};