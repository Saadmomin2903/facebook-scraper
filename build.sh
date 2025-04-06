#!/bin/bash

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Installing Playwright..."
pip install playwright

echo "Installing Playwright browsers with specific arguments for Vercel..."
# Use specific install options for serverless environment
python -m playwright install --with-deps chromium

echo "Making browser binaries executable..."
find /home/sbx_user1051/.cache/ms-playwright -name "chrome" -exec chmod +x {} \; || echo "No browser binaries found in expected location"

echo "Setting up alternative browser path in /tmp..."
mkdir -p /tmp/.playwright/chromium || echo "Failed to create tmp directory"
cp -R /home/sbx_user1051/.cache/ms-playwright/* /tmp/.playwright/ || echo "Failed to copy browser files to tmp"

echo "Verifying installation..."
python verify_playwright.py

echo "Listing key directories..."
ls -la /home/sbx_user1051/.cache/ms-playwright/ || echo "Cache directory not found"
ls -la /tmp/.playwright/ || echo "Temp directory not found"

echo "Build completed successfully!" 