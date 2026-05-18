#!/bin/bash

echo "Starting deployment..."

cd /home/ubuntu/technovasskillfoundation || exit

echo "Pulling latest code..."
git pull origin main

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Restarting Gunicorn..."
sudo systemctl restart gunicorn

echo "Restarting Nginx..."
sudo systemctl restart nginx

echo "Deployment completed successfully!"