// frontend/src/components/ui/FormField.tsx
import React from 'react';
import './../../styles/components/forms.css';

interface FormFieldProps {
  label?: string;
  required?: boolean;
  helperText?: string;
  error?: string;
  children: React.ReactNode;
  className?: string;
}

export const FormField: React.FC<FormFieldProps> = ({
  label,
  required = false,
  helperText,
  error,
  children,
  className = '',
}) => {
  return (
    <div className={`form-field ${className}`.trim()}>
      {label && (
        <label className="form-label">
          {label}
          {required && <span className="form-required">*</span>}
        </label>
      )}
      
      {children}
      
      {(helperText || error) && (
        <div className={`form-helper ${error ? 'form-helper--error' : ''}`}>
          {error || helperText}
        </div>
      )}
    </div>
  );
};