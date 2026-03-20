# DominusPrime Docker Deployment

## Overview

This Docker setup runs DominusPrime in a containerized environment with persistent external storage for all application data.

## Features

- **Persistent Storage**: All application data (configuration, files, folders) is stored in a mounted volume
- **External Volume**: Data persists outside the container in `./dominusprime-data/`
- **Read/Write Access**: The app can freely read and write files to the mounted storage
- **Auto-initialization**: Working directory is initialized on first run

## Quick Start

### Using Docker Compose (Recommended)

```bash
# Build and start the container
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the container
docker-compose down

# Stop and remove volumes (⚠️ deletes all data)
docker-compose down -v
```

### Using Docker Directly

```bash
# Build the image
docker build -f deploy/Dockerfile -t dominusprime:latest .

# Run with volume mount
docker run -d \
  --name dominusprime \
  -p 8088:8088 \
  -v ./dominusprime-data:/data \
  -e COPAW_PORT=8088 \
  dominusprime:latest

# View logs
docker logs -f dominusprime

# Stop container
docker stop dominusprime
docker rm dominusprime
```

## Volume Configuration

### Default Volume Structure

```
./dominusprime-data/
└── working/
    ├── config.json          # Main configuration file
    ├── HEARTBEAT.md         # Status file
    ├── sessions/            # Session data
    ├── memories/            # Memory storage
    ├── downloads/           # Downloaded files
    └── ... (other app data)
```

### Custom Volume Path

To use a different host path for storage:

**Docker Compose:**
```yaml
volumes:
  - /path/to/your/storage:/data
```

**Docker Run:**
```bash
docker run -v /path/to/your/storage:/data ...
```

### Volume Permissions

The container automatically sets permissions on `/data` to ensure the app can read and write files. If you encounter permission issues on the host:

```bash
# Linux/macOS
sudo chown -R $USER:$USER ./dominusprime-data
chmod -R 755 ./dominusprime-data

# Windows (run as Administrator in PowerShell)
icacls dominusprime-data /grant Users:F /t
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `COPAW_PORT` | `8088` | Web interface port |
| `COPAW_WORKING_DIR` | `/data/working` | Working directory inside container |
| `COPAW_ENABLED_CHANNELS` | `discord,telegram,...` | Enabled communication channels |

## Port Mapping

- **8088**: Web interface (configurable via `COPAW_PORT`)

## Data Persistence

All application data is stored in the mounted volume at `/data/working` inside the container. This includes:

- Configuration files
- Session data
- Memory/conversation history
- User-generated files
- Downloaded content
- Any files created by the AI agent

The data persists even when the container is stopped or removed, as long as you don't delete the volume.

## Backup and Restore

### Backup

```bash
# Create backup of all data
tar -czf dominusprime-backup-$(date +%Y%m%d).tar.gz dominusprime-data/

# Or copy the directory
cp -r dominusprime-data/ dominusprime-backup/
```

### Restore

```bash
# Extract backup
tar -xzf dominusprime-backup-YYYYMMDD.tar.gz

# Or copy back
cp -r dominusprime-backup/ dominusprime-data/
```

## Troubleshooting

### Container won't start
```bash
# Check logs
docker-compose logs

# Check if port is already in use
netstat -an | grep 8088  # Linux/macOS
netstat -an | findstr 8088  # Windows
```

### Permission denied errors
```bash
# Fix permissions (Linux/macOS)
sudo chown -R $USER:$USER ./dominusprime-data
chmod -R 755 ./dominusprime-data
```

### Data not persisting
```bash
# Verify volume is mounted
docker inspect dominusprime | grep Mounts -A 20

# Check volume exists
docker volume ls
```

### Reset to fresh state
```bash
# Stop and remove container
docker-compose down

# Delete data (⚠️ irreversible)
rm -rf dominusprime-data/

# Restart
docker-compose up -d
```

## Advanced Configuration

### Custom docker-compose.yml

```yaml
version: '3.8'

services:
  dominusprime:
    build:
      context: .
      dockerfile: deploy/Dockerfile
    container_name: dominusprime
    ports:
      - "8088:8088"
    volumes:
      # Main data volume
      - ./dominusprime-data:/data
      # Optional: Mount additional directories
      - ./models:/models:ro  # Read-only model directory
      - ./logs:/var/log:rw   # Separate log directory
    environment:
      - COPAW_PORT=8088
      - COPAW_WORKING_DIR=/data/working
      - COPAW_ENABLED_CHANNELS=console,discord
    restart: unless-stopped
    stdin_open: true
    tty: true
    # Optional: Resource limits
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
```

## Security Notes

- The working directory is set with `777` permissions to ensure compatibility
- For production use, consider implementing proper user/group permissions
- Sensitive data in `config.json` should be protected
- Use environment variables for secrets instead of storing in config files

## Support

For issues related to Docker deployment, please check:
- [DominusPrime GitHub Issues](https://github.com/BattlescarZA/DominusPrime/issues)
- Docker logs: `docker-compose logs -f`
- Container status: `docker-compose ps`
