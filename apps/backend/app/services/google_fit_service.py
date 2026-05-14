"""Google Fit Service — OAuth2 + data sync."""
from datetime import date, timedelta
from typing import Any, Optional

from app.core.config import settings


class GoogleFitService:
    """Syncs health data from Google Fit API."""

    SCOPES = [
        "https://www.googleapis.com/auth/fitness.activity.read",
        "https://www.googleapis.com/auth/fitness.body.read",
        "https://www.googleapis.com/auth/fitness.sleep.read",
        "https://www.googleapis.com/auth/fitness.heart_rate.read",
    ]

    def get_auth_url(self, redirect_uri: str) -> str:
        """Generate Google OAuth2 authorization URL."""
        from google_auth_oauthlib.flow import Flow

        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=self.SCOPES,
        )
        flow.redirect_uri = redirect_uri
        auth_url, state = flow.authorization_url(
            access_type="offline",
            prompt="consent",
            include_granted_scopes="true",
        )
        return auth_url, state

    async def exchange_code(self, code: str, redirect_uri: str) -> dict:
        """Exchange OAuth2 code for tokens."""
        from google_auth_oauthlib.flow import Flow

        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=self.SCOPES,
        )
        flow.redirect_uri = redirect_uri
        flow.fetch_token(code=code)
        creds = flow.credentials
        return {
            "access_token": creds.token,
            "refresh_token": creds.refresh_token,
            "expiry": creds.expiry.isoformat() if creds.expiry else None,
        }

    async def sync_metrics(
        self,
        access_token: str,
        days_back: int = 30,
        last_sync: Optional[date] = None,
    ) -> dict[str, list[dict]]:
        """Fetch weight, steps, sleep, heart rate, and active minutes from Google Fit."""
        from datetime import timezone

        end_date = date.today()
        start_date = last_sync or (end_date - timedelta(days=days_back))

        start_millis = int(
            __import__("datetime").datetime.combine(start_date, __import__("datetime").time.min)
            .replace(tzinfo=timezone.utc)
            .timestamp()
            * 1000
        )
        end_millis = int(
            __import__("datetime").datetime.combine(end_date, __import__("datetime").time.max)
            .replace(tzinfo=timezone.utc)
            .timestamp()
            * 1000
        )

        metrics = {
            "weight_kg": self._build_aggregate("com.google.weight", "com.google.weight.summary"),
            "steps": self._build_aggregate("com.google.step_count.delta", "com.google.step_count.delta"),
            "sleep_hours": self._build_aggregate("com.google.sleep.segment", "com.google.sleep.segment"),
            "resting_heart_rate_bpm": self._build_aggregate("com.google.heart_rate.bpm", "com.google.heart_rate.bpm.summary"),
            "active_minutes": self._build_aggregate("com.google.activity.segment", "com.google.active_minutes"),
        }

        results = {}
        for metric_type, aggregate in metrics.items():
            data = await self._fetch_dataset(access_token, aggregate, start_millis, end_millis)
            results[metric_type] = self._parse_dataset(data, metric_type)

        return results

    def _build_aggregate(self, data_type_name: str, aggregate_by: str) -> dict:
        return {
            "aggregateBy": [{"dataTypeName": aggregate_by}],
            "bucketByTime": {"durationMillis": 86400000},
            "startTimeMillis": 0,  # placeholder
            "endTimeMillis": 0,
        }

    async def _fetch_dataset(
        self, access_token: str, aggregate: dict, start_ms: int, end_ms: int
    ) -> dict:
        import httpx
        aggregate["startTimeMillis"] = start_ms
        aggregate["endTimeMillis"] = end_ms
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://fitness.googleapis.com/fitness/v1/users/me/dataset:aggregate",
                headers={"Authorization": f"Bearer {access_token}"},
                json=aggregate,
            )
            if resp.status_code == 401:
                raise PermissionError("Google token expired")
            resp.raise_for_status()
            return resp.json()

    def _parse_dataset(self, data: dict, metric_type: str) -> list[dict]:
        results = []
        for bucket in data.get("bucket", []):
            start_ms = int(bucket.get("startTimeMillis", 0))
            entry_date = date.fromtimestamp(start_ms / 1000).isoformat()
            value = 0.0
            for dataset in bucket.get("dataset", []):
                for point in dataset.get("point", []):
                    for val in point.get("value", []):
                        fp = val.get("fpVal", val.get("intVal", 0))
                        if metric_type in ("steps", "active_minutes", "sleep_hours"):
                            value += float(fp)
                        else:
                            value = float(fp)
            if value:
                results.append({"date": entry_date, "value": value})
        return results
