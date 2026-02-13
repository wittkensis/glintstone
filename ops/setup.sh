#!/bin/bash
# Automatic Web Server Setup for CUNEIFORM
# Installs Composer + Valet and configures everything

set -e  # Exit on error

PROJECT_DIR="/Volumes/Portable Storage/CUNEIFORM"
WEB_ROOT="$PROJECT_DIR/app/public_html"

echo "╔══════════════════════════════════════════════════════════╗"
echo "║      CUNEIFORM Web Server Setup (Automated)             ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Check if we're in the right directory
if [ ! -d "$PROJECT_DIR" ]; then
    echo "❌ Error: Project directory not found!"
    echo "Expected: $PROJECT_DIR"
    exit 1
fi

echo "✓ Project directory found"
echo ""

# Step 1: Check/Install Homebrew
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 1: Checking Homebrew..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if ! command -v brew &> /dev/null; then
    echo "Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
else
    echo "✓ Homebrew already installed"
fi
echo ""

# Step 2: Install Composer
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 2: Installing Composer..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if ! command -v composer &> /dev/null; then
    echo "Installing Composer via Homebrew..."
    brew install composer
    echo "✓ Composer installed"
else
    echo "✓ Composer already installed"
fi
echo ""

# Step 3: Install Valet
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 3: Installing Laravel Valet..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Add composer to PATH if not already there
if [[ ":$PATH:" != *":$HOME/.composer/vendor/bin:"* ]]; then
    export PATH="$HOME/.composer/vendor/bin:$PATH"
    echo 'export PATH="$HOME/.composer/vendor/bin:$PATH"' >> ~/.zshrc
    echo "✓ Added Composer to PATH"
fi

if ! command -v valet &> /dev/null; then
    echo "Installing Valet globally..."
    composer global require laravel/valet

    echo "Configuring Valet..."
    valet install
    echo "✓ Valet installed and configured"
else
    echo "✓ Valet already installed"
fi
echo ""

# Step 4: Link Project
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 4: Linking Project to Valet..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cd "$WEB_ROOT"
valet link glintstone
echo "✓ Project linked"
echo ""

# Step 5: Verify Setup
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 5: Verifying Setup..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Test PHP
echo -n "Testing PHP... "
php -v > /dev/null 2>&1 && echo "✓" || echo "❌"

# Test Valet
echo -n "Testing Valet... "
valet status > /dev/null 2>&1 && echo "✓" || echo "❌"

echo ""

# Success!
echo "╔══════════════════════════════════════════════════════════╗"
echo "║                  ✓ SETUP COMPLETE!                       ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "Your site is now available at:"
echo "  → http://glintstone.test"
echo ""
echo "Test it:"
echo "  → http://glintstone.test/tablets/detail.php?p=P388097"
echo ""
echo "ML Detection API:"
echo "  → http://glintstone.test/api/ml/detect-signs.php?p=P388097"
echo ""
echo "Useful commands:"
echo "  valet status    - Check server status"
echo "  valet restart   - Restart server"
echo "  valet links     - Show all linked projects"
echo "  valet unlink    - Remove project link"
echo ""
echo "Next: Start ML service for sign detection:"
echo "  cd ml-service && python app.py"
echo ""
