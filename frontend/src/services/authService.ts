import api from './api'

interface TokenResponse {
  access_token: string
  token_type: string
}

interface UserResponse {
  id: number
  full_name: string
  email: string
  organization_id: number
  is_active: boolean
  role: { id: number; name: string } | null
}

export const authService = {
  async login(email: string, password: string): Promise<TokenResponse> {
    const response = await api.post<TokenResponse>('/auth/login', { email, password })
    return response.data
  },

  async getMe(): Promise<UserResponse> {
    const response = await api.get<UserResponse>('/auth/me')
    return response.data
  },
}
