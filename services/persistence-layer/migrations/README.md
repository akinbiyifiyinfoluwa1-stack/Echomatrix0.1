# EchoMatrix database migrations

Alembic is the migration framework for the persistence layer.

The application currently creates its development tables automatically on startup so the service can run immediately. Before production deployment, generate and apply versioned Alembic revisions against PostgreSQL.

Set `DATABASE_URL` to the PostgreSQL connection string supplied by the deployment environment. Never commit credentials.
