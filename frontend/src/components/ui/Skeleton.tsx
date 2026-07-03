// frontend/src/components/ui/Skeleton.tsx
import React from 'react';
import './../../styles/components/skeleton.css';

interface SkeletonProps {
  width?: string | number;
  height?: string | number;
  className?: string;
  rounded?: boolean;
  animated?: boolean;
}

export const Skeleton: React.FC<SkeletonProps> = ({
  width,
  height,
  className = '',
  rounded = true,
  animated = true,
}) => (
  <div 
    className={`skeleton ${animated ? 'skeleton--animated' : ''} ${rounded ? 'skeleton--rounded' : ''} ${className}`.trim()}
    style={{
      width: typeof width === 'number' ? `${width}px` : width,
      height: typeof height === 'number' ? `${height}px` : height,
    }}
  />
);

export const SkeletonText: React.FC<{ lines?: number; className?: string }> = ({ 
  lines = 3, 
  className = '' 
}) => (
  <div className={`skeleton-text ${className}`.trim()}>
    {Array.from({ length: lines }).map((_, i) => (
      <Skeleton key={i} height={14} width={`${80 - i * 12}%`} />
    ))}
  </div>
);

export const SkeletonAvatar: React.FC<{ size?: number; className?: string }> = ({ 
  size = 40, 
  className = '' 
}) => (
  <Skeleton 
    width={size} 
    height={size} 
    rounded 
    className={`skeleton-avatar ${className}`.trim()} 
  />
);

export const SkeletonButton: React.FC<{ width?: number; className?: string }> = ({ 
  width = 100, 
  className = '' 
}) => (
  <Skeleton 
    width={width} 
    height={40} 
    rounded 
    className={`skeleton-button ${className}`.trim()} 
  />
);

export const SkeletonCard: React.FC = () => (
  <div className="skeleton-card">
    <Skeleton height={140} />
    <div className="skeleton-card-body">
      <SkeletonText lines={2} />
      <SkeletonButton width={120} />
    </div>
  </div>
);

export const SkeletonTable: React.FC<{ rows?: number; columns?: number }> = ({ 
  rows = 5, 
  columns = 6 
}) => (
  <div className="skeleton-table">
    {Array.from({ length: rows }).map((_, i) => (
      <div key={i} className="skeleton-table-row">
        {Array.from({ length: columns }).map((_, j) => (
          <Skeleton key={j} height={18} />
        ))}
      </div>
    ))}
  </div>
);

export const SkeletonForm: React.FC = () => (
  <div className="skeleton-form">
    <Skeleton height={18} width="40%" />
    <Skeleton height={42} />
    <Skeleton height={18} width="60%" />
    <Skeleton height={42} />
    <Skeleton height={18} width="35%" />
    <Skeleton height={100} />
  </div>
);