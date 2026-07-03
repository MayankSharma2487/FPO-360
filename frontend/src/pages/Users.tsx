// frontend/src/pages/Users.tsx
import { useEffect, useState } from 'react';
import { RoleGuard } from '../components/RoleGuard';
import { UserForm } from '../components/UserForm';
import { userService } from '../services/userService';
import { useAuth } from '../context/AuthContext';
import { UserActionsMenu } from '../components/UserActionsMenu';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { SearchInput } from '../components/ui/SearchInput';
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell, TableToolbar, TableLoading } from '../components/ui/Table';
import { Modal } from '../components/ui/Modal';
import { SkeletonTable } from '../components/ui/Skeleton';
import { EmptyState } from '../components/ui/EmptyState';
import { Icons } from '../components/ui/icons';
import { Alert } from '../components/ui/Alert';

interface Role {
  id: number;
  name: string;
}

interface User {
  id: number;
  full_name: string;
  email: string;
  organization_id: number;
  is_active: boolean;
  role: Role | null;
}

const ROLE_COLORS: Record<string, string> = {
  'Super Admin': '#ef4444',
  'FPO Admin': '#3b82f6',
  'Manager': '#8b5cf6',
  'Accountant': '#22c55e',
  'Viewer': '#64748b',
};

export default function Users() {
  const { user } = useAuth();
  const isSuperAdmin = user?.role?.name === 'Super Admin';
  
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editingUser, setEditingUser] = useState<Partial<User> | null>(null);

  const loadUsers = async () => {
    setLoading(true);
    try {
      const res = await userService.getUsers();
      setUsers(res.data);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadUsers();
  }, []);

  const filteredUsers = users.filter((u) =>
    u.full_name.toLowerCase().includes(search.toLowerCase()) ||
    u.email.toLowerCase().includes(search.toLowerCase()) ||
    (u.role?.name || '').toLowerCase().includes(search.toLowerCase())
  );

  const handleCreate = () => {
    setEditingUser(null);
    setShowForm(true);
  };

  const handleEdit = (userData: User) => {
    setEditingUser(userData);
    setShowForm(true);
  };

  const handleResetPassword = async (id: number) => {
    if (!confirm('Reset password for this user?')) return;
    try {
      await userService.resetPassword(id);
      alert('Password reset successful.');
      loadUsers();
    } catch (err) {
      alert('Failed to reset password');
    }
  };

  const handleToggleStatus = async (id: number, currentActive: boolean) => {
    const action = currentActive ? 'disable' : 'enable';
    if (!confirm(`Are you sure you want to ${action} this user?`)) return;
    try {
      await userService.toggleStatus(id, !currentActive);
      loadUsers();
    } catch (err) {
      alert('Failed to update user status');
    }
  };

  const activeCount = users.filter((u) => u.is_active).length;

  return (
    <RoleGuard allowedRoles={['Super Admin', 'FPO Admin']}>
      <div className="page-wrapper">
        <div className="page-header">
          <div>
            <h2 className="page-title">Users</h2>
            <p className="page-subtitle">Manage team accounts and permissions</p>
          </div>
          <div className="flex items-center gap-4">
            <div className="page-count-badge">
              {activeCount} active / {users.length} total
            </div>
            <Button onClick={handleCreate} leftIcon="UserPlus">
              New User
            </Button>
          </div>
        </div>

        <TableToolbar>
          <SearchInput
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by name, email or role..."
          />
        </TableToolbar>

        {error && (
          <Alert
            variant="danger"
            title="Error"
            description={error}
            dismissible
            onDismiss={() => setError(null)}
          />
        )}

        {loading ? (
          <div className="table-wrapper">
              <Table>
                  <TableLoading
                      rows={6}
                      columns={7}
                  />
              </Table>
          </div>
        ) : (
          <div className="table-wrapper table-scroll">
            <Table>
              <TableHeader>
                <TableHead>#</TableHead>
                <TableHead>Name</TableHead>
                <TableHead>Email</TableHead>
                <TableHead>Organization</TableHead>
                <TableHead>Role</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableHeader>
              <TableBody>
                {filteredUsers.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7}>
                      <EmptyState
                        icon="Users"
                        title="No users found"
                        description={search ? "No matching users." : "No team members yet."}
                        primaryAction={
                          <Button onClick={handleCreate} leftIcon="UserPlus">
                            Add First User
                          </Button>
                        }
                      />
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredUsers.map((u, idx) => {
                    const initials = u.full_name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
                    const roleColor = ROLE_COLORS[u.role?.name || 'Viewer'] || '#64748b';

                    return (
                      <TableRow key={u.id}>
                        <TableCell className="row-num">{idx + 1}</TableCell>
                        <TableCell>
                          <div className="user-cell">
                            <div className="mini-avatar" style={{ background: `${roleColor}22`, color: roleColor }}>
                              {initials}
                            </div>
                            <span className="primary-cell font-medium">{u.full_name}</span>
                          </div>
                        </TableCell>
                        <TableCell><span className="mono-tag">{u.email}</span></TableCell>
                        <TableCell className="font-mono text-sm text-gray-400">{u.organization_id}</TableCell>
                        <TableCell>
                          {u.role ? (
                            <Badge variant="neutral">{u.role.name}</Badge>
                          ) : '—'}
                        </TableCell>
                        <TableCell>
                          <Badge 
                            variant={u.is_active ? 'success' : 'neutral'}
                          >
                            {u.is_active ? 'Active' : 'Disabled'}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right">
                          <UserActionsMenu
                            user={u}
                            isActive={u.is_active}
                            onEdit={() => handleEdit(u)}
                            onResetPassword={handleResetPassword}
                            onToggleStatus={handleToggleStatus}
                          />
                        </TableCell>
                      </TableRow>
                    );
                  })
                )}
              </TableBody>
            </Table>
          </div>
        )}

        <Modal
          isOpen={showForm}
          onClose={() => setShowForm(false)}
          title={editingUser?.id ? 'Edit User' : 'Create New User'}
          subtitle={editingUser?.id ? 'Update account details.' : 'Add a new team member.'}
        >
          <UserForm
            initialData={editingUser || undefined}
            onSuccess={() => {
              setShowForm(false);
              loadUsers();
            }}
            onCancel={() => setShowForm(false)}
            isSuperAdmin={isSuperAdmin}
          />
        </Modal>
      </div>
    </RoleGuard>
  );
}