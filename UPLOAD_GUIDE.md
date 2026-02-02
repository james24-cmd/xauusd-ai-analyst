# GitHub Upload Guide (Without Git)

Since Git is not installed, follow these steps to upload your code to GitHub:

## Step 1: Create GitHub Account & Repository

1. Go to https://github.com/signup
2. Create an account (if you don't have one)
3. Click the **"+"** icon (top right) → **"New repository"**
4. **Repository name**: `xauusd-ai-analyst`
5. **Visibility**: ⚠️ **PRIVATE** (important for security!)
6. ✅ Check **"Add a README file"**
7. Click **"Create repository"**

## Step 2: Upload Files via Web Interface

1. In your new repository, click **"Add file"** → **"Upload files"**
2. Drag and drop these folders/files:
   ```
   ✅ src/           (entire folder)
   ✅ schema.sql
   ✅ prop_firm_config.json
   ✅ email_config.json
   ✅ requirements.txt
   ✅ build.sh
   ✅ start.sh
   ✅ .gitignore
   ✅ README.md
   ```

3. **⚠️ SKIP**: `database.db`, `test_email.py`, `__pycache__`

4. Commit message: "Initial commit - XAUUSD AI System"
5. Click **"Commit changes"**

## Step 3: Deploy for 24/7 Automation

### ⭐ Option 1: GitHub Actions (FREE & RECOMMENDED)

1. **See full guide**: `GITHUB_ACTIONS_DEPLOY.md`
2. **Quick Summary**:
   - Configure GitHub Secrets (EMAIL_USER, EMAIL_PASSWORD, EMAIL_RECIPIENT)
   - Enable GitHub Actions in your repo
   - Runs automatically every 10 minutes
   - Completely FREE (no credit card needed!)

### Option 2: Render.com (Paid)

⚠️ **Note**: Render no longer offers a free tier

1. Go to https://render.com
2. Sign up with your GitHub account
3. Click **"New +"** → **"Cron Job"**
   - **Name**: `xauusd-ai-cron`
   - **Region**: Oregon (US West)
   - **Repository**: Select `xauusd-ai-analyst`
   - **Schedule**: `*/10 * * * *`
   - **Command**: `python src/main.py --mode live --session AUTO`
4. Click **"Create"**

## Step 4: Monitor

### For GitHub Actions:
1. Go to your repo → **"Actions"** tab
2. View workflow runs (every 10 minutes)
3. Click any run to see detailed logs
4. Email alerts sent automatically for valid setups!

### For Render:
1. Go to Dashboard → Your service → **Logs**
2. You'll see analysis running every 10 minutes
3. Email alerts will be sent automatically!

## Troubleshooting

**If deployment fails:**
- Check Logs for errors
- Verify all files were uploaded
- Ensure `requirements.txt` is present

**To update code later:**
- Go to GitHub repo → Upload files again
- Render auto-deploys changes

## Security Note

Your `email_config.json` contains your password. That's why the repo MUST be **PRIVATE**.

For extra security, you can:
1. On Render, add Environment Variable: `EMAIL_PASSWORD`
2. Remove password from `email_config.json`
3. Update code to read from environment
