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