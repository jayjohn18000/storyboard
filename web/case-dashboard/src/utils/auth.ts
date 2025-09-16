// Simple session management utilities
// TODO: Replace with proper JWT token management when backend is ready

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

const SESSION_KEY = 'legal-sim-session';

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

// Mock login function for development
export const mockLogin = async (email: string, password: string): Promise<Session> => {
  // Simulate API call delay
  await new Promise(resolve => setTimeout(resolve, 1000));
  
  // Mock user data
  const mockUser: User = {
    id: 'user-001',
    email,
    name: email.split('@')[0],
    role: 'attorney'
  };
  
  const session: Session = {
    user: mockUser,
    token: 'mock-jwt-token',
    expiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000) // 24 hours
  };
  
  setSession(session);
  return session;
};

export const mockLogout = async (): Promise<void> => {
  // Simulate API call delay
  await new Promise(resolve => setTimeout(resolve, 500));
  clearSession();
};
