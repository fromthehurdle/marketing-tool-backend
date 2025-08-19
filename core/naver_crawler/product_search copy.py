from apify_client import ApifyClient
import os 
import urllib.parse
import re 
import requests 
import json
from dotenv import load_dotenv
load_dotenv()

class NaverProductSearch: 
    def __init__(self, search_query, num_results=5):
        self.search_query = search_query
        self.num_results = num_results
        self.client = ApifyClient(os.getenv("APIFY_TOKEN"))


    def search_products(self): 
        run_input = {
            "keywords": ["나이키운동화"],
            "maxCrawlPages": 2,
        }

        # Run the Actor and wait for it to finish
        run = self.client.actor(os.getenv("APIFY_NAVER_ACTOR_ID")).call(run_input=run_input)
        results = list(self.client.dataset(run["defaultDatasetId"]).iterate_items())

        for result in results[:self.num_results]: 
            result["channelUId"] = self.get_product_channel_uid(result["productPageUrl"])

        return results[:self.num_results] if results else []
    
    def get_product_channel_uid(self, product_url): 
        target_url = urllib.parse.quote_plus(product_url)
        api_url = f"https://api.scrape.do?token={os.getenv('SCRAPEDO_API_KEY')}&url={target_url}&super=true"

        response = requests.get(api_url)

        html = response.text
        channel_uid = re.search(r'"channelUid"\s*:\s*"([^"]+)"', html).group(1)

        return channel_uid if channel_uid else None


if __name__ == "__main__":
    search_query = "laptop"
    naver_search = NaverProductSearch(search_query)
    products = naver_search.search_products()
    with open("products.json", "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=4)