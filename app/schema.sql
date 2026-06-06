-- FoxGuard Security Portal — Cloud SQL (MySQL) schema
-- Tables required for the employee directory and security ticket management.

CREATE TABLE IF NOT EXISTS users (
    id         INT PRIMARY KEY,
    username   VARCHAR(64)  NOT NULL,
    email      VARCHAR(128),
    role       VARCHAR(32),
    department VARCHAR(64)
);

CREATE TABLE IF NOT EXISTS tickets (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    title       VARCHAR(160) NOT NULL,
    description TEXT,
    severity    VARCHAR(16) DEFAULT 'low',
    status      VARCHAR(16) DEFAULT 'open',
    created_by  VARCHAR(64),
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);
