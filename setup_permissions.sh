#!/bin/bash
set -e

# Default values
ADMIN_BOT_USER="root_adminbot"
ADMIN_BOT_GROUP="adminbot_group"
INSTALL_DIR="/opt/rootbot"
LOG_DIR="/var/log/rootbot"
CONFIG_DIR="/etc/rootbot"

# Create user and group if they don't exist
if ! getent group $ADMIN_BOT_GROUP >/dev/null; then
    groupadd $ADMIN_BOT_GROUP
fi

if ! id -u $ADMIN_BOT_USER >/dev/null 2>&1; then
    useradd -m -s /bin/bash -g $ADMIN_BOT_GROUP $ADMIN_BOT_USER
fi

# Create required directories
mkdir -p $INSTALL_DIR $LOG_DIR $CONFIG_DIR

# Set directory ownership and permissions
chown -R $ADMIN_BOT_USER:$ADMIN_BOT_GROUP $INSTALL_DIR $LOG_DIR $CONFIG_DIR
chmod 750 $INSTALL_DIR $LOG_DIR $CONFIG_DIR

# Create sudoers entry for specific commands
cat > /etc/sudoers.d/rootbot << EOF
# Allow RootBot to execute specific system commands
$ADMIN_BOT_USER ALL=(root) NOPASSWD: /usr/bin/ps, /usr/bin/top, /usr/bin/df, /usr/bin/du, /usr/bin/free
$ADMIN_BOT_USER ALL=(root) NOPASSWD: /usr/bin/netstat, /usr/bin/ss, /usr/bin/ip, /usr/sbin/ifconfig
$ADMIN_BOT_USER ALL=(root) NOPASSWD: /usr/bin/systemctl status*, /usr/bin/journalctl
$ADMIN_BOT_USER ALL=(root) NOPASSWD: /usr/bin/lsof, /usr/bin/iostat, /usr/bin/vmstat, /usr/bin/mpstat
EOF

chmod 440 /etc/sudoers.d/rootbot

# Set up log rotation
cat > /etc/logrotate.d/rootbot << EOF
$LOG_DIR/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 640 $ADMIN_BOT_USER $ADMIN_BOT_GROUP
}
EOF

echo "Permission setup completed successfully!"
echo "RootBot will run as user: $ADMIN_BOT_USER"
echo "Log directory: $LOG_DIR"
echo "Config directory: $CONFIG_DIR"
echo "Installation directory: $INSTALL_DIR"
