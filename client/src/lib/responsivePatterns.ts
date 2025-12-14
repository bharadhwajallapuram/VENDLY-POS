// ===========================================
// Responsive Layout Utilities
// ===========================================

/**
 * Common responsive patterns used throughout the application
 */

// Mobile-first responsive text sizes
export const responsiveText = {
  page_heading: 'text-2xl md:text-3xl lg:text-4xl font-bold',
  section_heading: 'text-lg md:text-xl lg:text-2xl font-bold',
  subheading: 'text-base md:text-lg font-semibold',
  label: 'text-xs md:text-sm font-medium',
  body: 'text-xs md:text-sm',
  small: 'text-xs',
  caption: 'text-xs text-gray-500',
};

// Responsive spacing
export const responsiveSpacing = {
  page_gap: 'space-y-4 md:space-y-6 lg:space-y-8',
  section_gap: 'space-y-3 md:space-y-4',
  form_gap: 'space-y-3 md:space-y-4',
  button_gap: 'gap-2 md:gap-3',
  table_padding: 'px-2 md:px-3 lg:px-4',
  card_padding: 'p-4 md:p-6',
};

// Responsive padding and margins
export const responsivePadding = {
  page: 'py-4 md:py-6 lg:py-8 px-3 md:px-4 lg:px-6',
  card: 'p-4 md:p-6',
  section: 'px-3 md:px-4',
  input: 'px-3 py-2 md:px-3 md:py-2',
  button: 'px-3 py-2 md:px-4 md:py-2',
};

// Responsive grid patterns
export const responsiveGrid = {
  auto_2col: 'grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6',
  auto_3col: 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6',
  form_layout: 'grid gap-3 md:gap-4',
};

// Responsive flex patterns
export const responsiveFlex = {
  header: 'flex flex-col sm:flex-row sm:justify-between sm:items-center gap-3',
  button_group: 'flex flex-col-reverse sm:flex-row justify-end gap-2 md:gap-3',
  nav: 'flex flex-col md:flex-row md:gap-6',
  filter_bar: 'flex flex-col md:flex-row md:flex-wrap md:gap-4 gap-3',
};

// Responsive containers
export const responsiveContainer = {
  main: 'max-w-7xl mx-auto',
  modal_sm: 'w-full max-w-sm md:max-w-md',
  modal_md: 'w-full max-w-md md:max-w-lg',
  modal_lg: 'w-full max-w-lg md:max-w-2xl',
};

// Touch-friendly sizing
export const touchTargets = {
  button: 'min-h-[44px] md:min-h-[40px]',
  input: 'min-h-[44px] md:min-h-[40px]',
  interactive: 'min-h-[48px] min-w-[48px]',
};

// Responsive table patterns
export const responsiveTable = {
  header: 'py-3 px-2 md:px-4 font-medium text-gray-700',
  cell: 'py-3 px-2 md:px-4',
  cell_right: 'py-3 px-2 md:px-4 text-right',
  cell_center: 'py-3 px-2 md:px-4 text-center',
};

// Mobile menu patterns
export const mobileMenu = {
  container: 'md:hidden',
  item: 'block px-3 py-2 text-sm hover:bg-gray-100 rounded',
  separator: 'my-2 border-t',
};

// Responsive visibility patterns
export const visibility = {
  mobile_only: 'md:hidden',
  tablet_up: 'hidden sm:block',
  desktop_only: 'hidden md:block',
  lg_only: 'hidden lg:block',
};
