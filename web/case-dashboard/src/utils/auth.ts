// Authentication utilities with real API integration

export interface User {
  id: string;
  email: string;
  name: string;
  role: 'admin' | 'attorney' | 'viewer';
}

export interface Session {
  user: User;
  token: string;
  expiresAt: Date;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  user: User;
  token: string;
  expiresAt: string;
}

const SESSION_KEY = 'legal-sim-session';
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export const getSession = (): Session | null => {
  try {
    const sessionData = localStorage.getItem(SESSION_KEY);
    if (!sessionData) return null;
    
    const session: Session = JSON.parse(sessionData);
    
    // Check if session is expired
    if (new Date() > new Date(session.expiresAt)) {
      localStorage.removeItem(SESSION_KEY);
      return null;
    }
    
    return session;
  } catch (error) {
    console.error('Error parsing session:', error);
    localStorage.removeItem(SESSION_KEY);
    return null;
  }
};

export const setSession = (session: Session): void => {
  localStorage.setItem(SESSION_KEY, JSON.stringify(session));
};

export const clearSession = (): void => {
  localStorage.removeItem(SESSION_KEY);
};

export const isAuthenticated = (): boolean => {
  return getSession() !== null;
};

export const getCurrentUser = (): User | null => {
  const session = getSession();
  return session?.user || null;
};

export const getAuthToken = (): string | null => {
  const session = getSession();
  return session?.token || null;
};

// Real authentication functions
export const login = async (email: string, password: string): Promise<Session> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Login failed: ${response.statusText}`);
    }

    const data: LoginResponse = await response.json();
    
    const session: Session = {
      user: data.user,
      token: data.token,
      expiresAt: new Date(data.expiresAt),
    };
    
    setSession(session);
    return session;
  } catch (error) {
    console.error('Login error:', error);
    throw error;
  }
};

export const logout = async (): Promise<void> => {
  try {
    const token = getAuthToken();
    if (token) {
      await fetch(`${API_BASE_URL}/api/v1/auth/logout`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });
    }
  } catch (error) {
    console.error('Logout error:', error);
  } finally {
    clearSession();
  }
};

export const refreshToken = async (): Promise<Session | null> => {
  try {
    const token = getAuthToken();
    if (!token) return null;

    const response = await fetch(`${API_BASE_URL}/api/v1/auth/refresh`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      clearSession();
      return null;
    }

    const data: LoginResponse = await response.json();
    
    const session: Session = {
      user: data.user,
      token: data.token,
      expiresAt: new Date(data.expiresAt),
    };
    
    setSession(session);
    return session;
  } catch (error) {
    console.error('Token refresh error:', error);
    clearSession();
    return null;
  }
};

// API request helper with automatic token handling
export const apiRequest = async (
  url: string,
  options: RequestInit = {}
): Promise<Response> => {
  const token = getAuthToken();
  
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${url}`, {
    ...options,
    headers,
  });

  // Handle token expiration
  if (response.status === 401) {
    const refreshedSession = await refreshToken();
    if (!refreshedSession) {
      clearSession();
      window.location.href = '/login';
      throw new Error('Session expired');
    }
    
    // Retry the request with the new token
    const newHeaders = {
      ...headers,
      'Authorization': `Bearer ${refreshedSession.token}`,
    };
    
    return fetch(`${API_BASE_URL}${url}`, {
      ...options,
      headers: newHeaders,
    });
  }

  return response;
};
