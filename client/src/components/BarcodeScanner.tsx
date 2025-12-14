import { useEffect, useRef, useCallback } from 'react';

interface BarcodeScannerProps {
  onBarcodeScanned: (barcode: string) => void | Promise<void>;
  minLength?: number;
  debounceMs?: number;
  enabled?: boolean;
}

export function useBarcodeScanner(
  onBarcodeScanned: (barcode: string) => void | Promise<void>,
  minLength: number = 6,
  debounceMs: number = 150,
  enabled: boolean = true,
  hookName: string = 'Unknown'
) {
  const barcodeBufferRef = useRef('');
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (!enabled) {
      return;
    }

    const handleGlobalKeyDown = (e: KeyboardEvent) => {
      // Ignore if user is typing in text input field or number input field
      const target = e.target as HTMLElement;
      const inputElement = target as HTMLInputElement;
      if (
        target.tagName === 'TEXTAREA' || 
        (target.tagName === 'INPUT' && (inputElement.type === 'text' || inputElement.type === 'number' || inputElement.type === 'email' || inputElement.type === 'password'))
      ) {
        return;
      }

      // Build barcode buffer from numeric characters
      if (/^[0-9]$/.test(e.key)) {
        barcodeBufferRef.current += e.key;

        // Clear existing timeout
        if (timeoutRef.current) {
          clearTimeout(timeoutRef.current);
        }

        // Prevent default number input
        e.preventDefault();

        // Set new timeout - if no more input in debounceMs, process as barcode
        timeoutRef.current = setTimeout(() => {
          const barcode = barcodeBufferRef.current;
          barcodeBufferRef.current = '';

          if (barcode.length >= minLength) {
            onBarcodeScanned(barcode);
          }
        }, debounceMs);
      }
      // Hardware scanners typically send Enter key after the barcode
      else if (e.key === 'Enter' && barcodeBufferRef.current.length >= minLength) {
        const barcode = barcodeBufferRef.current;
        barcodeBufferRef.current = '';
        onBarcodeScanned(barcode);
        e.preventDefault();
      }
    };

    window.addEventListener('keydown', handleGlobalKeyDown);
    return () => {
      window.removeEventListener('keydown', handleGlobalKeyDown);
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [enabled, onBarcodeScanned, minLength, debounceMs, hookName]);

  return {
    barcodeBuffer: barcodeBufferRef.current,
  };
}

/**
 * Barcode Scanner Component
 * 
 * Usage example:
 * ```tsx
 * const [scanFeedback, setScanFeedback] = useState<string | null>(null);
 * 
 * const handleBarcode = (barcode: string) => {
 *   // Do something with barcode
 *   setScanFeedback(`Scanned: ${barcode}`);
 * };
 * 
 * <BarcodeScanner 
 *   onBarcodeScanned={handleBarcode}
 *   feedback={scanFeedback}
 *   onFeedbackDismiss={() => setScanFeedback(null)}
 * />
 * ```
 */
export function BarcodeScanner({
  onBarcodeScanned,
  feedback,
  onFeedbackDismiss,
  minLength = 6,
  debounceMs = 150,
  enabled = true,
}: BarcodeScannerProps & {
  feedback?: string | null;
  onFeedbackDismiss?: () => void;
}) {
  const feedbackTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  useBarcodeScanner(
    async (barcode) => {
      await onBarcodeScanned(barcode);

      // Auto-dismiss feedback after 2 seconds
      if (onFeedbackDismiss) {
        if (feedbackTimeoutRef.current) {
          clearTimeout(feedbackTimeoutRef.current);
        }
        feedbackTimeoutRef.current = setTimeout(() => {
          onFeedbackDismiss();
        }, 2000);
      }
    },
    minLength,
    debounceMs,
    enabled,
    'BarcodeScanner-Component'
  );

  useEffect(() => {
    return () => {
      if (feedbackTimeoutRef.current) {
        clearTimeout(feedbackTimeoutRef.current);
      }
    };
  }, []);

  if (!feedback) return null;

  return (
    <div className={`px-4 py-2 text-center font-semibold text-white ${
      feedback.startsWith('✓') ? 'bg-green-500' : 'bg-red-500'
    }`}>
      {feedback}
    </div>
  );
}
