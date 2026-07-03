// frontend/src/components/ui/Textarea.tsx
import React, { useState, useRef, useEffect } from 'react';
import './../../styles/components/forms.css';

interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  helperText?: string;
  error?: string;
  showCounter?: boolean;
  maxLength?: number;
  size?: 'sm' | 'md' | 'lg';
  fullWidth?: boolean;
}

export const Textarea: React.FC<TextareaProps> = ({
  label,
  helperText,
  error,
  showCounter = false,
  maxLength,
  size = 'md',
  fullWidth = false,
  className = '',
  value = '',
  ...props
}) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [charCount, setCharCount] = useState(0);

  useEffect(() => {
    const ta = textareaRef.current;
    if (ta) {
      ta.style.height = 'auto';
      ta.style.height = `${Math.min(ta.scrollHeight, 200)}px`;
    }
    setCharCount(typeof value === 'string' ? value.length : 0);
  }, [value]);

  return (
    <div className={`form-field ${fullWidth ? 'form-field--full' : ''} ${className}`.trim()}>
      {label && (
        <label className="form-label">
          {label}
          {props.required && <span className="form-required">*</span>}
        </label>
      )}

      <div className={`input-wrapper input-wrapper--${size} ${error ? 'input--error' : ''}`}>
        <textarea
          ref={textareaRef}
          className="input textarea"
          value={value}
          maxLength={maxLength}
          {...props}
        />
      </div>

      <div className="form-footer">
        {(helperText || error) && (
          <div className={`form-helper ${error ? 'form-helper--error' : ''}`}>
            {error || helperText}
          </div>
        )}
        {showCounter && maxLength && (
          <div className="char-count">
            {charCount} / {maxLength}
          </div>
        )}
      </div>
    </div>
  );
};