# Cron Jobs Setup Guide for FCM Notifications

This guide shows how to set up cron jobs as an alternative to Celery for scheduled tasks.

## Available Management Commands

The app includes the following Django management commands that can be run via cron:

### 1. Send Scheduled Notifications
**Command:** `send_scheduled_notifications`

Processes and sends all pending notifications that are scheduled to be sent.

```bash
python manage.py send_scheduled_notifications
```

**Options:**
- `--dry-run`: Preview what would be sent without actually sending

**Example:**
```bash
# Dry run to see what would be sent
python manage.py send_scheduled_notifications --dry-run

# Actually send notifications
python manage.py send_scheduled_notifications
```

### 2. Cleanup Old Logs
**Command:** `cleanup_old_logs`

Deletes notification logs older than a specified number of days.

```bash
python manage.py cleanup_old_logs
```

**Options:**
- `--days N`: Delete logs older than N days (default: 90)
- `--dry-run`: Preview what would be deleted

**Example:**
```bash
# Delete logs older than 90 days (default)
python manage.py cleanup_old_logs

# Delete logs older than 30 days
python manage.py cleanup_old_logs --days 30

# Dry run
python manage.py cleanup_old_logs --days 30 --dry-run
```

### 3. Cleanup Inactive Tokens
**Command:** `cleanup_inactive_tokens`

Deletes inactive device tokens that haven't been used for a specified period.

```bash
python manage.py cleanup_inactive_tokens
```

**Options:**
- `--days N`: Delete tokens not used for N days (default: 90)
- `--dry-run`: Preview what would be deleted

**Example:**
```bash
# Delete inactive tokens not used for 90 days (default)
python manage.py cleanup_inactive_tokens

# Delete inactive tokens not used for 60 days
python manage.py cleanup_inactive_tokens --days 60

# Dry run
python manage.py cleanup_inactive_tokens --days 60 --dry-run
```

### 4. Test FCM Connection
**Command:** `test_fcm`

Tests FCM connection and sends a test notification.

```bash
python manage.py test_fcm
```

**Options:**
- `--token TOKEN`: Send to specific FCM token
- `--user-id USER_ID`: Send to user's first active device

**Example:**
```bash
# Use first available active device
python manage.py test_fcm

# Send to specific token
python manage.py test_fcm --token "fcm_token_here"

# Send to specific user
python manage.py test_fcm --user-id 1
```

---

## Setting Up Cron Jobs

### Linux/macOS Setup

#### 1. Edit Crontab
```bash
crontab -e
```

#### 2. Add Cron Jobs

Add the following lines (adjust paths and schedules as needed):

```bash
# Set environment variables
SHELL=/bin/bash
PATH=/usr/local/bin:/usr/bin:/bin
DJANGO_SETTINGS_MODULE=your_project.settings

# Python and project paths
PYTHON=/path/to/your/venv/bin/python
PROJECT_DIR=/path/to/your/django/project

# Send scheduled notifications every 5 minutes
*/5 * * * * cd $PROJECT_DIR && $PYTHON manage.py send_scheduled_notifications >> /var/log/fcm_scheduled.log 2>&1

# Cleanup old logs daily at 2 AM
0 2 * * * cd $PROJECT_DIR && $PYTHON manage.py cleanup_old_logs >> /var/log/fcm_cleanup_logs.log 2>&1

# Cleanup inactive tokens weekly on Monday at 3 AM
0 3 * * 1 cd $PROJECT_DIR && $PYTHON manage.py cleanup_inactive_tokens >> /var/log/fcm_cleanup_tokens.log 2>&1
```

#### 3. Example with Full Paths

```bash
# Send scheduled notifications every 5 minutes
*/5 * * * * cd /var/www/myproject && /var/www/myproject/venv/bin/python manage.py send_scheduled_notifications >> /var/log/fcm_scheduled.log 2>&1

# Cleanup old logs daily at 2 AM
0 2 * * * cd /var/www/myproject && /var/www/myproject/venv/bin/python manage.py cleanup_old_logs --days 90 >> /var/log/fcm_cleanup_logs.log 2>&1

# Cleanup inactive tokens weekly on Monday at 3 AM
0 3 * * 1 cd /var/www/myproject && /var/www/myproject/venv/bin/python manage.py cleanup_inactive_tokens --days 90 >> /var/log/fcm_cleanup_tokens.log 2>&1
```

#### 4. Verify Cron Jobs
```bash
# List current cron jobs
crontab -l

# Check cron logs
tail -f /var/log/fcm_scheduled.log
```

---

## Cron Schedule Examples

### Common Cron Patterns

```bash
# Every minute
* * * * * command

# Every 5 minutes
*/5 * * * * command

# Every 15 minutes
*/15 * * * * command

# Every hour at minute 0
0 * * * * command

# Every day at midnight
0 0 * * * command

# Every day at 2 AM
0 2 * * * command

# Every Monday at 3 AM
0 3 * * 1 command

# Every first day of month at midnight
0 0 1 * * command

# Weekdays only at 9 AM
0 9 * * 1-5 command

# Every 6 hours
0 */6 * * * command
```

### Recommended Schedules

```bash
# Send scheduled notifications: Every 5 minutes
*/5 * * * * python manage.py send_scheduled_notifications

# Cleanup old logs: Daily at 2 AM
0 2 * * * python manage.py cleanup_old_logs

# Cleanup inactive tokens: Weekly on Monday at 3 AM
0 3 * * 1 python manage.py cleanup_inactive_tokens
```

---

## Windows Task Scheduler Setup

### 1. Create Batch File

Create `send_scheduled_notifications.bat`:

```batch
@echo off
cd C:\path\to\your\django\project
C:\path\to\your\venv\Scripts\python.exe manage.py send_scheduled_notifications >> C:\logs\fcm_scheduled.log 2>&1
```

### 2. Create Task in Task Scheduler

1. Open Task Scheduler
2. Click "Create Basic Task"
3. Name: "FCM Send Scheduled Notifications"
4. Trigger: Daily or Custom
5. Action: Start a program
6. Program/script: `C:\path\to\send_scheduled_notifications.bat`
7. Set repeat interval (e.g., every 5 minutes for 1 day)

### 3. Example PowerShell Script

Create `fcm_tasks.ps1`:

```powershell
$PYTHON = "C:\path\to\venv\Scripts\python.exe"
$PROJECT = "C:\path\to\django\project"
$LOG_DIR = "C:\logs"

# Ensure log directory exists
New-Item -ItemType Directory -Force -Path $LOG_DIR

# Send scheduled notifications
Set-Location $PROJECT
& $PYTHON manage.py send_scheduled_notifications >> "$LOG_DIR\fcm_scheduled.log" 2>&1
```

---

## Docker Setup

If using Docker, you can use cron inside the container:

### 1. Create Cron File

Create `crontab.txt`:

```bash
*/5 * * * * /usr/local/bin/python /app/manage.py send_scheduled_notifications >> /var/log/cron.log 2>&1
0 2 * * * /usr/local/bin/python /app/manage.py cleanup_old_logs >> /var/log/cron.log 2>&1
0 3 * * 1 /usr/local/bin/python /app/manage.py cleanup_inactive_tokens >> /var/log/cron.log 2>&1
```

### 2. Update Dockerfile

```dockerfile
FROM python:3.11-slim

# Install cron
RUN apt-get update && apt-get install -y cron

# Copy project
COPY . /app
WORKDIR /app

# Install dependencies
RUN pip install -r requirements.txt

# Copy crontab file
COPY crontab.txt /etc/cron.d/fcm-cron

# Give execution rights
RUN chmod 0644 /etc/cron.d/fcm-cron

# Apply cron job
RUN crontab /etc/cron.d/fcm-cron

# Create log file
RUN touch /var/log/cron.log

# Run cron in foreground
CMD cron && tail -f /var/log/cron.log
```

### 3. Or Use Separate Cron Container

`docker-compose.yml`:

```yaml
version: '3.8'

services:
  web:
    build: .
    command: gunicorn myproject.wsgi:application --bind 0.0.0.0:8000
    volumes:
      - .:/app
    ports:
      - "8000:8000"

  cron:
    build: .
    command: >
      bash -c "
      cron &&
      tail -f /var/log/cron.log
      "
    volumes:
      - .:/app
    environment:
      - DJANGO_SETTINGS_MODULE=myproject.settings
```

---

## Logging and Monitoring

### 1. Check Logs

```bash
# View real-time logs
tail -f /var/log/fcm_scheduled.log

# View last 100 lines
tail -n 100 /var/log/fcm_scheduled.log

# Search for errors
grep -i error /var/log/fcm_scheduled.log

# View logs from specific date
grep "2024-01-15" /var/log/fcm_scheduled.log
```

### 2. Log Rotation

Create `/etc/logrotate.d/fcm`:

```bash
/var/log/fcm_*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
}
```

### 3. Monitor Cron Execution

```bash
# Check if cron is running
service cron status

# View cron logs
grep CRON /var/log/syslog

# Or on some systems
tail -f /var/log/cron
```

---

## Troubleshooting

### Common Issues

#### 1. Cron Not Running

```bash
# Check cron service
sudo service cron status

# Start cron service
sudo service cron start

# Restart cron service
sudo service cron restart
```

#### 2. Environment Variables Not Set

Add environment variables to crontab:

```bash
SHELL=/bin/bash
PATH=/usr/local/bin:/usr/bin:/bin
DJANGO_SETTINGS_MODULE=myproject.settings
PYTHONPATH=/path/to/your/project
```

#### 3. Permission Issues

```bash
# Make sure log directory is writable
chmod 755 /var/log
touch /var/log/fcm_scheduled.log
chmod 644 /var/log/fcm_scheduled.log
```

#### 4. Python/Django Not Found

Use absolute paths:

```bash
*/5 * * * * /usr/bin/python3 /path/to/manage.py send_scheduled_notifications
```

---

## Testing Cron Jobs

### 1. Test Command Manually

```bash
cd /path/to/project
source venv/bin/activate
python manage.py send_scheduled_notifications
```

### 2. Test with Cron

Set a cron to run in 2 minutes:

```bash
# Get current time + 2 minutes
date

# Add temporary cron (example: run at 14:32)
32 14 * * * cd /path/to/project && python manage.py send_scheduled_notifications >> /tmp/test_cron.log 2>&1
```

### 3. Check Execution

```bash
# Wait 2+ minutes, then check log
cat /tmp/test_cron.log

# Check if cron ran
grep send_scheduled_notifications /var/log/syslog
```

---

## Comparison: Cron vs Celery

### Use Cron When:
- Simple scheduling needs
- Limited resources
- Don't need distributed task processing
- Prefer simpler setup
- Running on single server

### Use Celery When:
- Need distributed task processing
- Complex workflows
- High-volume notifications
- Need task retries and monitoring
- Multiple workers needed
- Real-time task processing

### You Can Use Both:
- Use cron for scheduled maintenance tasks
- Use Celery for user-triggered notifications
- Hybrid approach for different needs

---

## Best Practices

1. **Always use absolute paths** in cron jobs
2. **Redirect output to logs** for debugging
3. **Use --dry-run first** when testing
4. **Set up log rotation** to prevent disk space issues
5. **Monitor cron execution** regularly
6. **Use virtual environment** Python interpreter
7. **Set environment variables** properly
8. **Test commands manually** before adding to cron
9. **Use appropriate schedules** - don't over-schedule
10. **Document your cron jobs** in version control

---

## Quick Start

Minimal setup to get started:

```bash
# 1. Edit crontab
crontab -e

# 2. Add this line (adjust paths)
*/5 * * * * cd /var/www/myproject && /var/www/myproject/venv/bin/python manage.py send_scheduled_notifications >> /var/log/fcm.log 2>&1

# 3. Save and verify
crontab -l

# 4. Test after 5 minutes
tail -f /var/log/fcm.log
```

That's it! Your cron jobs are now set up and running.
