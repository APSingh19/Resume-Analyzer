# Deployment

This Streamlit app is deployment-ready, but it needs a cloud MySQL database.

## Required Secrets

Set these values in your host dashboard:

```toml
MYSQL_HOST = "your-cloud-mysql-host"
MYSQL_PORT = "3306"
MYSQL_USER = "your-database-user"
MYSQL_PASSWORD = "your-database-password"
MYSQL_DATABASE = "VC"
```

## Render

1. Push this repository to GitHub.
2. Create a Web Service on Render.
3. Use the repository root.
4. Build command:

```bash
pip install -r requirements.txt
```

5. Start command:

```bash
cd App && streamlit run App.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true
```

6. Add the MySQL secrets above in Environment.

## Streamlit Community Cloud

1. Push this repository to GitHub.
2. Select `App/App.py` as the main file.
3. Add the MySQL secrets above in App settings.

If the host runs the app from the repository root, use Render or a host that supports the start command above.
