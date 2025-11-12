# API Documentation

## Base URL
- Development: `http://localhost:8000`
- Production: `https://api.vendly.com`

## Authentication

All API endpoints except `/auth/login` and `/auth/register` require authentication via JWT token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

## Endpoints

### Authentication

#### POST `/api/v1/auth/login`
Login with email and password.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "bearer",
    "expires_in": 3600
  }
}
```

#### POST `/api/v1/auth/register`
Register a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123",
  "first_name": "John",
  "last_name": "Doe"
}
```

### Products

#### GET `/api/v1/products`
Get all products with optional filtering and pagination.

**Query Parameters:**
- `page` (integer): Page number (default: 1)
- `limit` (integer): Items per page (default: 20)
- `category` (string): Filter by category ID
- `search` (string): Search in product name and description

#### POST `/api/v1/products`
Create a new product.

**Request Body:**
```json
{
  "name": "Product Name",
  "description": "Product description",
  "price": 29.99,
  "sku": "PROD-001",
  "barcode": "1234567890123",
  "category_id": "cat-id",
  "stock": 100,
  "min_stock": 10
}
```

#### GET `/api/v1/products/{product_id}`
Get a specific product by ID.

#### PUT `/api/v1/products/{product_id}`
Update a product.

#### DELETE `/api/v1/products/{product_id}`
Delete a product.

### Sales

#### GET `/api/v1/sales`
Get all sales with filtering and pagination.

#### POST `/api/v1/sales`
Create a new sale.

**Request Body:**
```json
{
  "items": [
    {
      "product_id": "prod-id",
      "quantity": 2,
      "unit_price": 29.99
    }
  ],
  "payment_method": "card",
  "customer_id": "customer-id"
}
```

#### GET `/api/v1/sales/{sale_id}`
Get a specific sale by ID.

### Reports

#### GET `/api/v1/reports/sales-summary`
Get sales summary for a date range.

**Query Parameters:**
- `start_date` (date): Start date (YYYY-MM-DD)
- `end_date` (date): End date (YYYY-MM-DD)
- `group_by` (string): Group by 'day', 'week', or 'month'

## WebSocket Connection

Connect to `/ws` for real-time updates:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');
```

### WebSocket Events

- `sale_created`: New sale completed
- `inventory_updated`: Product stock changed
- `user_activity`: User logged in/out

## Error Handling

All endpoints return errors in this format:

```json
{
  "success": false,
  "message": "Error description",
  "detail": "Detailed error information"
}
```

### HTTP Status Codes

- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `422` - Validation Error
- `500` - Internal Server Error