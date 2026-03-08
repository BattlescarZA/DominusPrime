---
name: cron
description: Manage scheduled tasks via dominusprime command - create, query, pause, resume, delete tasks
metadata: { "dominusprime": { "emoji": "⏰" } }
---

# Scheduled Task Management

Use `dominusprime cron` command to manage scheduled tasks.

## Common Commands

```bash
# List all tasks
dominusprime cron list

# View task details
dominusprime cron get <job_id>

# View task status
dominusprime cron state <job_id>

# Delete task
dominusprime cron delete <job_id>

# Pause/resume task
dominusprime cron pause <job_id>
dominusprime cron resume <job_id>

# Execute immediately once
dominusprime cron run <job_id>
```

## Create Tasks

Supports two task types:
- **text**: Send fixed messages to channel on schedule
- **agent**: Ask Agent questions on schedule and send replies to channel

### Quick Creation

```bash
# Send text message daily at 9:00 AM
dominusprime cron create \
  --type text \
  --name "Daily Morning Greeting" \
  --cron "0 9 * * *" \
  --channel imessage \
  --target-user "CHANGEME" \
  --target-session "CHANGEME" \
  --text "Good morning!"

# Ask Agent every 2 hours
dominusprime cron create \
  --type agent \
  --name "Check TODO Items" \
  --cron "0 */2 * * *" \
  --channel dingtalk \
  --target-user "CHANGEME" \
  --target-session "CHANGEME" \
  --text "What are my pending tasks?"
```

### Required Parameters

Creating a task requires:
- `--type`: Task type (text or agent)
- `--name`: Task name
- `--cron`: Cron expression (e.g., `"0 9 * * *"` means daily at 9:00 AM)
- `--channel`: Target channel (imessage / discord / dingtalk / qq / console)
- `--target-user`: User identifier
- `--target-session`: Session identifier
- `--text`: Message content (text type) or question content (agent type)

### Create from JSON (Complex Configuration)

```bash
dominusprime cron create -f job_spec.json
```

## Cron Expression Examples

```
0 9 * * *      # Daily at 9:00 AM
0 */2 * * *    # Every 2 hours
30 8 * * 1-5   # Weekdays at 8:30 AM
0 0 * * 0      # Every Sunday at midnight
*/15 * * * *   # Every 15 minutes
```

## Usage Recommendations

- When parameters are missing, ask the user for details before creating
- Before pausing/deleting/resuming, use `dominusprime cron list` to find job_id
- When troubleshooting, use `dominusprime cron state <job_id>` to check status
- Provide complete commands to users that can be copied and executed directly
