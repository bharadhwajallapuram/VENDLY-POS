'use client';

// ===========================================
// Vendly POS - Protected Route Wrapper
// ===========================================

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth, UserRole } from '@/store/auth';

interface ProtectedRouteProps {
  children: React.ReactNode;
  roles?: UserRole[];
}

export default function ProtectedRoute({ children, roles }: ProtectedRouteProps) {
  const router = useRouter();
  const { token, user, hasRole } = useAuth();
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthorized, setIsAuthorized] = useState(false);

  useEffect(() => {
    // No token means not logged in - redirect to login
    if (!token) {
      router.push('/login');
      return;
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
  }, [token, user, roles, router, hasRole]);

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
