import os 
import json 
import requests 
from PIL import Image
from .product_search import NaverProductSearch
from .product_information import ProductInformationExtractor
from .cookie_extractor import NaverCookieExtractor as CookieExtractor
import boto3
from botocore.client import Config 
from .. import models 

from celery.utils.log import get_task_logger
logger = get_task_logger(__name__)

from dotenv import load_dotenv
load_dotenv()


class Orchestrator: 
    def __init__(self, search_query, search_id, num_results=5, channel='naver'): 
        self.search_query = search_query
        self.search_id = search_id
        self.num_results = num_results
        self.channel = channel
        self.session = boto3.session.Session()
        self.client = None

    def initialize_digital_ocean_client(self): 
        self.client = self.session.client(
            's3', 
            region_name=os.getenv('SPACES_REGION_NAME'), 
            endpoint_url=f"https://{os.getenv('SPACES_REGION_NAME')}.digitaloceanspaces.com", 
            aws_access_key_id=os.getenv('SPACES_ACCESS_KEY'), 
            aws_secret_access_key=os.getenv('SPACES_SECRET_KEY'), 
        )

    def upload_to_digital_ocean(self, file_path, object_name=None): 
        try: 
            self.client.upload_file(
                file_path, 
                os.getenv('SPACES_SPACE_NAME'), 
                object_name,
                ExtraArgs={'ACL': 'public-read'}
            )

            cdn_endpoint = os.getenv('SPACES_CDN_ENDPOINT')

            return f"https://{cdn_endpoint}/{object_name}"
        except Exception as e: 
            print(f"Error uploading file to Digital Ocean Spaces: {e}")
            return False 
    
    def create_result(self, search_id): 
        try: 
            result = models.Result.objects.create(
                search_id=self.search_id,                
            )
            return result
        except Exception as e: 
            print(f"Error creating result: {e}")
            return None
        
    def save_product_search_to_db(self, result, product): 
        try: 
            # for product in products: 
            result_item = models.ResultItem.objects.create(
                result=result, 
                seller=product.get("mallName", ""), 
                product=product.get("productName", ""),
                original_price=product.get("salePrice", 0),
                sale_price=product.get("discountedSalePrice", 0),
                discount=product.get("discountedRatio", 0),
                shipping=product.get("productDeliveryInfo", {}).get("baseFee", 0),
                review_count=product.get("totalReviewCount", 0),
                rating=product.get("averageReviewScore", 0),
                product_url=product.get("productUrl", {}).get("pcUrl", ""),
            )
            result_item.save()
 
            return result_item  
        except Exception as e: 
            print(f"Error saving product search to database: {e}")
            return False

    def save_product_details_to_db(self, result_item, image_url, order): 
        try: 
            result_detail_image = models.ResultDetailImage.objects.create(
                result_item=result_item, 
                url=image_url, 
                order=order
            )
            result_detail_image.save()
            return order + 1
        except Exception as e: 
            print(f"Error saving product details to database: {e}")
            return False

    def save_product_reviews_to_db(self, result_item, product_reviews): 
        print(f"Saving product reviews to database for result item: {result_item.id}")
        try: 
            for reviews in product_reviews.get("top_reviews", {}).get("contents", []): 
                result_review = models.ResultReview.objects.create(
                    result_item=result_item, 
                    review_id=reviews.get("id", ""),
                    username=reviews.get("writerId", ""), 
                    content=reviews.get("reviewContent", ""), 
                    rating=reviews.get("reviewScore", 0),
                    date=reviews.get("createDate", ""), 
                    helpful_count=reviews.get("helpCount", 0),
                    review_type=models.ReviewTypeChoices.TOP
                )
                result_review.save()

            for reviews in product_reviews.get("bottom_reviews", {}).get("contents", []):
                result_review = models.ResultReview.objects.create(
                    result_item=result_item, 
                    review_id=reviews.get("id", ""),
                    username=reviews.get("writerId", ""), 
                    content=reviews.get("reviewContent", ""), 
                    rating=reviews.get("reviewScore", 0),
                    date=reviews.get("createDate", ""), 
                    helpful_count=reviews.get("helpCount", 0),
                    review_type=models.ReviewTypeChoices.WORST
                )
                result_review.save()

        except Exception as e: 
            print(f"Error saving product reviews to database: {e}")
            return False

    def run(self): 
        # Initialize Digital Ocean Spaces client
        try: 
            self.initialize_digital_ocean_client()
            if not self.client: 
                print("Failed to initialize Digital Ocean Spaces client.")
                return False
        except Exception as e: 
            print(f"Error initializing Digital Ocean Spaces client: {e}")
            return False
        

        # Extract cookies using the CookieExtractor
        cookie_extractor = CookieExtractor() 
        cookie = cookie_extractor.extract_cookies("https://naver.com/")
        if not cookie: 
            print("Failed to extract cookies.")
            return False
        print(f"Extracted cookie: {cookie}")
        
        # Create a result entry in the database
        result = self.create_result(self.search_id)
        if not result: 
            return False
    

        # Search for product and get the top 5 results 
        product_search = NaverProductSearch(self.search_query, num_results=self.num_results, cookie=cookie)
        products = product_search.search_products() 


        if not products: 
            print("No products found.")
            return False 
        
        # Save product search results to the database
        
        for product in products[:1]: 
            result_item = self.save_product_search_to_db(result, product.get("card", {}).get("product", {}))
            product_information = ProductInformationExtractor(
                channel_uid=product.get("channelUId", {}), 
                product_id=product.get("card", {}).get("product", {}).get("channelProductId", ""), 
                original_product_no=product.get("card", {}).get("product", {}).get("originalMallProductId", ""),
                checkout_merchant_no=product.get("card", {}).get("product", {}).get("naverPaySellerNo", ""),  # Example merchant number
                cookie=cookie
            )

            # Get product details
            product_details = product_information.get_product_details() 
            try: 
                with open("product_details.json", "w", encoding="utf-8") as f:
                    json.dump(product_details, f, ensure_ascii=False, indent=4)
            except Exception as e: 
                pass

            if product_details: 
                count = 1
                order = 0
                # for product_url in product_details[::2]: 
                for product_url in product_details: 
                    # Download product detail images 
                    try: 
                        proxies = {
                            os.getenv("PROXY_TYPE"): f"{os.getenv('PROXY_TYPE')}://{os.getenv('PROXY_USERNAME')}:{os.getenv('PROXY_PASSWORD')}@{os.getenv('PROXY_SERVER_ADDRESS')}:{os.getenv('PROXY_SERVER_PORT')}",
                        }
                        response = requests.get(product_url, proxies=proxies)
                        product_id = product.get("card", {}).get("product", {}).get("productUrl", {}).get("pcUrl", "").split("/")[-1]
                        if response.status_code == 200: 
                            file_name = "" 
                            if 'gif' in product_url:
                                file_name = f"{product_id}_{count}.gif"
                            elif product_url.endswith('.jpg') or 'jpg' in product_url:
                                # file_name = product_url.split('/')[-1]
                                file_name = f"{product_id}_{count}.jpg"
                            elif product_url.endswith('.png'):
                                file_name = f"{product_id}_{count}.png"
                            else:
                                file_name = f"{product_id}_{count}.jpg"

                            with open(file_name, 'wb') as file:
                                file.write(response.content)
                            gif_file_name = None
                            if 'gif' in product_url: 
                                im = Image.open(file_name)
                                im.save(f"{product_id}_{count}.png")
                                gif_file_name = file_name
                                file_name = f"{product_id}_{count}.png"
                            
                            # Upload to Digital Ocean Spaces
                            image_url = self.upload_to_digital_ocean(file_name, object_name=f"product_details/{file_name}")
                            count += 1
                            # Save product detail's url to database 
                            if os.path.exists(file_name):
                                os.remove(file_name)

                                if gif_file_name: 
                                    os.remove(gif_file_name)
                            
                            order = self.save_product_details_to_db(result_item, image_url, order)

                    except Exception as e: 
                        print(f"Error downloading product detail images: {e}")
                        continue 

            # Get product reviews
            product_reviews = product_information.get_product_reviews()
            if product_reviews: 
                self.save_product_reviews_to_db(result_item, product_reviews)

            return True


if __name__ == "__main__":
    search_query = "iphone"
    orchestrator = Orchestrator(search_query)
    orchestrator.run()
