/**
 * Authentication Types
 */

export interface User {
  id: string
  email: string
  username: string
  firstName?: string
  lastName?: string
  avatarUrl?: string
  createdAt: string
}

export interface LoginCredentials {
  email: string
  password: string
}

export interface RegisterCredentials {
  email: string
  username: string
  password: string
  firstName?: string
  lastName?: string
}

export interface AuthResponse {
  user: User
  token: string
}
