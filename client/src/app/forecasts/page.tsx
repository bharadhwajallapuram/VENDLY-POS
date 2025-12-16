'use client';

// ===========================================
// Vendly POS - Forecasts Page
// ===========================================

import ProtectedRoute from '@/components/ProtectedRoute';
import DemandForecastDashboard from '@/components/DemandForecastDashboard';

function ForecastsContent() {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">AI Demand Forecasting</h1>
      </div>
      <DemandForecastDashboard />
    </div>
  );
}

export default function ForecastsPage() {
  return (
    <ProtectedRoute roles={['manager', 'admin']}>
      <ForecastsContent />
    </ProtectedRoute>
  );
}
