import os
import socket
import datetime
import secrets
from flask import Flask, request, jsonify, render_template, g

app = Flask(__name__, static_folder='static')

# ── Database configuration ───────────────────────────────────────────────────
# The application supports two backends:
#   • Cloud SQL (MySQL) via PyMySQL  — used in deployed / cloud environments
#   • In-memory SQLite               — fallback for local dev, tests, and CI
#
# Cloud SQL is selected automatically when database credentials are supplied
# through environment variables. No secrets are hardcoded in the source; the
# connection settings are read from the environment (and, in production, from
# Google Secret Manager via the deployment pipeline).
DB_HOST     = os.environ.get('DB_HOST')      # TCP host, e.g. 127.0.0.1 (Cloud SQL Auth Proxy)
DB_SOCKET   = os.environ.get('DB_SOCKET')    # unix socket, e.g. /cloudsql/<INSTANCE_CONNECTION_NAME>
DB_USER     = os.environ.get('DB_USER')
DB_PASSWORD = os.environ.get('DB_PASSWORD')
DB_NAME     = os.environ.get('DB_NAME', 'foxguard')
DB_PORT     = int(os.environ.get('DB_PORT', '3306'))

USE_MYSQL = bool(DB_USER and DB_PASSWORD and (DB_HOST or DB_SOCKET))

# Seed data for the employee directory (used when the users table is empty).
SEED_USERS = [
    (1, 'alice',   'alice@corp.local',   'admin',   'Engineering'),
    (2, 'bob',     'bob@corp.local',     'user',    'Marketing'),
    (3, 'charlie', 'charlie@corp.local', 'user',    'Finance'),
    (4, 'diana',   'diana@corp.local',   'manager', 'Engineering'),
    (5, 'eve',     'eve@corp.local',     'admin',   'Security'),
    (6, 'frank',   'frank@corp.local',   'user',    'HR'),
]


if USE_MYSQL:
    # ── Cloud SQL (MySQL) backend ────────────────────────────────────────────
    import pymysql
    import pymysql.cursors

    def _connect():
        kwargs = dict(
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            charset='utf8mb4',
            autocommit=True,
            cursorclass=pymysql.cursors.Cursor,  # positional tuples: row[0..4]
        )
        if DB_SOCKET:
            kwargs['unix_socket'] = DB_SOCKET
        else:
            kwargs['host'] = DB_HOST
            kwargs['port'] = DB_PORT
        return pymysql.connect(**kwargs)

    def init_db():
        conn = _connect()
        try:
            with conn.cursor() as cur:
                cur.execute('''CREATE TABLE IF NOT EXISTS users (
                    id         INT PRIMARY KEY,
                    username   VARCHAR(64)  NOT NULL,
                    email      VARCHAR(128),
                    role       VARCHAR(32),
                    department VARCHAR(64)
                )''')
                cur.execute('''CREATE TABLE IF NOT EXISTS tickets (
                    id          INT AUTO_INCREMENT PRIMARY KEY,
                    title       VARCHAR(160) NOT NULL,
                    description TEXT,
                    severity    VARCHAR(16) DEFAULT 'low',
                    status      VARCHAR(16) DEFAULT 'open',
                    created_by  VARCHAR(64),
                    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
                )''')
                cur.execute('SELECT COUNT(*) FROM users')
                if cur.fetchone()[0] == 0:
                    cur.executemany(
                        'INSERT INTO users (id, username, email, role, department) '
                        'VALUES (%s, %s, %s, %s, %s)', SEED_USERS
                    )
        finally:
            conn.close()

    def search_users(username):
        conn = _connect()
        try:
            with conn.cursor() as cur:
                # Parameterized query — prevents SQL injection (%s placeholder).
                cur.execute(
                    'SELECT id, username, email, role, department '
                    'FROM users WHERE username = %s', (username,)
                )
                return cur.fetchall()
        finally:
            conn.close()

else:
    # ── In-memory SQLite backend (local dev / CI fallback) ───────────────────
    import sqlite3

    _DB = sqlite3.connect(':memory:', check_same_thread=False)

    def init_db():
        _DB.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY, username TEXT, email TEXT, role TEXT, department TEXT
        )''')
        _DB.execute('''CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            severity TEXT DEFAULT 'low',
            status TEXT DEFAULT 'open',
            created_by TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )''')
        cur = _DB.execute('SELECT COUNT(*) FROM users')
        if cur.fetchone()[0] == 0:
            _DB.executemany('INSERT INTO users VALUES (?,?,?,?,?)', SEED_USERS)
        _DB.commit()

    def search_users(username):
        # Parameterized query — prevents SQL injection (? placeholder).
        cur = _DB.execute(
            'SELECT id, username, email, role, department FROM users WHERE username = ?',
            (username,)
        )
        return cur.fetchall()


init_db()


def ctx():
    return {
        'hostname':    socket.gethostname(),
        'environment': os.environ.get('ENVIRONMENT', 'dev'),
        'version':     os.environ.get('APP_VERSION', '2.0.0-secure'),
        'deploy_time': os.environ.get('DEPLOY_TIME', 'unknown'),
        'commit_sha':  os.environ.get('COMMIT_SHA', 'local')[:7],
        'port':        os.environ.get('HOST_PORT', '5000'),
    }


# ── Generate a CSP nonce per request ─────────────────────────────────────────
@app.before_request
def generate_nonce():
    g.nonce = secrets.token_hex(16)


# ── Security headers on every response ───────────────────────────────────────
@app.after_request
def set_security_headers(response):
    nonce = getattr(g, 'nonce', '')

    # CSP — no unsafe-inline; style-src uses per-request nonce
    # form-action 'self' prevents form hijacking (fixes ZAP form-action finding)
    response.headers['Content-Security-Policy'] = (
        f"default-src 'self'; "
        f"script-src 'self'; "
        f"style-src 'self' 'nonce-{nonce}'; "
        f"img-src 'self' data:; "
        f"font-src 'self'; "
        f"form-action 'self'; "
        f"frame-ancestors 'none';"
    )
    response.headers['X-Frame-Options']               = 'DENY'
    response.headers['X-Content-Type-Options']        = 'nosniff'
    response.headers['Cross-Origin-Embedder-Policy']  = 'require-corp'
    response.headers['Cross-Origin-Opener-Policy']    = 'same-origin'
    response.headers['Cross-Origin-Resource-Policy']  = 'same-origin'
    response.headers['Permissions-Policy']            = (
        'camera=(), microphone=(), geolocation=(), payment=()'
    )
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, private'
    response.headers['Pragma']        = 'no-cache'
    response.headers['Expires']       = '0'
    return response


# ── WSGI middleware to override Server header ─────────────────────────────────
# after_request cannot override the Server header — Werkzeug sets it at the
# WSGI layer after Flask has finished. This middleware intercepts it correctly.
class HideServerVersion:
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        def custom_start_response(status, headers, exc_info=None):
            headers = [(k, v) for k, v in headers if k.lower() != 'server']
            headers.append(('Server', 'CorpDirectory'))
            return start_response(status, headers, exc_info)
        return self.wsgi_app(environ, custom_start_response)

app.wsgi_app = HideServerVersion(app.wsgi_app)


@app.route('/')
def index():
    return render_template('index.html', nonce=g.nonce, **ctx())


# ── FIX 1: Parameterized query ────────────────────────────────────────────────
@app.route('/search')
def search():
    q = request.args.get('q', '')
    results, error = [], None
    if q:
        try:
            results = search_users(q)
        except Exception as e:
            error = str(e)
    return render_template('search.html', q=q, results=results,
                           error=error, nonce=g.nonce, **ctx())


# ── FIX 2: /debug removed ────────────────────────────────────────────────────

@app.route('/health')
def health():
    return jsonify({
        'status':  'ok',
        'app':     'corpdirectory',
        'version': os.environ.get('APP_VERSION', '2.0.0-secure'),
        'env':     os.environ.get('ENVIRONMENT', 'dev'),
        'db':      'mysql' if USE_MYSQL else 'sqlite',
        'host':    socket.gethostname(),
        'time':    datetime.datetime.utcnow().isoformat() + 'Z',
    })


if __name__ == '__main__':
    # FIX 3: debug=False
    app.run(host='0.0.0.0', port=5000, debug=False)
