#search_engines.py
from typing import List
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
from config import SEARCH_ENGINES, CHROME_DRIVER_PATH
from webdriver_manager.chrome import ChromeDriverManager  # Import WebDriver Manager

def get_search_results(query: str, search_engine: str, num_pages: int) -> List[str]:
    """
    Scrape search results from a specified search engine.

    Args:
        query (str): The search query.
        search_engine (str): The name of the search engine to use.
        chrome_driver_path (str): Path to the Chrome WebDriver.
        num_pages (int): Number of result pages to scrape.

    Returns:
        List[str]: A list of unique result URLs.
    """
    # Get the base URL for the specified search engine
    base_url = SEARCH_ENGINES.get(search_engine)
    if not base_url:
        raise ValueError(f"Unsupported search engine: {search_engine}")

    # Set up the Chrome WebDriver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)
    
    results = set()  # Use a set to avoid duplicate URLs

    try:
        for page in range(num_pages):
            # Construct the URL for each page of results
            url = f"{base_url}{query}&start={page * 10}"
            driver.get(url)

            try:
                # Wait for the page to load
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            except TimeoutException:
                print(f"Page {page + 1} took too long to load. Skipping.")
                continue

            # Parse the page content
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            links = soup.find_all('a')

            # Extract and filter valid result URLs
            for link in links:
                href = link.get('href')
                if href and isinstance(href, str) and href.startswith('http') and not href.startswith(base_url):
                    results.add(href)

    finally:
        driver.quit()

    return list(results)



# This file contains functions for scraping search results from various search engines.
# It uses Selenium to automate web browsing and BeautifulSoup for parsing HTML.
# The main function, get_search_results(), is called by scrape_and_process.py to fetch links for a given query.
# It's designed to work with multiple search engines, making the scraping process more versatile.