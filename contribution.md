# Contributing to DevLegacy

## Before you start

1. Fork the repository and create a focused branch.
2. Read the relevant page in [`docs/`](./docs/).
3. Do not commit `.env` files, Firebase service-account files, model secrets, or access tokens.

## Local development

Start PostgreSQL, Redis, and the backend with:

```bash
docker compose up --build -d
```

Start the frontend separately:

```bash
cd frontend
npm install
npm run dev
```

## Pull requests

- Keep changes focused and explain the user-visible or architectural impact.
- Update the related documentation when behavior or data flow changes.
- Include reproduction steps for bug fixes.
- Run the applicable backend or frontend checks before opening a pull request.
- Never include credentials or generated private model artifacts in a commit.
