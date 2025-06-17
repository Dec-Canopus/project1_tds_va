import os
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tqdm import tqdm

TDS_URL = "https://tds.s-anand.net/#/"
OUTPUT_FILE = "data/tds_content.json"

def launch_browser(headless=True):
    options = Options()
    if headless:
        options.add_argument("--headless")
    options.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(options=options)

def expand_all_nodes(driver):
    driver.get(TDS_URL)
    time.sleep(5)
    elements = driver.find_elements(By.CSS_SELECTOR, "li.folder.level-1:not(.open), li.file > div:not(.open)")
    for el in elements:
        try:
            el.click()
            time.sleep(0.2)
        except Exception:
            continue

def extract_links(driver):
    return [
        {"title": el.text, "href": el.get_attribute("href")}
        for el in driver.find_elements(By.CSS_SELECTOR, "li.file a")
    ]

def fetch_page_content(driver, url):
    driver.get(url)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "content")))
    return driver.find_element(By.CLASS_NAME, "content").text.strip()

def scrape_sanand_net():
    driver = launch_browser(headless=True)
    expand_all_nodes(driver)
    links = extract_links(driver)

    scraped_data = []
    for item in tqdm(links, desc="Scraping TDS content"):
        try:
            content = fetch_page_content(driver, item["href"])
            scraped_data.append({
                "title": item["title"],
                "url": item["href"],
                "content": content
            })
        except Exception as e:
            print(f"⚠️ Failed: {item['title']} - {e}")

    driver.quit()
    save_data(scraped_data, OUTPUT_FILE)

def save_data(data, file_path):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ Data saved to {file_path}")

