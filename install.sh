#!/bin/bash

# Author: Samuel Giger
# Version: 1.0
# Description: Installation and Start of the SecOverview App

GITHUB_REPO="https://github.com/gigersam/SecOverview.git"  # Change this to your repo
PROJECT_NAME="secoverview"
VENV_NAME="venv"
DJANGO_USER="secoverview"
DJANGO_DIR="/home/$DJANGO_USER/$PROJECT_NAME" 
DJANGO_APP_DIR="/home/$DJANGO_USER/$PROJECT_NAME/$PROJECT_NAME"
DJANGO_ADMIN_PASSWORD=$(tr -dc 'A-Za-z0-9!@#$%^&*()_+' < /dev/urandom | head -c 12)
DJANGO_SECRET_KEY=$(tr -dc 'A-Za-z0-9!@#$%^&*()_+' < /dev/urandom | head -c 48)
LLM_MODEL="qwen3:latest"
LOCAL_INTERACTION_URL="https://localhost"

# Update system packages
echo "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install necessary dependencies
echo "Installing Python, pip, virtual environment, Git, and other dependencies..."
sudo apt install -y python3 python3-venv python3-pip git nginx nmap curl

sudo curl -fsSL https://ollama.com/install.sh | sudo sh

echo "Pulling $LLM_MODEL model for ollama"
sudo ollama pull $LLM_MODEL

# Create a new system user for Django
if id "$DJANGO_USER" &>/dev/null; then
    echo "User $DJANGO_USER already exists."
else
    echo "Creating Django user..."
    sudo useradd -m -s /bin/bash $DJANGO_USER
fi

# Clone the Django project from GitHub
echo "Cloning Django project from GitHub..."
sudo git clone $GITHUB_REPO $DJANGO_DIR

# Change ownership to the Django user
sudo chown -R $DJANGO_USER:www-data $DJANGO_DIR

# Navigate to project directory
cd $DJANGO_DIR

# Set up a virtual environment
echo "Setting up a virtual environment..."
sudo -u $DJANGO_USER python3 -m venv $VENV_NAME

# Activate virtual environment and install dependencies
echo "Installing dependencies from requirements.txt..."
sudo -u $DJANGO_USER bash -c "source $DJANGO_DIR/$VENV_NAME/bin/activate && pip install -r requirements.txt"

# Creating .env files
echo "Creating .env files..."
cat << EOF > services/auto_check_update_service/.env
CREDENTIALSUSERNAME=admin
CREDENTIALSPASSWORD=$DJANGO_ADMIN_PASSWORD
APISERVERURL=$LOCAL_INTERACTION_URL
UPDATE_CYCLE_ASSETS = 30 # MINTUES
UPDATE_CYCLE_RANSOMWARELIVE = 1 # DAYS
UPDATE_CYCLE_RSS_FEED=1 # HOURS
UPDATE_CYCLE_CVE_DATA=1 # DAYS
EOF

cat << EOF > services/mlnids_service/.env
CREDENTIALSUSERNAME=admin
CREDENTIALSPASSWORD=$DJANGO_ADMIN_PASSWORD
APISERVERURL=$LOCAL_INTERACTION_URL
EOF

cd $DJANGO_APP_DIR

mkdir media
mkdir media/scans
mkdir media/yararules
mkdir media/ragpool

cat << EOF > .env
DEBUG=False
SECRET_KEY=${DJANGO_SECRET_KEY}

OLLAMA_API_URL=http://localhost:11434
OLLAMA_API_MODEL=${LLM_MODEL}

ABUSEIPDB_API_KEY=your_api_key_here
MISP_SERVER=misp_server_address_here
MISP_API_KEY=your_api_key_here

DNS_WORDLIST_DEFAULT=
EOF

# Apply migrations
echo "Applying migrations..."
source $DJANGO_DIR/$VENV_NAME/bin/activate && python manage.py makemigrations accounts api assets backup chat cvedata dashboard dnsops ipcheck main mlnids nmapapp ransomwarelive rssapp webops yarascan
source $DJANGO_DIR/$VENV_NAME/bin/activate && python manage.py migrate

# Create a superuser (optional)
export DJANGO_SUPERUSER_USERNAME=admin
export DJANGO_SUPERUSER_PASSWORD=$DJANGO_ADMIN_PASSWORD
export DJANGO_SUPERUSER_EMAIL="admin@admin.test"

source $DJANGO_DIR/$VENV_NAME/bin/activate && python manage.py createsuperuser --noinput

unset DJANGO_SUPERUSER_USERNAME
unset DJANGO_SUPERUSER_PASSWORD
unset DJANGO_SUPERUSER_EMAIL

# Allow all hosts (for local development)
echo "Configuring Django settings..."
sed -i "s/ALLOWED_HOSTS = \[\]/ALLOWED_HOSTS = ['*']/" $PROJECT_NAME/settings.py

# Collect static files
echo "Collecting static files..."
source $DJANGO_DIR/$VENV_NAME/bin/activate && python manage.py collectstatic --noinput

# Change ownership to the Django user
sudo chown -R $DJANGO_USER:www-data $DJANGO_DIR

# Create a Gunicorn systemd service file
echo "Creating $PROJECT_NAME systemd service..."
cat <<EOF | sudo tee /etc/systemd/system/$PROJECT_NAME.service
[Unit]
Description=$PROJECT_NAME instance to serve Django project
After=network.target

[Service]
User=$DJANGO_USER
Group=www-data
WorkingDirectory=$DJANGO_APP_DIR
ExecStart=$DJANGO_DIR/$VENV_NAME/bin/gunicorn --workers 3 --bind unix:$DJANGO_DIR/$PROJECT_NAME.sock $PROJECT_NAME.wsgi:application --timeout 3600

[Install]
WantedBy=multi-user.target
EOF

cat <<EOF | sudo tee /etc/systemd/system/$PROJECT_NAME-update.service
[Unit]
Description=$PROJECT_NAME auto update script for resources
After=network.target

[Service]
User=$DJANGO_USER
WorkingDirectory=$DJANGO_DIR/services/auto_check_update_service
ExecStart=$DJANGO_DIR/$VENV_NAME/bin/python $DJANGO_DIR/services/auto_check_update_service/update.py
Restart=always
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF


# Reload systemd and enable the Gunicorn service
echo "Starting and enabling $PROJECT_NAME..."
sudo systemctl daemon-reload
sudo systemctl start $PROJECT_NAME
sudo systemctl enable $PROJECT_NAME

# Create an Nginx configuration file
echo "Setting up Nginx..."
sudo mkdir -p /etc/nginx/ssl
sudo openssl req -x509 -nodes -days 3650 \
  -newkey rsa:2048 \
  -keyout /etc/nginx/ssl/selfsigned.key \
  -out /etc/nginx/ssl/selfsigned.crt \
  -subj "/C=CH/ST=Zurich/L=Zurich/O=Secoverview/OU=Secoverview/CN=samuelgiger.com"

cat <<EOF | sudo tee /etc/nginx/sites-available/$PROJECT_NAME
server {
    listen 80;
    server_name _;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name _;

    ssl_certificate /etc/nginx/ssl/selfsigned.crt;
    ssl_certificate_key /etc/nginx/ssl/selfsigned.key;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        include proxy_params;
        proxy_pass http://unix:$DJANGO_DIR/$PROJECT_NAME.sock;
        proxy_read_timeout 3600s;
        proxy_connect_timeout 60s;
        proxy_send_timeout 3600s;
    }

    location /static/ {
        alias $DJANGO_APP_DIR/staticfiles/;
    }
}
EOF

# Enable Nginx configuration
sudo ln -s /etc/nginx/sites-available/$PROJECT_NAME /etc/nginx/sites-enabled
sudo rm -f /etc/nginx/sites-enabled/default

# Restart Nginx
echo "Restarting Nginx..."
sudo systemctl restart nginx
sudo systemctl enable nginx

# Starting $PROJECT_NAME-update service
echo "Starting and enabling $PROJECT_NAME-update service..."
sudo systemctl start $PROJECT_NAME-update.service
sudo systemctl enable $PROJECT_NAME-update.service

# Final message
echo "Django + Gunicorn + Nginx setup completed!"
echo "Visit your app at http://<your-server-ip>/"

echo "Admin Account:"
echo "Username: admin"
echo "Password: $DJANGO_ADMIN_PASSWORD"