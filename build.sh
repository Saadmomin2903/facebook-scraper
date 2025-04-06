#!/bin/bash

# Install dependencies
pip install -r requirements.txt

# Install Playwright
pip install playwright

# Install only Chromium browser to save space
playwright install chromium

echo "Build completed successfully!" 