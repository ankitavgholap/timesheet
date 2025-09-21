# 📋 Developer Setup Instructions - ActivityWatch Team Integration

## 🎯 What You Need to Do

You only need to do **TWO SIMPLE THINGS**:

1. **Install ActivityWatch** (if not already installed)
2. **Replace one config file**

That's it! No Python scripts, no additional software, no complex setup.

---

## ✅ Step 1: Install ActivityWatch

### If ActivityWatch is NOT installed:
1. Download from [activitywatch.net](https://activitywatch.net/)
2. Install and run it once to create the config directory
3. Close ActivityWatch

### If ActivityWatch IS already installed:
1. Close ActivityWatch completely
2. Proceed to Step 2

---

## ✅ Step 2: Add Config File

### Find your ActivityWatch config directory:

**Windows:**
```
%APPDATA%\activitywatch\aw-server\config.toml
```
*Full path example: `C:\Users\YourName\AppData\Roaming\activitywatch\aw-server\config.toml`*

**Linux:**
```
~/.config/activitywatch/aw-server/config.toml
```

**macOS:**
```
~/Library/Application Support/activitywatch/aw-server/config.toml
```

### Replace/Create the config.toml file:

1. **Navigate** to the config directory above
2. **Replace** the existing `config.toml` file (or create it if it doesn't exist)  
3. **Copy** the contents from your provided `{DEVELOPER_ID}_config.toml` file
4. **Save** the file

### Your config.toml should look like this:
```toml
# ActivityWatch Configuration for Your Name
[server]
host = "127.0.0.1"
port = 5600

[integrations.timesheet]
enabled = true
webhook_url = "https://your-server.com/api/v1/activitywatch/webhook"
developer_id = "your-dev-id"
api_token = "your-token"
sync_interval = 1800  # 30 minutes

# ... rest of config
```

---

## ✅ Step 3: Restart ActivityWatch

1. **Start ActivityWatch** normally
2. **Use your computer** as usual
3. **That's it!** Data will automatically sync every 30 minutes

---

## 🔍 How to Verify It's Working

### After 30+ minutes of computer use:

1. **Check ActivityWatch logs** for webhook messages:
   - Windows: `%APPDATA%\activitywatch\aw-server\logs\`
   - Linux/Mac: `~/.local/share/activitywatch/log/`

2. **Visit team dashboard**: [Your Team Dashboard URL]

3. **Look for your name** in the developer list

### You should see log messages like:
```
INFO: Sending webhook data to team server
INFO: Webhook sent successfully
```

---

## ❗ Troubleshooting

### "Webhook failing" or "Connection error"
- ✅ Check your internet connection
- ✅ Verify you can access the team dashboard URL in your browser
- ✅ Try restarting ActivityWatch

### "Config file not found"
- ✅ Make sure you're in the right directory
- ✅ Create the `aw-server` folder if it doesn't exist
- ✅ The file must be named exactly `config.toml`

### "ActivityWatch not starting"
- ✅ Close all ActivityWatch processes completely
- ✅ Wait 10 seconds
- ✅ Start ActivityWatch again

### Still having issues?
Contact your system administrator with:
- Your developer ID: `{DEVELOPER_ID}`
- Error messages from ActivityWatch logs
- Screenshot of the error

---

## 🔐 Privacy Information

### What gets sent to the server:
- ✅ **Application names** (e.g., "Chrome", "VS Code")
- ✅ **Window titles** (e.g., "project.py - VS Code") 
- ✅ **Time durations** (how long you used each app)
- ✅ **Timestamps** (when activities occurred)

### What does NOT get sent:
- ❌ **File contents** (your code, documents, etc.)
- ❌ **Keystrokes** or what you type
- ❌ **Screenshots** or visual data
- ❌ **Personal browsing** (automatically filtered)

### Security:
- 🔒 All data is **encrypted** during transmission (HTTPS)
- 🔒 Only **your team dashboard** can access your data
- 🔒 Your **ActivityWatch data stays local** on your machine

---

## 📊 What You'll Get

### Personal Benefits:
- **Track your productivity** patterns
- **See time allocation** across projects
- **Understand focus sessions** and deep work
- **No manual time tracking** needed

### Team Benefits:
- **Team productivity insights** for management
- **Project time allocation** visibility
- **Team collaboration** patterns
- **Data-driven work optimization**

---

## 🎉 That's It!

Once you've replaced the config file and restarted ActivityWatch:
- ✅ **Everything is automatic**
- ✅ **No more setup needed**
- ✅ **Works silently in background**
- ✅ **Data syncs every 30 minutes**

Your productivity data will start appearing in the team dashboard within 30-60 minutes of normal computer use.

**Welcome to the team productivity tracking system! 🚀**
