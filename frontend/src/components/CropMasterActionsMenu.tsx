import { ActionsMenu } from './ActionsMenu';

interface Props {
  recordId: number;
  isActive: boolean;
  onEdit: () => void;
  onToggleStatus: (id: number, current: boolean) => void;
}

export function CropMasterActionsMenu({ recordId, isActive, onEdit, onToggleStatus }: Props) {
  return (
    <ActionsMenu
      actions={[
        {
          label: 'Edit',
          icon: (
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
              <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
            </svg>
          ),
          onClick: onEdit,
        },
        {
          label: isActive ? 'Disable' : 'Enable',
          variant: isActive ? 'danger' : 'success',
          icon: (
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              {isActive ? (
                <>
                  <circle cx="12" cy="12" r="10"/>
                  <line x1="8" y1="12" x2="16" y2="12"/>
                </>
              ) : (
                <>
                  <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                  <polyline points="22 4 12 14.01 9 11.01"/>
                </>
              )}
            </svg>
          ),
          onClick: () => onToggleStatus(recordId, isActive),
        },
      ]}
    />
  );
}