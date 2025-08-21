import os, urllib.parse, requests
from dotenv import load_dotenv
load_dotenv()

private_api = "https://search.shopping.naver.com/ns/v1/channel-products/by-ids"
product_ids = ["10640341416"]

params = {
    "excludeSoldOut": "true",
    "includeNewShoppingExposureYn": "true",
    "includeGroupProduct": "false",
    "ids": product_ids,          # list -> needs doseq=True
}

# 1) Build target URL (encode ONCE)
qs = urllib.parse.urlencode(params, doseq=True)
target_url = f"{private_api}?{qs}"
encoded_target = urllib.parse.quote(target_url, safe="")

# 2) Scrape.do API endpoint
scrape_url = (
    f"http://api.scrape.do/?token={os.getenv('SCRAPEDO_API_KEY')}"
    f"&url={encoded_target}"
    f"&customHeaders=true&geocode=KR"
)

# 3) Minimal headers — avoid sec-*, sec-ch-*, upgrade-insecure-requests
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

r = requests.get(scrape_url, headers=headers, timeout=30)
print(r.status_code, r.headers.get("content-type"))
print(r.text)
