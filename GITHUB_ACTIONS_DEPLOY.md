# GitHub Actions Deployment Guide

## 🚀 Free 24/7 Automated XAUUSD Analysis

Deploy your XAUUSD AI trading system using **GitHub Actions** for completely free! Your analysis will run automatically every **10 minutes** during market hours.

---

## ✅ Prerequisites

1. **GitHub Account** (free) - Sign up at https://github.com/signup
2. **Gmail Account** with App Password
3. **Your code uploaded to GitHub**

---

## 📋 Step 1: Create GitHub Repository

### Option A: Using Web Interface (No Git Required)

1. Go to https://github.com/new
2. Fill in:
   - **Repository name**: `xauusd-ai-analyst`
   - **Visibility**: ✅ **PRIVATE** (important for security!)
   - **Add README**: ✅ Check this box
3. Click **"Create repository"**

4. Upload your files:
   - Click **"Add file"** → **"Upload files"**
   - Drag and drop these folders/files:
     ```
     ✅ .github/         (entire folder with workflow)
     ✅ src/             (entire folder)
     ✅ schema.sql
     ✅ prop_firm_config.json
     ✅ requirements.txt
     ✅ .gitignore
     ✅ README.md
     ```
   - **⚠️ SKIP**: `email_config.json`, `database.db`, `__pycache__`
   - Commit message: "Initial commit - XAUUSD AI System"
   - Click **"Commit changes"**

---

## 🔐 Step 2: Set Up Gmail App Password

1. Go to https://myaccount.google.com/apppasswords
2. Sign in to your Gmail account
3. Create an app password:
   - **App name**: "XAUUSD Trading Bot"
   - Click **"Create"**
4. **Copy the 16-character password** (you'll need this in Step 3)

---

## 🔑 Step 3: Configure GitHub Secrets

GitHub Secrets store your email credentials securely (encrypted).

1. Go to your repository on GitHub
2. Click **"Settings"** (top menu)
3. In left sidebar: **"Secrets and variables"** → **"Actions"**
4. Click **"New repository secret"** and add these **3 secrets**:

### Secret 1: EMAIL_USER
- **Name**: `EMAIL_USER`
- **Value**: Your full Gmail address (e.g., `yourname@gmail.com`)
- Click **"Add secret"**

### Secret 2: EMAIL_PASSWORD
- **Name**: `EMAIL_PASSWORD`
- **Value**: The 16-character App Password from Step 2
- Click **"Add secret"**

### Secret 3: EMAIL_RECIPIENT
- **Name**: `EMAIL_RECIPIENT`
- **Value**: Email where you want to receive trade alerts (can be same as EMAIL_USER)
- Click **"Add secret"**

✅ You should now have **3 secrets** configured!

---

## ⚙️ Step 4: Enable GitHub Actions

1. In your repository, click **"Actions"** (top menu)
2. If prompted, click **"I understand my workflows, go ahead and enable them"**
3. You should see your workflow: **"XAUUSD AI Analysis"**

### Run Your First Analysis (Manual Test)

1. Click on **"XAUUSD AI Analysis"** workflow
2. Click **"Run workflow"** (right side)
3. Click the green **"Run workflow"** button
4. Wait 1-2 minutes
5. Click on the running workflow to see logs

✅ **Success indicators:**
- Green checkmark ✅
- "Run live analysis" step completes
- Check your email for alerts (if valid setup detected)

---

## 📊 Step 5: Monitor Your System

### View Workflow Runs
- Go to **"Actions"** tab in your repository
- See all analysis runs (every 10 minutes)
- Click any run to see detailed logs

### Check Logs
```
✅ Market Analysis Complete
✅ Email Alert Sent
✅ Database Updated
```

### Database Persistence
- Your trading history is saved as a GitHub Artifact
- Automatically persists between runs
- Accessible for 90 days

---

## 🔧 Troubleshooting

### ❌ Workflow Fails with "Authentication Error"
**Solution**: Check GitHub Secrets
- Make sure all 3 secrets are set correctly
- Re-create the `EMAIL_PASSWORD` secret with a fresh App Password
- Ensure no extra spaces in secret values

### ❌ "No module named 'xyz'"
**Solution**: Missing dependency
- Check that `requirements.txt` is uploaded
- Verify all dependencies are listed
- Re-run the workflow

### ❌ No Email Alerts Received
**Possible reasons**:
1. No valid trade setups detected (market conditions)
2. Outside trading sessions (London: 07:00-11:00 UTC, NY: 13:00-16:00 UTC)
3. Email credentials incorrect

**Check logs**:
- Go to Actions → Click latest run
- Look for "Email Alert" messages
- "NO TRADE" verdicts are normal (strict filters)

### ❌ "Market Closed" Message
✅ This is **NORMAL**! The system:
- Automatically detects London/New York sessions
- Skips analysis outside these hours
- Prevents trading during low liquidity periods

---

## 📈 Understanding the Schedule

### Cron Schedule: `*/10 * * * *`
- Runs **every 10 minutes**, 24/7
- Automatically skips when market is closed
- Only analyzes during London & New York sessions

### Free Tier Limits
- **2,000 minutes/month** for private repos (enough!)
- **Unlimited** for public repos
- Each run uses ~1-2 minutes
- = ~200-300 analyses per month (plenty)

If you exceed limits (unlikely), workflow pauses until next month.

---

## 🛠️ Customization

### Change Analysis Frequency

Edit `.github/workflows/xauusd-analysis.yml`:

```yaml
schedule:
  - cron: '*/10 * * * *'  # Every 10 minutes
  # - cron: '*/5 * * * *'   # Every 5 minutes
  # - cron: '*/15 * * * *'  # Every 15 minutes
  # - cron: '0 * * * *'     # Every hour
```

### Disable Workflow Temporarily

1. Go to **"Actions"** tab
2. Click **"XAUUSD AI Analysis"**
3. Click **"•••"** (3 dots) → **"Disable workflow"**

Re-enable anytime the same way!

---

## 🎯 Next Steps

✅ Your system is now running 24/7 for FREE!

**What happens next:**
1. Analysis runs every 10 minutes
2. Valid setups trigger email alerts
3. All data persists in database artifact
4. Review performance weekly

**Weekly Review:**
```bash
# Run locally to see performance report
python src/main.py --mode review
```

---

## 📧 Email Alert Format

You'll receive professional HTML emails with:
- 📊 **Trade Details**: Entry, SL, TP, R:R
- 💰 **Position Sizing**: Risk amount, lot size, leverage
- 📈 **Market Context**: Session, trend, liquidity events
- 🎯 **Probability Score**: ML-powered success prediction

---

## 🔒 Security Notes

### ✅ Safe Practices:
- Repository is **PRIVATE**
- Secrets are **encrypted** by GitHub
- Email config is **NOT** uploaded to GitHub
- All credentials stored as **GitHub Secrets**

### ⚠️ Never:
- Share your App Password
- Upload `email_config.json` to GitHub
- Make the repository public with secrets

---

## 💡 Pro Tips

1. **Check emails regularly** - Don't miss valid setups!
2. **Review logs weekly** - Understand why trades were skipped
3. **Monitor during high-impact news** - System auto-avoids these
4. **Backtest improvements** - Use learning module for optimization

---

## 🆘 Need Help?

**Common Issues:**
- Actions tab → Click failed run → Check error logs
- Settings → Secrets → Verify all 3 secrets exist
- Test locally first: `python src/main.py --mode live --session AUTO`

**Resources:**
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Gmail App Passwords](https://support.google.com/accounts/answer/185833)

---

## 🎉 Congratulations!

Your XAUUSD AI system is now deployed and running automatically. No servers, no hosting fees - just professional-grade analysis delivered to your inbox! 📧📈
