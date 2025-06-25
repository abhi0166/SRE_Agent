# Slack Integration Setup Guide

## Prerequisites
You have provided the App Credentials, but you need to complete the OAuth installation process to get the Bot Token.

## Step 1: Install App to Workspace

1. **Go to your Slack App settings** at https://api.slack.com/apps/A091W3JKUDQ
2. **Navigate to "OAuth & Permissions"** in the left sidebar
3. **Add Bot Token Scopes** (required permissions):
   - `chat:write` - Send messages to channels
   - `channels:read` - Access channel information
   - `groups:read` - Access private channel information (if needed)

4. **Install App to Workspace**:
   - Click "Install to Workspace" button
   - Authorize the app for your workspace
   - Copy the **Bot User OAuth Token** (starts with `xoxb-`)

## Step 2: Get Channel ID

1. **Open Slack** in your browser or desktop app
2. **Navigate to the channel** where you want alerts sent
3. **Right-click on the channel name** and select "Copy link"
4. **Extract Channel ID** from the URL:
   - URL format: `https://yourworkspace.slack.com/channels/C1234567890`
   - Channel ID is the part after `/channels/`: `C1234567890`

## Step 3: Update Environment Variables

You need to provide:
- **SLACK_BOT_TOKEN**: The Bot User OAuth Token from Step 1 (starts with `xoxb-`)
- **SLACK_CHANNEL_ID**: The Channel ID from Step 2 (starts with `C`)

## Current App Credentials (for reference)
- App ID: A091W3JKUDQ
- Client ID: 8991856883520.9064120674466
- Client Secret: ff7a3eeef8aeb4502c9ba1696f06f21a (not used for Bot Token)

## Verification
Once you provide the correct Bot Token and Channel ID, the system will:
1. Test Slack connectivity automatically
2. Send formatted storage alerts to your Slack channel
3. Store all alerts in the NoSQL database for dashboard access
4. Display Slack status in the health endpoint

## Alert Format
Storage alerts will appear in Slack with:
- Rich formatting with severity colors
- Device and filesystem information
- Timestamps and descriptions
- Interactive message blocks

# Slack Events API Setup for Interactive Alert Assignment

This guide explains how to configure Slack Events API to enable 2-way communication for alert assignment through emoji reactions.

## Overview

The interactive alert assignment feature allows users to:
- React to storage alert messages with "taking a look" emojis (👀, 🔍, 🔨, 🛠️, ⚙️)
- Automatically assign themselves to alerts
- Update alert status in the database
- Show assignment information in the original Slack message

## Slack App Configuration

### 1. Enable Events API in Your Slack App

1. Go to [Slack API Apps](https://api.slack.com/apps)
2. Select your existing monitoring app
3. Navigate to **Event Subscriptions** in the left sidebar
4. Toggle **Enable Events** to On

### 2. Configure Request URL

Set the Request URL to your webhook server's events endpoint:
```
https://your-domain.replit.app/slack/events
```

**Important:** The URL must be publicly accessible and return a valid challenge response.

### 3. Subscribe to Bot Events

Add the following bot events:
- `reaction_added` - When users add emoji reactions to messages
- `reaction_removed` - When users remove emoji reactions (optional)

### 4. Reinstall App to Workspace

After adding events, you'll need to reinstall the app to your workspace to grant the new permissions.

## Supported Reaction Emojis

The system recognizes these emojis as "taking a look" assignments:
- 👀 `:eyes:` - Taking a look
- 🔍 `:mag:` - Investigating  
- 🔨 `:hammer_and_wrench:` - Working on it
- 🛠️ `:tools:` - Using tools to fix
- ⚙️ `:gear:` - Engineering response

## How It Works

### 1. Alert Flow
1. Storage monitor detects issue
2. Alert sent to Slack with rich formatting
3. Slack message timestamp stored in database
4. JIRA ticket created automatically

### 2. Assignment Flow
1. User reacts to alert message with supported emoji
2. Slack sends reaction event to `/slack/events` endpoint
3. System identifies user and alert from message timestamp
4. Database updated with assignment information
5. Original Slack message updated to show assignment

### 3. Database Updates
When a user reacts with an assignment emoji:
```json
{
  "assigned_to_slack_user": "U1234567890",
  "assigned_to_username": "John Smith",
  "assigned_at": "2025-06-17T20:30:00Z",
  "assignment_method": "slack_reaction",
  "status": "assigned"
}
```

## Required Permissions

Your Slack app needs these OAuth scopes:
- `chat:write` - Send messages
- `reactions:read` - Read message reactions
- `users:read` - Get user information
- `channels:history` - Read channel messages (for updating)

## Testing the Setup

### 1. URL Verification
First test will be Slack's URL verification challenge:
```bash
curl -X POST https://your-domain.replit.app/slack/events \
  -H "Content-Type: application/json" \
  -d '{"type":"url_verification","challenge":"test_challenge"}'
```

Expected response: `test_challenge`

### 2. Reaction Event Test
Send a test alert and react with 👀 emoji. Check logs for:
```
INFO:slack_events:Successfully assigned John Smith to alert alert_12345
```

### 3. Database Verification
Check alert assignment in database:
```bash
curl http://localhost:5000/api/alerts/alert_12345
```

## Troubleshooting

### Events Not Received
- Verify Request URL is publicly accessible
- Check Slack app has correct permissions
- Ensure app is reinstalled after adding events

### Assignment Not Working
- Check user permissions in channel
- Verify message timestamp matching in database
- Review server logs for error details

### Message Update Fails
- Ensure bot has `chat:write` permission
- Check if original message still exists
- Verify channel access permissions

## Security Considerations

1. **Request Verification**: Implement Slack request signature validation
2. **Rate Limiting**: Monitor reaction event frequency
3. **User Validation**: Verify users are authorized for alert assignment
4. **Channel Restrictions**: Limit events to designated monitoring channels

## Advanced Features

### Custom Assignment Rules
Modify `slack_events.py` to implement:
- Role-based assignment restrictions
- Escalation timeouts
- Multiple assignee support
- Assignment notifications

### Integration with JIRA
Extend functionality to:
- Update JIRA ticket assignee
- Add comments to tickets
- Sync assignment status

### Metrics and Analytics
Track assignment patterns:
- Response times by user
- Alert resolution rates
- Team engagement metrics

## Configuration Variables

Add these to your `.env` file:
```bash
# Existing Slack configuration
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_CHANNEL_ID=C1234567890

# Optional: Slack signing secret for request verification
SLACK_SIGNING_SECRET=your-signing-secret
```

## API Endpoints

- `POST /slack/events` - Handle Slack Events API callbacks
- `GET /api/alerts/{alert_id}` - View alert assignment status
- `PUT /api/alerts/{alert_id}/assign` - Manually assign alerts

The interactive assignment system is now ready to enhance your storage monitoring workflow with seamless Slack integration.
