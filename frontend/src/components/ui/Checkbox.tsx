// frontend/src/components/ui/Checkbox.tsx
import React from 'react';
import { Icons } from './icons';
import './../../styles/components/forms.css';

interface CheckboxProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'type'> {
  label?: string;
  description?: string;
}

export const Checkbox: React.FC<CheckboxProps> = ({
  label,
  description,
  className = '',
  ...props
}) => {
  const CheckIcon = Icons.Check;

  return (
    <label className={`checkbox-wrapper ${className}`.trim()}>
      <div className="checkbox-container">
        <input
          type="checkbox"
          className="checkbox-input"
          {...props}
        />
        <div className="checkbox-custom">
          <CheckIcon className="checkbox-check" />
        </div>
      </div>
      
      <div className="checkbox-label-group">
        {label && <div className="checkbox-label">{label}</div>}
        {description && <div className="checkbox-description">{description}</div>}
      </div>
    </label>
  );
};