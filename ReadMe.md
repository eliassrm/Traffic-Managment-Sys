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
