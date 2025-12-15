// ===========================================
// Responsive Modal Component
// ===========================================

import React, { useEffect, useRef, useCallback } from 'react';

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
  const modalRef = useRef<HTMLDivElement>(null);
  const closeButtonRef = useRef<HTMLButtonElement>(null);
  const previousActiveElement = useRef<HTMLElement | null>(null);

  // Handle keyboard events (ESC to close)
  useEffect(() => {
    if (!isOpen) return;

    // Store the element that had focus before modal opened
    previousActiveElement.current = document.activeElement as HTMLElement;

    // Focus close button when modal opens
    setTimeout(() => {
      closeButtonRef.current?.focus();
    }, 0);

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        onClose();
      }
    };

    window.addEventListener('keydown', handleKeyDown);

    // Trap focus within modal
    const handleTabKey = (e: KeyboardEvent) => {
      if (!modalRef.current) return;

      const focusableElements = modalRef.current.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );
      const firstElement = focusableElements[0] as HTMLElement;
      const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement;

      if (e.key === 'Tab') {
        if (e.shiftKey) {
          // Shift + Tab
          if (document.activeElement === firstElement) {
            e.preventDefault();
            lastElement.focus();
          }
        } else {
          // Tab
          if (document.activeElement === lastElement) {
            e.preventDefault();
            firstElement.focus();
          }
        }
      }
    };

    window.addEventListener('keydown', handleTabKey);

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('keydown', handleTabKey);
    };
  }, [isOpen, onClose]);

  // Restore focus when modal closes
  const handleClose = useCallback(() => {
    onClose();
    // Restore focus to the element that triggered the modal
    setTimeout(() => {
      previousActiveElement.current?.focus();
    }, 0);
  }, [onClose]);

  if (!isOpen) return null;

  const sizeClasses = {
    sm: 'max-w-sm',
    md: 'max-w-md md:max-w-lg',
    lg: 'max-w-lg md:max-w-2xl',
  };

  return (
    <div
      className="modal"
      onClick={handleClose}
      role="presentation"
      aria-modal="true"
    >
      <div
        ref={modalRef}
        className={`modal-content ${sizeClasses[size]}`}
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-labelledby="modal-title"
      >
        <div className="flex justify-between items-center mb-4 md:mb-6 pb-3 md:pb-4 border-b">
          <h2 id="modal-title" className="text-lg md:text-xl font-bold pr-4">{title}</h2>
          <button
            ref={closeButtonRef}
            onClick={handleClose}
            className="flex-shrink-0 text-gray-500 hover:text-gray-700 focus:outline-none focus:ring-2 focus:ring-primary-500 rounded text-2xl md:text-xl leading-none p-1"
            aria-label="Close dialog"
          >
            ✕
          </button>
        </div>
        <div className="max-h-[calc(90vh-120px)] overflow-y-auto">{children}</div>
      </div>
    </div>
  );
}
