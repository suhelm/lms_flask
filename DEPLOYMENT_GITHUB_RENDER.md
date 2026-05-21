# Complete GitHub + Render Deployment Guide

## Overview
This guide shows how to deploy the LMS system to GitHub and then live on Render.com in under 15 minutes.

---

## PART 1: SETUP GITHUB REPOSITORY (5 minutes)

### Step 1.1: Create GitHub Account
1. Go to https://github.com
2. Click "Sign up"
3. Create account (free)
4. Verify email

### Step 1.2: Create New Repository

1. Click "+" icon → "New repository"
2. Fill in:
   - **Repository name**: `lms-system`
   - **Description**: "Canvas-like Learning Management System"
   - **Visibility**: Public (required for free Render)
   - **Initialize with**: No (we'll add files)
3. Click "Create repository"

**You'll see:**
```
Quick setup — if you've done this kind of thing before

…or create a new repository on the command line
echo "# lms-system" >> README.md
git init
git add README.md
git commit -m "first commit"
git branch -M main
git push -u origin main
```

### Step 1.3: Copy Your Repository URL

Look at top of page - you'll see something like:
```
https://github.com/YOUR-USERNAME/lms-system.git
```

Copy this URL (you'll need it)

---

## PART 2: PUSH CODE TO GITHUB (5 minutes)

### Step 2.1: Prepare Files Locally

Make sure you have these files in your `lms-system` folder:

```
lms-system/
├── lms_system.py           ← Copy from outputs
├── lms_web_app.py          ← Copy from outputs
├── requirements.txt        ← Copy from outputs
├── render.yaml             ← Copy from outputs
├── .gitignore              ← Copy from outputs
└── README.md               ← Copy from outputs
```

Download all these files from the outputs folder.

### Step 2.2: Open Terminal/Command Prompt

Navigate to your `lms-system` folder:

```bash
cd path/to/lms-system
```

### Step 2.3: Initialize Git

```bash
# Initialize git
git init

# Configure git (replace with your GitHub email/name)
git config user.name "Your Name"
git config user.email "your-email@example.com"
```

### Step 2.4: Add Files to Git

```bash
# Add all files
git add .

# Check what will be committed
git status
```

You should see:
```
On branch master
Changes to be committed:
        new file:   .gitignore
        new file:   README.md
        new file:   lms_system.py
        new file:   lms_web_app.py
        new file:   render.yaml
        new file:   requirements.txt
```

### Step 2.5: Commit

```bash
git commit -m "Initial LMS system commit"
```

### Step 2.6: Add Remote & Push

```bash
# Replace YOUR-USERNAME with your actual GitHub username
git remote add origin https://github.com/YOUR-USERNAME/lms-system.git

# Rename branch to main (GitHub default)
git branch -M main

# Push to GitHub
git push -u origin main
```

**First time Git might ask for password:**
```
Username for 'https://github.com': YOUR-USERNAME
Password for 'https://YOUR-USERNAME@github.com': 
(your GitHub password or Personal Access Token)
```

### Step 2.7: Verify on GitHub

Go to https://github.com/YOUR-USERNAME/lms-system

You should see all your files there! ✓

---

## PART 3: DEPLOY ON RENDER (5 minutes)

### Step 3.1: Create Render Account

1. Go to https://render.com
2. Click "Sign up"
3. Choose "Sign up with GitHub" (easiest)
4. Authorize Render to access your GitHub

### Step 3.2: Create Web Service

1. Click "New +" button (top right)
2. Select "Web Service"
3. **Connect Repository**:
   - Click "Connect" next to `lms-system` repo
   - Render will scan it

### Step 3.3: Configure Service

Fill in the form:

```
Name: lms-system
(or anything you want)

Environment: Python 3
Region: Oregon (US) [closest to you]

Build Command: pip install -r requirements.txt

Start Command: gunicorn lms_web_app:app

Plan: Free
```

### Step 3.4: Set Environment Variables

Scroll down to "Environment Variables" section

Click "Add Environment Variable" and add:

```
Key: FLASK_ENV
Value: production

Key: SECRET_KEY
Value: dev-secret-key-change-in-production

Key: PYTHON_VERSION
Value: 3.11.0
```

### Step 3.5: Deploy

Click **"Create Web Service"**

**You'll see build progress:**
```
Building...
=== Fetching build plan from https://github.com/YOUR-USERNAME/lms-system.git...
=== Cloning repository...
=== Building application...
=== Installing Python dependencies...
Collecting Flask==2.3.0
  Downloading Flask-2.3.0-py3-none-any.whl
Installing collected packages: Flask, Gunicorn...
Successfully installed Flask-2.3.0 Gunicorn-21.2.0...
=== Build complete
=== Starting application...
Listening on 0.0.0.0:10000
```

**Wait 3-5 minutes for deployment to complete**

### Step 3.6: Access Your Live App

Once deployed, you'll see:
```
https://lms-system.onrender.com
```

Click this link! ✓

Your LMS is now LIVE! 🎉

---

## PART 4: INITIALIZE DATABASE ON RENDER

### Step 4.1: SSH into Render Instance

In Render dashboard:
1. Go to your service
2. Click "Shell" tab
3. You get a terminal

### Step 4.2: Initialize Database

In the shell, run:

```bash
python lms_system.py
```

This creates the SQLite database with test users.

### Step 4.3: Test Login

Go to your Render URL: https://lms-system.onrender.com

**Login as teacher:**
- Username: `prof_smith`
- Password: `password123`

**Or login as student:**
- Username: `student1`
- Password: `password123`

---

## PART 5: UPDATES & CHANGES (For Future)

### When you make changes locally:

```bash
# Make your code changes
# Then:

git add .
git commit -m "Description of changes"
git push origin main
```

**Render automatically redeploys when you push!** ✓

---

## PART 6: TROUBLESHOOTING

### Build Failed?

**Check logs:**
1. Go to Render dashboard
2. Click "Logs" tab
3. Scroll to see errors

**Common issues:**

**Error: "gunicorn: not found"**
- Fix: Add to `requirements.txt`:
```
Flask==2.3.0
Gunicorn==21.2.0
```

**Error: "ModuleNotFoundError: No module named 'lms_system'"**
- Fix: Make sure `lms_system.py` is in root directory (same as `lms_web_app.py`)

**Error: "Python version mismatch"**
- Fix: In Environment Variables, set:
```
PYTHON_VERSION=3.11.0
```

### App Running But Shows Error?

Check logs (same as above) and look for:

```
File "lms_web_app.py", line X, in ...
ImportError: cannot import name ...
```

Make sure both files are uploaded correctly.

### Can't Connect to https://lms-system.onrender.com?

Wait 5 minutes - free tier starts slowly.

Then try:
1. Hard refresh: Ctrl+Shift+R (or Cmd+Shift+R on Mac)
2. Try incognito mode
3. Check Render dashboard for "Deploy in Progress"

---

## FINAL CHECKLIST

- [ ] GitHub account created
- [ ] Repository created and named `lms-system`
- [ ] All 6 files committed to GitHub
- [ ] Render account created (via GitHub)
- [ ] Web Service created on Render
- [ ] Environment variables set
- [ ] Build completed successfully
- [ ] Database initialized (python lms_system.py)
- [ ] Can login at https://lms-system.onrender.com
- [ ] Test login works (prof_smith / password123)

---

## YOUR LIVE APP STATS

```
URL: https://lms-system.onrender.com
Status: ✓ Live
Database: SQLite (in-memory, persists)
Max Users: ∞ (limited by Render free tier)
Uptime: 24/7
Cost: FREE
```

---

## NEXT STEPS

### To Add Real Users:

1. **Via Web UI**: Click "Register" on login page
2. **Via Code**: Run this in Python:

```python
from lms_system import AuthenticationManager, DatabaseManager

db = DatabaseManager("lms.db")
auth = AuthenticationManager(db)

success, msg = auth.register_user(
    username="alice",
    email="alice@university.edu",
    password="secure_password",
    first_name="Alice",
    last_name="Johnson",
    role="student"
)
print(msg)
```

### To Scale Beyond Free Tier:

When you need more power:
1. Upgrade Render plan ($7-12/month)
2. Switch to PostgreSQL instead of SQLite
3. Add Redis for caching
4. Enable auto-scaling

---

## MONITORING YOUR APP

**In Render Dashboard:**

1. **Logs** - See all activity
2. **Events** - Deploy history
3. **Metrics** - CPU, memory, requests
4. **Settings** - Environment variables, redeploy

**Check Health:**
```
https://lms-system.onrender.com/api/health
```

Should return:
```json
{"status": "healthy"}
```

---

## SHARING YOUR APP

Your public URL:
```
https://lms-system.onrender.com
```

Share with:
- Teachers: Use prof_smith credentials
- Students: Create accounts via Register page
- Admins: Can modify roles via database

---

## FURTHER CUSTOMIZATION

### Change App Name (after deploying)

```bash
git clone https://github.com/YOUR-USERNAME/lms-system.git my-university-lms
```

Then push to new repo:
```bash
cd my-university-lms
git remote set-url origin https://github.com/YOUR-USERNAME/my-university-lms.git
git push origin main
```

### Add Custom Domain

In Render dashboard → Settings → Custom Domain

Requires domain (like university.edu)

### Add Database Backups

Upgrade to Postgres + enable automated backups

---

## SUCCESS! 🎉

Your LMS is now:
✅ On GitHub (version control)
✅ Deployed on Render (publicly accessible)
✅ Running live on the internet
✅ Free tier ($0/month)
✅ Scalable when needed

**Share the URL with your institution and start using it!**

---

## SUPPORT

- **Issues?** Check Render logs
- **Code problems?** Review `LMS_SETUP_GUIDE.md`
- **Deployment help?** See Part 6: Troubleshooting
- **GitHub help?** Visit github.com/docs

---

**Congratulations on deploying your LMS! 🚀**

Next: Create courses, enroll students, and start using it!
