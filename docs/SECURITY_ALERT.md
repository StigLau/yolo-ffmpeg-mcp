# 🚨 CRITICAL SECURITY ALERT - API KEY LEAK PREVENTION

## ⚠️ INCIDENT SUMMARY (2025-07-27)

**CRITICAL**: Google API keys were accidentally exposed in git history:
- **KompostEdit API Key**: `AIzaSyC4Hap5RqvrkBSCbwmBb1Kaog3PgQsQsWA` 
- **Kompost-Mixer API Key**: `AIzaSyAeqegM0PgYofXtjBFZ_VtDZ0twJ0_yack`

**Root Cause**: Webapp files from kompost-mixer project were merged into this FFMPEG MCP repository, exposing Firebase API keys in:
- `FIREBASE_SETUP_GUIDE.md` 
- `env.example`

**Resolution**: Used `git-filter-repo` to remove API keys from entire git history and force-pushed cleaned repo.

## 🛡️ IMMEDIATE SECURITY ACTIONS REQUIRED

### 1. **REGENERATE COMPROMISED API KEYS** ⚡
- [ ] Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
- [ ] Find project "KompostEdit" (id: kompostedit)
- [ ] Regenerate the compromised API key `AIzaSyC4Hap5RqvrkBSCbwmBb1Kaog3PgQsQsWA`
- [ ] Add proper API key restrictions
- [ ] Update applications using this key

### 2. **AUDIT GCP USAGE** 📊
- [ ] Review billing activity for unexpected usage
- [ ] Check API logs for unauthorized access
- [ ] Verify no malicious activity occurred

## 🔒 PREVENTION PROTOCOLS - NEVER AGAIN!

### **CRITICAL RULES FOR ANY REPOSITORY**

1. **NEVER commit actual API keys**:
   ```bash
   # ❌ WRONG - Never do this
   FIREBASE_API_KEY=AIzaSyC4Hap5RqvrkBSCbwmBb1Kaog3PgQsQsWA
   
   # ✅ CORRECT - Use placeholder
   FIREBASE_API_KEY=your_api_key_here
   ```

2. **Use .gitignore for sensitive files**:
   ```gitignore
   # Environment files
   .env
   .env.local
   .env.production
   .env.staging
   
   # Firebase config
   firebase-admin-key.json
   google-services.json
   ```

3. **Use environment-specific examples**:
   ```bash
   # In env.example - safe to commit
   FIREBASE_API_KEY=your_api_key_here
   FIREBASE_PROJECT_ID=your_project_id
   
   # In .env.local - NEVER commit
   FIREBASE_API_KEY=AIzaSyC4Hap5RqvrkBSCbwmBb1Kaog3PgQsQsWA
   FIREBASE_PROJECT_ID=kompostedit
   ```

### **SECURITY CHECKS BEFORE EVERY COMMIT**

```bash
# Check for API keys before committing
git diff --cached | grep -i "AIza\|ya29\|1//"
git diff --cached | grep -i "api.*key\|secret\|token"

# Use git-secrets (install once)
git secrets --scan
```

### **PROJECT SEPARATION SECURITY**

- **NEVER merge different projects** that might contain credentials
- **This incident happened because**: kompost-mixer webapp was merged into FFMPEG MCP repo
- **Always verify**: what files you're bringing in when merging projects

### **EMERGENCY RESPONSE CHECKLIST**

If API keys are accidentally committed:

1. **STOP** - Don't push if not pushed yet
2. **REGENERATE** API keys immediately  
3. **CLEAN GIT HISTORY**:
   ```bash
   # Install git-filter-repo
   uv pip install git-filter-repo
   
   # Remove API keys from history
   echo "leaked_api_key_here" > /tmp/secrets_to_remove.txt
   git-filter-repo --replace-text /tmp/secrets_to_remove.txt --force
   
   # Force push cleaned history
   git remote add origin https://github.com/user/repo.git
   git push origin main --force
   ```
4. **NOTIFY** - Alert team if applicable
5. **AUDIT** - Check for unauthorized usage

## 📋 POST-INCIDENT DOCUMENTATION

- **Date**: 2025-07-27 12:48 PM
- **Detection**: Google Cloud Platform automatic security alert
- **Response Time**: ~1 hour
- **Resolution**: API keys removed from git history, force-pushed
- **Follow-up**: API key regeneration required

## 🎯 LESSONS LEARNED

1. **Project separation is critical** - Never merge unrelated projects with different security contexts
2. **Git history is permanent** - Even "deleted" files remain in history until explicitly cleaned
3. **Automation helps** - Google's detection saved us from prolonged exposure
4. **Multiple layers** - API keys were in both documentation AND example files

---

**⚡ REMEMBER: Security is everyone's responsibility. When in doubt, ask!**