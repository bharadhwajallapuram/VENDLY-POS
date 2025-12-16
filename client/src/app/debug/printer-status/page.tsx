'use client';

import { useState, useEffect, useCallback } from 'react';

interface PrinterInfo {
  id: string;
  name: string;
  type: 'usb' | 'network' | 'bluetooth';
  status: 'online' | 'offline' | 'error' | 'out_of_paper' | 'unknown';
  ip_address?: string;
  port?: number;
  is_active: boolean;
  is_default: boolean;
}

export default function PrinterStatusDebug() {
  const [printers, setPrinters] = useState<PrinterInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [testingPrinterId, setTestingPrinterId] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<{ printerId: string; success: boolean; message: string } | null>(null);

  const fetchPrinters = useCallback(async () => {
    try {
      setRefreshing(true);
      const response = await fetch('/api/v1/peripherals/printers', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('vendly_token')}`,
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        setPrinters(data.printers || []);
      } else {
        console.error('Failed to fetch printers:', response.statusText);
      }
    } catch (error) {
      console.error('Error fetching printers:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchPrinters();
  }, [fetchPrinters]);

  const handleTestPrinter = async (printerId: string) => {
    try {
      setTestingPrinterId(printerId);
      const response = await fetch(`/api/v1/peripherals/printers/${printerId}/test`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('vendly_token')}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setTestResult({
          printerId,
          success: data.success,
          message: data.message || data.error || 'Test complete',
        });
        
        // Refresh status after test
        setTimeout(() => {
          fetchPrinters();
        }, 1000);
      }
    } catch (error) {
      setTestResult({
        printerId,
        success: false,
        message: `Error: ${error instanceof Error ? error.message : 'Unknown error'}`,
      });
    } finally {
      setTestingPrinterId(null);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online':
        return 'bg-green-50 border-green-300';
      case 'offline':
        return 'bg-red-50 border-red-300';
      case 'error':
        return 'bg-orange-50 border-orange-300';
      case 'out_of_paper':
        return 'bg-yellow-50 border-yellow-300';
      default:
        return 'bg-gray-50 border-gray-300';
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'online':
        return <span className="px-2 py-1 bg-green-200 text-green-800 rounded text-sm font-semibold">🟢 Online</span>;
      case 'offline':
        return <span className="px-2 py-1 bg-red-200 text-red-800 rounded text-sm font-semibold">🔴 Offline</span>;
      case 'error':
        return <span className="px-2 py-1 bg-orange-200 text-orange-800 rounded text-sm font-semibold">⚠️ Error</span>;
      case 'out_of_paper':
        return <span className="px-2 py-1 bg-yellow-200 text-yellow-800 rounded text-sm font-semibold">📄 No Paper</span>;
      default:
        return <span className="px-2 py-1 bg-gray-200 text-gray-800 rounded text-sm font-semibold">❓ Unknown</span>;
    }
  };

  if (loading) {
    return (
      <div className="p-8">
        <h1 className="text-2xl font-bold mb-4">Printer Status Monitor</h1>
        <p className="text-gray-600">Loading printer information...</p>
      </div>
    );
  }

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-6">Printer Status Monitor</h1>

      <div className="mb-8 p-4 bg-blue-50 border border-blue-200 rounded">
        <h2 className="text-lg font-semibold mb-4">Overview</h2>
        <div className="grid grid-cols-4 gap-4">
          <div>
            <p className="text-sm text-gray-600">Total Printers</p>
            <p className="text-2xl font-bold">{printers.length}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Online</p>
            <p className="text-2xl font-bold text-green-600">
              {printers.filter(p => p.status === 'online').length}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Offline</p>
            <p className="text-2xl font-bold text-red-600">
              {printers.filter(p => p.status === 'offline').length}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Default</p>
            <p className="text-2xl font-bold">
              {printers.find(p => p.is_default)?.name || 'None'}
            </p>
          </div>
        </div>
      </div>

      <div className="mb-6 flex gap-2">
        <button
          onClick={fetchPrinters}
          disabled={refreshing}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-gray-400"
        >
          {refreshing ? 'Refreshing...' : 'Refresh Status'}
        </button>
      </div>

      {printers.length === 0 ? (
        <div className="p-8 bg-gray-50 border border-gray-300 rounded text-center">
          <p className="text-gray-600 mb-2">No printers configured</p>
          <p className="text-sm text-gray-500">Configure a printer in Settings &gt; Peripherals</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {printers.map(printer => (
            <div key={printer.id} className={`p-4 border rounded ${getStatusColor(printer.status)}`}>
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="text-lg font-semibold">{printer.name}</h3>
                  <p className="text-sm text-gray-600">{printer.id}</p>
                </div>
                <div className="flex items-center gap-2">
                  {getStatusBadge(printer.status)}
                  {printer.is_default && (
                    <span className="px-2 py-1 bg-blue-200 text-blue-800 rounded text-sm font-semibold">⭐ Default</span>
                  )}
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4 mb-4">
                <div>
                  <span className="text-sm text-gray-600">Type:</span>
                  <p className="font-mono text-sm font-semibold">{printer.type.toUpperCase()}</p>
                </div>
                {printer.type === 'network' && (
                  <>
                    <div>
                      <span className="text-sm text-gray-600">IP Address:</span>
                      <p className="font-mono text-sm font-semibold">{printer.ip_address || 'N/A'}</p>
                    </div>
                    <div>
                      <span className="text-sm text-gray-600">Port:</span>
                      <p className="font-mono text-sm font-semibold">{printer.port || 9100}</p>
                    </div>
                  </>
                )}
                <div>
                  <span className="text-sm text-gray-600">Active:</span>
                  <p className="font-semibold">{printer.is_active ? '✓ Yes' : '✗ No'}</p>
                </div>
              </div>

              {printer.type === 'network' && printer.status === 'offline' && (
                <div className="mb-4 p-3 bg-red-100 border border-red-300 rounded text-sm">
                  <p className="font-semibold text-red-800 mb-2">Troubleshooting Tips:</p>
                  <ul className="list-disc list-inside text-red-700 space-y-1">
                    <li>Check if printer is powered on and connected to the network</li>
                    <li>Verify correct IP address: <span className="font-mono">{printer.ip_address}</span></li>
                    <li>Ensure printer is listening on port <span className="font-mono">{printer.port || 9100}</span></li>
                    <li>Check network connectivity from the POS terminal to the printer</li>
                    <li>Try power cycling the printer</li>
                    <li>Verify firewall rules allow connections to the printer port</li>
                  </ul>
                </div>
              )}

              <div className="flex gap-2">
                <button
                  onClick={() => handleTestPrinter(printer.id)}
                  disabled={testingPrinterId === printer.id}
                  className="px-4 py-2 bg-purple-500 text-white rounded hover:bg-purple-600 disabled:bg-gray-400"
                >
                  {testingPrinterId === printer.id ? 'Testing...' : '🖨️ Test Print'}
                </button>
              </div>

              {testResult?.printerId === printer.id && (
                <div className={`mt-4 p-3 rounded ${testResult.success ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                  <p className="font-semibold">{testResult.success ? '✓ Success' : '✗ Failed'}:</p>
                  <p className="text-sm mt-1">{testResult.message}</p>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      <div className="mt-8 p-4 bg-gray-50 border border-gray-300 rounded">
        <h3 className="font-semibold mb-3">How to Resolve Printer Offline Issues</h3>
        <div className="space-y-3 text-sm">
          <div>
            <p className="font-semibold text-gray-800">For Network Printers:</p>
            <ol className="list-decimal list-inside text-gray-700 space-y-1 ml-2">
              <li>Check printer power and network connection</li>
              <li>Verify printer IP address and port in the printer menu</li>
              <li>Test connectivity from terminal: <span className="font-mono bg-white px-1">ping {printers[0]?.ip_address || '[IP]'}</span></li>
              <li>Restart the printer and the POS terminal</li>
              <li>Check for firmware updates for the printer</li>
            </ol>
          </div>
          <div>
            <p className="font-semibold text-gray-800">For USB Printers:</p>
            <ol className="list-decimal list-inside text-gray-700 space-y-1 ml-2">
              <li>Check physical USB connection</li>
              <li>Try a different USB port</li>
              <li>Install/reinstall printer drivers</li>
              <li>Restart the POS application</li>
            </ol>
          </div>
        </div>
      </div>
    </div>
  );
}
