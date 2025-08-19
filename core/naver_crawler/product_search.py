from apify_client import ApifyClient
import os 
import urllib.parse
import re 
import requests 
import json
from dotenv import load_dotenv
load_dotenv()
from requests.auth import HTTPProxyAuth

class NaverProductSearch: 
    def __init__(self, search_query, num_results=5, base_target_url="https://search.shopping.naver.com/ns/v1/search/paged-composite-cards", cookie=None):
        self.search_query = search_query
        self.num_results = num_results
        self.client = ApifyClient(os.getenv("APIFY_TOKEN"))
        self.base_target_url = base_target_url
        self.cookie = cookie

    def search_products(self): 
        query = {
            'hiddenNonProductCard': 'false', 
            'hasMoreAd': 'true', 
            'cursor': '1', 
            'pageSize': '50', 
            'query': self.search_query,
            'searchMethod': 'all.basic', 
            'isFreshCategory': 'false', 
            'isOriginalQuerySearch': 'false', 
            'isCatalogDiversifyOff': 'true', 
            'listPage': '1', 
        }

        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "application/json",
            "cookie": self.cookie,
            "priority": "u=1, i",
            "referer": f"https://search.shopping.naver.com/ns/search?query={urllib.parse.quote(self.search_query)}",
            "sec-ch-ua": '"Not)A;Brand";v="8", "Chromium";v="138", "Microsoft Edge";v="138"',
            "sec-ch-ua-arch": '"x86"',
            "sec-ch-ua-bitness": "64",
            "sec-ch-ua-form-factors": '"Desktop"',
            "sec-ch-ua-full-version-list": '"Not)A;Brand";v="8.0.0.0", "Chromium";v="138.0.7204.169", "Microsoft Edge";v="138.0.3351.109"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-ch-ua-model": "",
            "sec-ch-ua-platform-version": '"10.0.0"',
            "sec-ch-ua-wow64": "?0",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0"
        }

        query_string = urllib.parse.urlencode(query)
        full_target_url = f"{self.base_target_url}?{query_string}"
        encoded_url = urllib.parse.quote(full_target_url, safe='')

        # Scrape.do wrapper URL
        scrape_do_url = (
            f"http://api.scrape.do/?token={os.getenv('SCRAPEDO_API_KEY')}&url={encoded_url}"
            "&super=true&geocode=KR&customHeaders=true"
        )

        response = requests.get(scrape_do_url, headers=headers)
        print(f"Product search status code: {response.status_code}")
        print(f"product search content: {response.content}")


        if response.status_code == 200: 
            response_data = response.json() 
            results = response_data.get("data", {}).get("data", [])[:self.num_results]

            if results: 
                for result in results: 
                    product_url = result.get("card", {}).get("product", {}).get("productUrl", {}).get("pcUrl", "") 
                    if product_url: 
                        result["channelUId"] = self.get_product_channel_uid(product_url)
                    else: 
                        return None 

                return results[:self.num_results] if results else []
            else: 
                return None           

        else: 
            return []
    
    def get_product_channel_uid(self, product_url): 

        private_api = "https://search.shopping.naver.com/ns/v1/channel-products/by-ids"

        product_ids = [product_url.split("/")[-1]]

        print(f"Product IDs: {product_ids}")

        params = {
            "excludeSoldOut": "true", 
            "includeNewShoppingExposureYn": "true", 
            "includeGroupProduct": "false",
            "ids": product_ids,
        }

        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9",
            "cache-control": "max-age=0",
            "priority": "u=0, i",
            "sec-ch-ua": '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
            "sec-ch-ua-arch": '"x86"',
            "sec-ch-ua-bitness": '"64"',
            "sec-ch-ua-form-factors": '"Desktop"',
            "sec-ch-ua-full-version": '"139.0.7258.67"',
            "sec-ch-ua-full-version-list": '"Not;A=Brand";v="99.0.0.0", "Google Chrome";v="139.0.7258.67", "Chromium";v="139.0.7258.67"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-model": '""',
            "sec-ch-ua-platform": '"Windows"',
            "sec-ch-ua-platform-version": '"10.0.0"',
            "sec-ch-ua-wow64": "?0",
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"
        }

        # cookies = self.cookie.split("; ")
        # cookie_dict = {cookie.split("=")[0]: cookie.split("=")[1] for cookie in cookies}

        cookies = "PM_CK_loc=73c3d5639091fc36cc17344174ee75fca59885c1f41cc1e4cee7b84910b85ccf; NAC=oeo1DYhxRWiVB; NACT=1; NM_srt_chzzk=1; NNB=ZTUIV5OEGWOWQ; SRT30=1755133380; SRT5=1755133380; BUC=2YPg7CA_egD9BSWXjQLRiWakj09_WqeAPzTtcH9NDvQ="
        cookies = cookies.split("; ")
        cookies = {cookie.split("=")[0]: cookie.split("=")[1] for cookie in cookies}

        proxy_server = "http://kr.decodo.com:10001"
        proxy_username = "spe2t84yz6"
        proxy_password = "+jlyDjNahl1Rm868Fy"
        proxies = {
            'http': f'http://{proxy_server}'
        }

        auth = HTTPProxyAuth(proxy_username, proxy_password)

        response = requests.get(private_api, params=params, headers=headers, cookies=cookies, proxies=proxies, auth=auth)

        print(f"Channel UID response: {response.content}")

        if response.status_code == 200:            
            try:
                data = response.json()
                channel_uid = data.get("data", [])[0].get("channelUid", None)
                return channel_uid
            except:
                return None 
        else:
            return None 


if __name__ == "__main__":
    search_query = "laptop"
    naver_search = NaverProductSearch(search_query)
    products = naver_search.search_products()
    with open("products.json", "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=4)