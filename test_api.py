import requests
import json
import sys

# Test the API locally or on the deployed URL
def test_api(url="http://localhost:8000", post_url=None):
    if not post_url:
        print("Please provide a Facebook post URL as argument")
        sys.exit(1)
        
    print(f"Testing API at {url} with post URL: {post_url}")
    
    # Test the root endpoint
    try:
        response = requests.get(url)
        if response.status_code == 200:
            print("Root endpoint test: ✓")
            print(response.json())
        else:
            print(f"Root endpoint test: ✗ (Status code: {response.status_code})")
            print(response.text)
    except Exception as e:
        print(f"Root endpoint test failed: {str(e)}")
    
    # Test the scrape endpoint
    try:
        response = requests.post(
            f"{url}/api/scrape-facebook-post", 
            json={"post_url": post_url},
            timeout=60
        )
        
        if response.status_code == 200:
            print("Scrape endpoint test: ✓")
            data = response.json()
            
            # Print summary of results
            print("\nScrape Results Summary:")
            print(f"Post Content: {data['post']['content'][:100]}..." if len(data['post']['content']) > 100 else data['post']['content'])
            print(f"Total Comments: {data['metadata']['total_comments']}")
            print(f"First Comment: {data['comments'][0]['comment'][:50]}..." if data['comments'] and len(data['comments'][0]['comment']) > 50 else "No comments found")
            print(f"First Comment Author: {data['comments'][0]['author']}" if data['comments'] else "No authors found")
            
            # Save the full results to a file
            with open("scrape_result.json", "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print("\nFull results saved to scrape_result.json")
            
        else:
            print(f"Scrape endpoint test: ✗ (Status code: {response.status_code})")
            print(response.text)
    except Exception as e:
        print(f"Scrape endpoint test failed: {str(e)}")

if __name__ == "__main__":
    # Check if URL argument is provided
    if len(sys.argv) > 1:
        post_url = sys.argv[1]
        # Check if API URL is also provided
        api_url = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:8000"
        test_api(api_url, post_url)
    else:
        print("Usage: python test_api.py <facebook_post_url> [api_url]")
        print("Example: python test_api.py https://www.facebook.com/SaamTV/videos/1729089121344119 http://localhost:8000") 