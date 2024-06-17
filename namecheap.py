from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import string
from itertools import product
from webdriver_manager.chrome import ChromeDriverManager
import multiprocessing

# Set up the Chrome driver with headless mode
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--window-size=1920,1080")

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

# Base URL for Namecheap domain search
base_url = "https://www.namecheap.com/domains/registration/results/?domain={}"

# List of all possible three-letter combinations
# letters = string.ascii_lowercase
letters = "abcdef"

three_letter_combos = [''.join(combo) for combo in product(letters, repeat=4)]
# three_letter_combos = ["nadu"]

# Navigate to the domain search page
def scrape_domain_info(domain):
    url = base_url.format(domain)
    driver.get(url)

    # Wait for the page to load and the dynamic content to be rendered
    time.sleep(5)  # Adjust the delay as needed

    # Try to find the article with class 'domain-com available'
    try:
        availability_article = driver.find_element(By.CSS_SELECTOR, 'article.domain-com.available')
        available = True
        price_tag = availability_article.find_element(By.CSS_SELECTOR, 'div.price strong')
        price = price_tag.text.strip()
        renewal_tag = availability_article.find_element(By.CSS_SELECTOR, 'div.price small')
        renewal_price = renewal_tag.text.strip().split(" ")[2]
    except Exception as e:
        available = False
        renewal_price = "N/A"
        price = "N/A"

    return {"domain": domain, "available": available, "price": price, "renewal_price": renewal_price}

    print({"domain": f"{domain}", "available": available, "price": price, "renewal_price": renewal_price})

    # Close the browser
    driver.quit()

# Function to process combinations in parallel
def process_combos(combos):
    results = []
    combo_count = 0
    for combo in combos:
        domain = f"{combo}.com"
        domain_info = scrape_domain_info(domain)
        if domain_info["available"]:
            results.append(domain_info)

        combo_count += 1
        if combo_count % 100 == 0:
            current_time = time.time()
            print(f"Timestamp: {time.ctime(current_time)} - Processing combination {combo} ({combo_count}/{len(combos)})")
    return results


if __name__ == "__main__":
    start_time = time.time()
    num_processes = multiprocessing.cpu_count()  # Number of processes based on CPU count
    chunk_size = len(three_letter_combos) // num_processes  # Chunk size for dividing combinations

    # Split combinations into chunks for parallel processing
    chunks = [three_letter_combos[i:i + chunk_size] for i in range(0, len(three_letter_combos), chunk_size)]

    # Create a pool of processes
    pool = multiprocessing.Pool(processes=num_processes)
    results = pool.map(process_combos, chunks)

    # Flatten the results and print available domains
    available_domains = [domain for chunk_result in results for domain in chunk_result]
    for domain_info in available_domains:
        print(domain_info)

    end_time = time.time()
    total_time = end_time - start_time
    print(f"Total time taken: {total_time:.2f} seconds")