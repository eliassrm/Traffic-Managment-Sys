# Traffic Management System

## Authentication

This project uses JWT authentication with the following endpoints:

- `POST /api/auth/token/`
- `POST /api/auth/token/refresh/`
- `POST /api/auth/token/verify/`
- `GET /api/auth/me/`

### Get JWT token (bash)

```bash
curl -X POST http://127.0.0.1:8000/api/auth/token/ \
	-H "Content-Type: application/json" \
	-d '{"username":"YOUR_USERNAME","password":"YOUR_PASSWORD"}'
```

## Role-Based Authorization

Default roles:

- `viewer`: read-only access to API models
- `operator`: read/write (no delete) on API models
- `admin`: full CRUD access on API models

Create or refresh role groups and permissions:

```bash
py manage.py setup_roles
```

Assign a user to a role:

```bash
py manage.py shell
```

```python
from django.contrib.auth.models import Group, User
u = User.objects.get(username="YOUR_USERNAME")
u.groups.clear()
u.groups.add(Group.objects.get(name="viewer"))
u.save()
```

## Traffic Prediction (Markov + Kalman)

This project uses a non-ML prediction pipeline:

- Markov chain for congestion state transitions
- Kalman filtering for smoothing vehicle count, speed, and occupancy

Prediction endpoints:

- `GET /api/traffic/predictions/`
- `POST /api/traffic/predictions/generate/`

Generate for one camera:

```bash
curl -X POST http://127.0.0.1:8000/api/traffic/predictions/generate/ \
	-H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
	-H "Content-Type: application/json" \
	-d '{"camera_code":"CAM-001","horizon_minutes":10}'
```

Generate for all active cameras:

```bash
curl -X POST http://127.0.0.1:8000/api/traffic/predictions/generate/ \
	-H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
	-H "Content-Type: application/json" \
	-d '{"horizon_minutes":5}'
```

Run periodic prediction updates:

```bash
py manage.py generate_traffic_predictions --loop --interval-seconds 300
```

## Data Storage and Archival

Traffic data is split into two tables:

- `Traffic`: active near-real-time records
- `TrafficArchive`: historical records moved by retention jobs

Archive records older than 30 days:

```bash
py manage.py archive_traffic_data --older-than-days 30
```

Preview archival without moving/deleting data:

```bash
py manage.py archive_traffic_data --older-than-days 30 --dry-run
```

Tune batch size for large datasets:

```bash
py manage.py archive_traffic_data --older-than-days 30 --batch-size 5000
```

## Alert System

Features implemented:

- Overflow threshold rules (`AlertRule`)
- Automatic alert generation from live traffic ingestion and predictions
- Notification history records (`AlertNotification`) for channels (`console`, `email`, `push`)
- Alert lifecycle actions (`acknowledge`, `resolve`)

Alert endpoints:

- `GET/POST /api/alert-rules/`
- `GET/PUT/PATCH/DELETE /api/alert-rules/{id}/`
- `GET/POST /api/alerts/`
- `POST /api/alerts/{id}/acknowledge/`
- `POST /api/alerts/{id}/resolve/`
- `GET /api/alert-notifications/`

Run rule evaluation manually for recent records:

```bash
py manage.py process_alerts --lookback-minutes 30
```

## Frontend Dashboard

The web dashboard is available at:

- `/`

It provides:

- Real-time metrics cards
- Vehicle count chart by camera
- Alert stream with severity styling
- Camera feed viewer cards
- Responsive layout for desktop and mobile

Usage:

1. Start server: `py manage.py runserver`
2. Open `http://127.0.0.1:8000/`
3. Login from the top panel to get an access token, then click `Refresh Data`
4. Optionally enable auto refresh

Seed sample camera output data for dashboard/API testing:

```bash
py manage.py seed_sample_camera_data --reset --records-per-camera 24
```

## Testing

Run full test suite:

```bash
py manage.py test
```

Run integration workflow test only:

```bash
py manage.py test users
```
