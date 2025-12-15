/**
 * Accessibility Implementation Examples
 * Practical code examples for common a11y patterns in the Vendly POS application
 */

// ===== EXAMPLE 1: Creating an Accessible Modal =====

import ResponsiveModal from '@/components/ResponsiveModal';
import { useState, useCallback, useEffect, useRef } from 'react';

export function ProductEditModal() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      {/* Trigger Button - Accessible */}
      <button
        onClick={() => setIsOpen(true)}
        className="btn btn-primary"
        aria-label="Edit product details"
      >
        Edit Product
      </button>

      {/* Modal - Automatically handles keyboard, focus, and ARIA */}
      <ResponsiveModal
        isOpen={isOpen}
        title="Edit Product"
        onClose={() => setIsOpen(false)}
      >
        <form onSubmit={(e) => {
          e.preventDefault();
          setIsOpen(false);
        }}>
          {/* Form fields */}
          <div className="space-y-4">
            <div>
              <label htmlFor="product-name" className="block font-medium mb-1">
                Product Name <span aria-label="required">*</span>
              </label>
              <input
                id="product-name"
                type="text"
                className="input w-full"
                required
                aria-required="true"
              />
            </div>

            <div>
              <label htmlFor="product-price" className="block font-medium mb-1">
                Price
              </label>
              <input
                id="product-price"
                type="number"
                step="0.01"
                className="input w-full"
                aria-describedby="price-help"
              />
              <small id="price-help" className="text-gray-500">
                Enter price in dollars
              </small>
            </div>
          </div>

          {/* Buttons */}
          <div className="flex gap-2 justify-end mt-6">
            <button
              type="button"
              onClick={() => setIsOpen(false)}
              className="btn btn-secondary"
              aria-label="Cancel editing"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-success"
              aria-label="Save product changes"
            >
              Save Changes
            </button>
          </div>
        </form>
      </ResponsiveModal>
    </>
  );
}

// ===== EXAMPLE 2: Accessible Data Table =====

import ResponsiveTable from '@/components/ResponsiveTable';

export function UsersList() {
  const users = [
    { id: 1, name: 'John Doe', email: 'john@example.com', role: 'manager' },
    { id: 2, name: 'Jane Smith', email: 'jane@example.com', role: 'cashier' },
  ];

  const handleEdit = (userId: number) => {
    console.log('Edit user:', userId);
    // Handle edit action
  };

  return (
    <section aria-label="User management">
      <h2 className="text-xl font-bold mb-4">Users</h2>

      <ResponsiveTable
        headers={['Name', 'Email', 'Role', 'Actions']}
        caption="List of all system users with their roles"
      >
        {users.map((user) => (
          <tr key={user.id}>
            <td className="py-3 px-2 md:px-4">{user.name}</td>
            <td className="py-3 px-2 md:px-4">{user.email}</td>
            <td className="py-3 px-2 md:px-4">
              <span 
                className="px-2 py-1 rounded-full text-xs bg-gray-100 text-gray-800"
                aria-label={`Role: ${user.role}`}
              >
                {user.role}
              </span>
            </td>
            <td className="py-3 px-2 md:px-4">
              <button
                onClick={() => handleEdit(user.id)}
                className="btn btn-sm btn-info"
                aria-label={`Edit ${user.name}'s profile`}
              >
                Edit
              </button>
            </td>
          </tr>
        ))}
      </ResponsiveTable>
    </section>
  );
}

// ===== EXAMPLE 3: Accessible Form with Validation =====

import { ErrorMessage, SuccessMessage } from '@/components/ErrorHandling';

export function ProductForm() {
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    sku: '',
    price: 0,
  });

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    // Validation
    if (!formData.name.trim()) {
      setError('Product name is required');
      return;
    }

    if (formData.price <= 0) {
      setError('Price must be greater than 0');
      return;
    }

    try {
      // Submit form
      // await saveProduct(formData);
      setSuccess('Product saved successfully');
      setFormData({ name: '', sku: '', price: 0 });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save product');
    }
  }, [formData]);

  return (
    <form onSubmit={handleSubmit} className="max-w-md space-y-4">
      <h2 className="text-lg font-bold">Add Product</h2>

      {/* Error and Success Messages - Screen Reader Announced */}
      {error && <ErrorMessage error={error} onDismiss={() => setError(null)} />}
      {success && <SuccessMessage message={success} onDismiss={() => setSuccess(null)} />}

      {/* Product Name Input */}
      <div>
        <label htmlFor="product-name" className="block font-medium mb-1">
          Product Name <span className="text-red-500" aria-label="required">*</span>
        </label>
        <input
          id="product-name"
          type="text"
          value={formData.name}
          onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          className="input w-full"
          required
          aria-required="true"
          aria-invalid={!!error && !formData.name}
          placeholder="Enter product name"
        />
      </div>

      {/* SKU Input */}
      <div>
        <label htmlFor="product-sku" className="block font-medium mb-1">
          SKU
        </label>
        <input
          id="product-sku"
          type="text"
          value={formData.sku}
          onChange={(e) => setFormData({ ...formData, sku: e.target.value })}
          className="input w-full"
          aria-describedby="sku-help"
          placeholder="e.g., SKU-001"
        />
        <small id="sku-help" className="text-gray-500">
          Optional: Stock Keeping Unit identifier
        </small>
      </div>

      {/* Price Input */}
      <div>
        <label htmlFor="product-price" className="block font-medium mb-1">
          Price <span className="text-red-500" aria-label="required">*</span>
        </label>
        <input
          id="product-price"
          type="number"
          step="0.01"
          min="0.01"
          value={formData.price}
          onChange={(e) => setFormData({ ...formData, price: parseFloat(e.target.value) })}
          className="input w-full"
          required
          aria-required="true"
          aria-invalid={!!error && formData.price <= 0}
          aria-describedby="price-help"
          placeholder="0.00"
        />
        <small id="price-help" className="text-gray-500">
          Price in dollars and cents
        </small>
      </div>

      {/* Form Buttons */}
      <div className="flex gap-2 justify-end pt-4">
        <button
          type="reset"
          className="btn btn-secondary"
          aria-label="Clear form"
        >
          Clear
        </button>
        <button
          type="submit"
          className="btn btn-success"
          aria-label="Save new product"
          disabled={!formData.name || formData.price <= 0}
        >
          Save Product
        </button>
      </div>
    </form>
  );
}

// ===== EXAMPLE 4: Using Accessibility Utilities =====

import { 
  announceToScreenReader, 
  prefersReducedMotion,
  onEscapeKey,
} from '@/lib/a11y';

export function CartNotification() {
  useEffect(() => {
    // Announce to screen reader immediately
    announceToScreenReader(
      'Item added to cart',
      'polite'
    );

    // Auto-clear notification after 3 seconds
    const timeout = setTimeout(() => {
      announceToScreenReader('Notification cleared', 'polite');
    }, 3000);

    return () => clearTimeout(timeout);
  }, []);

  return (
    <div
      className={prefersReducedMotion() ? 'opacity-100' : 'animate-fade-in'}
      role="status"
      aria-live="polite"
      aria-atomic="true"
    >
      ✓ Item added to cart
    </div>
  );
}

// ===== EXAMPLE 5: Keyboard Shortcut Handler =====

export function SearchWithKeyboardShortcut() {
  const [isOpen, setIsOpen] = useState(false);
  const searchInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ctrl+K or Cmd+K to open search
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        setIsOpen(true);
        setTimeout(() => searchInputRef.current?.focus(), 0);
        announceToScreenReader('Search opened. Type to search.', 'assertive');
      }

      // ESC to close
      if (e.key === 'Escape') {
        setIsOpen(false);
        announceToScreenReader('Search closed', 'polite');
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  return (
    <>
      <button
        onClick={() => setIsOpen(true)}
        className="btn btn-secondary"
        aria-label="Open search (Press Ctrl+K)"
      >
        Search (Ctrl+K)
      </button>

      {isOpen && (
        <div 
          role="dialog" 
          aria-modal="true"
          aria-labelledby="search-title"
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center"
        >
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 id="search-title" className="font-bold mb-4">
              Search
            </h2>
            <input
              ref={searchInputRef}
              type="search"
              placeholder="Type to search..."
              className="input w-full"
              aria-label="Search products"
            />
          </div>
        </div>
      )}
    </>
  );
}

// ===== EXAMPLE 6: Skip Link for Keyboard Users =====

export function SkipLink() {
  return (
    <a
      href="#main-content"
      className="skip-link"
      onClick={(e) => {
        const main = document.getElementById('main-content');
        if (main) {
          main.focus();
          main.scrollIntoView();
        }
        announceToScreenReader('Navigated to main content', 'polite');
      }}
    >
      Skip to main content
    </a>
  );
}

// ===== EXAMPLE 7: Accessible Loading State =====

import { LoadingSpinner } from '@/components/ErrorHandling';

export function DataLoadingExample() {
  const [isLoading, setIsLoading] = useState(true);
  const [data, setData] = useState<any>(null);

  return (
    <div aria-label="Loading data" role="region">
      {isLoading ? (
        <div className="flex flex-col items-center gap-4">
          <LoadingSpinner size="lg" />
          <p id="loading-message">Loading product data...</p>
        </div>
      ) : (
        <div role="status" aria-live="polite">
          Data loaded successfully
        </div>
      )}
    </div>
  );
}

// ===== BEST PRACTICES =====

/**
 * Accessibility Checklist for New Components:
 *
 * 1. KEYBOARD NAVIGATION
 * ✓ All interactive elements accessible via Tab
 * ✓ Logical tab order (left-to-right, top-to-bottom)
 * ✓ No keyboard traps
 * ✓ Focus visible on all interactive elements
 *
 * 2. SEMANTIC HTML
 * ✓ Use <button> not <div role="button">
 * ✓ Use <a> for navigation
 * ✓ Use <label htmlFor="id"> for form fields
 * ✓ Use <h1>, <h2>, <h3> in order
 *
 * 3. ARIA ATTRIBUTES
 * ✓ aria-label for icon buttons
 * ✓ aria-labelledby for modals/dialogs
 * ✓ aria-live for dynamic content
 * ✓ aria-invalid for form errors
 * ✓ aria-required for required fields
 *
 * 4. SCREEN READERS
 * ✓ Error/success messages announced
 * ✓ Form validation feedback provided
 * ✓ Loading states indicated
 * ✓ Status updates announced
 *
 * 5. TESTING
 * ✓ Test with keyboard only (no mouse)
 * ✓ Test with screen reader (NVDA or VoiceOver)
 * ✓ Test with browser DevTools accessibility panel
 * ✓ Check color contrast (4.5:1 for normal text)
 */

export default {
  ProductEditModal,
  UsersList,
  ProductForm,
  CartNotification,
  SearchWithKeyboardShortcut,
  SkipLink,
  DataLoadingExample,
};
