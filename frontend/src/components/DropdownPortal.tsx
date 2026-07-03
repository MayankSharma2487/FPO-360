import { useEffect, useRef, useState, useCallback, ReactNode } from 'react';
import { createPortal } from 'react-dom';

interface DropdownPortalProps {
  triggerRef: React.RefObject<HTMLElement>;
  open: boolean;
  onClose: () => void;
  children: ReactNode;
}

export function DropdownPortal({ triggerRef, open, onClose, children }: DropdownPortalProps) {
  const [coords, setCoords] = useState({ top: 0, left: 0 });
  const dropRef = useRef<HTMLDivElement>(null);

  const reposition = useCallback(() => {
    if (!triggerRef.current) return;
    const rect = triggerRef.current.getBoundingClientRect();
    const dropW = 188;
    const left = rect.right - dropW < 8 ? 8 : rect.right - dropW;
    setCoords({ top: rect.bottom + 6, left });
  }, [triggerRef]);

  useEffect(() => {
    if (!open) return;
    reposition();
    window.addEventListener('scroll', onClose, true);
    window.addEventListener('resize', reposition);
    return () => {
      window.removeEventListener('scroll', onClose, true);
      window.removeEventListener('resize', reposition);
    };
  }, [open, reposition, onClose]);

  useEffect(() => {
    if (!open) return;
    const handler = (e: MouseEvent) => {
      if (
        dropRef.current && !dropRef.current.contains(e.target as Node) &&
        triggerRef.current && !triggerRef.current.contains(e.target as Node)
      ) onClose();
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [open, onClose, triggerRef]);

  if (!open) return null;

  return createPortal(
    <div
      ref={dropRef}
      className="actions-menu-dropdown"
      style={{ position: 'fixed', top: coords.top, left: coords.left, zIndex: 9999 }}
    >
      {children}
    </div>,
    document.body
  );
}