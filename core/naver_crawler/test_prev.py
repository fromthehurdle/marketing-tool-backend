import requests 
from requests.auth import HTTPProxyAuth
import urllib.parse 
import os 
from dotenv import load_dotenv
load_dotenv()

private_api = "https://search.shopping.naver.com/ns/v1/channel-products/by-ids"

product_ids = ["10640341416"]

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
    # "sec-ch-ua-platform": '"Windows"',
    "cookie": "PM_CK_loc=a92ad47d5e1bf1997d75f3d18e2fe7a767d6af7f37cb862df3e2d04b50b7469b; NAC=DosHBwACsUSR; NACT=1; NM_srt_chzzk=1; NNB=ALOCFXNPQ2TGQ; SRT30=1755743919; nstore_session=Zpo1f0td6e0JNIMvrZPIVxtt; nstore_pagesession=j6jb1sqlvFqbFlsL7VC-330325; _fbp=fb.1.1755743967716.717207700179034216; BUC=8Kthq2ZZumjnLmfjsn3ZlMqawegwK_E15KjDHmICiw4=", 
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

query_string = urllib.parse.urlencode(params)
full_target_url = f"{private_api}?{query_string}"
encoded_url = urllib.parse.quote(full_target_url, safe='')

# Scrape.do wrapper URL
scrape_do_url = (
    f"http://api.scrape.do/?token={os.getenv('SCRAPEDO_API_KEY')}&url={encoded_url}"
    "&super=true&geocode=KR&customHeaders=true"
)

response = requests.get(scrape_do_url, headers=headers)
print(f"Scrape.do response: {response.content}")

# cookies = "PM_CK_loc=a92ad47d5e1bf1997d75f3d18e2fe7a767d6af7f37cb862df3e2d04b50b7469b; NAC=DosHBwACsUSR; NACT=1; NM_srt_chzzk=1; NNB=ALOCFXNPQ2TGQ; SRT30=1755743919; nstore_session=Zpo1f0td6e0JNIMvrZPIVxtt; nstore_pagesession=j6jb1sqlvFqbFlsL7VC-330325; _fbp=fb.1.1755743967716.717207700179034216; BUC=8Kthq2ZZumjnLmfjsn3ZlMqawegwK_E15KjDHmICiw4="
# cookies = cookies.split("; ")
# cookies = {cookie.split("=")[0]: cookie.split("=")[1] for cookie in cookies}

# proxy_server = "http://kr.decodo.com:10001"
# proxy_username = "spe2t84yz6"
# proxy_password = "+jlyDjNahl1Rm868Fy"
# proxies = {
#     'http': f'http://{proxy_server}'
# }

# auth = HTTPProxyAuth(proxy_username, proxy_password)

# response = requests.get(private_api, params=params, headers=headers, proxies=proxies, auth=auth)

# print(f"Channel UID response: {response.content}")

# if response.status_code == 200:            
#     try:
#         data = response.json()
#         channel_uid = data.get("data", [])[0].get("channelUid", None)
#         return channel_uid
#     except:
#         return None 
# else:
#     return None 