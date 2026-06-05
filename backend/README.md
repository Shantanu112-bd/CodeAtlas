# CodeAtlas Backend Services

This project implements the backend API services for CodeAtlas, including GitHub OAuth Authentication and the Repository Ingestion Engine.

## Setup & Configuration

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Environment Setup**:
    Copy the `.env.example` file and configure with your credentials:
    ```bash
    cp .env.example .env
    ```

    Configure the following values inside `.env`:
    *   `GITHUB_CLIENT_ID`: The Client ID from your GitHub Developer Settings OAuth App.
    *   `GITHUB_CLIENT_SECRET`: The Client Secret from your GitHub Developer Settings OAuth App.
    *   `JWT_SECRET`: A secure cryptographically random string.
    *   `REPO_STORAGE_PATH`: Directory location on disk to save cloned code repositories (e.g., `./repos`).

3.  **Run Database Migrations**:
    Apply the database schema configurations using Alembic:
    ```bash
    alembic upgrade head
    ```

4.  **Start API Development Server**:
    Run FastAPI backend server using Uvicorn:
    ```bash
    uvicorn app.main:app --reload --port 8000
    ```

## API Endpoint Documentation

### Authentication APIs
*   `GET /v1/auth/github/login`: Redirects browser client to GitHub's OAuth approval screen.
*   `POST /v1/auth/github/callback`: Receives authentication codes from GitHub callback redirects. Verifies tokens, creates/retrieves database user record, and outputs API JWT Bearer session tokens.
*   `GET /v1/auth/me`: Fetches profile details of current authorized session credentials.

### Repository Ingestion APIs
*   `POST /v1/repositories`: Register a new GitHub URL, storing metadata and initiating an asynchronous background git clone.
*   `GET /v1/repositories`: List all registered repositories.
*   `GET /v1/repositories/{id}`: Fetch sync status and details for a single repository.
*   `DELETE /v1/repositories/{id}`: Delete metadata and wipe local repository files from disk.

## Testing Suite

Run backend test logic utilizing Pytest:
```bash
pytest
```
