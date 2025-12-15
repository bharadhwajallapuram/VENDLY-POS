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
8. [Cloud Backup System](#-cloud-backup-system)
9. [Tax Management (GST/VAT)](#-tax-management-gstvat)
10. [Legal Documents (Privacy & Terms)](#-legal-documents-privacy--terms)
11. [Error Handling & CI/CD](#-error-handling--cicd-pipeline-safety)
12. [Security](#-security)
13. [Common Commands](#-common-commands)
14. [Monitoring & Observability](#-monitoring--observability)
15. [Feature Documentation](#-feature-documentation)
16. [Contributing](#-contributing)
17. [Support](#-support)

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

## ☁️ Cloud Backup System

### Overview

A comprehensive, production-ready cloud backup system for Vendly POS that automatically backs up sales and inventory data to AWS S3, Azure Blob Storage, Google Cloud Storage, or local storage. Includes scheduled execution, retention policies, complete audit logging, and a full REST API for management.

### ✨ Key Features

✅ **Multi-Cloud Support**: AWS S3, Azure Blob Storage, Google Cloud Storage, Local filesystem
✅ **Automatic Scheduling**: Hourly, Daily, Weekly, Monthly with configurable times
✅ **Selective Backups**: Sales data, Inventory data, or Full backup
✅ **Data Protection**: Gzip compression (70-90%), HTTPS/TLS, cloud encryption
✅ **Retention Management**: Configurable 1-365 day retention with auto-cleanup
✅ **Audit & Compliance**: Complete execution history, error tracking, admin-only access
✅ **REST API**: 12+ endpoints for full backup management
✅ **Production Ready**: Comprehensive testing, error handling, security

### 🚀 Quick Start (5 minutes)

#### 1. Install Dependencies
```bash
pip install boto3 azure-storage-blob google-cloud-storage apscheduler
```

#### 2. Set Environment Variables (Local Storage for Testing)
```bash
export BACKUP_ENABLED=true
export BACKUP_PROVIDER=local
export BACKUP_LOCAL_PATH=./backups
export SCHEDULER_ENABLED=true
```

#### 3. Run Database Migration
```bash
cd server
alembic upgrade head
```

#### 4. Start Application
```bash
python -m uvicorn app.main:app --reload
```

#### 5. Create Your First Backup Job
```bash
curl -X POST "http://localhost:8000/api/v1/backups/jobs" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Daily Sales Backup",
    "backup_type": "sales",
    "schedule_type": "daily",
    "schedule_time": "02:00",
    "retention_days": 30,
    "is_enabled": true
  }'
```

#### 6. Trigger Manual Backup
```bash
curl -X POST "http://localhost:8000/api/v1/backups/sales" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### 7. Check Status
```bash
curl -X GET "http://localhost:8000/api/v1/backups/status" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Architecture

#### System Components

```
FastAPI Application
  ↓
REST API (/api/v1/backups)
  ↓
CloudBackupService (backup.py)
  ├─ backup_sales_data()
  ├─ backup_inventory_data()
  ├─ backup_all_data()
  ├─ restore_backup()
  └─ list_backups()
  ↓
BackupScheduler (backup_scheduler.py)
  ├─ APScheduler Jobs
  ├─ Hourly/Daily/Weekly/Monthly schedules
  └─ Auto-execution & cleanup
  ↓
Cloud Storage Providers
  ├─ AWS S3 (boto3)
  ├─ Azure Blob Storage
  ├─ Google Cloud Storage
  └─ Local Filesystem
  ↓
Database (SQLAlchemy)
  ├─ backup_jobs (scheduled job definitions)
  └─ backup_logs (execution history)
```

#### Data Flow

**Manual Backup**:
User Request → API Validation → Database Query → Serialize Data → Compress → Cloud Upload → Log Entry

**Scheduled Backup**:
APScheduler Trigger → Load Job → Execute Backup → Cloud Upload → Log Entry → Auto-cleanup Old

**Restore**:
Cloud Download → Decompress → Deserialize → Database Import → Validation

### API Endpoints

#### Backup Operations

##### POST /api/v1/backups/sales
Trigger sales data backup (optional date range)
```bash
curl -X POST "http://localhost:8000/api/v1/backups/sales" \
  -H "Authorization: Bearer TOKEN"
```

Query Parameters:
- `start_date`: Optional ISO datetime
- `end_date`: Optional ISO datetime

Response:
```json
{
  "backup_id": "sales_20241215_020000_a1b2c3d4",
  "type": "sales",
  "status": "completed",
  "records": 1250,
  "file_key": "backups/sales/sales_20241215_020000_a1b2c3d4.json.gz",
  "timestamp": "2024-12-15T02:00:00"
}
```

##### POST /api/v1/backups/inventory
Trigger inventory backup
```bash
curl -X POST "http://localhost:8000/api/v1/backups/inventory" \
  -H "Authorization: Bearer TOKEN"
```

##### POST /api/v1/backups/full
Trigger full backup (all data)
```bash
curl -X POST "http://localhost:8000/api/v1/backups/full" \
  -H "Authorization: Bearer TOKEN"
```

##### GET /api/v1/backups/list
List all available backups
```bash
curl -X GET "http://localhost:8000/api/v1/backups/list" \
  -H "Authorization: Bearer TOKEN"
```

Query Parameters:
- `backup_type`: Optional filter (sales, inventory)

##### POST /api/v1/backups/restore/{backup_id}
Restore from specific backup
```bash
curl -X POST "http://localhost:8000/api/v1/backups/restore/sales_20241215_020000_a1b2c3d4" \
  -H "Authorization: Bearer TOKEN"
```

##### DELETE /api/v1/backups/cleanup
Delete backups older than retention period
```bash
curl -X DELETE "http://localhost:8000/api/v1/backups/cleanup?retention_days=30" \
  -H "Authorization: Bearer TOKEN"
```

#### Scheduled Job Management

##### POST /api/v1/backups/jobs
Create scheduled backup job
```bash
curl -X POST "http://localhost:8000/api/v1/backups/jobs" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Daily Sales Backup",
    "backup_type": "sales",
    "schedule_type": "daily",
    "schedule_time": "02:00",
    "retention_days": 30,
    "is_enabled": true
  }'
```

Schedule Types:
- `hourly` - Every hour at minute 0
- `daily` - Every day at configured time (default: 02:00)
- `weekly` - Every Sunday at configured time
- `monthly` - 1st of month at configured time

##### GET /api/v1/backups/jobs
List all backup jobs
```bash
curl -X GET "http://localhost:8000/api/v1/backups/jobs" \
  -H "Authorization: Bearer TOKEN"
```

##### GET /api/v1/backups/jobs/{job_id}
Get specific job details
```bash
curl -X GET "http://localhost:8000/api/v1/backups/jobs/1" \
  -H "Authorization: Bearer TOKEN"
```

##### PUT /api/v1/backups/jobs/{job_id}
Update job
```bash
curl -X PUT "http://localhost:8000/api/v1/backups/jobs/1" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "schedule_time": "03:00",
    "retention_days": 45,
    "is_enabled": true
  }'
```

##### DELETE /api/v1/backups/jobs/{job_id}
Delete job
```bash
curl -X DELETE "http://localhost:8000/api/v1/backups/jobs/1" \
  -H "Authorization: Bearer TOKEN"
```

#### Logs & Monitoring

##### GET /api/v1/backups/logs
View backup logs with pagination and filtering
```bash
curl -X GET "http://localhost:8000/api/v1/backups/logs?limit=10&offset=0" \
  -H "Authorization: Bearer TOKEN"
```

Query Parameters:
- `limit`: 1-500 (default: 50)
- `offset`: 0+ (default: 0)
- `backup_type`: Filter by type (sales, inventory)
- `status`: Filter by status (pending, completed, failed)

##### GET /api/v1/backups/logs/{backup_id}
Get specific log entry
```bash
curl -X GET "http://localhost:8000/api/v1/backups/logs/sales_20241215_020000_a1b2c3d4" \
  -H "Authorization: Bearer TOKEN"
```

##### GET /api/v1/backups/status
Get backup system status
```bash
curl -X GET "http://localhost:8000/api/v1/backups/status" \
  -H "Authorization: Bearer TOKEN"
```

Response:
```json
{
  "service_initialized": true,
  "provider": "s3",
  "total_backups": 45,
  "successful_backups": 43,
  "failed_backups": 2,
  "last_backup_time": "2024-12-15T02:00:00",
  "enabled_jobs": 3
}
```

### Configuration

#### AWS S3
```bash
export BACKUP_PROVIDER=s3
export BACKUP_BUCKET=my-vendly-backups
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_REGION=us-east-1
```

#### Azure Blob Storage
```bash
export BACKUP_PROVIDER=azure
export BACKUP_BUCKET=vendly-backups
export AZURE_STORAGE_CONNECTION_STRING=your_connection_string
```

#### Google Cloud Storage
```bash
export BACKUP_PROVIDER=gcs
export BACKUP_BUCKET=vendly-backups
export GCS_PROJECT_ID=your_project_id
export GCS_CREDENTIALS=/path/to/service-account-key.json
```

#### Local (Development)
```bash
export BACKUP_PROVIDER=local
export BACKUP_LOCAL_PATH=./backups
```

### Database Models

#### BackupJob
Stores scheduled backup job definitions
- Job configuration and schedule
- Last run status
- Next scheduled execution
- Retention policy

#### BackupLog  
Complete audit trail of backup executions
- Backup metadata
- Execution status
- Error messages
- Cloud file locations
- Record counts

### Security

✅ Admin-only API access (role-based)
✅ Token authentication (JWT)
✅ HTTPS/TLS for data in transit
✅ Cloud provider encryption at rest
✅ Environment-based credential management
✅ No sensitive data in logs
✅ Complete audit trail

### Performance

- **Backup Duration**: 1-5 sec (typical POS data)
- **Compression Ratio**: 70-90%
- **Memory Usage**: ~50 MB
- **CPU Usage**: <1%
- **Network**: 50-500 MB/s

### Testing

Comprehensive test suite included:
```bash
cd server
pytest tests/test_backup.py -v
```

Tests cover:
- Backup operations
- Scheduling
- Error handling
- Cloud provider integration
- Database models

### File Structure

```
server/
├── app/
│   ├── services/
│   │   ├── backup.py              (700+ lines)
│   │   └── backup_scheduler.py    (400+ lines)
│   ├── api/v1/routers/
│   │   └── backups.py             (300+ lines)
│   ├── schemas/
│   │   └── backup.py              (100+ lines)
│   ├── db/models.py               (+ BackupJob, BackupLog)
│   ├── core/config.py             (+ backup settings)
│   └── main.py                    (+ scheduler init)
├── alembic/versions/
│   └── backup_tables_001.py
├── tests/
│   └── test_backup.py             (300+ lines)
└── requirements.txt               (updated)
```

### Deployment

#### Development
```bash
BACKUP_PROVIDER=local
SCHEDULER_ENABLED=true
BACKUP_RETENTION_DAYS=7
```

#### Staging
```bash
BACKUP_PROVIDER=s3
SCHEDULER_ENABLED=true
BACKUP_RETENTION_DAYS=30
```

#### Production
```bash
BACKUP_PROVIDER=s3  # or azure/gcs
BACKUP_SCHEDULE_TYPE=daily
BACKUP_SCHEDULE_TIME=02:00
BACKUP_RETENTION_DAYS=90
SCHEDULER_ENABLED=true
```

### Scalability

✅ Handles 1M+ transactions
✅ Supports large deployments
✅ Configurable batch processing
✅ Connection pooling
✅ Background task execution
✅ No blocking of main API

### Disaster Recovery

Complete disaster recovery support:
1. **List available backups** - API endpoint
2. **Select backup** - Choose from history
3. **Restore** - One API call
4. **Verify** - Data validation
5. **Monitor** - Status tracking

### Troubleshooting

#### Issue: Backup fails with authentication error
- Verify cloud provider credentials in environment variables
- Check IAM permissions for bucket access
- Ensure credentials have not expired

#### Issue: Scheduler not running
- Verify `SCHEDULER_ENABLED=true` in environment
- Check backend logs for scheduler initialization
- Restart application to reload scheduler

#### Issue: Restore returns 404
- Verify backup ID is correct
- Check backup still exists in cloud storage
- Ensure retention period has not expired

#### Issue: Out of disk space on local backups
- Verify `BACKUP_LOCAL_PATH` has sufficient space
- Reduce `BACKUP_RETENTION_DAYS`
- Run cleanup endpoint to remove old backups

### Production Checklist

- [ ] Cloud provider credentials configured
- [ ] Environment variables set (BACKUP_PROVIDER, bucket, credentials)
- [ ] Database migration applied (alembic upgrade head)
- [ ] Backup jobs created and enabled
- [ ] Manual backup tested successfully
- [ ] Restore procedure tested on test database
- [ ] Scheduler verified running
- [ ] Retention policy configured
- [ ] Logs accessible and monitored
- [ ] Backup coverage meets compliance requirements

### Production Ready ✅

- [x] Multi-cloud support
- [x] Automatic scheduling
- [x] Complete REST API
- [x] Database models
- [x] Error handling
- [x] Audit logging
- [x] Security features
- [x] Comprehensive testing

---

## 💰 Tax Management (GST/VAT)

### Overview

Vendly POS includes comprehensive tax management supporting multiple global tax systems including:
- **GST** (India, Australia, New Zealand, Singapore)
- **VAT** (UK, EU countries)
- **Sales Tax** (US states, Canada)
- **Custom tax rates** for other regions

### Key Features

#### 1. Multi-Region Tax Support
```
Supported Regions:
- India (GST): CGST, SGST, IGST
- Australia (GST): Single rate
- New Zealand (GST): Single rate
- Singapore (GST): Single rate
- UK (VAT): Standard & reduced rates
- EU (VAT): Standard rates
- Canada: GST/HST
- US: State-based sales tax
- Other: Custom regions
```

#### 2. Flexible Tax Configuration
- **Tax Rates Management**: Create, update, and manage tax rates by region
- **Effective Dates**: Set when rates become active/inactive
- **State-Level Support**: US state codes for granular control
- **Compound Tax**: Support for multi-tier taxes (India GST with CGST + SGST)
- **Reverse Charge**: Enable/disable reverse charge mechanism
- **Tax Invoicing**: Generate tax-compliant invoices

#### 3. Tax Calculations
- **Simple Tax**: Single tax rate application
- **Compound Tax**: Multiple taxes applied in sequence (e.g., CGST + SGST = 18%)
- **Rounding Methods**: Round, truncate, or ceiling options
- **Tax Exemption**: Mark customers as tax-exempt
- **Audit Trail**: All calculations recorded for compliance

#### 4. Tax Reporting
- **By Region**: Aggregate tax collection by region
- **By Tax Type**: GST, VAT, Sales Tax breakdowns
- **By Rate**: Summary by individual rate
- **Date Ranges**: Filter reports by date period
- **Export Ready**: Data suitable for tax filing

### API Endpoints

#### Tax Rates
```bash
# Get tax rates
GET /api/v1/tax/rates?region=in&tax_type=gst

# Create new tax rate (admin only)
POST /api/v1/tax/rates
{
  "region": "in",
  "tax_type": "gst",
  "name": "CGST",
  "rate": 9.0
}

# Update tax rate
PUT /api/v1/tax/rates/{rate_id}
{
  "rate": 9.0,
  "is_active": true
}
```

#### Tax Configuration
```bash
# Get store tax config
GET /api/v1/tax/config/{region}

# Update configuration
PUT /api/v1/tax/config/{config_id}
{
  "tax_id": "27AAPFU0142R1Z0",
  "enable_compound_tax": true,
  "enable_tax_invoice": true
}
```

#### Tax Calculations
```bash
# Calculate single tax
POST /api/v1/tax/calculate?subtotal=1000&tax_rate_id=5
Response: { "tax_amount": 90, "tax_rate": 9.0, "tax_type": "gst" }

# Calculate compound tax (GST)
POST /api/v1/tax/calculate-compound?subtotal=1000&tax_rate_ids=1,2
Response: {
  "total_tax": 180,
  "subtotal": 1000,
  "total_with_tax": 1180,
  "calculations": [...]
}
```

#### Tax Reports
```bash
# Get tax report by region
GET /api/v1/tax/report?region=in&start_date=2024-01-01&end_date=2024-12-31

# Get summary by tax rate
GET /api/v1/tax/report/by-rate?start_date=2024-01-01
```

### Database Models

```python
# Tax rates configuration
class TaxRate(Base):
    id: int
    region: str  # in, au, uk, us, ca, etc.
    tax_type: str  # gst, vat, sales_tax
    name: str  # CGST, SGST, Standard VAT, etc.
    rate: float  # 9.0, 18.0, 20.0, etc.
    state_code: Optional[str]  # CA, NY, etc.
    is_active: bool
    effective_from: datetime
    effective_to: Optional[datetime]

# Store-level configuration
class TaxConfiguration(Base):
    id: int
    user_id: int
    region: str
    tax_id: Optional[str]  # GST ID, VAT ID
    is_tax_exempt: bool
    enable_compound_tax: bool
    enable_reverse_charge: bool
    enable_tax_invoice: bool
    rounding_method: str

# Audit trail for tax calculations
class TaxCalculation(Base):
    id: int
    sale_id: int
    tax_rate_id: int
    subtotal: float
    tax_amount: float
    tax_rate: float
    tax_type: str
    is_compound: bool
    created_at: datetime
```

### Setup Example: India GST

```python
from app.services.tax_service import TaxService, setup_default_tax_rates

# Initialize database with default rates
setup_default_tax_rates(db)

# Get service
tax_service = TaxService(db)

# Create config
config = tax_service.get_or_create_config(user_id=1, region="in")
tax_service.update_config(
    config.id,
    tax_id="27AAPFU0142R1Z0",
    enable_compound_tax=True
)

# Calculate GST (CGST 9% + SGST 9%)
result = tax_service.calculate_compound_tax(
    subtotal=1000.0,
    tax_rate_ids=[1, 2]  # CGST and SGST
)
# Result: total_tax=180, total_with_tax=1180
```

### Integration with Sales

Tax calculations are automatically integrated into the sales workflow:
1. When creating a sale, the system determines applicable tax rates
2. Tax is calculated and recorded
3. Receipt includes tax breakdown
4. Calculation is logged for reporting

---

## 📜 Legal Documents (Privacy & Terms)

### Overview

Vendly POS provides a complete legal documents management system for:
- **Privacy Policy**: Inform users about data collection and usage
- **Terms of Service**: Establish usage agreements
- **Return Policy**: Define return and exchange procedures
- **Warranty Policy**: Document product warranties
- **Cookie Policy**: Explain cookie usage

### Key Features

#### 1. Document Management
- **Versioning**: Track all document versions
- **Active/Inactive**: Only active documents are shown to users
- **HTML Rendering**: Store both markdown and rendered HTML
- **Display Order**: Control the order in which documents appear
- **Acceptance Required**: Mark documents that require user acceptance

#### 2. Consent Tracking
- **User Acceptance**: Track which employees accepted documents
- **Customer Acceptance**: Track customer acceptance (during login/signup)
- **IP & User Agent**: Record device info for compliance
- **Timestamp Logging**: Know exactly when acceptance occurred
- **Acceptance Report**: Generate compliance reports

#### 3. Consent Workflows
- **Get Required Consents**: Fetch all documents requiring acceptance
- **Get Pending Consents**: Show documents user hasn't accepted yet
- **Accept Single Document**: Record acceptance of one document
- **Accept All**: Batch accept all required documents (e.g., during onboarding)

#### 4. Compliance & Audit
- **Audit Trail**: All acceptances logged with timestamps
- **Acceptance Reports**: Count acceptances by document and date
- **Version Tracking**: Know which version was accepted
- **GDPR Ready**: Supports data collection consents

### API Endpoints

#### Document Management
```bash
# Create new document version
POST /api/v1/legal/documents
{
  "doc_type": "privacy_policy",
  "title": "Privacy Policy",
  "content": "# Our Privacy Policy\n...",
  "requires_acceptance": true
}

# Get all active documents
GET /api/v1/legal/documents

# Get specific document type (latest active version)
GET /api/v1/legal/documents/type/privacy_policy

# Get all versions of a document
GET /api/v1/legal/documents/type/privacy_policy/versions

# Update a document
PUT /api/v1/legal/documents/{doc_id}
{
  "title": "Privacy Policy v2",
  "content": "Updated content..."
}
```

#### Consent Management
```bash
# Get all required consents (with acceptance status)
GET /api/v1/legal/consent
Response: [
  {
    "id": 1,
    "doc_type": "privacy_policy",
    "title": "Privacy Policy",
    "content": "...",
    "version": 2,
    "requires_acceptance": true,
    "has_accepted": false
  }
]

# Get pending documents (not yet accepted)
GET /api/v1/legal/pending-consents
Response: [...]

# Accept single document
POST /api/v1/legal/accept/{doc_id}
Response: { "id": 1, "legal_document_id": 1, "accepted_at": "2024-12-15..." }

# Accept all required documents at once
POST /api/v1/legal/accept-all
Response: [{ acceptance1 }, { acceptance2 }, ...]

# Get user's acceptance history
GET /api/v1/legal/user-acceptances
Response: [...]
```

#### Reporting
```bash
# Get acceptance statistics
GET /api/v1/legal/report/acceptance/privacy_policy?start_date=2024-01-01
Response: {
  "doc_type": "privacy_policy",
  "total_acceptances": 125,
  "by_users": 45,
  "by_customers": 80,
  "first_acceptance": "2024-01-05T10:30:00",
  "last_acceptance": "2024-12-15T14:22:00"
}
```

### Database Models

```python
# Legal documents with versioning
class LegalDocument(Base):
    id: int
    doc_type: str  # privacy_policy, terms_of_service, etc.
    version: int
    title: str
    content: str  # Markdown
    content_html: Optional[str]  # Rendered HTML
    is_active: bool
    requires_acceptance: bool
    display_order: int
    created_by_user_id: int
    created_at: datetime
    updated_at: datetime

# Track who accepted what document
class LegalDocumentAcceptance(Base):
    id: int
    legal_document_id: int
    user_id: Optional[int]  # Employee
    customer_id: Optional[int]  # Customer
    ip_address: Optional[str]
    user_agent: Optional[str]
    accepted_at: datetime
```

### Setup Example

```python
from app.services.legal_service import LegalService, setup_default_documents

# Initialize with default documents
setup_default_documents(db, admin_user_id=1)

# Get service
legal_service = LegalService(db)

# Create new document
doc = legal_service.create_document(
    doc_type="privacy_policy",
    title="Privacy Policy v2",
    content="Updated privacy policy content...",
    created_by_user_id=1,
    requires_acceptance=True
)

# Get pending consents for user
pending = legal_service.get_pending_consents(user_id=user.id)

# User accepts all required documents
acceptances = legal_service.accept_all_required(
    user_id=user.id,
    ip_address=request.client.host,
    user_agent=request.headers.get("user-agent")
)

# Generate acceptance report
report = legal_service.get_acceptance_report(
    "privacy_policy",
    start_date=datetime(2024, 1, 1)
)
```

### Frontend Integration

```typescript
import { Legal } from '@/lib/api';

// Get pending consents to show on login
const pending = await Legal.getPendingConsents();

if (pending.length > 0) {
  // Show consent modal
  showConsentModal(pending);
}

// User accepts
await Legal.acceptAll();

// Get acceptance history
const history = await Legal.getUserAcceptances();
```

### Compliance Checklist

- [x] Privacy Policy management
- [x] Terms of Service versioning
- [x] Acceptance tracking
- [x] GDPR-ready consent workflow
- [x] Audit trail with timestamps
- [x] IP and device logging
- [x] Acceptance reports
- [x] Multiple document types
- [x] HTML and markdown support
- [x] Automatic default documents

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

### Error Tracking (Sentry)

**Setup:**
1. Create Sentry project at https://sentry.io
2. Add to `.env`:
   ```env
   SENTRY_ENABLED=true
   SENTRY_DSN=https://your-key@sentry.io/project-id
   SENTRY_ENVIRONMENT=production
   SENTRY_TRACES_SAMPLE_RATE=0.1
   ```
3. Add to `client/.env.local`:
   ```env
   NEXT_PUBLIC_SENTRY_DSN=https://your-key@sentry.io/project-id
   NEXT_PUBLIC_SENTRY_ENVIRONMENT=production
   ```

**Features:**
- Real-time error notification with stack traces
- Performance monitoring (P95, P99 latencies)
- User session tracking and breadcrumbs
- Automatic sensitive data filtering
- Release version tracking

**Using Sentry:**
```python
# Backend: Errors are automatically captured
# Manual capture:
from app.core.error_tracking import sentry_config
sentry_config.capture_exception(error, context={"user_id": 123})
sentry_config.capture_message("Important event", level="warning")
```

```typescript
// Frontend: Automatic error capture
import { captureException, addBreadcrumb } from "@/lib/sentry";
captureException(error, { page: "/checkout" });
addBreadcrumb("User started checkout", "user-action");
```

### Health Check Endpoints

**Kubernetes-Ready Health Checks:**

| Endpoint | Purpose | Status Code |
|----------|---------|-------------|
| `GET /api/v1/health/` | Basic health (load balancer) | 200 OK |
| `GET /api/v1/health/live` | Liveness probe (K8s) | 200/503 |
| `GET /api/v1/health/ready` | Readiness probe (K8s) | 200/503 |
| `GET /api/v1/health/startup` | Startup probe (K8s) | 200/503 |
| `GET /api/v1/health/detailed` | Complete system status | 200/503 |

**Test locally:**
```bash
curl http://localhost:8000/api/v1/health/detailed | jq
```

**Response includes:**
- API status
- Database connectivity and response time
- Redis cache status and memory usage
- Kafka connectivity (if enabled)
- Overall system status

### Automated Database Backups

**Configuration:**
```env
BACKUP_ENABLED=true
BACKUP_PROVIDER=local              # local, s3, azure, gcs
BACKUP_LOCAL_PATH=./backups
BACKUP_SCHEDULE_TYPE=daily         # hourly, daily, weekly, monthly
BACKUP_SCHEDULE_TIME=02:00
BACKUP_RETENTION_DAYS=30
SCHEDULER_ENABLED=true
```

**Commands:**
```bash
# Create backup
python scripts/backup_manager.py backup --db-url $DATABASE_URL

# List backups
python scripts/backup_manager.py list --backup-path ./backups

# Verify backup integrity
python scripts/backup_manager.py verify --backup ./backups/vendly_backup_20240115_023000.sql.gz

# Restore from backup
python scripts/backup_manager.py restore --backup ./backups/vendly_backup_20240115_023000.sql.gz
```

**Cloud Backup (AWS S3):**
```env
BACKUP_PROVIDER=s3
AWS_ACCESS_KEY_ID=xxx
AWS_SECRET_ACCESS_KEY=xxx
AWS_REGION=us-east-1
BACKUP_BUCKET=vendly-backups
```

### Docker & Kubernetes Health Monitoring

**Docker:**
- Health checks configured in Dockerfile
- Status visible in `docker ps` output
- Use: `docker compose -f docker-compose.health.yml up`

**Kubernetes:**
- Liveness probe: Restarts unhealthy pods
- Readiness probe: Removes from service load balancer
- Startup probe: Gives apps time to initialize
- All probes use the health endpoints above

**Monitor K8s:**
```bash
kubectl get pods -w                          # Watch pod status
kubectl describe pod <pod-name>              # View probe details
kubectl logs <pod-name>                      # Check logs
kubectl get events --sort-by='.lastTimestamp'  # View events
```

### Prometheus Metrics
- Backend metrics: http://localhost:8000/metrics
- Prometheus UI: http://localhost:9090
- Grafana: http://localhost:3001 (admin/admin)
- Dashboard: Import `monitoring/grafana-dashboard.json`

### Quick Testing

```bash
# Test all health endpoints
python scripts/test_monitoring.py

# Test with custom URL
python scripts/test_monitoring.py --base-url http://localhost:8000

# Test backups
python scripts/backup_manager.py list
```

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
