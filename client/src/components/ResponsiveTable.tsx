// ===========================================
// Responsive Table Component
// ===========================================

import React from 'react';

interface ResponsiveTableProps {
  headers: string[];
  children: React.ReactNode;
}

export default function ResponsiveTable({ headers, children }: ResponsiveTableProps) {
  return (
    <div className="table-responsive">
      <table className="w-full text-xs md:text-sm">
        <thead>
          <tr className="border-b bg-gray-50">
            {headers.map((header, idx) => (
              <th key={idx} className="text-left py-3 px-2 md:px-3 font-medium text-gray-700">
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>{children}</tbody>
      </table>
    </div>
  );
}
