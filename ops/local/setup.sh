#!/bin/bash
# Glintstone v2 — Local Development Setup (macOS)
# One-time: installs PostgreSQL, creates venv, installs deps, creates DB, runs migrations.
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "=== Glintstone v2 Local Setup ==="
echo ""

# 1. Check Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 not found."
    exit 1
fi
echo "Python: $(python3 --version)"

# 2. Check/install PostgreSQL and add to PATH
if ! command -v psql &> /dev/null; then
    # Check Homebrew keg-only install location
    if [ -d "/opt/homebrew/opt/postgresql@17/bin" ]; then
        export PATH="/opt/homebrew/opt/postgresql@17/bin:$PATH"
    elif [ -d "/usr/local/opt/postgresql@17/bin" ]; then
        export PATH="/usr/local/opt/postgresql@17/bin:$PATH"
    else
        echo "Installing PostgreSQL via Homebrew..."
        brew install postgresql@17
        export PATH="/opt/homebrew/opt/postgresql@17/bin:$PATH"
    fi
fi

if ! pg_isready -q 2>/dev/null; then
    echo "Starting PostgreSQL..."
    brew services start postgresql@17
    sleep 2
fi
echo "PostgreSQL: $(psql --version | head -1)"

# 3. Create database and user
echo ""
echo "Setting up database..."
createuser glintstone 2>/dev/null && echo "  Created user: glintstone" || echo "  User 'glintstone' already exists"
createdb -O glintstone glintstone 2>/dev/null && echo "  Created database: glintstone" || echo "  Database 'glintstone' already exists"
psql -c "ALTER USER glintstone WITH PASSWORD 'glintstone';" postgres > /dev/null 2>&1

# 4. Create .env from template
if [ ! -f "$PROJECT_DIR/.env" ]; then
    cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
    echo "  Created .env from .env.example"
else
    echo "  .env already exists"
fi

# 5. Create virtual environment and install dependencies
echo ""
if [ ! -d "$PROJECT_DIR/venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$PROJECT_DIR/venv"
fi
echo "Installing dependencies..."
"$PROJECT_DIR/venv/bin/pip" install --quiet -r "$PROJECT_DIR/requirements.txt"

# 6. Add .test domains to /etc/hosts (requires sudo, one-time)
echo ""
HOSTS_ENTRY="127.0.0.1 glintstone.test app.glintstone.test api.glintstone.test"
if ! grep -q "glintstone.test" /etc/hosts 2>/dev/null; then
    echo "Adding .test domains to /etc/hosts (requires sudo)..."
    echo "$HOSTS_ENTRY" | sudo tee -a /etc/hosts > /dev/null
    echo "  Added: $HOSTS_ENTRY"
else
    echo "  .test domains already in /etc/hosts"
fi

# 7. Run migrations
echo ""
echo "Running migrations..."
"$PROJECT_DIR/venv/bin/python" "$PROJECT_DIR/database/migrate.py"

echo ""
echo "=== Setup complete ==="
echo "Run: ./ops/local/start.sh"
