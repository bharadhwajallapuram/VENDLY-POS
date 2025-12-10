# Offline Mode - Complete Documentation

> **Status**: ✅ Production Ready | **Version**: 1.0 | **Date**: Dec 9, 2025

## Quick Summary

Vendly POS now supports **offline mode** - sales automatically queue when internet is lost and sync when reconnected. No manual intervention needed.

### Key Capabilities
- ✅ Queue sales locally when offline
- ✅ Automatic sync on reconnection (2 second delay for stability)
- ✅ Periodic sync every 30 seconds when online
- ✅ Manual sync button for immediate sync
- ✅ Visual status indicators (online/offline + pending count)
- ✅ Retry logic (up to 3 attempts per sale)
- ✅ Batch processing for efficiency
- ✅ Full error handling & validation

---

## Overview

Vendly POS now supports **offline mode** - the ability to queue sales transactions when the user loses internet connection and automatically sync them when reconnected. This ensures uninterrupted service even in low-connectivity environments.

## Features

### 1. **Offline Sales Queueing**
- When offline, sales are stored locally in browser localStorage
- Each sale receives a unique UUID for tracking
- Sales data includes all transaction details (items, payments, discounts, customer info)
- Users can continue processing sales without interruption

### 2. **Automatic Sync on Reconnection**
- When connection is restored, sync automatically triggers after 2 seconds (for stability)
- Periodic sync every 30 seconds when online (if pending sales exist)
- Manual sync button available in the UI for immediate sync
- Progress tracking with retry logic (up to 3 retries per sale)

### 3. **Visual Indicators**
- **Status Dot**: Green (online) or Red (offline) with animation during sync
- **Status Text**: "Online" or "Offline" label
- **Pending Badge**: Yellow/orange badge showing count of unsync'd sales
- **Sync Button**: Manual trigger with loading animation
- **Offline Banner**: Fixed top alert when offline or pending
- **Receipt Status**: Different emoji & messaging for offline vs online sales

### 4. **Batch Sync Processing**
- Efficient batch endpoint that syncs multiple sales in one request
- Fallback to individual sync if batch fails
- Detailed result tracking (success/failure for each sale)
- Automatic retry on failure

## Architecture

### Frontend Components

#### 1. **`lib/offlineQueue.ts`** - Queue Service
Handles all offline queue operations:

```typescript
// Key functions:
getQueuedSales()              // Retrieve all queued sales
queueSale()                   // Add sale to queue
syncAllSales()                // Sync one-by-one
batchSyncSales()              // Efficient batch sync
getPendingCount()             // Count unsync'd sales
clearSyncedSales()            // Clean up
```

**Storage Details**:
- Uses `localStorage` key: `vendly_offline_queue`
- Stores array of `OfflineSale` objects
- Each sale tracks: UUID, items, payments, discounts, customer info, sync status

#### 2. **`lib/useOffline.ts`** - React Hook
Provides React integration for offline functionality:

```typescript
interface UseOfflineReturn {
  isOnline: boolean              // Current connection status
  pendingCount: number           // # of unsync'd sales
  queuedSales: OfflineSale[]     // Array of queued sales
  isSyncing: boolean             // Sync in progress
  lastSyncTime: Date | null      // Last sync timestamp
  lastSyncResult: {              // Last sync results
    synced: number
    failed: number
  }
  syncNow: () => Promise<void>   // Manual sync trigger
  queueOfflineSale: typeof queueSale  // Queue function
}
```

**Features**:
- Listens to `online`/`offline` events
- Detects network reconnection with stability delay
- Periodic sync polling (30s interval)
- Custom event listeners for queue changes
- Automatic sync on mount if pending sales exist

#### 3. **`components/OfflineIndicator.tsx`** - UI Components
Three exported components:

**`<OfflineIndicator />`** (Main indicator)
- Shows status dot + text
- Displays pending count badge
- Manual sync button
- Optional detailed stats

**`<OfflineIndicatorCompact />`** (Navbar version)
- Minimal footprint
- Only shows when offline or pending

**`<OfflineBanner />`** (Top banner)
- Fixed position alert
- Contextual messaging
- Manual sync action

#### 4. **Updated `app/pos/page.tsx`** - Integration
Modified to support offline mode:

```tsx
// New state
const [isOfflineSale, setIsOfflineSale] = useState(false);
const { isOnline, pendingCount, queueOfflineSale, syncNow } = useOffline();

// handlePayment() now:
// 1. Checks if online
// 2. If offline: queues sale locally
// 3. If online but network error: queues as fallback
// 4. Shows different UI feedback for offline vs online sales
```

**UI Changes**:
- Offline status bar below header
- Receipt modal shows "📱 Sale Saved Offline!" for queued sales
- Message: "Will sync when back online"
- Reassuring note about automatic sync

### Backend Components

#### 1. **`schemas/sales.py`** - New Schemas
Added offline-specific schemas:

```python
class OfflineSaleIn(BaseModel):
    """Offline sale data structure"""
    id: str                    # Client-side UUID
    items: List[SaleItemIn]
    payments: List[OfflinePayment]
    discount: float
    coupon_code: Optional[str]
    notes: Optional[str]
    customer_id: Optional[int]
    customer_name: Optional[str]
    customer_phone: Optional[str]
    customer_email: Optional[str]
    created_at: str            # ISO timestamp

class BatchSyncRequest(BaseModel):
    sales: List[OfflineSaleIn]

class BatchSyncResponse(BaseModel):
    synced: int
    failed: int
    results: List[SyncResultItem]
```

#### 2. **`routers/sales.py`** - Batch Sync Endpoint
New POST endpoint: `/api/v1/sales/batch-sync`

**Endpoint Details**:
- Requires authentication
- Accepts list of offline sales
- For each sale:
  - Creates/looks up customer
  - Validates items and stock
  - Calculates totals with coupon/discount
  - Creates sale record
  - Updates inventory
  - Tracks result
- Returns detailed success/failure info
- **Important**: Marks synced sales with `payment_method: "offline_sync"` for tracking

**Error Handling**:
- Validates all items exist and have sufficient stock
- Validates coupon codes
- Rolls back on individual sale failure
- Returns error details for client to retry

## Data Flow

### Offline Sale Flow
```
1. User makes sale (no internet)
   ↓
2. handlePayment() detects isOnline = false
   ↓
3. Call queueOfflineSale()
   ↓
4. Save to localStorage
   ↓
5. Show receipt with "📱 Saved Offline" message
   ↓
6. User can continue selling
```

### Reconnection & Sync Flow
```
1. User regains internet connection
   ↓
2. Browser fires "online" event
   ↓
3. useOffline hook detects change
   ↓
4. Waits 2 seconds for stability
   ↓
5. Calls syncNow() → batchSyncSales()
   ↓
6. POST to /api/v1/sales/batch-sync
   ↓
7. Server creates sales records
   ↓
8. Updates localStorage with sync status
   ↓
9. Displays sync results to user
```

## Configuration

### Retry Logic
- **Max Retries**: 3 attempts per sale
- **Retry Trigger**: Manual sync or periodic (30s)
- **Batch Fallback**: If batch endpoint fails, falls back to individual sync

### Storage
- **Key**: `vendly_offline_queue`
- **Location**: `localStorage` (persists across sessions)
- **Data Type**: JSON array of OfflineSale objects

### Timing
- **Reconnection Delay**: 2 seconds (wait for stable connection)
- **Periodic Sync Interval**: 30 seconds (when online)
- **Sync Timeout**: Uses standard fetch timeout

## Usage Examples

### Basic Implementation (Already Done in POS Page)
```tsx
import { useOffline } from '@/lib/useOffline';
import OfflineIndicator, { OfflineBanner } from '@/components/OfflineIndicator';

function MyComponent() {
  const { isOnline, pendingCount, syncNow } = useOffline();

  return (
    <div>
      <OfflineBanner />
      <OfflineIndicator />
      
      {!isOnline && <p>Working offline</p>}
      {pendingCount > 0 && <button onClick={syncNow}>Sync {pendingCount}</button>}
    </div>
  );
}
```

### Adding Offline Sales Manually
```tsx
import { queueSale } from '@/lib/offlineQueue';

const offlineSale = queueSale({
  items: [...],
  payments: [...],
  discount: 0,
  coupon_code: 'SAVE10',
  notes: 'Manual entry',
  customer_id: 123,
});

console.log('Queued with UUID:', offlineSale.id);
```

## Testing Offline Mode

### In Browser DevTools
1. Open Network tab
2. Set throttling to "Offline"
3. Create a sale → Should queue locally
4. Go back Online
5. Should auto-sync

### Manual Testing
```javascript
// Simulate offline (in browser console)
window.dispatchEvent(new Event('offline'));

// Queue a sale
queueOfflineSales([{...}]);

// Simulate back online
window.dispatchEvent(new Event('online'));
// Should trigger sync automatically
```

## Error Handling

### Client-Side
- **Network Error**: Falls back to offline queue automatically
- **Validation Error**: Shows error message, allows retry
- **Max Retries Reached**: Sale stays in queue with error status

### Server-Side
- **Invalid Product**: Returns error, sale not created
- **Insufficient Stock**: Returns error, sale not created
- **Invalid Coupon**: Returns error, sale not created
- **Customer Lookup Failure**: Creates new customer, continues

## Future Enhancements

1. **IndexedDB Storage**: Migrate from localStorage for larger data capacity
2. **Sync Scheduling**: Background sync API for truly offline-first approach
3. **Conflict Resolution**: Handle inventory conflicts when syncing
4. **Analytics**: Track offline usage patterns
5. **Selective Retry**: Ability to retry failed sales with modifications
6. **Offline Reports**: Local reporting before sync

## Performance Considerations

- **Minimal Impact**: Offline queue operations are instant (synchronous)
- **Batch Sync**: More efficient than individual requests
- **Storage Limit**: localStorage has ~5-10MB limit (should accommodate thousands of sales)
- **Memory**: useOffline hook is lightweight, minimal re-renders

## Security Considerations

- **Token Required**: Sync endpoint requires valid auth token
- **User Isolation**: Each user can only sync their own sales
- **Data Validation**: Server validates all fields and permissions
- **Payment Obfuscation**: Payment methods stored minimally
- **Local Data**: Stored in browser's protected localStorage

## Troubleshooting

### Sales Not Syncing
1. Check browser console for errors
2. Verify internet connection actually restored
3. Check auth token is still valid
4. Try manual sync button
5. Check browser localStorage quota

### Duplicate Sales
- Should not occur - each sale has unique offline ID
- If suspected, check server logs for payment_reference duplication

### Lost Offline Sales
- Only if localStorage is cleared manually
- Recommend periodic manual backups for important data
- Consider implementing automatic export feature

## API Reference

### Batch Sync Endpoint

**Endpoint**: `POST /api/v1/sales/batch-sync`

**Authentication**: Required (JWT Bearer token)

**Request Body**:
```json
{
  "sales": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "items": [
        {
          "product_id": 1,
          "quantity": 2,
          "price": 99.99,
          "discount": 0
        }
      ],
      "payments": [
        {
          "method": "card",
          "amount": 199.98
        }
      ],
      "discount": 0,
      "coupon_code": null,
      "notes": null,
      "customer_id": null,
      "customer_name": "John Doe",
      "customer_phone": "+91-9876543210",
      "customer_email": "john@example.com",
      "created_at": "2025-12-09T14:30:00Z"
    }
  ]
}
```

**Response (Success - 200)**:
```json
{
  "synced": 1,
  "failed": 0,
  "results": [
    {
      "success": true,
      "offlineId": "550e8400-e29b-41d4-a716-446655440000",
      "serverId": 42,
      "error": null
    }
  ]
}
```

**Response (Partial Success - 200)**:
```json
{
  "synced": 1,
  "failed": 1,
  "results": [
    {
      "success": true,
      "offlineId": "550e8400-e29b-41d4-a716-446655440000",
      "serverId": 42,
      "error": null
    },
    {
      "success": false,
      "offlineId": "660e8400-e29b-41d4-a716-446655440001",
      "serverId": null,
      "error": "Product 999 not found"
    }
  ]
}
```

**Error Cases**:
- `401`: Unauthorized (invalid/expired token)
- `400`: Invalid request body
- `500`: Server error during sync

---

## Queue Service API Reference

### `offlineQueue.ts` Functions

#### `queueSale(sale: OfflineSaleIn): OfflineSale`
Adds a sale to the offline queue.

```typescript
const queued = queueSale({
  items: [{product_id: 1, quantity: 2, price: 99.99, discount: 0}],
  payments: [{method: 'card', amount: 199.98}],
  discount: 0,
  coupon_code: 'SAVE10',
  customer_phone: '+91-9876543210',
  created_at: new Date().toISOString()
});

console.log('UUID:', queued.id);  // Client-generated UUID
console.log('Status:', queued.status);  // 'queued'
```

#### `getQueuedSales(): OfflineSale[]`
Retrieves all queued sales from localStorage.

```typescript
const all = getQueuedSales();
console.log(`${all.length} sales in queue`);
```

#### `getPendingCount(): number`
Returns count of unsync'd sales.

```typescript
const pending = getPendingCount();
if (pending > 0) {
  console.log(`${pending} sales waiting to sync`);
}
```

#### `batchSyncSales(token: string): Promise<BatchSyncResponse>`
Syncs all queued sales to server (primary method).

```typescript
const result = await batchSyncSales(authToken);
console.log(`Synced: ${result.synced}, Failed: ${result.failed}`);

// Automatically retries failed sales individually
```

#### `syncNow(): Promise<void>`
Manual sync trigger (typically called from UI button).

---

## React Hook API Reference

### `useOffline()` Hook

**Returns**:
```typescript
{
  isOnline: boolean                    // Current connection status
  pendingCount: number                 // # of queued sales
  queuedSales: OfflineSale[]          // Array of all queued sales
  isSyncing: boolean                   // Sync in progress
  lastSyncTime: Date | null            // Last successful sync
  lastSyncResult: {                    // Last sync counts
    synced: number
    failed: number
  }
  syncNow: () => Promise<void>        // Manual sync trigger
  queueOfflineSale: (sale) => OfflineSale  // Queue function
}
```

**Usage**:
```tsx
function OrderSummary() {
  const { 
    isOnline, 
    pendingCount, 
    isSyncing,
    syncNow 
  } = useOffline();

  return (
    <div>
      {!isOnline && <span>📱 Offline</span>}
      {pendingCount > 0 && (
        <>
          <span>{pendingCount} pending</span>
          <button 
            onClick={syncNow}
            disabled={isSyncing}
          >
            {isSyncing ? 'Syncing...' : 'Sync Now'}
          </button>
        </>
      )}
    </div>
  );
}
```

---

## Component Reference

### `<OfflineIndicator />`
Main offline status component.

**Props**:
```typescript
interface Props {
  compact?: boolean              // Use compact version
  showDetails?: boolean          // Show detailed stats
}
```

**Example**:
```tsx
<OfflineIndicator showDetails={true} />
```

### `<OfflineIndicatorCompact />`
Navbar-friendly minimal indicator.

**Example**:
```tsx
<nav>
  <OfflineIndicatorCompact />
</nav>
```

### `<OfflineBanner />`
Fixed-position top alert banner.

**Example**:
```tsx
<>
  <OfflineBanner />
  {/* Rest of page */}
</>
```

---

## Implementation Checklist

- [x] Created offline queue service (`offlineQueue.ts`)
- [x] Created React hook (`useOffline.ts`)
- [x] Created UI components (`OfflineIndicator.tsx`)
- [x] Integrated into POS page
- [x] Added backend schemas
- [x] Implemented batch sync endpoint
- [x] Added error handling & validation
- [x] Added retry logic
- [x] Tested offline queueing
- [x] Tested automatic sync
- [x] Tested fallback behavior
- [x] Documented API
- [x] Validated TypeScript (0 errors)
- [x] Validated Python (0 errors)

---

## Files Modified/Created

### New Files
- `client/src/lib/offlineQueue.ts` (275 lines)
- `client/src/lib/useOffline.ts` (150 lines)
- `client/src/components/OfflineIndicator.tsx` (160 lines)

### Modified Files
- `client/src/app/pos/page.tsx` (+ 180 lines of offline support)
- `server/app/api/v1/schemas/sales.py` (+ new schemas)
- `server/app/api/v1/routers/sales.py` (+ batch-sync endpoint)

---

## Quick Start for New Developers

1. **Offline queueing happens automatically** - No code needed in most cases
2. **To check pending sales**: `const { pendingCount } = useOffline()`
3. **To manually sync**: `const { syncNow } = useOffline(); await syncNow()`
4. **To add indicator UI**: Import and use `<OfflineIndicator />` or `<OfflineBanner />`
5. **For custom offline handling**: Use `queueOfflineSale()` from the hook

---

## Summary

The offline mode implementation provides:
✅ **Seamless Offline Sales**: Continue selling without internet
✅ **Automatic Sync**: Transparent reconnection handling
✅ **Visual Feedback**: Clear status indicators
✅ **Reliability**: Retry logic and error handling
✅ **Efficiency**: Batch processing for fast sync
✅ **User Experience**: No manual intervention needed

Users can now confidently operate the POS system in areas with intermittent connectivity, knowing their sales data is safe and will sync automatically.
