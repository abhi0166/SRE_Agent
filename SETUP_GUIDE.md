# Disk Monitoring Webhook Server - Setup Guide

## Overview
The webhook server is now running and ready to receive Prometheus alerts and create JIRA tickets. The server provides several endpoints for monitoring and testing.

## Current Status
✅ Flask webhook server running on port 5000
✅ Health check endpoint working
✅ Test endpoint with sample data available
⚠️ JIRA integration not configured (requires API credentials)

## Available Endpoints

### 1. Home Page
- **URL**: `http://localhost:5000/`
- **Method**: GET
- **Purpose**: Shows server status and available endpoints

### 2. Health Check
- **URL**: `http://localhost:5000/health`
- **Method**: GET
- **Purpose**: Monitor server health and JIRA configuration status

### 3. Webhook Endpoint
- **URL**: `http://localhost:5000/webhook/alert`
- **Method**: POST
- **Purpose**: Receives Prometheus alerts and creates JIRA tickets
- **Content-Type**: application/json

### 4. Test Endpoint
- **URL**: `http://localhost:5000/test`
- **Method**: GET/POST
- **Purpose**: Test webhook functionality with sample alert data

## JIRA Configuration

To enable JIRA ticket creation, you need to set up the following environment variables:

1. **JIRA_URL**: Your JIRA instance URL (e.g., `https://yourcompany.atlassian.net`)
2. **JIRA_USERNAME**: Your JIRA username/email
3. **JIRA_API_TOKEN**: JIRA API token (generate from Account Settings > Security > API tokens)
4. **JIRA_PROJECT**: Project key where tickets will be created (default: DCOPS)
5. **JIRA_ASSIGNEE**: Default assignee for tickets (default: datacenter.ops)

### Setting up JIRA API Token
1. Log into your JIRA instance
2. Go to Account Settings > Security > API tokens
3. Create a new API token
4. Copy the token and add it to your environment variables

## Testing the Webhook

### Test without JIRA (Formatting Only)
```bash
curl -X POST http://localhost:5000/test
```

### Test with Custom Alert Data
```bash
curl -X POST http://localhost:5000/webhook/alert \
  -H "Content-Type: application/json" \
  -d '{
    "status": "firing",
    "alerts": [{
      "labels": {
        "alertname": "DiskSpaceHigh",
        "instance": "localhost:9100",
        "severity": "critical"
      },
      "annotations": {
        "summary": "Disk space critical",
        "description": "Disk usage is 95%"
      }
    }]
  }'
```

## Integration with Prometheus

To integrate with Prometheus Alertmanager, add this webhook configuration to your `alertmanager.yml`:

```yaml
route:
  receiver: 'web.hook'

receivers:
- name: 'web.hook'
  webhook_configs:
  - url: 'http://localhost:5000/webhook/alert'
    send_resolved: true
```

## Monitoring Logs

The server logs all activity including:
- Incoming webhook requests
- Alert processing
- JIRA ticket creation attempts
- Error messages

Monitor the logs in the workflow console to troubleshoot any issues.

## Next Steps

1. **Configure JIRA credentials** in the `.env` file
2. **Test JIRA integration** using the test endpoint
3. **Set up Prometheus/Alertmanager** to send alerts to this webhook
4. **Configure alert rules** for disk monitoring
5. **Test end-to-end** alert flow

## Security Considerations

- The server runs on all interfaces (0.0.0.0:5000)
- Consider adding authentication for production use
- Store sensitive credentials securely
- Monitor access logs for unauthorized requests