#!/bin/bash

# Author: Samuel Giger
# Version: 1.0
# Description: Installation and Start of the SecOverview App

GITHUB_REPO="https://github.com/gigersam/SecOverview.git"  # Change this to your repo
PROJECT_NAME="secoverview"
VENV_NAME="venv"
DJANGO_PORT=8000
DJANGO_USER="secoverview"
DJANGO_DIR="/home/$DJANGO_USER/$PROJECT_NAME"
DJANGO_APP_DIR = "/home/$DJANGO_USER/$PROJECT_NAME/$PROJECT_NAME"

# Update system packages
echo "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install necessary dependencies
echo "Installing Python, pip, virtual environment, Git, and other dependencies..."
sudo apt install -y python3 python3-venv python3-pip git nginx nmap

# Create a new system user for Django
if id "$DJANGO_USER" &>/dev/null; then
    echo "User $DJANGO_USER already exists."
else
    echo "Creating Django user..."
    sudo adduser $DJANGO_USER
fi

# Clone the Django project from GitHub
echo "Cloning Django project from GitHub..."
sudo git clone $GITHUB_REPO $DJANGO_DIR

# Navigate to project directory
cd $DJANGO_DIR

# Set up a virtual environment
echo "Setting up a virtual environment..."
sudo python3 -m venv $VENV_NAME

# Activate virtual environment and install dependencies
echo "Installing dependencies from requirements.txt..."
sudo bash -c "source $DJANGO_DIR/$VENV_NAME/bin/activate && pip install -r requirements.txt"

cd $DJANGO_APP_DIR

# Apply migrations
echo "Applying migrations..."
sudo bash -c "source $DJANGO_DIR/$VENV_NAME/bin/activate && python manage.py migrate"

# Create a superuser (optional)
read -p "Do you want to create a superuser? (y/n): " CREATE_SUPERUSER
if [[ "$CREATE_SUPERUSER" == "y" ]]; then
    sudo bash -c "source $DJANGO_DIR/$VENV_NAME/bin/activate && python manage.py createsuperuser"
fi

# Allow all hosts (for local development)
echo "Configuring Django settings..."
sudo sed -i "s/ALLOWED_HOSTS = \[\]/ALLOWED_HOSTS = ['*']/" $PROJECT_NAME/settings.py

# Collect static files
echo "Collecting static files..."
sudo bash -c "source $DJANGO_DIR/$VENV_NAME/bin/activate && python manage.py collectstatic --noinput"

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
ExecStart=$DJANGO_DIR/$VENV_NAME/bin/gunicorn --workers 3 --bind unix:$DJANGO_DIR/$PROJECT_NAME.sock $PROJECT_NAME.wsgi:application

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
cat <<EOF | sudo tee /etc/nginx/sites-available/$PROJECT_NAME
server {
    listen 80;
    server_name _;

    location / {
        include proxy_params;
        proxy_pass http://unix:$DJANGO_DIR/$PROJECT_NAME.sock;
    }

    location /static/ {
        alias $DJANGO_DIR/static/;
    }

    location /media/ {
        alias $DJANGO_DIR/media/;
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

# Final message
echo "Django + Gunicorn + Nginx setup completed!"
echo "Visit your app at http://<your-server-ip>/"