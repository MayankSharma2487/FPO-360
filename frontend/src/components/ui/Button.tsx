// frontend/src/components/ui/Button.tsx
import React from 'react';
import { Icons, type IconName } from './icons';
import './../../styles/components/button.css';

export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger' | 'success';
export type ButtonSize = 'sm' | 'md' | 'lg';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  leftIcon?: IconName;
  rightIcon?: IconName;
  loading?: boolean;
  fullWidth?: boolean;
  children: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  leftIcon,
  rightIcon,
  loading = false,
  fullWidth = false,
  children,
  className = '',
  disabled,
  ...props
}) => {
  const isDisabled = disabled || loading;

  const LeftIcon = leftIcon ? Icons[leftIcon] : null;
  const RightIcon = rightIcon ? Icons[rightIcon] : null;
  const LoaderIcon = Icons.Loader;

  return (
    <button
      className={`
        btn 
        btn--${variant} 
        btn--${size} 
        ${loading ? 'btn--loading' : ''} 
        ${fullWidth ? 'btn--full' : ''} 
        ${className}
      `.trim()}
      disabled={isDisabled}
      {...props}
    >
      {loading ? (
        <LoaderIcon className="btn-spinner" />
      ) : (
        <>
          {LeftIcon && <LeftIcon className="btn-icon-left" />}
          <span className="btn-content">{children}</span>
          {RightIcon && <RightIcon className="btn-icon-right" />}
        </>
      )}
    </button>
  );
};