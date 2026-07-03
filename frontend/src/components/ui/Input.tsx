// frontend/src/components/ui/Input.tsx
import React from 'react';
import './../../styles/components/forms.css';

export type InputVariantSize = 'sm' | 'md' | 'lg';

interface InputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'size'> {
  inputSize?: InputVariantSize;
  label?: string;
  error?: string;
  fullWidth?: boolean;
}

export const Input: React.FC<InputProps> = ({
  inputSize = 'md',
  label,
  error,
  fullWidth = true,
  className = '',
  ...props
}) => {
  return (
    <div className={`form-group ${fullWidth ? 'w-full' : ''}`}>
      {label && <label className="form-label">{label}</label>}
      <input
        className={`form-input form-input--${inputSize} ${error ? 'form-input--error' : ''} ${className}`.trim()}
        {...props}
      />
      {error && <div className="form-error">{error}</div>}
    </div>
  );
};