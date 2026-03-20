#!/bin/sh
# Substitute COPAW_PORT in supervisord template and start supervisord.
# Default port 8088; override at runtime with -e COPAW_PORT=3000.
set -e

# Set defaults
export COPAW_PORT="${COPAW_PORT:-8088}"
export COPAW_WORKING_DIR="${COPAW_WORKING_DIR:-/data/working}"

# Ensure the working directory exists and has proper permissions
echo "Initializing working directory at: ${COPAW_WORKING_DIR}"
mkdir -p "${COPAW_WORKING_DIR}"
chmod -R 777 /data

# Initialize working directory if config.json doesn't exist
if [ ! -f "${COPAW_WORKING_DIR}/config.json" ]; then
  echo "First run detected. Initializing DominusPrime configuration..."
  cd "${COPAW_WORKING_DIR}"
  copaw init --defaults --accept-security
  echo "Configuration initialized at ${COPAW_WORKING_DIR}"
else
  echo "Existing configuration found at ${COPAW_WORKING_DIR}"
fi

# Generate supervisord config from template
envsubst '${COPAW_PORT}' \
  < /etc/supervisor/conf.d/supervisord.conf.template \
  > /etc/supervisor/conf.d/supervisord.conf

# Start supervisord
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
