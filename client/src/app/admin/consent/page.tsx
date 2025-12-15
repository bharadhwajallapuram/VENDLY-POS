'use client';

import React, { useEffect, useState } from 'react';
import { Legal } from '@/lib/api';
import { toastManager } from '@/components/Toast';

interface ComplianceReport {
  doc_type: string;
  total_acceptances: number;
  by_users: number;
  by_customers: number;
  first_acceptance?: string;
  last_acceptance?: string;
  acceptance_rate?: number;
}

interface ConsentStats {
  totalDocuments: number;
  totalAcceptances: number;
  averageAcceptanceRate: number;
  reports: ComplianceReport[];
}

export default function ConsentDashboardPage() {
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState<ConsentStats | null>(null);
  const [dateRange, setDateRange] = useState({
    startDate: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    endDate: new Date().toISOString().split('T')[0],
  });

  const docTypes = [
    { code: 'privacy_policy', label: 'Privacy Policy', color: 'blue' },
    { code: 'terms_of_service', label: 'Terms of Service', color: 'green' },
    { code: 'return_policy', label: 'Return Policy', color: 'purple' },
    { code: 'warranty_policy', label: 'Warranty Policy', color: 'yellow' },
    { code: 'cookie_policy', label: 'Cookie Policy', color: 'red' },
  ];

  useEffect(() => {
    loadReports();
  }, [dateRange]);

  async function loadReports() {
    setLoading(true);
    try {
      const reports: ComplianceReport[] = [];
      
      for (const docType of docTypes) {
        try {
          const report = await Legal.getAcceptanceReport(
            docType.code,
            dateRange.startDate
          );
          reports.push({
            ...report,
            doc_type: docType.label,
          });
        } catch (err) {
          console.error(`Failed to load report for ${docType.code}:`, err);
        }
      }

      // Calculate statistics
      const totalAcceptances = reports.reduce((sum, r) => sum + r.total_acceptances, 0);
      const totalDocuments = reports.length;
      const averageAcceptanceRate = totalDocuments > 0
        ? reports.reduce((sum, r) => sum + ((r.total_acceptances || 0) / Math.max(r.by_users + r.by_customers, 1)), 0) / totalDocuments
        : 0;

      setStats({
        totalDocuments,
        totalAcceptances,
        averageAcceptanceRate,
        reports,
      });
    } catch (err) {
      console.error('Failed to load compliance reports:', err);
      toastManager.error('Failed to load compliance reports');
    } finally {
      setLoading(false);
    }
  }

  const getColorClass = (color: string) => {
    const colors: { [key: string]: string } = {
      blue: 'bg-blue-100 text-blue-800',
      green: 'bg-green-100 text-green-800',
      purple: 'bg-purple-100 text-purple-800',
      yellow: 'bg-yellow-100 text-yellow-800',
      red: 'bg-red-100 text-red-800',
    };
    return colors[color] || 'bg-gray-100 text-gray-800';
  };

  const getChartColor = (color: string) => {
    const colors: { [key: string]: string } = {
      blue: 'bg-blue-500',
      green: 'bg-green-500',
      purple: 'bg-purple-500',
      yellow: 'bg-yellow-500',
      red: 'bg-red-500',
    };
    return colors[color] || 'bg-gray-500';
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">Consent & Compliance Dashboard</h1>

      {/* Date Range Filter */}
      <div className="mb-8 p-4 bg-blue-50 rounded-lg border border-blue-200">
        <h2 className="text-lg font-semibold mb-3">Date Range</h2>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-2">Start Date</label>
            <input
              type="date"
              value={dateRange.startDate}
              onChange={(e) => setDateRange({ ...dateRange, startDate: e.target.value })}
              className="w-full p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">End Date</label>
            <input
              type="date"
              value={dateRange.endDate}
              onChange={(e) => setDateRange({ ...dateRange, endDate: e.target.value })}
              className="w-full p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
      </div>

      {/* Key Metrics */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <div className="p-6 bg-white rounded-lg border border-gray-200 shadow-sm">
            <p className="text-gray-600 text-sm mb-1">Total Documents</p>
            <p className="text-3xl font-bold text-blue-600">{stats.totalDocuments}</p>
          </div>
          <div className="p-6 bg-white rounded-lg border border-gray-200 shadow-sm">
            <p className="text-gray-600 text-sm mb-1">Total Acceptances</p>
            <p className="text-3xl font-bold text-green-600">{stats.totalAcceptances.toLocaleString()}</p>
          </div>
          <div className="p-6 bg-white rounded-lg border border-gray-200 shadow-sm">
            <p className="text-gray-600 text-sm mb-1">Avg Acceptance Rate</p>
            <p className="text-3xl font-bold text-purple-600">
              {(stats.averageAcceptanceRate * 100).toFixed(1)}%
            </p>
          </div>
        </div>
      )}

      {/* Detailed Reports */}
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-6">
        <h2 className="text-xl font-semibold mb-4">Acceptance by Document Type</h2>

        {loading ? (
          <div className="text-center py-8 text-gray-500">Loading reports...</div>
        ) : !stats || stats.reports.length === 0 ? (
          <div className="text-center py-8 text-gray-500">No data available for the selected date range</div>
        ) : (
          <div className="space-y-6">
            {stats.reports.map((report, idx) => {
              const docType = docTypes.find(dt => dt.label === report.doc_type);
              const totalRecipients = report.by_users + report.by_customers;
              const acceptanceRate = totalRecipients > 0 ? (report.total_acceptances / totalRecipients) * 100 : 0;

              return (
                <div key={report.doc_type} className="border-t pt-4 last:border-t-0">
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <h3 className="font-semibold text-lg">{report.doc_type}</h3>
                      <p className="text-sm text-gray-600">
                        {new Date(report.last_acceptance || '').toLocaleDateString()} - Last acceptance
                      </p>
                    </div>
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${getColorClass(docType?.color || 'gray')}`}>
                      {acceptanceRate.toFixed(1)}% Acceptance
                    </span>
                  </div>

                  <div className="grid grid-cols-4 gap-4 mb-4">
                    <div>
                      <p className="text-sm text-gray-600">Total Acceptances</p>
                      <p className="text-2xl font-bold">{report.total_acceptances}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">By Users</p>
                      <p className="text-2xl font-bold text-blue-600">{report.by_users}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">By Customers</p>
                      <p className="text-2xl font-bold text-green-600">{report.by_customers}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Coverage</p>
                      <p className="text-2xl font-bold text-purple-600">{totalRecipients}</p>
                    </div>
                  </div>

                  {/* Progress Bar */}
                  <div className="mb-4">
                    <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
                      <div
                        className={`${getChartColor(docType?.color || 'gray')} h-full transition-all`}
                        style={{ width: `${Math.min(acceptanceRate, 100)}%` }}
                      />
                    </div>
                  </div>

                  {/* Details */}
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div className="bg-gray-50 p-3 rounded">
                      <p className="text-gray-600">First Acceptance</p>
                      <p className="font-medium">
                        {report.first_acceptance 
                          ? new Date(report.first_acceptance).toLocaleDateString()
                          : 'N/A'
                        }
                      </p>
                    </div>
                    <div className="bg-gray-50 p-3 rounded">
                      <p className="text-gray-600">Last Acceptance</p>
                      <p className="font-medium">
                        {report.last_acceptance
                          ? new Date(report.last_acceptance).toLocaleDateString()
                          : 'N/A'
                        }
                      </p>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Compliance Summary */}
      {stats && (
        <div className="mt-8 p-6 bg-blue-50 rounded-lg border border-blue-200">
          <h2 className="text-lg font-semibold mb-3">Compliance Summary</h2>
          <ul className="space-y-2 text-sm">
            <li className="flex items-center">
              <span className="inline-block w-2 h-2 bg-green-600 rounded-full mr-2"></span>
              {stats.totalDocuments} legal documents configured for acceptance
            </li>
            <li className="flex items-center">
              <span className="inline-block w-2 h-2 bg-blue-600 rounded-full mr-2"></span>
              {stats.totalAcceptances.toLocaleString()} total acceptances recorded in date range
            </li>
            <li className="flex items-center">
              <span className="inline-block w-2 h-2 bg-purple-600 rounded-full mr-2"></span>
              {(stats.averageAcceptanceRate * 100).toFixed(1)}% average acceptance rate across all documents
            </li>
            <li className="flex items-center">
              <span className="inline-block w-2 h-2 bg-yellow-600 rounded-full mr-2"></span>
              All acceptances logged with IP address and user agent for audit trail compliance
            </li>
          </ul>
        </div>
      )}
    </div>
  );
}
