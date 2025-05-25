from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time
import pandas as pd

service = Service(ChromeDriverManager().install())

options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-gpu')
options.add_argument('--window-size=1920,1080')
options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36')

category_list = [
{"name": "하우스/스텝", "url": "https://dogpre.com/category/042"},
{"name": "급식기/급수기", "url": "https://dogpre.com/category/041"},
{"name": "산책/훈련", "url": "https://dogpre.com/category/045"},
{"name": "의류/액세서리", "url": "https://dogpre.com/category/044"},
{"name": "목욕용품", "url": "https://dogpre.com/category/064"},
{"name": "위생/배변", "url": "https://dogpre.com/category/039"},
{"name": "장난감", "url": "https://dogpre.com/category/047"},
{"name": "생활/가전", "url": "https://dogpre.com/category/058"},
{"name": "케어용품", "url": "https://dogpre.com/category/040"},
{"name": "이동장/유모차", "url": "https://dogpre.com/category/043"}
]


all_products = []

def scroll_to_bottom(driver, pause_time=2, max_scroll=100):
    last_height = driver.execute_script("return document.body.scrollHeight")
    scroll_count = 0
    while scroll_count < max_scroll:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(pause_time)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
        scroll_count += 1

try:
    driver = webdriver.Chrome(service=service, options=options)

    for category in category_list:
        print(f"\n[{category['name']}] 카테고리 시작")
        driver.get(category["url"])
        time.sleep(3)

        scroll_to_bottom(driver, pause_time=2, max_scroll=100)
        time.sleep(2)

        product_elements = driver.find_elements(By.CSS_SELECTOR, '.item')

        for elem in product_elements:
            try:
                name_elem = elem.find_element(By.CSS_SELECTOR, '.style-itemList-title')
                product_name = name_elem.text.strip() if name_elem else None

                price_elem = elem.find_element(By.CSS_SELECTOR, '.style-itemList-price .price')
                price = price_elem.text.strip() if price_elem else None

                img_elem = elem.find_element(By.CSS_SELECTOR, 'img')
                img_url = img_elem.get_attribute('src') if img_elem else None

                product_info = {
                    "category": category["name"],
                    "name": product_name,
                    "price": price,
                    "image_url": img_url
                }
                all_products.append(product_info)
            except Exception as e:
                print(f"상품 추출 중 오류: {e}")

    df = pd.DataFrame(all_products)
    print(f"총 {len(df)}개 상품 정보 추출 완료")
    df.to_csv('dogpre_products_all.csv', index=False, encoding='utf-8-sig')
    print("CSV 파일 저장 완료")

except Exception as e:
    print(f"실행 중 오류 발생: {e}")
finally:
    try:
        driver.quit()
    except:
        pass
