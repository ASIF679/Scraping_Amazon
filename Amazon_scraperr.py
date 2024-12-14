from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import json
from urllib.parse import urljoin

def setup_driver():
    # Set up Chrome options to run in headless mode
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # Ensure GUI is off
    chrome_options.add_argument('--no-sandbox')  # Required for Linux systems
    chrome_options.add_argument('--disable-dev-shm-usage')  # Overcome limited resources

    # Set up WebDriver using the installed chromedriver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver

def get_product_titles_prices_and_images(driver, url):
    driver.get(url)
    time.sleep(2)  # Wait for the page to load

    # Get the page source and parse it with BeautifulSoup
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, 'html.parser')

    # Find all product title elements, prices, and images
    product_data = []
    products = soup.find_all('a', class_='a-link-normal s-line-clamp-2 s-link-style a-text-normal')

    for product in products:
        # Extract the product title
        title = product.find('h2', class_='a-size-medium a-spacing-none a-color-base a-text-normal')

        # Extract the price
        price = product.find_next('span', class_='a-price')
        if price:
            price_value = price.find('span', class_='a-offscreen')
            if price_value:
                price_text = price_value.get_text(strip=True)
            else:
                price_text = "Price Not Available"
        else:
            price_text = "Price Not Available"

        # Extract the product image URL
        img_tag = product.find_next('img', class_='s-image')
        if img_tag:
            img_url = img_tag.get('src', 'Image Not Available')
        else:
            img_url = "Image Not Available"

        if title:
            product_data.append({
                'title': title.get_text(strip=True),
                'price': price_text,
                'image_url': img_url
            })

    return product_data

def get_next_page_url(driver, base_url):
    try:
        # Find the "Next" button element using the updated method
        next_button = driver.find_element(By.CLASS_NAME, 's-pagination-next')
        # Get the relative URL of the next page
        next_page_relative_url = next_button.get_attribute('href')
        # Combine it with the base URL to get the full URL
        next_page_url = urljoin(base_url, next_page_relative_url)
        return next_page_url
    except Exception as e:
        print("No next page found or error while fetching next page:", e)
        return None

def scrape_category(driver, category, pages_to_scrape=20):
    base_url = f"https://www.amazon.com/s?k={category}"
    current_url = base_url
    category_data = []

    for page in range(1, pages_to_scrape + 1):
        print(f"Scraping page {page} for category '{category}'...")
        data = get_product_titles_prices_and_images(driver, current_url)
        category_data.extend(data)

        # Get the next page URL
        next_page_url = get_next_page_url(driver, base_url)
        if next_page_url:
            current_url = next_page_url
        else:
            print(f"Reached the last page or could not find next page for category '{category}'.")
            break

        time.sleep(2)  # Wait a bit before scraping the next page

    return category_data

def main():
    # Read categories from JSON file
    with open('categories.json', 'r') as f:
        categories = json.load(f)

    driver = setup_driver()
    complete_data = {}

    try:
        for category in categories:
            print(f"Scraping data for category: {category}...")
            category_data = scrape_category(driver, category)
            complete_data[category] = category_data

        # Save all data to a JSON file
        with open('complete_data.json', 'w') as f:
            json.dump(complete_data, f, indent=4)
        print("Saved data for all categories to 'complete_data.json'.")

    finally:
        driver.quit()

if __name__ == '__main__':
    main()
