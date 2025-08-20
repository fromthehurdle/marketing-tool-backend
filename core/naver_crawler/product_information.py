import requests 
import urllib.parse 
import json 
import re
import os 
from dotenv import load_dotenv
load_dotenv()

class ProductInformationExtractor: 
    def __init__(self, channel_uid, product_id, original_product_no, checkout_merchant_no, cookie=None): 
        self.channel_uid = channel_uid
        self.product_id = product_id 
        self.original_product_no = original_product_no
        self.checkout_merchant_no = checkout_merchant_no
        self.cookie = cookie
        self.referer = None

    def get_product_details(self): 
        target_url = f"https://smartstore.naver.com/i/v2/channels/{self.channel_uid}/products/{self.product_id}/contents/10824611867/PC"
        print(f"Target URL: {target_url}")
        encoded_url = urllib.parse.quote_plus(target_url)
        api_url = f"https://api.scrape.do?token={os.getenv('SCRAPEDO_API_KEY')}&url={encoded_url}&super=true"

        response = requests.get(api_url)
        print(f"Product details status code: {response.status_code}")
        print(f"Product details content: {response.content}")
        data = response.json()

        print(f"Product details response: {data}")
        
        parsed_urls = self.parse_product_details(data)
        self.referer = self.get_referer(data)
        return parsed_urls if parsed_urls else []

    # def parse_product_details(self, data):
    #     html = data.get("renderContent", "")
    #     if html: 
    #         urls = re.findall(r'https://shop-phinf\.pstatic\.net/[^\s"\\]+', html)
    #         return urls 

    def parse_product_details(self, data):
        html = data.get("renderContent", "")
        if not html:
            return []

        # Match both src= and data-src=, with or without file extensions
        urls = re.findall(
            r'(?:src|data-src)\s*=\s*["\'](https?://[^\s"\'>]+)',
            html
        )
        return urls
    
    def get_referer(self, data):
        html = data.get("renderContent", "")
        match = re.search(r'https://smartstore\.naver\.com/[^\s"\'<>]+', html)
        if match:
            return match.group(0) 
        return None 
    
    def get_product_reviews(self):
        if self.cookie: 
            # original_product_no = self.get_original_product_no()
            # if not original_product_no: 
            #     return None

            print(f"getting reviews for original product no: {self.original_product_no}")
            

            target_url = "https://smartstore.naver.com/i/v1/contents/reviews/query-pages"
            print(f"Target URL for reviews: {target_url}")
            encoded_url = urllib.parse.quote(target_url)
            api_url = (
                f"http://api.scrape.do/?token={os.getenv('SCRAPEDO_API_KEY')}&url={encoded_url}"
                "&super=true&geocode=KR&customHeaders=true"
            )

            headers = {
                "accept": "application/json, text/plain, */*",
                "accept-encoding": "gzip, deflate, br, zstd",
                "accept-language": "en-US,en;q=0.9",
                "content-type": "application/json",
                "cookie": "PM_CK_loc=73c3d5639091fc36cc17344174ee75fca59885c1f41cc1e4cee7b84910b85ccf; NAC=oeo1DYhxRWiVB; NACT=1; NM_srt_chzzk=1; NNB=ZTUIV5OEGWOWQ; SRT30=1755133380; SRT5=1755133380; BUC=2YPg7CA_egD9BSWXjQLRiWakj09_WqeAPzTtcH9NDvQ=",
                # "cookie": self.cookie,
                "origin": "https://smartstore.naver.com",
                "priority": "u=1, i",
                "referer": self.referer,
                "sec-ch-ua": '"Not)A;Brand";v="8", "Chromium";v="138", "Microsoft Edge";v="138"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"',
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-origin",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0",
                "x-client-version": "20250723205012",
            }


            payload_top = {
                "checkoutMerchantNo": self.checkout_merchant_no,
                "originProductNo": self.original_product_no,
                "page": 1,
                "pageSize": 20,
                "reviewSearchSortType": "REVIEW_SCORE_DESC" # REVIEW_SCORE_DESC REVIEW_SCORE_ASC
            }

            payload_bottom = {
                "checkoutMerchantNo": self.checkout_merchant_no,
                "originProductNo": self.original_product_no,
                "page": 1,
                "pageSize": 20,
                "reviewSearchSortType": "REVIEW_SCORE_ASC" # REVIEW_SCORE_DESC REVIEW_SCORE_ASC
            }

            

            response_top = requests.post(api_url, headers=headers, data=json.dumps(payload_top))
            response_bottom = requests.post(api_url, headers=headers, data=json.dumps(payload_bottom))
            # print(f"response_top: {response_top.content}")
            # print(f"response_bottom: {response_bottom.content}")
            if response_top.status_code == 200 and response_bottom.status_code == 200:
                review_data = {
                    "top_reviews": response_top.json(),#.get("data", {}).get("reviews", []),
                    "bottom_reviews": response_bottom.json()#.get("data", {}).get("reviews", [])
                }

                # print("=" * 10)
                # print(f"Review data: {review_data}")
                # print("=" * 10)
                return review_data
        return None

    def get_original_product_no(self):
        target_url = f"https://smartstore.naver.com/i/v2/channels/{self.channel_uid}/products/{self.product_id}?withWindow=false"
        encoded_url = urllib.parse.quote_plus(target_url)
        api_url = f"https://api.scrape.do?token={os.getenv('SCRAPEDO_API_KEY')}&url={encoded_url}&super=true"

        response = requests.get(api_url)
        data = response.json()
        
        original_product_no = data.get("productNo", "")

        return original_product_no if original_product_no else None


if __name__ == "__main__":
    channel_uid = "2vibtYtcXiB957iWjZyW8"
    product_id = "11864273440"
    cookie = None  # Optional, if you have a cookie

    extractor = ProductInformationExtractor(channel_uid, product_id, cookie)
    product_details = extractor.get_product_details()
    print(product_details)




