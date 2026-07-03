import { useRef, useState } from 'react';
import { DropdownPortal } from './DropdownPortal';

interface VillageActionsMenuProps {
  villageId: number;
  isActive: boolean;
  onEdit: (id: number) => void;
  onToggleStatus: (id: number, isActive: boolean) => void;
}

export function VillageActionsMenu({
  villageId,
  isActive,
  onEdit,
  onToggleStatus,
}: VillageActionsMenuProps) {
  const [open, setOpen] = useState(false);
  const buttonRef = useRef<HTMLButtonElement>(null);

  return (
    <>
      <button
        ref={buttonRef}
        onClick={() => setOpen(!open)}
        className="actions-menu-trigger"
      >
        ⋮
      </button>

      <DropdownPortal
        triggerRef={buttonRef}
        open={open}
        onClose={() => setOpen(false)}
      >
        <button
          className="actions-menu-item"
          onClick={() => {
            onEdit(villageId);
            setOpen(false);
          }}
        >
          ✏️ Edit Village
        </button>

        <div className="actions-menu-divider" />

        <button
          className={`actions-menu-item ${
            isActive
              ? 'actions-menu-item--danger'
              : 'actions-menu-item--success'
          }`}
          onClick={() => {
            onToggleStatus(villageId, isActive);
            setOpen(false);
          }}
        >
          {isActive ? '🚫 Disable Village' : '✅ Enable Village'}
        </button>
      </DropdownPortal>
    </>
  );
}