'use client';

// ===========================================
// Vendly POS - Protected Route Wrapper
// ===========================================

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth, UserRole } from '@/store/auth';
import { me } from '@/lib/api';

interface ProtectedRouteProps {
  children: React.ReactNode;
  roles?: UserRole[];
}

export default function ProtectedRoute({ children, roles }: ProtectedRouteProps) {
  const router = useRouter();
  const { token, user, setUser, clearAuth, hasRole } = useAuth();
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthorized, setIsAuthorized] = useState(false);

  useEffect(() => {
    async function checkAuth() {
      // No token means not logged in - redirect to login
      if (!token) {
        router.push('/login');
        return;
      }

      // If we have a token but no user, fetch user info
      if (token && !user) {
        try {
          const userInfo = await me();
          setUser({
            id: userInfo.id,
            email: userInfo.email,
            role: userInfo.role as UserRole,
            full_name: userInfo.full_name,
          });
        } catch (error) {
          // Token is invalid or expired
          console.error('Failed to fetch user info:', error);
          clearAuth();
          router.push('/login');
          return;
        }
      }

      // Check role authorization
      if (roles && roles.length > 0) {
        const authorized = hasRole(roles);
        if (!authorized) {
          router.push('/pos'); // Redirect to POS if not authorized
          return;
        }
      }

      setIsAuthorized(true);
      setIsLoading(false);
    }

    checkAuth();
  }, [token, user, roles, router, hasRole, setUser, clearAuth]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
      </div>
    );
  }

  if (!isAuthorized) {
    return null;
  }

  return <>{children}</>;
}
