from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import string
from itertools import product
import concurrent.futures
import csv
import os
import fcntl  # For file-based locking
from multiprocessing import Manager, Lock, Value

# Base URL for Namecheap domain search
base_url = "https://www.namecheap.com/domains/registration/results/?domain={}"

# List of all possible three-letter combinations
letters = "qdnxbhvzyusacefgijklmoprtw"
two_letter_combos = [''.join(combo) for combo in product(letters, repeat=2)]

csv_file = "avail_two_letters.csv"

def create_driver():
    # Set up the Chrome driver with headless mode
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

# Navigate to the domain search page
def scrape_domain_info(driver, domain):
    url = base_url.format(domain)
    driver.get(url)

    # Wait for the page to load and the dynamic content to be rendered
    time.sleep(6)  # Adjust the delay as needed
    try:
        availability_article = driver.find_element(By.CSS_SELECTOR, 'article.domain-com.available')
        available = True
        price_tag = availability_article.find_element(By.CSS_SELECTOR, 'div.price strong')
        price = price_tag.text.strip().replace('$', '').replace(',', '')
        renewal_tag = availability_article.find_element(By.CSS_SELECTOR, 'div.price small')
        renewal_price = renewal_tag.text.strip().split(" ")[2].replace('$', '').replace(',', '').replace('/yr', '')
    except Exception as e:
        available = False
        renewal_price = "N/A"
        price = "N/A"

    return {"domain": domain, "available": available, "price": price, "renewal_price": renewal_price}

def process_combos(combos):
    driver = create_driver()
    for i, combo in enumerate(combos):
        domain = f"{combo}.com"
        domain_info = scrape_domain_info(driver, domain)
        if domain_info["available"]:
            with open(csv_file, 'a', newline='') as csvfile:
                fieldnames = ['domain', 'available', 'price', 'renewal_price']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writerow(domain_info)
                print(f"Written {domain_info} results to CSV")

        print(f"Timestamp: {time.ctime(time.time())} - Num: {i} - Domain: {domain}")
    driver.quit()

def split_list(lst, n):
    """Splits a list into n approximately equal parts"""
    k, m = divmod(len(lst), n)
    return [lst[i*k + min(i, m):(i+1)*k + min(i+1, m)] for i in range(n)]

if __name__ == "__main__":
    start_time = time.time()

    # Write the CSV header before starting the pool
    if not os.path.exists(csv_file):
        with open(csv_file, 'w', newline='') as csvfile:
            fieldnames = ['domain', 'available', 'price', 'renewal_price']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

    for lst in split_list(two_letter_combos, 6):
        process_combos(lst)
    
    end_time = time.time()
    total_time = end_time - start_time
    print(f"Total time taken: {total_time:.2f} seconds")
    print(f"Available domains have been written to " + csv_file)
