from playwright.sync_api import sync_playwright
from playwright_stealth.stealth import Stealth
import requests
import json
import time
import os 
from dotenv import load_dotenv
load_dotenv()

response = requests.get(f"https://headers.scrapeops.io/v1/user-agents?api_key={os.getenv('SCRAPEOPS_API_KEY')}")
USER_AGENT = json.loads(response.content)['result'][0]

class NaverCookieExtractor:
    def __init__(self): 
        pass

    def get_user_agent(self): 
        response = requests.get(f"https://headers.scrapeops.io/v1/user-agents?api_key={os.getenv('SCRAPEOPS_API_KEY')}")
        return json.loads(response.content)['result'][0]
    
    def extract_cookies(self, url):
        with sync_playwright() as pw: 
            browser = pw.chromium.launch(
                headless=False,
                proxy={
                    "server": os.getenv("PROXY_SERVER"),
                    "username": os.getenv("PROXY_USERNAME"),
                    "password": os.getenv("PROXY_PASSWORD")
                }
            )

            context = browser.new_context(
                geolocation={"longitude": 128.88111, "latitude": 35.23417},
                permissions=["geolocation"],
                locale="ko-KR",
                timezone_id="Asia/Seoul",
                user_agent=self.get_user_agent(),
                extra_http_headers={"Accept-Language": "ko-KR,ko;q=0.9"},
                viewport={"width": 1280, "height": 720}
            )

            page = context.new_page()

            raw_cookie_holder = {}

            # Intercept any request from shopping.naver.com that has cookies
            def capture_cookie(request):
                if "lazy" in request.url and "cookie" in request.headers: 
                    raw_cookie_holder["cookie"] = request.headers["cookie"]
            
            page.on("request", capture_cookie)

            # Navigate to the URL
            page.goto(url, timeout=60000)

            for _ in range(5): 
                page.mouse.wheel(0, 2000)
                time.sleep(2)

            page.reload()
            time.sleep(30)  # Wait for the page to load

            for _ in range(5): 
                page.mouse.wheel(0, 2000)
                time.sleep(2)

            raw_cookie = raw_cookie_holder.get("cookie", "")
            if raw_cookie:
                return raw_cookie
            
            return None 

                


