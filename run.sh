#!/bin/bash

LOG_FILE="/home/brucho/Projects/Taionca-discord-notificator/cron.log"

echo "=== $(date): Initializing Discord bot ===" >> "$LOG_FILE"

cd /home/brucho/Projects/Taionca-discord-notificator

source venv/bin/activate

python notifications.py >> "$LOG_FILE" 2>&1
PYTHON_EXIT_CODE=$?

deactivate

if [ $PYTHON_EXIT_CODE -eq 0 ]; then
    echo "$(date): Discord bot finished successfully" >> "$LOG_FILE"
else
    echo "$(date): Discord bot failed with exit code $PYTHON_EXIT_CODE" >> "$LOG_FILE"
fi

exit $PYTHON_EXIT_CODE