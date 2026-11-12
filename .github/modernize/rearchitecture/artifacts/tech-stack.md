# Technology Stack

## Runtime and frameworks

- Python 3.11 is used by CI; backend is FastAPI `0.115.6` with Uvicorn `0.34.0`.
- Pydantic `2.10.4` and pydantic-settings `2.7.0` provide validation and environment configuration.
- MongoDB is accessed through PyMongo `4.10.1`; local Docker uses MongoDB 7.
- JWT authentication uses PyJWT `2.10.1`; passwords use bcrypt `4.2.1`.
- External HTTP calls use httpx `0.28.1`.
- Frontend uses React `19.0.0`, Vite `6.0.7`, React Router `7.1.1`, Axios `1.7.9`, Recharts `2.x`, and Tailwind CSS `3.4.17`.
- Node 20 is used by CI.

## External integrations

PayPal Orders API and JavaScript SDK in Sandbox mode; Gemini REST API with a rule-based fallback; optional Cloudinary receipt storage.

## Build and test

- Backend dependencies: `backend/requirements.txt`; tests: `backend/tests/test_core.py`.
- Frontend dependencies: `frontend/package.json` and `frontend/package-lock.json`; build command: `npm run build`.
- CI runs backend `pytest -q` and frontend `npm run build`.

## Observed warnings

The current frontend dependency resolution emits a warning that Recharts 2.x is no longer actively maintained. The production build also reports a JavaScript chunk over 500 kB; neither prevents the current build.
