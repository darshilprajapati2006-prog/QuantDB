# QuantDB Web

A React, TypeScript and Vite research terminal for the existing QuantDB provider and Python services. The Streamlit dashboard remains available in `dashboard/`.

## Local run

From the repository root, install backend dependencies and run the API:

```bash
pip install -r requirements.txt
uvicorn api.main:app --reload
```

In another terminal:

```bash
cd web
npm install
cp .env.example .env.local
npm run dev
```

Vite proxies `/api` to `http://localhost:8000`. The default data provider is `mock`; `DATA_MODE=real` selects the MySQL provider. The interface labels mock data as a simulation and no longer fills missing portfolio, order, or trade results with invented rows.

## Firebase and database setup

1. In Firebase Console, enable **Authentication → Sign-in method → Email/Password** and set the email verification template and authorized domains.
2. Set the public `VITE_FIREBASE_*` values in `web/.env.local` (the Firebase web API key is client configuration, not a service-account secret).
3. Configure the API host with `FIREBASE_PROJECT_ID`, `FIREBASE_SERVICE_ACCOUNT_JSON` or `FIREBASE_SERVICE_ACCOUNT_PATH`, plus the existing MySQL `DB_*` settings. Keep the service-account private key in the hosting provider’s secret manager; never put it in `web/.env.local` or commit it.
4. Run `database/13_role_requests.sql` once against the QuantDB MySQL database so role upgrades can be requested and reviewed. New Firebase sign-ups receive `USER`; the browser cannot choose a privileged role.
5. Configure `FRONTEND_ORIGINS` on the API host with the exact local and deployed web origins, comma-separated. Set `VITE_API_BASE_URL` in the Vercel project to the deployed API origin, for example `https://api.example.com` (no trailing slash).
6. Deploy the FastAPI API separately from the static Vercel frontend. A browser app cannot reach `localhost` on the visitor’s computer. Google Cloud hosts can use their attached runtime service account; elsewhere, configure the Firebase Admin service account in the API host’s secret settings.

The API returns HTTP 503 when Firebase Admin credentials are missing or invalid. This cannot be fixed in the browser; configure server credentials for the same Firebase project as the web client, then restart/redeploy the API. For better verification-email sender trust, configure a custom authentication email domain in Firebase Authentication → Templates and add the requested DNS records. Inbox placement is ultimately controlled by each mail provider, so no app can guarantee Inbox instead of Spam.

New accounts must verify their Firebase email before a MySQL profile is linked. The API creates new profiles with the `USER` role; an assigned role is read from the MySQL `users` record and is never accepted from the browser. Admin can update the role in the existing QuantDB admin dashboard. API requests verify Firebase ID tokens and enforce role access server-side. A verified Firebase account still needs the API service-account and database configuration to load its profile.

## Production build

```bash
npm run build
```

The dashboard overview and each product module load as separate chunks. `VITE_API_BASE_URL` is optional for local Vite use and required when the deployed frontend and API have different origins.

Paper trading routes create simulated orders only; they do not send real market orders.
