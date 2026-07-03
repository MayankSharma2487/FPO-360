// frontend/src/components/ui/Toast.tsx
import React, { useEffect } from 'react';
import { Icons } from './icons';
import './../../styles/components/toast.css';

interface ToastProps {
  id: string;
  variant?: 'success' | 'warning' | 'danger' | 'info';
  title?: string;
  message: string;
  duration?: number;
  onClose: (id: string) => void;
  icon?: keyof typeof Icons;
}

export const Toast: React.FC<ToastProps> = ({
  id,
  variant = 'info',
  title,
  message,
  duration = 4000,
  onClose,
  icon,
}) => {
  const getIcon = () => {
    if (icon) return Icons[icon];
    switch (variant) {
      case 'success': return Icons.CheckCircle;
      case 'warning': return Icons.AlertTriangle;
      case 'danger': return Icons.XCircle;
      default: return Icons.Info;
    }
  };

  const IconComponent = getIcon();

  useEffect(() => {
    if (duration <= 0) return;

    const timer = setTimeout(() => {
      onClose(id);
    }, duration);

    return () => clearTimeout(timer);
  }, [duration, id, onClose]);

  return (
    <div className={`toast toast--${variant}`}>
      <div className="toast-icon">
        <IconComponent />
      </div>
      
      <div className="toast-content">
        {title && <div className="toast-title">{title}</div>}
        <div className="toast-message">{message}</div>
      </div>

      <button className="toast-close" onClick={() => onClose(id)}>
        <Icons.Close size={16} />
      </button>

      <div className="toast-progress" style={{ animationDuration: `${duration}ms` }} />
    </div>
  );
};