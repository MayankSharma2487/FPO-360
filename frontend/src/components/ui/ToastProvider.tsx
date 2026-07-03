// frontend/src/components/ui/ToastProvider.tsx
import React, { createContext, useContext, useState, useCallback } from 'react';
import { Toast } from './Toast';

interface ToastItem {
  id: string;
  variant: 'success' | 'warning' | 'danger' | 'info';
  title?: string;
  message: string;
  duration?: number;
}

interface ToastContextType {
  toast: {
    success: (message: string, options?: Partial<ToastItem>) => void;
    error: (message: string, options?: Partial<ToastItem>) => void;
    warning: (message: string, options?: Partial<ToastItem>) => void;
    info: (message: string, options?: Partial<ToastItem>) => void;
  };
}

const ToastContext = createContext<ToastContextType | null>(null);

export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) throw new Error('useToast must be used within ToastProvider');
  return context.toast;
};

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const addToast = useCallback((variant: ToastItem['variant'], message: string, options: Partial<ToastItem> = {}) => {
    const id = `toast-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    
    setToasts((prev) => [
      ...prev,
      { id, variant, message, ...options }
    ]);
  }, []);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const toast = {
    success: (message: string, options?: Partial<ToastItem>) => addToast('success', message, options),
    error: (message: string, options?: Partial<ToastItem>) => addToast('danger', message, options),
    warning: (message: string, options?: Partial<ToastItem>) => addToast('warning', message, options),
    info: (message: string, options?: Partial<ToastItem>) => addToast('info', message, options),
  };

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      
      <div className="toast-container">
        {toasts.map((t) => (
          <Toast
            key={t.id}
            {...t}
            onClose={removeToast}
          />
        ))}
      </div>
    </ToastContext.Provider>
  );
};