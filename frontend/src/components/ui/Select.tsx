// frontend/src/components/ui/Select.tsx
import React from 'react';
import './../../styles/components/forms.css';

export type SelectVariantSize = 'sm' | 'md' | 'lg';

interface SelectProps extends Omit<React.SelectHTMLAttributes<HTMLSelectElement>, 'size'> {
  selectSize?: SelectVariantSize;
  label?: string;
  error?: string;
  fullWidth?: boolean;
  options?: { value: string | number; label: string }[];
}

export const Select: React.FC<SelectProps> = ({
  selectSize = 'md',
  label,
  error,
  fullWidth = true,
  options = [],
  className = '',
  ...props
}) => {
  return (
    <div className={`form-group ${fullWidth ? 'w-full' : ''}`}>
      {label && <label className="form-label">{label}</label>}
      <select
        className={`form-select form-select--${selectSize} ${error ? 'form-select--error' : ''} ${className}`.trim()}
        {...props}
      >
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
      {error && <div className="form-error">{error}</div>}
    </div>
  );
};