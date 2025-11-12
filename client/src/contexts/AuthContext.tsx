import { createContext, useContext, useState, useEffect, ReactNode } from 'react'

export type User = { email: string; role: 'cashier'|'manager'|'admin'; full_name?: string }

type AuthContextType = {
  user: User | null
  setUser: (user: User | null) => void
  token: string | null
  setToken: (token: string) => void
  clearAuth: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

const TOKEN_KEY = 'vendly_token'
const USER_KEY = 'vendly_user'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUserState] = useState<User | null>(null)
  const [token, setTokenState] = useState<string | null>(null)

  // Initialize from localStorage on mount
  useEffect(() => {
    const savedToken = localStorage.getItem(TOKEN_KEY)
    const savedUser = localStorage.getItem(USER_KEY)
    
    if (savedToken) {
      setTokenState(savedToken)
    }
    
    if (savedUser) {
      try {
        setUserState(JSON.parse(savedUser) as User)
      } catch {
        localStorage.removeItem(USER_KEY)
      }
    }
  }, [])

  const setUser = (newUser: User | null) => {
    setUserState(newUser)
    if (newUser) {
      localStorage.setItem(USER_KEY, JSON.stringify(newUser))
    } else {
      localStorage.removeItem(USER_KEY)
    }
  }

  const setToken = (newToken: string) => {
    setTokenState(newToken)
    localStorage.setItem(TOKEN_KEY, newToken)
  }

  const clearAuth = () => {
    setUserState(null)
    setTokenState(null)
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
  }

  return (
    <AuthContext.Provider value={{ user, setUser, token, setToken, clearAuth }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

// Legacy functions for backward compatibility
export function getUser(): User | null {
  const raw = localStorage.getItem(USER_KEY)
  return raw ? JSON.parse(raw) as User : null
}

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function setUserLegacy(user: User) {
  localStorage.setItem(USER_KEY, JSON.stringify(user))
}

export function setTokenLegacy(token: string) {
  localStorage.setItem(TOKEN_KEY, token)
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
}