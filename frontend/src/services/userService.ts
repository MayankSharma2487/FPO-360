import api from './api';

export const userService = {
  getUsers: () => api.get('/users/'),

  createUser: (data: any) => api.post('/users/', data),

  updateUser: (id: number, data: any) => api.put(`/users/${id}`, data),

  toggleStatus: (id: number, isActive: boolean) => 
    api.patch(`/users/${id}/status?is_active=${isActive}`),

  resetPassword: (id: number) => api.post(`/users/${id}/reset-password`),

  assignRole: (id: number, roleId: number) => 
    api.put(`/users/${id}/role`, { role_id: roleId }),
};