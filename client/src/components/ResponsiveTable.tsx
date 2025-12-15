// ===========================================
// Responsive Table Component
// ===========================================

import React from 'react';

interface ResponsiveTableProps {
  headers: string[];
  children: React.ReactNode;
  caption?: string;
}

export default function ResponsiveTable({ headers, children, caption }: ResponsiveTableProps) {
  return (
    <div className="table-responsive">
      <table className="w-full text-xs md:text-sm" role="table">
        {caption && <caption className="sr-only">{caption}</caption>}
        <thead>
          <tr className="border-b bg-gray-50">
            {headers.map((header, idx) => (
              <th
                key={idx}
                className="text-left py-3 px-2 md:px-3 font-medium text-gray-700"
                scope="col"
                role="columnheader"
              >
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody role="rowgroup">{children}</tbody>
      </table>
    </div>
  );
}
