'use client';

// ===========================================
// Vendly POS - Register Page (Disabled)
// Public registration is disabled. Users are created by admin only.
// ===========================================

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function RegisterPage() {
  const router = useRouter();

  useEffect(() => {
    // Redirect to login - public registration is disabled
    router.replace('/login');
  }, [router]);

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <p className="text-gray-600">Public registration is disabled.</p>
        <p className="text-gray-600">Please contact an administrator for access.</p>
      </div>
    </div>
  );
}
