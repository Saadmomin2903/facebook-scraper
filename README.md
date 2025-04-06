# Facebook Post Scraper API

A FastAPI service that scrapes Facebook posts and comments, including author names and content. Perfect for social media monitoring, sentiment analysis, and data collection.

## Features

- Scrapes post content and comments from public Facebook posts
- Extracts author names for each comment
- Handles Facebook's dynamic loading for comments
- Avoids detection with browser anti-fingerprinting
- Returns structured JSON data with post content, comments and metadata

## Deployment to Vercel

This service is designed to work with Vercel's serverless environment. Follow these steps to deploy:

### Prerequisites

- A [Vercel](https://vercel.com/) account
- [Vercel CLI](https://vercel.com/docs/cli) (optional for local development)
- Git

### Step 1: Clone the Repository

```bash
git clone <your-repo-url>
cd <your-repo-directory>
```

### Step 2: Set up Environment Variables on Vercel

In the Vercel dashboard, add the following environment variables:

- `FB_EMAIL` - Your Facebook account email
- `FB_PASSWORD` - Your Facebook account password

### Step 3: Deploy to Vercel

#### Option 1: Using Vercel Dashboard

1. Push your code to GitHub
2. Import your project in the Vercel dashboard
3. Configure the environment variables
4. Deploy

#### Option 2: Using Vercel CLI

```bash
# Install Vercel CLI
npm install -g vercel

# Login to Vercel
vercel login

# Deploy
vercel
```

### Step 4: Install Playwright Dependencies on Vercel

After deployment, you'll need to install Playwright dependencies. In your Vercel dashboard:

1. Go to your project
2. Navigate to "Settings" > "Build & Development Settings"
3. Add this build command:
   ```
   pip install playwright && playwright install chromium && pip install -r requirements.txt
   ```

## Usage

### API Endpoints

- `GET /` - Health check and API information
- `POST /api/scrape-facebook-post` - Scrape a Facebook post

### Example Request

```bash
curl -X POST \
  https://your-vercel-deployment-url.vercel.app/api/scrape-facebook-post \
  -H 'Content-Type: application/json' \
  -d '{"post_url": "https://www.facebook.com/SaamTV/videos/1729089121344119"}'
```

### Example Response

```json
{
  "post": {
    "content": "Post content here...",
    "url": "https://www.facebook.com/SaamTV/videos/1729089121344119"
  },
  "comments": [
    {
      "comment": "Comment text here",
      "author": "Author Name",
      "index": 0
    }
    // More comments...
  ],
  "metadata": {
    "total_comments": 23,
    "scraped_at": "2025-04-07T01:05:59.452696",
    "clicks_to_expand": 3
  }
}
```

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt
pip install playwright
playwright install chromium

# Run the server
python api/index.py
```

## Important Notes

- Facebook may change their HTML structure, requiring updates to the selectors
- Using this scraper excessively might lead to your Facebook account being rate-limited
- This tool is intended for research and legitimate data collection purposes only
