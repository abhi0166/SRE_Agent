#!/bin/bash

# MacBook Disk Monitoring Setup Script
# This script installs and configures all necessary components

set -e

echo "=== MacBook Disk Monitoring System Setup ==="
echo "This script will install Prometheus, Node Exporter, Alertmanager, and smartmontools"
echo

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "Error: This script is designed for macOS only"
    exit 1
fi

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    echo "Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

echo "Updating Homebrew..."
brew update

# Install required tools
echo "Installing monitoring tools..."
brew install prometheus
brew install node_exporter
brew install alertmanager
brew install smartmontools

# Install Python dependencies
echo "Installing Python dependencies..."
if ! command -v python3 &> /dev/null; then
    brew install python3
fi

pip3 install flask requests python-dotenv

# Create necessary directories
echo "Creating configuration directories..."
mkdir -p ~/disk-monitoring/data/prometheus
mkdir -p ~/disk-monitoring/data/alertmanager
mkdir -p ~/disk-monitoring/logs

# Copy configuration files
echo "Setting up configuration files..."
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Create Prometheus data directory and copy config
cp "$PROJECT_DIR/prometheus/prometheus.yml" ~/disk-monitoring/prometheus.yml
cp "$PROJECT_DIR/prometheus/alert_rules.yml" ~/disk-monitoring/alert_rules.yml
cp "$PROJECT_DIR/alertmanager/alertmanager.yml" ~/disk-monitoring/alertmanager.yml

# Update config paths to use absolute paths
sed -i '' "s|alert_rules.yml|$HOME/disk-monitoring/alert_rules.yml|g" ~/disk-monitoring/prometheus.yml

# Create environment file if it doesn't exist
if [[ ! -f ~/disk-monitoring/.env ]]; then
    echo "Creating environment configuration file..."
    cp "$PROJECT_DIR/.env.example" ~/disk-monitoring/.env
    echo
    echo "IMPORTANT: Please edit ~/disk-monitoring/.env with your JIRA credentials"
    echo "Required variables:"
    echo "  - JIRA_URL"
    echo "  - JIRA_USERNAME"
    echo "  - JIRA_API_TOKEN"
    echo "  - JIRA_PROJECT"
    echo "  - JIRA_ASSIGNEE"
fi

# Create launch agents for auto-start (optional)
echo "Creating macOS launch agents..."
cat > ~/Library/LaunchAgents/com.diskmonitoring.prometheus.plist << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.diskmonitoring.prometheus</string>
    <key>ProgramArguments</key>
    <array>
        <string>$(brew --prefix)/bin/prometheus</string>
        <string>--config.file=$HOME/disk-monitoring/prometheus.yml</string>
        <string>--storage.tsdb.path=$HOME/disk-monitoring/data/prometheus</string>
        <string>--web.console.templates=$(brew --prefix)/etc/prometheus/consoles</string>
        <string>--web.console.libraries=$(brew --prefix)/etc/prometheus/console_libraries</string>
        <string>--web.listen-address=0.0.0.0:9090</string>
    </array>
    <key>RunAtLoad</key>
    <false/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$HOME/disk-monitoring/logs/prometheus.log</string>
    <key>StandardErrorPath</key>
    <string>$HOME/disk-monitoring/logs/prometheus.error.log</string>
</dict>
</plist>
EOF

cat > ~/Library/LaunchAgents/com.diskmonitoring.node_exporter.plist << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.diskmonitoring.node_exporter</string>
    <key>ProgramArguments</key>
    <array>
        <string>$(brew --prefix)/bin/node_exporter</string>
        <string>--web.listen-address=0.0.0.0:9100</string>
    </array>
    <key>RunAtLoad</key>
    <false/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$HOME/disk-monitoring/logs/node_exporter.log</string>
    <key>StandardErrorPath</key>
    <string>$HOME/disk-monitoring/logs/node_exporter.error.log</string>
</dict>
</plist>
EOF

cat > ~/Library/LaunchAgents/com.diskmonitoring.alertmanager.plist << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.diskmonitoring.alertmanager</string>
    <key>ProgramArguments</key>
    <array>
        <string>$(brew --prefix)/bin/alertmanager</string>
        <string>--config.file=$HOME/disk-monitoring/alertmanager.yml</string>
        <string>--storage.path=$HOME/disk-monitoring/data/alertmanager</string>
        <string>--web.listen-address=0.0.0.0:9093</string>
    </array>
    <key>RunAtLoad</key>
    <false/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$HOME/disk-monitoring/logs/alertmanager.log</string>
    <key>StandardErrorPath</key>
    <string>$HOME/disk-monitoring/logs/alertmanager.error.log</string>
</dict>
</plist>
EOF

echo
echo "=== Setup Complete ==="
echo
echo "Configuration files created in ~/disk-monitoring/"
echo "Launch agents created in ~/Library/LaunchAgents/"
echo
echo "Next steps:"
echo "1. Edit ~/disk-monitoring/.env with your JIRA credentials"
echo "2. Run './scripts/start_services.sh' to start all services"
echo "3. Access Prometheus at http://localhost:9090"
echo "4. Access Alertmanager at http://localhost:9093"
echo
echo "To start services automatically at login:"
echo "  launchctl load ~/Library/LaunchAgents/com.diskmonitoring.*.plist"
echo
