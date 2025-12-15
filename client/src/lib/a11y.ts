/**
 * Accessibility (a11y) Utilities
 * Helpers for keyboard navigation, focus management, and screen reader support
 */

/**
 * Trap focus within a container element
 * Useful for modals and dialogs
 */
export function createFocusTrap(container: HTMLElement) {
  const focusableElements = container.querySelectorAll(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  );

  const firstElement = focusableElements[0] as HTMLElement;
  const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement;

  function handleTabKey(e: KeyboardEvent) {
    if (e.key !== 'Tab') return;

    if (e.shiftKey) {
      if (document.activeElement === firstElement) {
        e.preventDefault();
        lastElement.focus();
      }
    } else {
      if (document.activeElement === lastElement) {
        e.preventDefault();
        firstElement.focus();
      }
    }
  }

  container.addEventListener('keydown', handleTabKey);

  return () => {
    container.removeEventListener('keydown', handleTabKey);
  };
}

/**
 * Announce message to screen readers using aria-live region
 */
export function announceToScreenReader(message: string, priority: 'polite' | 'assertive' = 'polite') {
  let liveRegion = document.querySelector(`[role="status"][aria-live="${priority}"]`);

  if (!liveRegion) {
    liveRegion = document.createElement('div');
    liveRegion.setAttribute('role', 'status');
    liveRegion.setAttribute('aria-live', priority);
    liveRegion.setAttribute('aria-atomic', 'true');
    liveRegion.className = 'sr-only';
    document.body.appendChild(liveRegion);
  }

  liveRegion.textContent = message;

  // Clear after announcement
  setTimeout(() => {
    liveRegion!.textContent = '';
  }, 1000);
}

/**
 * Check if user prefers reduced motion
 */
export function prefersReducedMotion(): boolean {
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

/**
 * Get all interactive elements within a container
 */
export function getInteractiveElements(container: HTMLElement): HTMLElement[] {
  return Array.from(
    container.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    )
  ) as HTMLElement[];
}

/**
 * Check if element is visible for screen readers
 */
export function isVisibleToScreenReaders(element: HTMLElement): boolean {
  return !element.hasAttribute('aria-hidden') && element.offsetParent !== null;
}

/**
 * Set focus with optional announcement
 */
export function setFocusWithAnnouncement(element: HTMLElement, announcement?: string) {
  element.focus();
  if (announcement) {
    announceToScreenReader(announcement);
  }
}

/**
 * Handle escape key press
 */
export function onEscapeKey(callback: () => void): () => void {
  const handler = (e: KeyboardEvent) => {
    if (e.key === 'Escape') {
      callback();
    }
  };

  window.addEventListener('keydown', handler);

  return () => {
    window.removeEventListener('keydown', handler);
  };
}

/**
 * Generate unique ID for aria-labelledby/aria-describedby
 */
export function generateId(prefix: string = 'id'): string {
  return `${prefix}-${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Check if element is keyboard accessible
 */
export function isKeyboardAccessible(element: HTMLElement): boolean {
  const tabindex = element.getAttribute('tabindex');
  if (tabindex === '-1') return false;

  const isNativelyFocusable = ['BUTTON', 'A', 'INPUT', 'SELECT', 'TEXTAREA'].includes(element.tagName);
  if (isNativelyFocusable && !element.hasAttribute('disabled')) return true;

  return tabindex !== null && parseInt(tabindex) >= 0;
}
