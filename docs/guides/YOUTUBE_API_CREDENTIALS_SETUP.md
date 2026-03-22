# YouTube API Credentials Setup Guide

## Complete Step-by-Step Instructions for Google Cloud Console

This guide walks you through obtaining YouTube API credentials for the MCP FFMPEG Server's direct upload functionality.

## Prerequisites

- Google Account (Gmail or Google Workspace)
- Access to [Google Cloud Console](https://console.cloud.google.com/)

## Step 1: Create Google Cloud Project

### 1.1 Navigate to Google Cloud Console
- Go to: https://console.cloud.google.com/
- Sign in with your Google account

### 1.2 Create New Project
1. Click the **project dropdown** at the top of the page
2. Click **"New Project"**
3. Enter project details:
   - **Project Name**: `YouTube MCP Upload` (or your preferred name)
   - **Organization**: Leave as default (or select your organization)
4. Click **"Create"**
5. Wait for project creation (30-60 seconds)
6. **Select your new project** from the dropdown

## Step 2: Enable YouTube Data API v3

### 2.1 Navigate to APIs & Services
1. Click the **hamburger menu** (☰) in top-left corner
2. Go to **"APIs & Services"** → **"Library"**

### 2.2 Enable YouTube Data API
1. In the search bar, type: `YouTube Data API v3`
2. Click on **"YouTube Data API v3"** in the results
3. Click the **"Enable"** button
4. Wait for API to be enabled (10-30 seconds)

## Step 3: Configure OAuth2 Consent Screen

### 3.1 Navigate to OAuth Consent Screen
1. Go to **"APIs & Services"** → **"OAuth consent screen"**

### 3.2 Configure Consent Screen
1. **User Type**: Select **"External"** (unless you have Google Workspace)
2. Click **"Create"**

### 3.3 App Information
Fill in the required fields:
- **App name**: `MCP YouTube Uploader`
- **User support email**: Your email address
- **App logo**: (Optional) Upload a logo image
- **App domain**: (Optional) Leave blank for testing
- **Developer contact information**: Your email address

### 3.4 Scopes Configuration
1. Click **"Add or Remove Scopes"**
2. Search for and add: `https://www.googleapis.com/auth/youtube.upload`
3. Click **"Update"**
4. Click **"Save and Continue"**

### 3.5 Test Users (For Development)
1. Click **"Add Users"**
2. Add your email address (and any other Google accounts you want to test with)
3. Click **"Save and Continue"**

### 3.6 Summary
- Review your settings
- Click **"Back to Dashboard"**

## Step 4: Create OAuth2 Credentials

### 4.1 Navigate to Credentials
1. Go to **"APIs & Services"** → **"Credentials"**

### 4.2 Create OAuth2 Client ID
1. Click **"+ Create Credentials"**
2. Select **"OAuth client ID"**

### 4.3 Configure Application Type
1. **Application type**: Select **"Desktop application"**
2. **Name**: `MCP YouTube Upload Client`
3. Click **"Create"**

### 4.4 Download Credentials
1. A popup will show your **Client ID** and **Client Secret**
2. Click **"Download JSON"**
3. Save the file as `client_secrets.json`
4. **Important**: Keep this file secure and never commit it to version control!

## Step 5: Setup Environment Variables

### 5.1 Place Credentials File
```bash
# Create a secure directory for credentials
mkdir -p ~/.config/mcp-youtube/
mv ~/Downloads/client_secrets_*.json ~/.config/mcp-youtube/client_secrets.json
chmod 600 ~/.config/mcp-youtube/client_secrets.json
```

### 5.2 Set Environment Variable
Add to your shell profile (`.bashrc`, `.zshrc`, etc.):
```bash
export YOUTUBE_CREDENTIALS_FILE="$HOME/.config/mcp-youtube/client_secrets.json"
```

Or set temporarily:
```bash
export YOUTUBE_CREDENTIALS_FILE="/path/to/your/client_secrets.json"
```

## Step 6: Test the Integration

### 6.1 Verify Credentials
```bash
cd /path/to/mcp-ffmpeg-server
./test-youtube-upload.sh --upload
```

### 6.2 First OAuth2 Flow
1. The script will open your web browser
2. Sign in to Google if prompted
3. **Grant permissions** for YouTube upload access
4. Browser will show: "The authentication flow has completed"
5. Return to terminal - authentication is complete!

## Step 7: Production Considerations

### 7.1 Quota Limits
- **Default quota**: 10,000 units per day
- **Video upload cost**: 1,600 units per video
- **Practical limit**: ~6 uploads per day

### 7.2 Request Quota Increase (Optional)
If you need more uploads:
1. Go to **"APIs & Services"** → **"Quotas"**
2. Find **"YouTube Data API v3"**
3. Click **"Edit Quotas"**
4. Request higher limits (requires justification)

### 7.3 Publishing Status
- **Testing phase**: Videos uploaded as "Private"
- **Production**: Can upload as "Public", "Unlisted", or "Private"

### 7.4 App Verification (For Production)
For production apps that upload public videos:
1. Go to **OAuth consent screen**
2. Click **"Publish App"**
3. May require Google verification process

## Security Best Practices

### 8.1 Credential Security
```bash
# Correct permissions
chmod 600 client_secrets.json
chmod 600 token.json  # Created after first auth

# Never commit these files
echo "client_secrets.json" >> .gitignore
echo "token.json" >> .gitignore
```

### 8.2 Token Management
- **Access tokens**: Expire in 1 hour (auto-refreshed)
- **Refresh tokens**: Long-lived (6 months of inactivity)
- **Token storage**: Automatically managed in `token.json`

## Troubleshooting

### Common Issues

#### 1. "Access blocked" Error
**Solution**: Make sure OAuth consent screen is configured and your email is added as a test user.

#### 2. "Quota exceeded" Error  
**Solution**: You've hit the daily 10,000 unit limit. Wait 24 hours or request quota increase.

#### 3. "Invalid client" Error
**Solution**: Check that `client_secrets.json` is correctly formatted and credentials are valid.

#### 4. "Insufficient permissions" Error
**Solution**: Ensure the YouTube Data API v3 is enabled and OAuth scopes include `youtube.upload`.

### Debug Commands
```bash
# Test credentials file
python -c "import json; print(json.load(open('client_secrets.json'))['installed']['client_id'])"

# Check API status
curl "https://www.googleapis.com/youtube/v3/channels?part=id&mine=true" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Complete Example

Here's the complete flow in action:

```bash
# 1. Set credentials
export YOUTUBE_CREDENTIALS_FILE="$HOME/.config/mcp-youtube/client_secrets.json"

# 2. Run test (dry run)
./test-youtube-upload.sh

# 3. Upload to YouTube (real upload)
./test-youtube-upload.sh --upload

# 4. Check result
# Video will be uploaded as "Private" to your YouTube channel
```

## Next Steps

After completing this setup:

1. **✅ Credentials configured**: Environment variable set
2. **✅ First OAuth flow complete**: Token saved for future use  
3. **✅ Test upload successful**: Video uploaded to YouTube
4. **🎬 Ready for production**: Use MCP tools for automated uploads

Your YouTube direct upload integration is now fully operational! 🚀

---

## Quick Reference

**Key Files:**
- `client_secrets.json` - OAuth2 credentials (keep secure)  
- `token.json` - Access/refresh tokens (auto-generated)

**Key Environment Variable:**
- `YOUTUBE_CREDENTIALS_FILE` - Path to client_secrets.json

**MCP Tools:**
- `upload_youtube_video(file_id, title, description, tags)`
- `validate_youtube_video(file_id)`

**API Quotas:**
- Daily limit: 10,000 units
- Upload cost: 1,600 units
- Practical limit: ~6 uploads/day