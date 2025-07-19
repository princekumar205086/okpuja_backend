// Frontend Token Management Solution
// Place this in your React/Next.js application

// 1. Token Management Utility
class TokenManager {
    constructor() {
        this.accessToken = null;
        this.refreshToken = null;
        this.isRefreshing = false;
        this.failedQueue = [];
        this.baseURL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    }

    // Get tokens from storage
    getTokens() {
        if (typeof window !== 'undefined') {
            this.accessToken = localStorage.getItem('access_token');
            this.refreshToken = localStorage.getItem('refresh_token');
        }
        return {
            access: this.accessToken,
            refresh: this.refreshToken
        };
    }

    // Save tokens to storage
    setTokens(accessToken, refreshToken) {
        this.accessToken = accessToken;
        this.refreshToken = refreshToken;
        
        if (typeof window !== 'undefined') {
            if (accessToken) {
                localStorage.setItem('access_token', accessToken);
            }
            if (refreshToken) {
                localStorage.setItem('refresh_token', refreshToken);
            }
        }
    }

    // Clear tokens
    clearTokens() {
        this.accessToken = null;
        this.refreshToken = null;
        
        if (typeof window !== 'undefined') {
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
        }
    }

    // Check if token is expired
    isTokenExpired(token) {
        if (!token) return true;
        
        try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            const currentTime = Date.now() / 1000;
            return payload.exp < currentTime;
        } catch (error) {
            return true;
        }
    }

    // Refresh access token
    async refreshAccessToken() {
        const { refresh } = this.getTokens();
        
        if (!refresh) {
            throw new Error('No refresh token available');
        }

        if (this.isTokenExpired(refresh)) {
            this.clearTokens();
            throw new Error('Refresh token expired');
        }

        try {
            const response = await fetch(`${this.baseURL}/api/auth/refresh/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ refresh })
            });

            if (!response.ok) {
                throw new Error('Token refresh failed');
            }

            const data = await response.json();
            
            // Handle token rotation
            this.setTokens(
                data.access, 
                data.refresh || refresh // Use new refresh token if provided
            );

            return data.access;
        } catch (error) {
            this.clearTokens();
            throw error;
        }
    }

    // Process failed queue after successful refresh
    processQueue(error, token = null) {
        this.failedQueue.forEach(({ resolve, reject }) => {
            if (error) {
                reject(error);
            } else {
                resolve(token);
            }
        });
        
        this.failedQueue = [];
    }
}

// 2. Axios Interceptor Setup
import axios from 'axios';

const tokenManager = new TokenManager();

// Create axios instance
const apiClient = axios.create({
    baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
});

// Request interceptor to add token
apiClient.interceptors.request.use(
    (config) => {
        const { access } = tokenManager.getTokens();
        if (access && !tokenManager.isTokenExpired(access)) {
            config.headers.Authorization = `Bearer ${access}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

// Response interceptor to handle token refresh
apiClient.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;

        if (error.response?.status === 401 && !originalRequest._retry) {
            if (tokenManager.isRefreshing) {
                // If already refreshing, wait for it to complete
                return new Promise((resolve, reject) => {
                    tokenManager.failedQueue.push({ resolve, reject });
                }).then(token => {
                    originalRequest.headers.Authorization = `Bearer ${token}`;
                    return apiClient(originalRequest);
                });
            }

            originalRequest._retry = true;
            tokenManager.isRefreshing = true;

            try {
                const newAccessToken = await tokenManager.refreshAccessToken();
                tokenManager.processQueue(null, newAccessToken);
                
                originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
                return apiClient(originalRequest);
                
            } catch (refreshError) {
                tokenManager.processQueue(refreshError, null);
                
                // Redirect to login page
                if (typeof window !== 'undefined') {
                    window.location.href = '/login';
                }
                
                return Promise.reject(refreshError);
            } finally {
                tokenManager.isRefreshing = false;
            }
        }

        return Promise.reject(error);
    }
);

// 3. React Hook for Authentication
import { createContext, useContext, useEffect, useState } from 'react';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        checkAuth();
    }, []);

    const checkAuth = async () => {
        try {
            const { access } = tokenManager.getTokens();
            
            if (access && !tokenManager.isTokenExpired(access)) {
                const response = await apiClient.get('/api/auth/profile/');
                setUser(response.data);
            }
        } catch (error) {
            console.error('Auth check failed:', error);
            tokenManager.clearTokens();
        } finally {
            setLoading(false);
        }
    };

    const login = async (email, password) => {
        try {
            const response = await apiClient.post('/api/auth/login/', {
                email,
                password
            });

            const { access, refresh, ...userData } = response.data;
            
            tokenManager.setTokens(access, refresh);
            setUser(userData);
            
            return { success: true };
        } catch (error) {
            return { 
                success: false, 
                error: error.response?.data?.detail || 'Login failed' 
            };
        }
    };

    const logout = async () => {
        try {
            const { refresh } = tokenManager.getTokens();
            if (refresh) {
                await apiClient.post('/api/auth/logout/', { refresh });
            }
        } catch (error) {
            console.error('Logout error:', error);
        } finally {
            tokenManager.clearTokens();
            setUser(null);
        }
    };

    const value = {
        user,
        login,
        logout,
        loading,
        isAuthenticated: !!user
    };

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within AuthProvider');
    }
    return context;
};

// 4. Protected Route Component
import { useRouter } from 'next/router';
import { useEffect } from 'react';

export const ProtectedRoute = ({ children }) => {
    const { isAuthenticated, loading } = useAuth();
    const router = useRouter();

    useEffect(() => {
        if (!loading && !isAuthenticated) {
            router.push('/login');
        }
    }, [isAuthenticated, loading, router]);

    if (loading) {
        return <div>Loading...</div>;
    }

    if (!isAuthenticated) {
        return null;
    }

    return children;
};

// 5. Usage Example
export default apiClient;

// Usage in components:
/*
import { useAuth } from './path/to/auth';
import apiClient from './path/to/api';

function MyComponent() {
    const { user, logout } = useAuth();
    
    const fetchData = async () => {
        try {
            const response = await apiClient.get('/api/some-endpoint/');
            // Handle response
        } catch (error) {
            // Error handling
        }
    };
    
    return (
        <div>
            <h1>Welcome {user?.email}</h1>
            <button onClick={logout}>Logout</button>
        </div>
    );
}
*/
