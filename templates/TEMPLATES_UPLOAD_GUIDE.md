# Add HTML Templates to GitHub

## Quick Fix for TemplateNotFound Error

Your Flask app is looking for HTML templates but can't find them. Here's how to fix:

### Option 1: Upload via GitHub Web Interface (Easiest)

1. **Go to your repo:**
   ```
   https://github.com/suhelm/lms_flask
   ```

2. **Create templates folder:**
   - Click "Add file" → "Create new file"
   - Type filename: `templates/login.html`
   - GitHub will auto-create the `templates/` folder
   - Copy content from `login.html` (provided)
   - Click "Commit changes"

3. **Add all templates:**
   - `templates/login.html` ← Copy from outputs
   - `templates/register.html` ← Copy from outputs
   - `templates/404.html` ← Copy from outputs
   - `templates/500.html` ← Copy from outputs
   - `templates/teacher/dashboard.html` ← Copy from outputs
   - `templates/student/dashboard.html` ← Copy from outputs

4. **Redeploy on Render:**
   - Go to Render dashboard
   - Click "Redeploy Latest Commit"
   - Wait 2-3 minutes

---

### Option 2: Push from Local (If you have files)

```bash
# Navigate to project folder
cd /path/to/lms_flask

# Create templates folder structure
mkdir -p templates/teacher
mkdir -p templates/student

# Copy HTML files (from outputs folder):
# - Copy login.html to templates/
# - Copy register.html to templates/
# - Copy 404.html to templates/
# - Copy 500.html to templates/
# - Copy teacher/dashboard.html to templates/teacher/
# - Copy student/dashboard.html to templates/student/

# Add to git
git add templates/

# Commit
git commit -m "Add HTML templates"

# Push to GitHub
git push origin main
```

Render will auto-redeploy!

---

## Folder Structure You Need

After adding templates, your GitHub should look like:

```
lms_flask/
├── lms_system.py
├── lms_web_app.py
├── requirements.txt
├── render.yaml
├── .gitignore
├── README.md
└── templates/                    ← NEW FOLDER
    ├── login.html              ← NEW FILE
    ├── register.html           ← NEW FILE
    ├── 404.html                ← NEW FILE
    ├── 500.html                ← NEW FILE
    ├── teacher/                ← NEW FOLDER
    │   └── dashboard.html      ← NEW FILE
    └── student/                ← NEW FOLDER
        └── dashboard.html      ← NEW FILE
```

---

## Files You Need to Create

Download these 6 HTML files from outputs and add them:

1. **templates/login.html** - Login page
2. **templates/register.html** - Registration page
3. **templates/404.html** - 404 error page
4. **templates/500.html** - 500 error page
5. **templates/teacher/dashboard.html** - Teacher dashboard
6. **templates/student/dashboard.html** - Student dashboard

---

## Fastest Way (Copy-Paste in GitHub)

1. Go to: https://github.com/suhelm/lms_flask
2. Click **Add file** → **Create new file**
3. In filename field, type: `templates/login.html`
4. GitHub auto-creates folder
5. Paste the login.html content from outputs
6. Click **Commit changes**
7. Repeat for each file

---

## After Adding Templates

1. Go to Render dashboard
2. Click your service
3. Click **Redeploy Latest Commit**
4. Wait 3 minutes
5. Visit your URL

Your app should now show proper login page! ✓

---

## Troubleshooting

**Still getting TemplateNotFound error?**

Check folder names match exactly:
- ✓ `templates/` (lowercase, no space)
- ✓ `templates/teacher/` (lowercase folder)
- ✓ `templates/student/` (lowercase folder)
- ✓ `login.html` (exact filename)

**Can't see templates in GitHub?**

Click the folder icon in GitHub, not "Code" tab. Templates folder might be collapsed.

---

## Test After Deployment

Once deployed, visit:
```
https://lms-flask-qzoh.onrender.com/login
```

Should show beautiful login page (not 502 error) ✓

---

Done! Your app will work perfectly now. 🎉
