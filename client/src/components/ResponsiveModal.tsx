// ===========================================
// Responsive Modal Component
// ===========================================

import React from 'react';

interface ResponsiveModalProps {
  isOpen: boolean;
  title: string;
  onClose: () => void;
  children: React.ReactNode;
  size?: 'sm' | 'md' | 'lg';
}

export default function ResponsiveModal({
  isOpen,
  title,
  onClose,
  children,
  size = 'md',
}: ResponsiveModalProps) {
  if (!isOpen) return null;

  const sizeClasses = {
    sm: 'max-w-sm',
    md: 'max-w-md md:max-w-lg',
    lg: 'max-w-lg md:max-w-2xl',
  };

  return (
    <div className="modal" onClick={onClose}>
      <div
        className={`modal-content ${sizeClasses[size]}`}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex justify-between items-center mb-4 md:mb-6 pb-3 md:pb-4 border-b">
          <h2 className="text-lg md:text-xl font-bold pr-4">{title}</h2>
          <button
            onClick={onClose}
            className="flex-shrink-0 text-gray-500 hover:text-gray-700 text-2xl md:text-xl leading-none"
            aria-label="Close"
          >
            ✕
          </button>
        </div>
        <div className="max-h-[calc(90vh-120px)] overflow-y-auto">{children}</div>
      </div>
    </div>
  );
}
