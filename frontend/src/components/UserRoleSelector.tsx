import React from 'react';

const ROLE_DESCRIPTIONS: Record<string, string> = {
  'FPO Admin':  'Full FPO access',
  'Manager':    'Field operations',
  'Accountant': 'Finance & reports',
  'Viewer':     'Read-only access',
};

interface UserRoleSelectorProps {
  value: string;
  onChange: (role: string) => void;
  isSuperAdmin: boolean;
}

export const UserRoleSelector: React.FC<UserRoleSelectorProps> = ({ value, onChange, isSuperAdmin }) => {
  const roles = isSuperAdmin
    ? ['FPO Admin', 'Manager', 'Accountant', 'Viewer']
    : ['Manager', 'Accountant', 'Viewer'];

  return (
    <div className="form-group">
      <label className="form-label">Role <span style={{ color: 'var(--red)' }}>*</span></label>
      <select className="form-select" value={value} onChange={(e) => onChange(e.target.value)}>
        {roles.map(role => (
          <option key={role} value={role}>{role}</option>
        ))}
      </select>
      {ROLE_DESCRIPTIONS[value] && (
        <span className="form-hint">{ROLE_DESCRIPTIONS[value]}</span>
      )}
    </div>
  );
};