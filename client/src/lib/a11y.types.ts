/**
 * Accessibility TypeScript Types and Interfaces
 * For use with the a11y utility library and accessible components
 */

/**
 * ARIA Live Region Priority Levels
 * - 'polite': Wait for user to finish current action
 * - 'assertive': Interrupt user immediately (errors, warnings)
 * - 'off': No announcement (use with caution)
 */
export type AriaLive = 'polite' | 'assertive' | 'off';

/**
 * ARIA Roles for different component types
 */
export type AriaRole =
  | 'dialog'
  | 'alertdialog'
  | 'menu'
  | 'menuitem'
  | 'alert'
  | 'status'
  | 'button'
  | 'tab'
  | 'tabpanel'
  | 'progressbar'
  | 'slider'
  | 'menubar'
  | 'tablist'
  | 'separator'
  | 'switch'
  | 'table'
  | 'columnheader'
  | 'rowheader'
  | 'row'
  | 'cell'
  | 'main'
  | 'navigation'
  | 'region'
  | 'complementary'
  | 'contentinfo'
  | 'application';

/**
 * Component-specific accessibility properties
 */
export interface AccessibilityProps {
  /** ARIA label for icon buttons or unlabeled elements */
  ariaLabel?: string;

  /** ID of element that labels this element */
  ariaLabelledBy?: string;

  /** ID of element that describes this element */
  ariaDescribedBy?: string;

  /** For form inputs: whether the field is required */
  ariaRequired?: boolean;

  /** For form inputs: whether the value is invalid */
  ariaInvalid?: boolean;

  /** For form inputs: description or error message */
  ariaErrorMessage?: string;

  /** For expandable elements: whether expanded */
  ariaExpanded?: boolean;

  /** For elements with hidden content: target element IDs */
  ariaControls?: string;

  /** For dialogs: whether the element is modal */
  ariaModal?: boolean;

  /** For live regions: announcement priority */
  ariaLive?: AriaLive;

  /** For live regions: whether to announce whole or just changes */
  ariaAtomic?: boolean;

  /** Current page indicator for navigation links */
  ariaCurrent?: 'page' | 'step' | 'location' | 'date' | 'time' | boolean;

  /** Hide element from accessibility tree */
  ariaHidden?: boolean;

  /** For disabled elements */
  disabled?: boolean;

  /** Accessible name for element */
  title?: string;
}

/**
 * Modal/Dialog Accessibility Configuration
 */
export interface DialogA11yConfig {
  /** The title of the dialog (will be used for aria-labelledby) */
  title: string;

  /** Description of the dialog (optional, for aria-describedby) */
  description?: string;

  /** Whether the dialog is modal (should trap focus) */
  isModal?: boolean;

  /** Whether to close on ESC key */
  closeOnEscape?: boolean;

  /** Whether to trap focus within dialog */
  trapFocus?: boolean;

  /** Whether to restore focus on close */
  restoreFocus?: boolean;

  /** Initial focus element (by ref) */
  initialFocus?: React.RefObject<HTMLElement>;

  /** Callback when dialog is closed */
  onClose?: () => void;
}

/**
 * Form Field Accessibility Configuration
 */
export interface FormFieldA11yConfig {
  /** Field ID for label association */
  id: string;

  /** Label text */
  label: string;

  /** Whether field is required */
  required?: boolean;

  /** Whether field is invalid */
  invalid?: boolean;

  /** Error message to display */
  errorMessage?: string;

  /** Help text (hint) */
  helpText?: string;

  /** Placeholder text (not a substitute for label) */
  placeholder?: string;

  /** Whether field is disabled */
  disabled?: boolean;

  /** For multi-field groups, the group label */
  groupLabel?: string;
}

/**
 * Keyboard Event Handlers
 */
export interface KeyboardHandlers {
  /** Handle Enter/Space key press */
  onActivate?: () => void;

  /** Handle Escape key press */
  onEscape?: () => void;

  /** Handle Tab key press */
  onTab?: (isShift: boolean) => void;

  /** Handle custom key combination */
  onCustom?: (key: string, modifiers: KeyModifiers) => void;
}

/**
 * Keyboard Modifiers
 */
export interface KeyModifiers {
  ctrl: boolean;
  shift: boolean;
  alt: boolean;
  meta: boolean;
}

/**
 * Screen Reader Announcement Options
 */
export interface AnnouncementOptions {
  /** Priority of announcement */
  priority?: 'polite' | 'assertive';

  /** Time to keep message visible (ms) */
  duration?: number;

  /** Whether to replace previous announcement */
  replace?: boolean;
}

/**
 * Focus Management Options
 */
export interface FocusOptions {
  /** Element to focus */
  element: HTMLElement;

  /** Announcement to make when focused */
  announcement?: string;

  /** Whether to scroll element into view */
  scrollIntoView?: boolean;

  /** Options for scrollIntoView */
  scrollOptions?: ScrollIntoViewOptions;
}

/**
 * Alert/Toast A11y Configuration
 */
export interface AlertA11yConfig {
  /** Alert type: error, warning, success, info */
  type: 'error' | 'warning' | 'success' | 'info';

  /** Alert message */
  message: string;

  /** How long to display (ms, 0 = indefinite) */
  duration?: number;

  /** Whether to auto-dismiss */
  autoDismiss?: boolean;

  /** Callback on dismiss */
  onDismiss?: () => void;

  /** Whether user can dismiss */
  dismissible?: boolean;
}

/**
 * Skip Link Configuration
 */
export interface SkipLinkConfig {
  /** Target element ID or ref */
  target: string | HTMLElement;

  /** Skip link text */
  text: string;

  /** CSS class for styling */
  className?: string;

  /** Callback when link is used */
  onSkip?: () => void;
}

/**
 * Table A11y Configuration
 */
export interface TableA11yConfig {
  /** Table caption for screen readers */
  caption?: string;

  /** Column headers */
  headers: string[];

  /** Whether to include role attributes */
  useRoles?: boolean;

  /** Row label function (for complex tables) */
  getRowLabel?: (rowIndex: number, rowData: any) => string;

  /** Cell header scope ('col' or 'row') */
  headerScope?: 'col' | 'row';
}

/**
 * Menu A11y Configuration
 */
export interface MenuA11yConfig {
  /** Menu label */
  label: string;

  /** Menu items */
  items: MenuItem[];

  /** Whether menu is open */
  isOpen?: boolean;

  /** On menu open callback */
  onOpen?: () => void;

  /** On menu close callback */
  onClose?: () => void;

  /** On item select callback */
  onSelect?: (item: MenuItem) => void;
}

/**
 * Menu Item Configuration
 */
export interface MenuItem {
  /** Menu item ID */
  id: string;

  /** Menu item label */
  label: string;

  /** Whether item is disabled */
  disabled?: boolean;

  /** Whether item is selected */
  selected?: boolean;

  /** Submenu items (for nested menus) */
  submenu?: MenuItem[];

  /** Icon or custom content */
  icon?: React.ReactNode;
}

/**
 * Breadcrumb A11y Configuration
 */
export interface BreadcrumbA11yConfig {
  /** Breadcrumb items */
  items: BreadcrumbItem[];

  /** Separator element (default: "/") */
  separator?: string | React.ReactNode;

  /** Aria-label for nav element */
  ariaLabel?: string;

  /** Additional CSS class */
  className?: string;
}

/**
 * Breadcrumb Item
 */
export interface BreadcrumbItem {
  /** Item label */
  label: string;

  /** Item URL/href */
  href?: string;

  /** Whether item is current page */
  current?: boolean;

  /** Callback when item clicked */
  onClick?: () => void;
}

/**
 * Keyboard Shortcut Configuration
 */
export interface KeyboardShortcut {
  /** Shortcut key combination */
  keys: string[];

  /** What the shortcut does */
  description: string;

  /** Callback when shortcut is pressed */
  onPress: () => void;

  /** Whether to prevent default browser behavior */
  preventDefault?: boolean;

  /** Whether shortcut is enabled */
  enabled?: boolean;
}

/**
 * Tooltip A11y Configuration
 */
export interface TooltipA11yConfig {
  /** Tooltip ID */
  id: string;

  /** Tooltip text */
  content: string;

  /** Position: 'top' | 'bottom' | 'left' | 'right' */
  position?: 'top' | 'bottom' | 'left' | 'right';

  /** Show on hover, focus, or both */
  trigger?: 'hover' | 'focus' | 'both';

  /** Delay before showing (ms) */
  delay?: number;

  /** Whether tooltip should be interactive */
  interactive?: boolean;
}

/**
 * Dropdown A11y Configuration
 */
export interface DropdownA11yConfig {
  /** Button label */
  label: string;

  /** Dropdown items */
  items: DropdownItem[];

  /** Whether dropdown is open */
  isOpen?: boolean;

  /** On item select callback */
  onSelect?: (item: DropdownItem) => void;

  /** Whether to close on select */
  closeOnSelect?: boolean;
}

/**
 * Dropdown Item
 */
export interface DropdownItem {
  /** Item ID */
  id: string;

  /** Item label */
  label: string;

  /** Item value */
  value?: any;

  /** Whether item is disabled */
  disabled?: boolean;

  /** Icon or custom content */
  icon?: React.ReactNode;

  /** Divider line after item */
  divider?: boolean;
}

/**
 * Validation Error for Accessible Forms
 */
export interface ValidationError {
  /** Field ID */
  field: string;

  /** Error message */
  message: string;

  /** Error type for ARIA attributes */
  type: 'required' | 'invalid' | 'custom';
}

/**
 * Accessibility Test Report
 */
export interface A11yTestReport {
  /** Test timestamp */
  timestamp: Date;

  /** Total issues found */
  issueCount: number;

  /** Critical issues */
  critical: string[];

  /** Major issues */
  major: string[];

  /** Minor issues */
  minor: string[];

  /** Suggestions for improvement */
  suggestions: string[];

  /** Compliance status */
  wcagLevel: 'A' | 'AA' | 'AAA' | 'FAIL';

  /** Tool used for testing */
  tool: string;
}

/**
 * Motion Preference Configuration
 */
export interface MotionPreferences {
  /** User prefers reduced motion */
  prefersReducedMotion: boolean;

  /** User prefers reduced transparency */
  prefersReducedTransparency: boolean;

  /** User prefers dark color scheme */
  prefersDarkMode: boolean;

  /** User prefers high contrast */
  prefersHighContrast: boolean;
}

/**
 * Utility type for accessible button props
 */
export type AccessibleButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> &
  AccessibilityProps & {
    /** Button variant */
    variant?: 'primary' | 'secondary' | 'danger' | 'success' | 'info';

    /** Button size */
    size?: 'sm' | 'md' | 'lg';

    /** Whether button is loading */
    isLoading?: boolean;

    /** Whether button is disabled */
    disabled?: boolean;

    /** Icon or custom content */
    icon?: React.ReactNode;

    /** Loading indicator text for screen readers */
    loadingText?: string;
  };

/**
 * Utility type for accessible input props
 */
export type AccessibleInputProps = React.InputHTMLAttributes<HTMLInputElement> &
  AccessibilityProps & {
    /** Form field config */
    field?: FormFieldA11yConfig;

    /** Input size */
    size?: 'sm' | 'md' | 'lg';

    /** Input icon */
    icon?: React.ReactNode;

    /** On validation callback */
    onValidate?: (valid: boolean, error?: string) => void;
  };

// All types and interfaces are already exported individually above
