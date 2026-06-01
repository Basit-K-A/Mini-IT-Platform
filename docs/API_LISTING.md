# List endpoints — pagination, filters, sorting

All primary collection endpoints return:

```json
{
  "data": [],
  "pagination": {
    "total_records": 100,
    "total_pages": 10,
    "current_page": 1,
    "page_size": 10
  }
}
```

## Devices `GET /devices`

| Parameter | Description |
|-----------|-------------|
| `page`, `limit` | Pagination (default page=1, limit=10, max limit=100) |
| `status` | Enum: active, online, offline, maintenance, inactive |
| `department` | Exact match (e.g. IT) |
| `owner_id` / `assigned_to` | Owner user id |
| `hostname` | Substring search (case-insensitive) |
| `operating_system` | Exact match |
| `sort_by` | id, hostname, status, department, owner_id, created_at, ip_address, operating_system |
| `sort_order` | asc or desc (default desc) |

Examples:

```
GET /devices?page=1&limit=10
GET /devices?status=active&department=IT
GET /devices?assigned_to=123&sort_by=created_at&sort_order=desc
```

## Events `GET /events`

Filters: `device_id`, `severity`, `event_type`, `message_contains`  
Sort: `id`, `timestamp`, `event_type`, `severity`, `device_id` (default `timestamp` desc)

## Audit logs `GET /audit-logs`

Filters: `action`, `user_id`, `ip_address`, `status_code`, `endpoint_contains`  
Requires admin or analyst role.

## Users `GET /users`

Filters: `role`, `is_active`, `username`, `email`  
Admin only.
