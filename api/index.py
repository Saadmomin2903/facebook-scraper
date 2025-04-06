from fastapi import FastAPI, HTTPException, Body
from typing import Dict
import asyncio
from datetime import datetime
from pydantic import BaseModel, Field
import os
import json
from playwright.async_api import async_playwright
from playwright.async_api._generated import Page, Browser, BrowserContext
import traceback
import sys

app = FastAPI(
    title="Facebook Post Scraper API",
    description="API to scrape Facebook posts and comments using stored credentials",
    version="1.0.0"
)

# Hardcoded Facebook credentials as environment variables
# For better security, set these in Vercel's environment variables
FB_CREDENTIALS = {
    "email": os.environ.get("FB_EMAIL", ""),
    "password": os.environ.get("FB_PASSWORD", "")
}

# Input model for better API documentation
class PostRequest(BaseModel):
    post_url: str = Field(..., description="URL of the Facebook post to scrape")

# Initialize browser once per cold start
browser = None
browser_context = None
is_browser_initialized = False

async def initialize_browser():
    global browser, browser_context, is_browser_initialized
    
    if is_browser_initialized:
        return
    
    try:
        playwright = await async_playwright().start()
        
        print("Starting browser initialization...")
        # Check if we're in Vercel environment
        is_vercel = os.environ.get("VERCEL", "false") == "true"
        
        # Custom browser launch arguments based on environment
        browser_args = [
            '--disable-blink-features=AutomationControlled',
            '--no-sandbox',
            '--disable-web-security',
            '--disable-features=IsolateOrigins,site-per-process',
            '--window-size=1920,1080',
            '--disable-dev-shm-usage',
            '--disable-infobars',
            '--disable-background-networking',
            '--disable-background-timer-throttling',
            '--disable-backgrounding-occluded-windows',
            '--disable-breakpad',
            '--disable-component-extensions-with-background-pages',
            '--disable-extensions',
            '--disable-features=TranslateUI',
            '--disable-ipc-flooding-protection',
            '--disable-renderer-backgrounding',
            '--enable-features=NetworkService,NetworkServiceInProcess',
            '--force-color-profile=srgb',
            '--metrics-recording-only',
            '--mute-audio',
        ]
        
        if is_vercel:
            # Additional args for Vercel serverless environment
            browser_args.extend([
                '--single-process',
                '--no-zygote'
            ])
        
        print("Launching browser with arguments:", browser_args)
        browser = await playwright.chromium.launch(
            headless=True,
            args=browser_args
        )
        
        print("Browser launched successfully, creating context...")
        # Create a context with more realistic browser parameters
        browser_context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            is_mobile=False,
            has_touch=False,
            locale='en-US',
            timezone_id='America/New_York',
            color_scheme='light',
            java_script_enabled=True,
            bypass_csp=True,
        )
        
        # Enable JavaScript console logging
        browser_context.on('console', lambda msg: print(f'BROWSER LOG: {msg.text}'))
        
        # Add anti-detection script
        await browser_context.add_init_script('''() => {
            // Overwrite the 'webdriver' property to undefined
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // Overwrite the chrome driver related properties
            window.navigator.chrome = { runtime: {} };
            
            // Overwrite the permissions API
            window.navigator.permissions = {
                query: () => Promise.resolve({ state: 'granted' })
            };
            
            // Add missing plugins that a normal browser would have
            const originalPlugins = navigator.plugins;
            const pluginsData = [
                { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer' },
                { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai' },
                { name: 'Native Client', filename: 'internal-nacl-plugin' }
            ];
            
            // Define a new plugins property
            Object.defineProperty(navigator, 'plugins', {
                get: () => {
                    const plugins = { 
                        ...originalPlugins,
                        length: pluginsData.length 
                    };
                    
                    // Add the missing plugins
                    pluginsData.forEach((plugin, i) => {
                        plugins[i] = plugin;
                    });
                    
                    return plugins;
                }
            });
            
            // Fake the language property
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
            
            // Fake the platform to match a Mac
            Object.defineProperty(navigator, 'platform', {
                get: () => 'MacIntel'
            });
            
            // Add a fake notification API
            if (window.Notification) {
                window.Notification.permission = 'default';
            }
        }''')
        
        is_browser_initialized = True
        print("Browser initialization complete")
    
    except Exception as e:
        print(f"Browser initialization failed: {str(e)}")
        print(f"Python version: {sys.version}")
        print(f"System path: {sys.path}")
        
        # Full traceback for debugging
        traceback_str = traceback.format_exc()
        print(f"Full traceback: {traceback_str}")
        
        # Try to get more information about the environment
        try:
            import os
            print(f"Current working directory: {os.getcwd()}")
            print(f"Directory contents: {os.listdir()}")
            
            # Check if we're in Vercel
            print(f"Is this Vercel? {os.environ.get('VERCEL', 'Not defined')}")
            
            # Check where Playwright is installed
            try:
                import playwright
                print(f"Playwright path: {playwright.__file__}")
                print(f"Playwright version: {playwright.__version__}")
            except Exception as pe:
                print(f"Playwright import error: {str(pe)}")
                
        except Exception as oe:
            print(f"Environment inspection error: {str(oe)}")
            
        raise HTTPException(
            status_code=500, 
            detail=f"Browser initialization failed: {str(e)}\nTraceback: {traceback_str}"
        )

async def login_to_facebook(page):
    # Step 1: Login to Facebook
    await page.goto('https://www.facebook.com/', timeout=60000)
    
    # Wait for page to fully load
    await page.wait_for_load_state('networkidle')
    await asyncio.sleep(2)  # Additional delay

    # Accept cookies if present
    try:
        cookie_button = await page.query_selector('button[data-cookiebanner="accept_button"]')
        if cookie_button:
            await cookie_button.click()
            await asyncio.sleep(1)
    except Exception:
        print('No cookie banner found')

    # Login
    await page.fill('#email', FB_CREDENTIALS["email"])
    await page.fill('#pass', FB_CREDENTIALS["password"])
    
    # Click login button
    await page.click('button[name="login"]')
    await page.wait_for_load_state('networkidle')
    await asyncio.sleep(3)

    # Check for CAPTCHA or checkpoint
    if 'checkpoint' in page.url:
        print("Detected checkpoint/CAPTCHA page")
        raise HTTPException(status_code=401, detail='Facebook security checkpoint detected. Manual intervention required.')
        
    # Check login success
    if 'login' in page.url:
        raise HTTPException(status_code=401, detail='Login failed - Please check credentials')

async def scrape_post(post_url):
    # Initialize browser if needed
    await initialize_browser()
    
    # Create a new page
    page = await browser_context.new_page()
    
    try:
        # Login to Facebook
        await login_to_facebook(page)

        # Navigate to post
        print(f"Navigating to post URL: {post_url}")
        await page.goto(post_url, timeout=60000)
        await page.wait_for_load_state('networkidle')
        await asyncio.sleep(5)  # Wait longer for all elements to load

        # Get post content
        post_data = await page.evaluate('''() => {
            // Try to get the post description directly from where Facebook actually stores it
            const getPostDescription = () => {
                // First approach: Get the full text content from the post container
                const postContainer = document.querySelector('.xjkvuk6, .xuyqlj2');
                if (postContainer) {
                    // Get all text content divs in the post container
                    const textDivs = Array.from(postContainer.querySelectorAll('div[dir="auto"]'))
                        .map(el => el.textContent.trim())
                        .filter(text => text.length > 10 && !text.includes('See more') && !text.includes('See less'));
                    
                    // Get the full post content by joining all text segments (this gets the complete text even if split across divisions)
                    if (textDivs.length > 0) {
                        return textDivs.join(' ');
                    }
                }
                
                // Second approach: Look for specific post wrapper divs by their class names
                const wrapperSelectors = [
                    'div.x11i5rnm.xat24cr.x1mh8g0r.x1vvkbs',
                    'div.x78zum5.xdt5ytf.x4cne27.xifccgj',
                    'div.xzueoph.x1k70j0n',
                    'div.x1n2onr6'
                ];
                
                for (const selector of wrapperSelectors) {
                    const wrappers = document.querySelectorAll(selector);
                    for (const wrapper of wrappers) {
                        const texts = Array.from(wrapper.querySelectorAll('div[dir="auto"], span[dir="auto"]'))
                            .map(el => el.textContent.trim())
                            .filter(text => 
                                text.length > 30 && 
                                !text.includes('See more') && 
                                !text.includes('See less') &&
                                !text.includes('#') // Avoid hashtag sections
                            );
                        
                        if (texts.length > 0) {
                            // Sort by length and get the longest text
                            return texts.sort((a, b) => b.length - a.length)[0];
                        }
                    }
                }
                
                // Third approach: look for any lengthy content in the first article element (likely the post itself)
                const firstArticle = document.querySelector('div[role="article"]');
                if (firstArticle) {
                    const articleTexts = Array.from(firstArticle.querySelectorAll('div[dir="auto"]'))
                        .map(el => el.textContent.trim())
                        .filter(text => 
                            text.length > 40 && 
                            !text.includes('See more') && 
                            !text.includes('See less')
                        );
                    
                    if (articleTexts.length > 0) {
                        // Sort by length to get the most substantial content
                        return articleTexts.sort((a, b) => b.length - a.length)[0];
                    }
                }
                
                // Final fallback: any meaningful content on the page
                const allTextElements = Array.from(document.querySelectorAll('div[dir="auto"]'));
                const allTexts = allTextElements
                    .map(el => el.textContent.trim())
                    .filter(text => text.length > 50);
                    
                if (allTexts.length > 0) {
                    return allTexts.sort((a, b) => b.length - a.length)[0];
                }
                
                return '';
            };

            return {
                post_content: getPostDescription(),
                post_url: window.location.href
            };
        }''')

        # Expand comments
        max_attempts = 20  # Maximum attempts for loading more comments
        attempts = 0
        total_clicks = 0
        last_comment_count = 0
        
        while attempts < max_attempts:
            # Get current comment count to check if we're making progress
            current_comment_count = await page.evaluate('''() => {
                return document.querySelectorAll('div[role="article"]').length;
            }''')
            
            print(f"Current comment count: {current_comment_count}")
            
            if current_comment_count == last_comment_count and attempts > 5:
                print("No new comments loaded after several attempts, stopping")
                break
                
            last_comment_count = current_comment_count
            
            # Scroll down to load more content
            await page.evaluate('''() => {
                window.scrollTo(0, document.body.scrollHeight);
                return true;
            }''')
            await asyncio.sleep(2)
            
            # Try to click "View more comments" buttons
            click_happened = await page.evaluate('''() => {
                // Look for and click on "View more comments" or similar buttons
                const buttons = Array.from(document.querySelectorAll('div[role="button"]'));
                for (const button of buttons) {
                    if (button.textContent.includes('View more comments') || 
                        button.textContent.includes('Previous comments')) {
                        button.scrollIntoView({behavior: "smooth", block: "center"});
                        setTimeout(() => button.click(), 100);
                        return true;
                    }
                }
                
                // Try spans with comments text
                const spans = Array.from(document.querySelectorAll('span'));
                for (const span of spans) {
                    if (span.textContent.includes('View more comments') || 
                        span.textContent.includes('Previous comments')) {
                        const clickable = span.closest('div[role="button"]');
                        if (clickable) {
                            clickable.scrollIntoView({behavior: "smooth", block: "center"});
                            setTimeout(() => clickable.click(), 100);
                            return true;
                        }
                    }
                }
                
                return false;
            }''')
            
            if click_happened:
                print("Clicked on 'View more comments' button")
                total_clicks += 1
                await asyncio.sleep(3)
                await page.wait_for_load_state('networkidle')
            else:
                attempts += 1
            
            if attempts >= 3 and total_clicks == 0:
                break  # Break early if we can't find any buttons to click

        # Scrape the comments
        comments = await page.evaluate('''() => {
            const comments = [];
            const commentElements = Array.from(document.querySelectorAll('div[role="article"]'));
            
            console.log("Total comment elements found:", commentElements.length);
            
            // Skip the first element as it's likely the post itself
            const actualComments = commentElements.slice(1);
            
            actualComments.forEach((comment, index) => {
                try {
                    // Extract the comment content
                    const contentElements = comment.querySelectorAll('div[dir="auto"]:not([style*="display: none"])');
                    let content = '';
                    
                    // Take the longest text content as the comment
                    contentElements.forEach(el => {
                        const text = el.textContent.trim();
                        if (text && text.length > content.length) {
                            content = text;
                        }
                    });
                    
                    // Extract the author name using various selectors to catch different FB layouts
                    let author = '';
                    
                    // First try: Look for the author name in specific class patterns
                    const authorElements = [
                        // Common desktop FB pattern - strong tag with author name
                        ...comment.querySelectorAll('strong.x1heor9g, strong.html-strong'),
                        // Mobile FB pattern - span with author class
                        ...comment.querySelectorAll('span.f20'),
                        // Another common pattern - profile link with author name
                        ...comment.querySelectorAll('a[role="link"] span.xt0psk2, a[aria-label*="profile"] span'),
                        // Alternative pattern - any link within header area
                        ...comment.querySelectorAll('h3 a, h4 a, .x1heor9g a, .x11i5rnm a')
                    ];
                    
                    // Try to extract author from the found elements
                    for (const el of authorElements) {
                        const name = el.textContent.trim();
                        if (name && name.length > 0 && name.length < 50) {
                            author = name;
                            break;
                        }
                    }
                    
                    // If no author found with specific selectors, try more general approach
                    if (!author) {
                        // Look for typical author layout patterns
                        const topElements = Array.from(comment.querySelectorAll('div[dir="auto"]')).slice(0, 3);
                        for (const el of topElements) {
                            const text = el.textContent.trim();
                            // Author names are typically short and at the beginning of the comment
                            if (text && text.length > 0 && text.length < 40 && 
                                !text.includes("Commented") && !text.includes("replied") && 
                                !text.includes("http") && !text.includes("www.")) {
                                author = text;
                                break;
                            }
                        }
                    }
                    
                    if (content) {
                        comments.push({
                            'comment': content,
                            'author': author || 'Unknown User',
                            'index': index
                        });
                    }
                } catch (e) {
                    console.error('Error processing comment:', e);
                }
            });

            return comments;
        }''')

        # Format the data
        formatted_data = {
            'post': {
                'content': post_data['post_content'],
                'url': post_data['post_url']
            },
            'comments': comments,
            'metadata': {
                'total_comments': len(comments),
                'scraped_at': datetime.now().isoformat(),
                'clicks_to_expand': total_clicks
            }
        }

        # Close the page (but keep the browser running for future requests)
        await page.close()
        
        return formatted_data

    except Exception as e:
        # Close the page and browser in case of error
        try:
            if page:
                await page.close()
        except:
            pass
        
        # Get full traceback for debugging
        error_details = str(e)
        error_trace = traceback.format_exc()
        
        print(f"Error scraping post: {error_details}")
        print(f"Traceback: {error_trace}")
        
        raise HTTPException(
            status_code=500, 
            detail=f"Error scraping post: {error_details}\nTraceback: {error_trace}"
        )

@app.post("/api/scrape-facebook-post")
async def scrape_facebook_post(request: PostRequest):
    # Validate Facebook credentials
    if not FB_CREDENTIALS["email"] or not FB_CREDENTIALS["password"]:
        raise HTTPException(
            status_code=500, 
            detail="Facebook credentials not configured. Please set FB_EMAIL and FB_PASSWORD environment variables."
        )
    
    # Get the post URL from the request
    post_url = request.post_url
    
    # Scrape the post
    result = await scrape_post(post_url)
    
    return result

@app.get("/")
async def root():
    return {
        "message": "Facebook Post Scraper API is running!",
        "version": "1.0.0",
        "endpoints": {
            "POST /api/scrape-facebook-post": "Scrape a Facebook post and its comments"
        },
        "usage": "Send a POST request to /api/scrape-facebook-post with JSON body: {'post_url': 'https://www.facebook.com/your-post-url'}"
    }

# For local development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("index:app", host="0.0.0.0", port=8000) 