---
name: log-analysis
description: Systematic approach to analyzing system and application logs to identify issues, patterns, and anomalies
platforms: [linux, macos, windows]
required_tools: [execute_shell_command, read_file, grep_search]
tags: [logs, analysis, troubleshooting, monitoring, system]
author: DominusPrime
version: 1.0.0
---

# Log Analysis Skill

## Overview

This skill provides techniques and strategies for effective log analysis across different systems and applications.

## When to Use

- Troubleshooting application errors
- Investigating system issues
- Security incident analysis
- Performance debugging
- Auditing user activity
- Identifying patterns and trends

## Prerequisites

- Access to log files
- Basic command-line knowledge
- Understanding of log formats

## Log Analysis Process

### 1. Locate Log Files

**Common Log Locations:**

**Linux/macOS:**
```
/var/log/syslog          # System logs
/var/log/auth.log        # Authentication logs
/var/log/kern.log        # Kernel logs
/var/log/apache2/        # Apache web server
/var/log/nginx/          # Nginx web server
~/.pm2/logs/             # PM2 process manager
```

**Windows:**
```
C:\Windows\System32\winevt\Logs\  # Event logs
C:\ProgramData\                    # Application logs
Event Viewer                       # GUI for viewing logs
```

**Application Logs:**
```
./logs/                  # Application directory
./var/log/              # App-specific logs
~/.dominusprime/logs/   # DominusPrime logs
```

### 2. Understand Log Formats

**Common Formats:**

**Syslog:**
```
Dec 31 23:59:59 hostname processname[PID]: message
```

**Apache Combined:**
```
IP - - [datetime] "METHOD /path HTTP/1.1" status bytes "referrer" "user-agent"
```

**JSON:**
```json
{
  "timestamp": "2024-01-01T00:00:00Z",
  "level": "ERROR",
  "message": "Connection failed",
  "context": {...}
}
```

**Structured:**
```
2024-01-01 00:00:00 [ERROR] module.function:123 - Connection timeout
```

### 3. Basic Log Commands

**View Recent Logs:**
```bash
# Last 100 lines
tail -n 100 /var/log/syslog

# Follow in real-time
tail -f /var/log/syslog

# View with pagination
less /var/log/syslog
```

**Search Logs:**
```bash
# Search for pattern
grep "ERROR" /var/log/application.log

# Case-insensitive search
grep -i "error" /var/log/application.log

# Show context (3 lines before/after)
grep -C 3 "ERROR" /var/log/application.log

# Multiple files
grep "ERROR" /var/log/*.log

# Recursive search
grep -r "ERROR" /var/log/
```

**Filter by Date/Time:**
```bash
# Logs after specific time
awk '$0 > "2024-01-01"' /var/log/syslog

# Specific date range
sed -n '/2024-01-01/,/2024-01-31/p' /var/log/syslog

# Last hour (requires timestamp parsing)
grep "$(date -d '1 hour ago' '+%Y-%m-%d %H')" /var/log/syslog
```

### 4. Analyze Error Patterns

**Count Error Types:**
```bash
# Count occurrences
grep "ERROR" application.log | wc -l

# Count by error type
grep "ERROR" application.log | cut -d':' -f2 | sort | uniq -c | sort -rn

# Top 10 errors
grep "ERROR" application.log | sort | uniq -c | sort -rn | head -10
```

**Extract Stack Traces:**
```bash
# Python tracebacks
grep -A 20 "Traceback (most recent call last)" app.log

# Java stack traces
grep -A 30 "Exception" java.log
```

### 5. Time-based Analysis

**Identify Time Patterns:**
```bash
# Errors per hour
grep "ERROR" app.log | awk '{print $1, $2}' | cut -d':' -f1 | uniq -c

# Peak error times
grep "ERROR" app.log | awk '{print $2}' | cut -d':' -f1 | sort | uniq -c | sort -rn
```

**Timeline of Events:**
```bash
# Extract timestamps of errors
grep "ERROR" app.log | awk '{print $1, $2}'

# Create timeline
grep -E "(ERROR|WARN|CRITICAL)" app.log | awk '{print $1, $2, $4}'
```

### 6. Advanced Analysis Techniques

**Correlation Analysis:**
```bash
# Find related events
ERROR_TIME=$(grep "Connection failed" app.log | head -1 | awk '{print $1, $2}')
grep "$ERROR_TIME" /var/log/syslog
```

**Pattern Detection:**
```bash
# Detect repeated failures
grep "ERROR" app.log | awk '{print $5}' | sort | uniq -c | awk '$1 > 10'

# Find cascade failures
grep -B 5 -A 5 "CRITICAL" app.log
```

**Performance Analysis:**
```bash
# Extract response times
grep "response_time" app.log | awk '{sum+=$NF; count++} END {print sum/count}'

# Slow queries
grep "slow query" mysql.log | sort -t'=' -k2 -n
```

## Tool Integration with DominusPrime

### Using grep_search Tool

```python
# Search for errors in log files
result = await grep_search(
    pattern="ERROR",
    path="/var/log",
    recursive=True
)
```

### Using Shell Commands

```python
# Analyze error counts
result = await execute_shell_command(
    command="grep 'ERROR' app.log | wc -l"
)

# Extract unique errors
result = await execute_shell_command(
    command="grep 'ERROR' app.log | sort | uniq -c | sort -rn | head -20"
)
```

### Reading Log Files

```python
# Read entire log file
content = await read_file(path="/var/log/application.log")

# Parse and analyze
lines = content.split('\n')
errors = [line for line in lines if 'ERROR' in line]
```

## Common Log Analysis Scenarios

### Scenario 1: Application Crash Investigation

**Steps:**
1. Find crash time from error logs
2. Check system logs at that time
3. Look for resource issues (OOM, disk full)
4. Examine stack traces
5. Check for related errors before crash

```bash
# Find crash time
grep -i "crash\|fatal\|killed" app.log | tail -1

# Check system resources at crash time
grep "$(date -d '10 minutes ago' '+%Y-%m-%d %H:%M')" /var/log/syslog
```

### Scenario 2: Performance Degradation

**Steps:**
1. Identify slow requests in access logs
2. Correlate with application logs
3. Check for database slow queries
4. Review system resource usage
5. Analyze traffic patterns

```bash
# Find slow requests (>1 second)
awk '$NF > 1000 {print $0}' access.log

# Database slow queries
grep "slow query" mysql.log
```

### Scenario 3: Security Incident

**Steps:**
1. Check authentication logs
2. Look for failed login attempts
3. Identify unusual access patterns
4. Review privilege escalations
5. Check for data exfiltration

```bash
# Failed login attempts
grep "Failed password" /var/log/auth.log

# Successful logins after failures
grep "Accepted password" /var/log/auth.log
```

## Log Aggregation and Tools

### Centralized Logging

**Popular Tools:**
- **ELK Stack**: Elasticsearch, Logstash, Kibana
- **Splunk**: Enterprise log management
- **Graylog**: Open-source log management
- **Loki**: Lightweight log aggregation

### JSON Log Parsing

```bash
# Parse JSON logs with jq
cat app.log | jq 'select(.level=="ERROR")'

# Extract specific fields
cat app.log | jq -r '.timestamp + " " + .message'

# Aggregate by field
cat app.log | jq -r '.error_type' | sort | uniq -c
```

### Real-time Monitoring

```bash
# Monitor multiple logs
tail -f /var/log/syslog /var/log/auth.log

# Filter in real-time
tail -f app.log | grep --line-buffered "ERROR"

# Highlight errors
tail -f app.log | grep --color=always -E "ERROR|WARN|$"
```

## Best Practices

1. **Use Timestamps**: Always include timestamps in logs
2. **Structured Logging**: Use consistent formats (preferably JSON)
3. **Log Levels**: Use appropriate levels (DEBUG, INFO, WARN, ERROR, CRITICAL)
4. **Context**: Include relevant context (request ID, user ID, session)
5. **Rotation**: Implement log rotation to manage size
6. **Retention**: Define retention policies
7. **Security**: Protect sensitive data in logs
8. **Indexing**: Use log aggregation for large-scale analysis

## Red Flags to Watch For

- **Sudden spike in errors**: System or application issue
- **Repeated failures**: Configuration or dependency problem
- **Memory leaks**: Gradually increasing resource usage
- **Authentication failures**: Potential security threat
- **Slow queries**: Database performance issue
- **Timeouts**: Network or service availability problem
- **Disk space warnings**: Capacity planning needed

## Log Rotation

**Configure logrotate (Linux):**
```
/var/log/application/*.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    missingok
    create 0644 user group
}
```

## Automation Scripts

**Error Report Generator:**
```bash
#!/bin/bash
DATE=$(date +%Y-%m-%d)
LOGFILE="/var/log/application.log"
REPORT="/tmp/error_report_${DATE}.txt"

echo "Error Report for $DATE" > $REPORT
echo "===================" >> $REPORT
echo "" >> $REPORT

echo "Total Errors: $(grep -c 'ERROR' $LOGFILE)" >> $REPORT
echo "" >> $REPORT

echo "Top 10 Error Types:" >> $REPORT
grep "ERROR" $LOGFILE | cut -d':' -f2 | sort | uniq -c | sort -rn | head -10 >> $REPORT

echo "Report saved to $REPORT"
```

## References

See the `references/` directory for:
- `log-formats-cheatsheet.md`: Common log format patterns
- `regex-patterns.md`: Useful regex for log parsing
- `analysis-checklist.md`: Systematic analysis checklist

## Related Skills

- `system-troubleshooting`: General system diagnostics
- `performance-analysis`: Performance optimization
- `security-audit`: Security log analysis
