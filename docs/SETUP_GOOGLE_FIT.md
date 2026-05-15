# Google Fit Setup

## Prerequisites

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project and enable the **Fitness API**
3. Configure OAuth consent screen (Internal)
4. Create OAuth 2.0 credentials (Desktop/Web application)
5. Add authorized redirect URI: `http://localhost:8000/api/v1/auth/google/callback`

## Configuration

Add to `.env`:
```
GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/google/callback
```

## Data Accessed
- Weight
- Steps
- Sleep duration
- Resting heart rate
- Active minutes

## Privacy
All Google Fit data is encrypted at rest using Fernet. OAuth tokens are encrypted before storage.
