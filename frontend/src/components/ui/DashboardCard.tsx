// frontend/src/components/ui/DashboardCard.tsx
import React from 'react';
import { Icons, type IconName } from './icons';
import { Button } from './Button';
import { Badge } from './Badge';
import { Skeleton } from './Skeleton';
import './../../styles/components/dashboard-card.css';

interface TrendProps {
  value: number;
  label?: string;
  direction?: 'up' | 'down' | 'neutral';
}

const Trend: React.FC<TrendProps> = ({ value, label, direction = 'up' }) => {
  const isPositive = direction === 'up';
  const IconComponent = isPositive ? Icons.Growth : Icons.Decline;

  return (
    <div className={`trend trend--${direction}`}>
      <IconComponent />
      <span>{Math.abs(value)}%</span>
      {label && <span className="trend-label">{label}</span>}
    </div>
  );
};

interface DashboardCardProps {
  title: string;
  value?: string | number;
  subtitle?: string;
  icon?: IconName;
  trend?: { value: number; label?: string; direction?: 'up' | 'down' | 'neutral' };
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'info' | 'neutral';
  loading?: boolean;
  onClick?: () => void;
  footer?: React.ReactNode;
  actions?: React.ReactNode;
  badge?: React.ReactNode;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  children?: React.ReactNode;
}

export const DashboardCard: React.FC<DashboardCardProps> = ({
  title,
  value,
  subtitle,
  icon,
  trend,
  variant = 'default',
  loading = false,
  onClick,
  footer,
  actions,
  badge,
  size = 'md',
  className = '',
  children,
}) => {
  const IconComponent = icon ? Icons[icon] : null;

  if (loading) {
    return (
      <div className={`dashboard-card dashboard-card--${size} ${className}`.trim()}>
        <div className="dashboard-card-header">
          <Skeleton width={32} height={32} rounded />
          <Skeleton width="60%" height={18} />
        </div>
        <Skeleton width="75%" height={48} />
        <Skeleton width="45%" height={14} />
      </div>
    );
  }

  return (
    <div 
      className={`
        dashboard-card 
        dashboard-card--${size} 
        dashboard-card--${variant}
        ${onClick ? 'dashboard-card--clickable' : ''}
        ${className}
      `.trim()}
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
    >
      <div className="dashboard-card-header">
        {IconComponent && (
          <div className="dashboard-card-icon">
            <IconComponent />
          </div>
        )}
        
        <div className="dashboard-card-title-group">
          <div className="dashboard-card-title">{title}</div>
          {badge && <div className="dashboard-card-badge">{badge}</div>}
        </div>

        {actions && <div className="dashboard-card-actions">{actions}</div>}
      </div>

      <div className="dashboard-card-value">
        {value}
      </div>

      <div className="dashboard-card-subtitle-row">
        {subtitle && <div className="dashboard-card-subtitle">{subtitle}</div>}
        {trend && <Trend {...trend} />}
      </div>

      {children && <div className="dashboard-card-content">{children}</div>}

      {footer && <div className="dashboard-card-footer">{footer}</div>}
    </div>
  );
};