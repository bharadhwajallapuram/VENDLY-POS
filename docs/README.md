# Vendly POS - Complete Documentation

Welcome to Vendly POS! This comprehensive guide covers all features, systems, architecture, and implementation details.

---

## 📚 Table of Contents

1. [System Architecture](#-system-architecture)
2. [Quick Start](#-quick-start)
3. [Project Structure](#-project-structure)
4. [Key Features](#-key-features)
5. [Offline Mode](#-offline-mode)
6. [Granular Permissions System](#-granular-permissions-system)
7. [End-of-Day Reports & Z-Reports](#-end-of-day-reports--z-reports)
8. [Error Handling & CI/CD](#-error-handling--cicd-pipeline-safety)
9. [Security](#-security)
10. [Common Commands](#-common-commands)
11. [Monitoring & Observability](#-monitoring--observability)
12. [Feature Documentation](#-feature-documentation)
13. [Contributing](#-contributing)
14. [Support](#-support)

---

## 🏗️ System Architecture

Vendly follows a microservices-inspired architecture with event-driven patterns:

```
┌──────────────────────────────────────────────────────────────────┐
│                         VENDLY POS                                │
├──────────────────────────────────────────────────────────────────┤
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐       │
│  │ Frontend│────│  Nginx  │────│ Backend │────│  AI/ML  │       │
│  │ (React) │    │ (Proxy) │    │(FastAPI)│    │ Service │       │
│  └─────────┘    └─────────┘    └────┬────┘    └─────────┘       │
│                                     │                            │
│        ┌────────────────────────────┼────────────────────┐       │
│        │                            │                    │       │
│  ┌─────▼─────┐    ┌─────────┐    ┌──▼──────┐    ┌───────▼───┐  │
│  │PostgreSQL │    │  Redis  │    │  Kafka  │    │Prometheus │  │
│  │(Database) │    │ (Cache) │    │(Events) │    │(Metrics)  │  │
│  └───────────┘    └─────────┘    └─────────┘    └───────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites
- Node.js >= 18.0.0
- Python >= 3.11
- Docker & Docker Compose (optional)
- npm >= 9.0.0

### Local Development

1. **Clone and setup:**
   ```bash
   git clone https://github.com/bharadhwajallapuram/Vendly-fastapi-Js.git
   cd Vendly-fastapi-Js
   npm run setup
   ```

2. **Start development servers:**
   ```bash
   npm run dev
   ```
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000

3. **(Optional) Seed demo data:**
   ```bash
   cd server
   python scripts/seed_products.py
   ```

### Docker Deployment

```bash
docker-compose up -d
```

This starts:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- PostgreSQL: localhost:5432
- Redis: localhost:6379
- Prometheus: http://localhost:9090

---

## 📁 Project Structure

```
vendly/
├── docs/                    # 📖 Documentation (you are here)
├── client/                  # Frontend (Next.js 14, React, TypeScript)
├── server/                  # Backend (FastAPI, Python 3.11)
├── shared/                  # Shared types and utilities
├── ai_ml/                   # AI/ML services
├── scripts/                 # Utility scripts
├── docker-compose.yaml      # Container orchestration
├── config.example.yaml      # Configuration template
└── .env.example             # Environment template
```

---

## 🔑 Key Features

### ✅ Offline Mode
- Queue sales when offline
- Automatic sync on reconnection
- No manual intervention needed
- Visual status indicators
- **Details**: [Offline Mode](#-offline-mode)

### ✅ Granular Permissions
- Cashier, Manager, Admin roles
- 30+ permissions with inheritance
- Frontend and backend validation
- **Details**: [Granular Permissions System](#-granular-permissions-system)

### ✅ Error Handling
- Non-hardcoded error constants
- Centralized error management
- CI/CD pipeline safe
- **Details**: [Error Handling](#-error-handling--cicd-pipeline-safety)

### ✅ Advanced Features
- Sales, refunds, and returns management
- Inventory tracking
- Customer management with loyalty points
- Real-time reporting and analytics
- AI-powered recommendations and forecasting
- Multiple payment methods (Stripe, UPI, Cash)
- Audit logging for compliance

---

## 🛒 Offline Mode

### Quick Summary

Vendly POS supports **offline mode** - sales automatically queue when internet is lost and sync when reconnected. No manual intervention needed.

### Key Capabilities
- ✅ Queue sales locally when offline
- ✅ Automatic sync on reconnection (2 second delay for stability)
- ✅ Periodic sync every 30 seconds when online
- ✅ Manual sync button for immediate sync
- ✅ Visual status indicators (online/offline + pending count)
- ✅ Retry logic (up to 3 attempts per sale)
- ✅ Batch processing for efficiency
- ✅ Full error handling & validation

### Features

#### 1. Offline Sales Queueing
- Sales stored locally in browser localStorage
- Each sale receives a unique UUID for tracking
- Complete transaction details preserved (items, payments, discounts, customer info)
- Users can continue processing sales without interruption

#### 2. Automatic Sync on Reconnection
- Sync triggered automatically after 2 seconds when connection restored
- Periodic sync every 30 seconds when online (if pending sales exist)
- Manual sync button available in the UI for immediate sync
- Progress tracking with retry logic (up to 3 retries per sale)

#### 3. Visual Indicators
- **Status Dot**: Green (online) or Red (offline) with animation during sync
- **Status Text**: "Online" or "Offline" label
- **Pending Badge**: Yellow/orange badge showing count of unsync'd sales
- **Sync Button**: Manual trigger with loading animation
- **Offline Banner**: Fixed top alert when offline or pending
- **Receipt Status**: Different emoji & messaging for offline vs online sales

#### 4. Batch Sync Processing
- Efficient batch endpoint that syncs multiple sales in one request
- Fallback to individual sync if batch fails
- Detailed result tracking (success/failure for each sale)
- Automatic retry on failure

### Architecture

**Frontend Components:**

1. **`lib/offlineQueue.ts`** - Queue Service
   - `getQueuedSales()` - Retrieve all queued sales
   - `queueSale()` - Add sale to queue
   - `syncAllSales()` - Sync one-by-one
   - `batchSyncSales()` - Efficient batch sync
   - `getPendingCount()` - Count unsync'd sales

2. **`lib/useOffline.ts`** - React Hook
   - Current connection status
   - Pending count and queued sales array
   - Manual sync trigger function
   - Last sync tracking

3. **`components/OfflineIndicator.tsx`** - UI Components
   - Status indicator (online/offline dot)
   - Pending count badge
   - Manual sync button
   - Optional detailed stats

**Backend Components:**

1. **`schemas/sales.py`** - Offline Schemas
   - `OfflineSaleIn` - Offline sale data structure
   - `BatchSyncRequest` - Batch sync request
   - `BatchSyncResponse` - Batch sync response

2. **`routers/sales.py`** - Batch Sync Endpoint
   - `POST /api/v1/sales/batch-sync`
   - Creates/looks up customers
   - Validates items and stock
   - Marks synced sales with `payment_method: "offline_sync"`
   - Returns detailed success/failure info

### Data Flow

**Offline Sale Flow:**
```
User makes sale (no internet) → queueOfflineSale() → 
Save to localStorage → Show receipt with "📱 Saved Offline" → 
User continues selling
```

**Reconnection & Sync Flow:**
```
User regains internet → Browser fires "online" event → 
useOffline hook detects change → Wait 2 seconds → 
Call syncNow() → POST to /api/v1/sales/batch-sync → 
Server creates sales records → Update localStorage → 
Display sync results
```

### Configuration

- **Max Retries**: 3 attempts per sale
- **Reconnection Delay**: 2 seconds
- **Periodic Sync Interval**: 30 seconds
- **Storage Key**: `vendly_offline_queue` in localStorage

### Usage Examples

**Basic Implementation:**
```tsx
import { useOffline } from '@/lib/useOffline';
import OfflineIndicator from '@/components/OfflineIndicator';

function MyComponent() {
  const { isOnline, pendingCount, syncNow } = useOffline();

  return (
    <div>
      <OfflineIndicator />
      {!isOnline && <p>Working offline</p>}
      {pendingCount > 0 && <button onClick={syncNow}>Sync {pendingCount}</button>}
    </div>
  );
}
```

**Adding Offline Sales:**
```tsx
import { queueSale } from '@/lib/offlineQueue';

const offlineSale = queueSale({
  items: [...],
  payments: [...],
  discount: 0,
  customer_id: 123,
});
```

### Testing Offline Mode

**In Browser DevTools:**
1. Open Network tab
2. Set throttling to "Offline"
3. Create a sale → Should queue locally
4. Go back Online
5. Should auto-sync

### Batch Sync API

**Endpoint**: `POST /api/v1/sales/batch-sync`

**Response (Success - 200):**
```json
{
  "synced": 1,
  "failed": 0,
  "results": [
    {
      "success": true,
      "offlineId": "uuid",
      "serverId": 42,
      "error": null
    }
  ]
}
```

---

## 🔐 Granular Permissions System

### Overview

Comprehensive granular permissions model for three roles: **Cashier**, **Manager**, and **Admin**. 30+ distinct permissions with inheritance.

### Permission Hierarchy

```
Admin (Full Access)
├── Manager
│   ├── Cashier
│   │   └── Basic POS Operations
```

### Roles & Permissions

#### 👨‍💼 Cashier / Clerk
Core POS operations for daily transactions.

**Permissions (9):**
- `PROCESS_SALES`, `PROCESS_PAYMENTS`, `REFUND_SALES`
- `VIEW_PRODUCTS`, `APPLY_DISCOUNTS`
- `VIEW_CUSTOMERS`, `CREATE_CUSTOMERS`, `UPDATE_CUSTOMERS`
- `VIEW_SALES_REPORTS`

#### 🔧 Manager
Inherits all Cashier permissions, plus (15 additional):
- `VOID_SALES`, `CREATE_PRODUCTS`, `UPDATE_PRODUCTS`
- `MANAGE_INVENTORY`, `MANAGE_CATEGORIES`
- `VIEW_DISCOUNTS`, `CREATE_DISCOUNTS`, `UPDATE_DISCOUNTS`
- `DELETE_CUSTOMERS`, `MANAGE_LOYALTY`
- `VIEW_INVENTORY_REPORTS`, `VIEW_CUSTOMER_REPORTS`, `EXPORT_REPORTS`
- `MANAGE_PAYMENT_METHODS`, `VIEW_AUDIT_LOG`

#### 👑 Admin
Inherits all Manager permissions, plus (9 additional):
- `DELETE_PRODUCTS`, `DELETE_DISCOUNTS`
- `VIEW_USERS`, `CREATE_USERS`, `UPDATE_USERS`, `DELETE_USERS`
- `MANAGE_ROLES`, `MANAGE_SETTINGS`, `VIEW_REPORTS`

### Backend Usage

**Option 1: Require specific permission**
```python
from app.core.deps import require_permission
from app.core.permissions import Permission

@router.post("")
def create_product(
    payload: ProductIn,
    db: Session = Depends(get_db),
    user=Depends(require_permission(Permission.CREATE_PRODUCTS))
):
    ...
```

**Option 2: Require ANY of multiple permissions**
```python
@router.post("")
def create_sale(
    payload: SaleIn,
    user=Depends(require_permission([Permission.PROCESS_SALES, Permission.PROCESS_PAYMENTS]))
):
    ...
```

**Option 3: Require ALL permissions**
```python
@router.post("")
def create_user(
    payload: UserIn,
    user=Depends(require_all_permissions([Permission.CREATE_USERS, Permission.MANAGE_ROLES]))
):
    ...
```

### Frontend Usage

**Using Permissions in Components:**
```typescript
import { useRoleCheck } from '@/store/auth';

export function ProductMenu() {
  const { canCreateProducts, canUpdateProducts, canDeleteProducts } = useRoleCheck();
  
  return (
    <>
      {canCreateProducts && <button>Add Product</button>}
      {canUpdateProducts && <button>Edit Product</button>}
      {canDeleteProducts && <button>Delete Product</button>}
    </>
  );
}
```

**Direct Permission Checks:**
```typescript
import { useAuth, Permission } from '@/store/auth';

export function AdminPanel() {
  const { hasPermission, hasAllPermissions } = useAuth();
  
  if (hasPermission(Permission.CREATE_PRODUCTS)) {
    // Show create product button
  }
  
  if (hasAllPermissions([Permission.MANAGE_SETTINGS, Permission.MANAGE_ROLES])) {
    // Show advanced admin settings
  }
}
```

### Files

**Backend:**
- `server/app/core/permissions.py` - Granular permissions definition
- `server/app/core/deps.py` - Permission checking dependencies

**Frontend:**
- `client/src/store/auth.ts` - Permission enum and checks

---

## 📊 End-of-Day Reports & Z-Reports

### Overview

Comprehensive end-of-day reporting system with Z-reports, sales summaries, and cash drawer reconciliation. Generate detailed daily reports for audit, compliance, and financial reconciliation.

### Features

#### 1. Z-Report (End-of-Day Report)
- Complete daily sales summary
- Payment method breakdown with percentages
- Top products analysis
- Refund and return statistics
- Shift timing information
- Employee count

#### 2. Cash Drawer Reconciliation
- Expected vs. actual cash comparison
- Automatic variance calculation
- Variance percentage tracking
- Notes for discrepancies
- Status indicators (reconciled, variance detected)

#### 3. Sales Summary
- Daily transaction count
- Total revenue and tax
- Discount tracking
- Items sold count
- Average transaction value

### Backend Endpoints

**Z-Report Endpoint:**
```
GET /api/v1/reports/z-report?report_date=YYYY-MM-DD
```

**Response:**
```json
{
  "report_date": "2025-12-11",
  "report_time": "18:30:45",
  "total_sales": 45,
  "total_revenue": 2450.75,
  "total_tax": 245.08,
  "total_discount": 50.00,
  "items_sold": 87,
  "total_refunds": 2,
  "total_returns": 1,
  "refund_amount": 125.50,
  "return_amount": 45.00,
  "payment_methods": [
    {
      "method": "card",
      "count": 30,
      "revenue": 1500.00,
      "percentage": 61.22
    },
    {
      "method": "cash",
      "count": 15,
      "revenue": 950.75,
      "percentage": 38.78
    }
  ],
  "top_products": [
    {
      "name": "Premium Product",
      "quantity": 12,
      "revenue": 480.00
    }
  ],
  "shift_start_time": "06:00:00",
  "shift_end_time": "18:30:45",
  "employee_count": 5
}
```

**Cash Reconciliation Endpoint:**
```
POST /api/v1/reports/z-report/reconcile?report_date=YYYY-MM-DD

Request:
{
  "actual_cash": 950.75,
  "notes": "Counted and verified"
}

Response:
{
  "report_date": "2025-12-11",
  "reconciliation": {
    "expected_cash": 950.75,
    "actual_cash": 950.75,
    "variance": 0.00,
    "variance_percentage": 0.00,
    "notes": "Counted and verified"
  },
  "status": "success",
  "message": "Cash drawer reconciled successfully"
}
```

**Sales Summary Endpoint:**
```
GET /api/v1/reports/sales-summary?report_date=YYYY-MM-DD
```

### Frontend Implementation

**Access EOD Reports:**
- Navigate to `/eod-reports` page
- Select report date (defaults to today)
- View comprehensive Z-report with all metrics
- Perform cash drawer reconciliation

**Z-Report Page Features:**
- Date selector for historical reports
- Summary cards (sales, revenue, discounts)
- Payment method breakdown table
- Refunds and returns section
- Top products list
- Cash reconciliation form
- Export options (text, print)

### Usage Examples

**Getting Today's Z-Report (Frontend):**
```typescript
import { Reports } from '@/lib/api';

const zReport = await Reports.zReport(); // Defaults to today
const summary = await Reports.salesSummary(); // Daily summary
```

**Getting Historical Z-Report:**
```typescript
const zReport = await Reports.zReport('2025-12-10');
const summary = await Reports.salesSummary('2025-12-10');
```

**Reconciling Cash Drawer:**
```typescript
const result = await Reports.reconcileCash(
  950.75,  // actual cash amount
  '2025-12-11',  // report date
  'Counted and verified'  // optional notes
);

if (result.status === 'success') {
  // Cash matches - no variance
} else {
  // Variance detected - review notes
}
```

### Backend Implementation

**Python Service:**
```python
@router.get("/z-report", response_model=ZReportData)
def get_z_report(
    report_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Get end-of-day Z-Report for a specific date"""
    # Defaults to today if no date provided
    if not report_date:
        report_date = datetime.now().strftime("%Y-%m-%d")
    
    # Calculate all metrics
    # Return comprehensive report
```

### Data Included in Z-Reports

1. **Sales Metrics**
   - Total number of transactions
   - Total revenue
   - Total tax collected
   - Total discounts applied
   - Items sold count

2. **Payment Breakdown**
   - Count per payment method
   - Revenue per payment method
   - Percentage distribution

3. **Product Analytics**
   - Top 10 products by revenue
   - Quantity sold per product
   - Revenue per product

4. **Refunds & Returns**
   - Count of refunds
   - Count of returns
   - Refund amount
   - Return amount

5. **Shift Information**
   - Shift start time
   - Shift end time
   - Employee count
   - Report generation time

### Cash Reconciliation Process

1. **System calculates expected cash:**
   - Sums all cash sales for the day
   - Excludes card, mobile, other methods

2. **Manager counts actual cash:**
   - Counts physical cash in drawer
   - Enters amount in reconciliation form

3. **System calculates variance:**
   - Compares expected vs. actual
   - Calculates percentage difference
   - Flags if variance exceeds tolerance

4. **Records reconciliation:**
   - Saves reconciliation record
   - Allows notes for discrepancies
   - Generates status report

### Variance Handling

**Acceptable Variance:** < $1.00 (or configurable)
- Status: ✅ Success
- Message: "Cash drawer reconciled successfully"

**Detected Variance:** >= $1.00
- Status: ⚠️ Variance Detected
- Message: Shows variance amount and percentage
- Recommendation: Review notes and investigate

### Compliance & Audit

- All Z-reports are timestamped
- Reports include employee information
- Cash reconciliation records maintained
- Historical reports available
- Export functionality for audits
- Print-friendly format

### API Reference

**Z-Report Endpoint**
- **Route:** `GET /api/v1/reports/z-report`
- **Authentication:** Required (JWT)
- **Parameters:** `report_date` (optional, YYYY-MM-DD)
- **Response:** ZReportData object

**Cash Reconciliation**
- **Route:** `POST /api/v1/reports/z-report/reconcile`
- **Authentication:** Required (JWT)
- **Body:** `actual_cash` (float), `notes` (optional string)
- **Response:** Reconciliation result with status

**Sales Summary**
- **Route:** `GET /api/v1/reports/sales-summary`
- **Authentication:** Required (JWT)
- **Parameters:** `report_date` (optional, YYYY-MM-DD)
- **Response:** Daily summary metrics

### Files

**Backend:**
- `server/app/api/v1/routers/reports.py` - Report endpoints
- `server/tests/test_eod_reports.py` - EOD report tests

**Frontend:**
- `client/src/app/eod-reports/page.tsx` - Z-report UI
- `client/src/lib/api.ts` - Report API functions

---

## 🛡️ Error Handling & CI/CD Pipeline Safety

### Overview

Error handling standards and CI/CD safeguards prevent pipeline failures due to unhandled errors or hardcoded error messages.

### Best Practices

#### 1. Use Error Constants (NOT Hardcoded Strings)

❌ **BAD:**
```python
raise HTTPException(status_code=400, detail="Coupon code already exists")
```

✅ **GOOD:**
```python
from app.core.error_constants import ErrorMessages, ErrorCodes
from app.core.errors import ConflictError

raise ConflictError(
    message=ErrorMessages.COUPON_CODE_EXISTS,
    details={"error_code": ErrorCodes.COUPON_001}
)
```

#### 2. Frontend Error Handling

❌ **BAD:**
```typescript
if (!res.ok) throw new Error("Failed to create payment");
```

✅ **GOOD:**
```typescript
import { ErrorMessages, formatApiError } from '@/lib/errorConstants';

if (!res.ok) {
  const error = await res.json();
  throw new Error(formatApiError(error));
}
```

#### 3. Consistent Error Response Format

```json
{
  "error": {
    "message": "Coupon code already exists",
    "code": "CONFLICT_001",
    "status_code": 409,
    "details": {
      "field": "code",
      "timestamp": "2025-12-11T18:00:00Z"
    }
  }
}
```

### CI/CD Pipeline Safety

#### ✅ What Won't Break the Pipeline

1. **No Hardcoded Error Strings** - All use centralized constants
2. **Standardized Error Format** - Consistent API responses
3. **Proper Exception Handling** - All errors caught and logged
4. **Permission Validation** - Backend enforces all checks
5. **Type Safety** - Python type hints + TypeScript strict mode

### Error Categories (63+ Messages)

- **Authentication**: Invalid token, Token expired, Invalid credentials
- **Users**: User not found, Already exists, Inactive, Invalid password
- **Products**: Not found, Already exists, Insufficient stock, Invalid quantity
- **Payments**: Failed, Invalid method, Amount mismatch, Processing error
- **Sales/Orders**: Not found, Already refunded, Cannot refund, Void not allowed
- **Validation**: Invalid request, Missing field, Invalid data type, Invalid date range
- **Network/Offline**: Network error, Timeout, Server error, Offline mode, Sync failed
- **Plus more**: Categories, Customers, Inventory, Rate Limiting, Database

### How to Use

**For Backend Developers:**

1. Import error constants:
   ```python
   from app.core.error_constants import ErrorMessages, ErrorCodes
   from app.core.errors import ConflictError, NotFoundError
   ```

2. Use instead of hardcoded strings:
   ```python
   raise ConflictError(message=ErrorMessages.COUPON_CODE_EXISTS)
   ```

**For Frontend Developers:**

1. Import error utilities:
   ```typescript
   import { ErrorMessages, formatApiError, retryWithBackoff } from '@/lib/errorConstants';
   ```

2. Format API errors:
   ```typescript
   if (!res.ok) {
     const error = await res.json();
     throw new Error(formatApiError(error));
   }
   ```

3. Implement retry logic:
   ```typescript
   await retryWithBackoff(() => createPayment(data), 3, 1000);
   ```

### Files

**Backend:**
- `server/app/core/error_constants.py` - Error message constants
- `server/app/core/errors.py` - Custom exception classes
- `server/app/core/deps.py` - Permission checking

**Frontend:**
- `client/src/lib/errorConstants.ts` - Error message constants
- `client/src/lib/api.ts` - API error handling

---

## 🔐 Security

### Default Development Credentials
- **Email:** `admin@vendly.com`
- **Password:** `admin123`

⚠️ **IMPORTANT:** Change these immediately in production!

### Security Features
- ✅ bcrypt password hashing
- ✅ JWT authentication
- ✅ Granular permissions system
- ✅ Rate limiting
- ✅ Audit logging
- ✅ Input validation (Pydantic)
- ✅ SQL injection prevention

### Security Best Practices
- No information leakage (stack traces never exposed)
- Generic error messages for sensitive operations
- Detailed logging only in server logs
- Consistent error format across API
- All errors are properly typed and validated

---

## 🛠️ Common Commands

```bash
# Development
npm run dev              # Start frontend and backend
npm run dev:client       # Start frontend only
npm run dev:server       # Start backend only

# Building
npm run build            # Build client
npm run setup            # Install dependencies

# Docker
docker-compose up -d     # Start all services
docker-compose down      # Stop all services
docker-compose logs -f   # View logs

# Testing
npm run test             # Run all tests
npm run test:client      # Frontend tests
npm run test:server      # Backend tests
```

---

## 📊 Monitoring & Observability

### Health Checks
- Frontend health: http://localhost:3000/health
- Backend health: http://localhost:8000/health
- API Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Prometheus Metrics
- Backend metrics: http://localhost:8000/metrics
- Prometheus UI: http://localhost:9090
- Grafana: http://localhost:3001 (admin/admin)

---

## 📖 Feature Documentation

### Frontend Features
- **POS**: Sales transactions, payments, receipts
- **Inventory**: Product management, stock tracking
- **Customers**: Customer profiles, loyalty points
- **Reports**: Sales analytics, inventory reports, customer insights
- **Settings**: System configuration, payment methods
- **Admin Panel**: User management, role assignment, audit logs

### Backend APIs
All backend endpoints documented in Swagger UI:
- **Swagger**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Available Endpoints
- `/api/v1/sales` - Sales management
- `/api/v1/products` - Product catalog
- `/api/v1/customers` - Customer management
- `/api/v1/payments` - Payment processing
- `/api/v1/reports` - Analytics and reporting
- `/api/v1/users` - User management
- `/api/v1/ai` - AI features

---

## 🤝 Contributing

1. Create a feature branch
2. Make your changes
3. Ensure no TypeScript/Python errors
4. Test thoroughly
5. Submit a pull request

### Code Quality Standards

- Use error constants instead of hardcoded strings
- Implement proper permission checks
- Add comprehensive error handling
- Follow TypeScript strict mode
- Include Python type hints
- Test edge cases

---

## 📞 Support

For issues, questions, or suggestions:
1. Check existing documentation (this file)
2. Review API docs at http://localhost:8000/docs
3. Check browser console and backend logs
4. File an issue on GitHub

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 📝 Last Updated
December 11, 2025

**Documentation Status**: ✅ **COMPLETE & CONSOLIDATED**

All documentation has been consolidated into this single comprehensive README.md file covering:
- System architecture and project structure
- Offline mode implementation and API
- Granular permissions system
- Error handling standards and CI/CD safety
- Security best practices
- Quick start and common commands
- Monitoring and feature documentation

This is your one-stop reference for everything you need to know about Vendly POS!
