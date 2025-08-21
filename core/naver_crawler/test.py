import requests 
from requests.auth import HTTPProxyAuth
import json 
import os
import re
import urllib.parse
import uuid
from dotenv import load_dotenv
load_dotenv()
# private_api = "https://search.shopping.naver.com/ns/v1/channel-products/by-ids"

# private_api = "https://brand.naver.com/donsimon/products/9873465182"

# private_api = "https://brand.naver.com/woongjinfood/products/11471001427"

# private_api = "https://smartstore.naver.com/happyu/products/5053802796"

# private_api = "https://brand.naver.com/woongjinfood/products/11471001427"

private_api = "https://brand.naver.com/tnatur/products/10640341416"

# product_ids = ["7506207013"]

# print(f"Product IDs: {product_ids}")

# params = {
#     "excludeSoldOut": "true", 
#     "includeNewShoppingExposureYn": "true", 
#     "includeGroupProduct": "false",
#     "ids": product_ids,
# }

params = {
    # "nl-query": "juice", 
    # "nl-au": uuid.uuid4().hex, 
    "nl-au": "akslsdkl",
    # "NaPm": "ci=895983072ad648d88730dce4ceb5f745|ct=mekynzh6|tr=nslsl|sn=2044038|hk=15c5553b30eb938db358bdb02b380d56ead7ebbf"
}

# params = {
#     # "nl-query": "juice", 
#     # "nl-au": "a3da0da9c3274620b124349602705b27", 
#     # "NaPm": "ci=a3da0da9c3274620b124349602705b27|ct=mekx1gsz|tr=nslsl|sn=269500|hk=f29e51dd1dc8dda0cd69d68f7c7792b08e6853c6"
# }

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
    # "cookie": "PM_CK_loc=a92ad47d5e1bf1997d75f3d18e2fe7a767d6af7f37cb862df3e2d04b50b7469b; NAC=DosHBwACsUSR; NACT=1; NM_srt_chzzk=1; NNB=ALOCFXNPQ2TGQ; SRT30=1755743919; nstore_session=Zpo1f0td6e0JNIMvrZPIVxtt; nstore_pagesession=j6jb1sqlvFqbFlsL7VC-330325; _fbp=fb.1.1755743967716.717207700179034216; BUC=4YrVvze-w-VxVFvHkKlKP2Gplh2A_OagW_WM1O0aQ44=; PM_CK_nrefreshx=1",
    # "cookie": "NA_CO=ct%3Dmekx1gsx%7Cci%3D6f6488a1b7b8439d9761c035f9f5f85a%7Ctr%3Dnslctg%7Chk%3D32ab5caa5dcfca708dd2370766241e4b40c3c83c%7Ctrx%3Dundefined; NNB=3SSSY35BZ7SGO; nstore_session=uM7KmlGelxFdyKDGAGXQXn4B; ASID=4f6e3708000001983657db190000001b; _fwb=10IjCOac4mBTd3QTeIQhQe.1753258416309; _fbp=fb.1.1753258418424.797424718838749593; NAC=qdCbBswdpVuA; SRT30=1755751173; SRT5=1755751173; nstore_pagesession=j6jBzwqlvFryXlsL0Ed-310392; wcs_bt=s_449bdf90521e4ce7:1755751392|s_e74ce96babb9:1755587753|s_253ce9ba62a34:1755569316|s_83604740704915812:1753313581; BUC=ZFPzadc7hLGQumbVRfIdqPMljO8qOx25U_B0ANZOVkE=",
    # "cookie": "NACT=1; wcs_bt=s_213a7c8d95b54:1755754862; NNB=3SSSY35BZ7SGO; nstore_session=uM7KmlGelxFdyKDGAGXQXn4B; ASID=4f6e3708000001983657db190000001b; _fbp=fb.1.1753258418424.797424718838749593; _fwb=150KjOvRCsmOO9IHOMhriQA.1753259958626; NAC=qdCbBswdpVuA; SRT30=1755751173; nstore_pagesession=j6jX6dqqitMK9wsdvxG-379243; SRT5=1755754789; BUC=boC3_SrsKkCw0oDTgVtCiiLwwLZNOcj_5GD8ymrLNwk=",
    "cookie": "PM_CK_loc=a92ad47d5e1bf1997d75f3d18e2fe7a767d6af7f37cb862df3e2d04b50b7469b; NAC=DosHBwACsUSR; NACT=1; NM_srt_chzzk=1; NNB=ALOCFXNPQ2TGQ; SRT30=1755743919; nstore_session=Zpo1f0td6e0JNIMvrZPIVxtt; nstore_pagesession=j6jb1sqlvFqbFlsL7VC-330325; _fbp=fb.1.1755743967716.717207700179034216; BUC=8Kthq2ZZumjnLmfjsn3ZlMqawegwK_E15KjDHmICiw4=", 
    "referer": "https://search.shopping.naver.com/ns/search?query=juice",
    # "sec-ch-ua-platform": '"Windows"',
    "sec-ch-ua-platform-version": '"10.0.0"',
    "sec-ch-ua-wow64": "?0",
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "sec-fetch-user": "?1",
    # "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"
}

query_string = urllib.parse.urlencode(params)
full_target_url = f"{private_api}?{query_string}"
encoded_url = urllib.parse.quote(full_target_url, safe='')

scrape_do_url = (
    f"http://api.scrape.do/?token={os.getenv('SCRAPEDO_API_KEY')}&url={encoded_url}"
    "&super=true&geocode=KR&customHeaders=true"
)

cookies = "PM_CK_loc=a92ad47d5e1bf1997d75f3d18e2fe7a767d6af7f37cb862df3e2d04b50b7469b; NAC=DosHBwACsUSR; NACT=1; NM_srt_chzzk=1; NNB=ALOCFXNPQ2TGQ; SRT30=1755743919; nstore_session=Zpo1f0td6e0JNIMvrZPIVxtt; nstore_pagesession=j6jb1sqlvFqbFlsL7VC-330325; _fbp=fb.1.1755743967716.717207700179034216; BUC=8Kthq2ZZumjnLmfjsn3ZlMqawegwK_E15KjDHmICiw4="
# cookies = cookies.split("; ")
cookies = cookies.split("; ")
cookies = {cookie.split("=")[0]: cookie.split("=")[1] for cookie in cookies}

response = requests.get(scrape_do_url, headers=headers, cookies=cookies)

print(f"Scrape.do response: {response.content}")
match = re.search(r'"channelUid"\s*:\s*"([^"]+)"', response.content.decode())

if match: 
    channel_uid = match.group(1)
    print(f"Channel UID: {channel_uid}")



# print(f"Scrape.do response: {response.content}")



# # cookies = self.cookie.split("; ")
# # cookie_dict = {cookie.split("=")[0]: cookie.split("=")[1] for cookie in cookies}

# cookies = "PM_CK_loc=73c3d5639091fc36cc17344174ee75fca59885c1f41cc1e4cee7b84910b85ccf; NAC=oeo1DYhxRWiVB; NACT=1; NM_srt_chzzk=1; NNB=ZTUIV5OEGWOWQ; SRT30=1755133380; SRT5=1755133380; BUC=2YPg7CA_egD9BSWXjQLRiWakj09_WqeAPzTtcH9NDvQ="
# # cookies = cookies.split("; ")
# cookies = cookies.split("; ")
# cookies = {cookie.split("=")[0]: cookie.split("=")[1] for cookie in cookies}

# proxy_server = "http://kr.decodo.com:10001"
# proxy_username = "spe2t84yz6"
# proxy_password = "+jlyDjNahl1Rm868Fy"
# proxies = {
#     'http': f'http://{proxy_server}'
# }

# auth = HTTPProxyAuth(proxy_username, proxy_password)

# response = requests.get(private_api, params=params, headers=headers, cookies=cookies, proxies=proxies, auth=auth)

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