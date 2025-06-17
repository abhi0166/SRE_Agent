#!/bin/bash

# Start all monitoring services
set -e

echo "=== Starting Disk Monitoring Services ==="

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Check if configuration exists
if [[ ! -f ~/disk-monitoring/.env ]]; then
    echo "Error: Configuration file ~/disk-monitoring/.env not found"
    echo "Please run setup.sh first"
    exit 1
fi

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to start a service
start_service() {
    local service_name=$1
    local port=$2
    local command="$3"
    
    if check_port $port; then
        echo "$service_name is already running on port $port"
    else
        echo "Starting $service_name on port $port..."
        eval "$command" &
        sleep 2
        if check_port $port; then
            echo "$service_name started successfully"
        else
            echo "Failed to start $service_name"
            return 1
        fi
    fi
}

# Create logs directory
mkdir -p ~/disk-monitoring/logs

# Start Node Exporter
start_service "Node Exporter" 9100 \
    "nohup $(brew --prefix)/bin/node_exporter --web.listen-address=0.0.0.0:9100 > ~/disk-monitoring/logs/node_exporter.log 2>&1"

# Start Alertmanager
start_service "Alertmanager" 9093 \
    "nohup $(brew --prefix)/bin/alertmanager --config.file=$HOME/disk-monitoring/alertmanager.yml --storage.path=$HOME/disk-monitoring/data/alertmanager --web.listen-address=0.0.0.0:9093 > ~/disk-monitoring/logs/alertmanager.log 2>&1"

# Start Prometheus
start_service "Prometheus" 9090 \
    "nohup $(brew --prefix)/bin/prometheus --config.file=$HOME/disk-monitoring/prometheus.yml --storage.tsdb.path=$HOME/disk-monitoring/data/prometheus --web.console.templates=$(brew --prefix)/etc/prometheus/consoles --web.console.libraries=$(brew --prefix)/etc/prometheus/console_libraries --web.listen-address=0.0.0.0:9090 > ~/disk-monitoring/logs/prometheus.log 2>&1"

# Start Flask webhook server
echo "Starting Flask webhook server on port 5000..."
cd "$PROJECT_DIR"
export PYTHONPATH="$PROJECT_DIR:$PYTHONPATH"
cp ~/disk-monitoring/.env .env
nohup python3 webhook_server/app.py > ~/disk-monitoring/logs/webhook.log 2>&1 &

sleep 3

if check_port 5000; then
    echo "Webhook server started successfully"
else
    echo "Failed to start webhook server"
fi

echo
echo "=== Service Status ==="
echo "Prometheus:      http://localhost:9090"
echo "Alertmanager:    http://localhost:9093"
echo "Node Exporter:   http://localhost:9100"
echo "Webhook Server:  http://localhost:5000"
echo "SMART Metrics:   http://localhost:5000/smart_metrics"
echo
echo "Log files are in ~/disk-monitoring/logs/"
echo
echo "To stop all services: pkill -f 'prometheus|alertmanager|node_exporter'; pkill -f 'webhook_server/app.py'"
