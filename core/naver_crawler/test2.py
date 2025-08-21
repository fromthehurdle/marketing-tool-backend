import urllib.parse
import requests
from requests.auth import HTTPProxyAuth
import os

private_api = "https://brand.naver.com/donsimon/products/9873465182?nl-query=juice&nl-au=2c901f210f1a426dbcf7e5f4eb922e6a&NaPm=ci%3D2c901f210f1a426dbcf7e5f4eb922e6a%7Cct%3Dmeksme3d%7Ctr%3Dnslsl%7Csn%3D1057845%7Chk%3Dc0b0adb5824e0c05d98f58743726c61aa120e94f"


# params = {
#     "excludeSoldOut": "true", 
#     "includeNewShoppingExposureYn": "true", 
#     "includeGroupProduct": "false",
#     "ids": ['11471001427'],
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
    "cookies": "PM_CK_loc=a92ad47d5e1bf1997d75f3d18e2fe7a767d6af7f37cb862df3e2d04b50b7469b; NAC=DosHBwACsUSR; NACT=1; NM_srt_chzzk=1; NNB=ALOCFXNPQ2TGQ; SRT30=1755743919; SRT5=1755743919; nstore_session=Zpo1f0td6e0JNIMvrZPIVxtt; nstore_pagesession=j6jb1sqlvFqbFlsL7VC-330325; _fbp=fb.1.1755743967716.717207700179034216; BUC=R_VWqQfWRSlELUT5KzmQIlkbj64VSX5mCnfoVz9VPUE=",
    # "sec-ch-ua-platform": '"Windows"',
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

# cookies = "PM_CK_loc=73c3d5639091fc36cc17344174ee75fca59885c1f41cc1e4cee7b84910b85ccf; NAC=oeo1DYhxRWiVB; NACT=1; NM_srt_chzzk=1; NNB=ZTUIV5OEGWOWQ; SRT30=1755133380; SRT5=1755133380; BUC=2YPg7CA_egD9BSWXjQLRiWakj09_WqeAPzTtcH9NDvQ="
# cookies = cookies.split("; ")

cookies = "PM_CK_loc=a92ad47d5e1bf1997d75f3d18e2fe7a767d6af7f37cb862df3e2d04b50b7469b; NAC=DosHBwACsUSR; NACT=1; NM_srt_chzzk=1; NNB=ALOCFXNPQ2TGQ; SRT30=1755743919; SRT5=1755743919; nstore_session=Zpo1f0td6e0JNIMvrZPIVxtt; nstore_pagesession=j6jb1sqlvFqbFlsL7VC-330325; _fbp=fb.1.1755743967716.717207700179034216; BUC=R_VWqQfWRSlELUT5KzmQIlkbj64VSX5mCnfoVz9VPUE="
cookies = cookies.split("; ")
cookies = {cookie.split("=")[0]: cookie.split("=")[1] for cookie in cookies}

# proxy_server = "http://kr.decodo.com:10001"
# proxy_username = "spe2t84yz6"
# proxy_password = "+jlyDjNahl1Rm868Fy"
# proxies = {
#     'http': f'http://{proxy_server}'
# }

# auth = HTTPProxyAuth(proxy_username, proxy_password)

# response = requests.get(private_api, headers=headers, cookies=cookies, proxies=proxies, auth=auth)

# print(f"Channel UID response: {response.content}")

# query_string = urllib.parse.urlencode(query)
# full_target_url = f"{self.base_target_url}?{query_string}"
encoded_url = urllib.parse.quote(private_api, safe='')

# Scrape.do wrapper URL
scrape_do_url = (
    f"http://api.scrape.do/?token=5dfc132e87ee46d6a20da4cbb1cc4ec9c8ab6073179&url={encoded_url}"
    "&super=true&geocode=KR&customHeaders=true"
)

response = requests.get(scrape_do_url, headers=headers, cookies=cookies)


print(f"Scrape.do response: {response.content}")
