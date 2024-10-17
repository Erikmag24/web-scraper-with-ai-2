from translator import translate_text, get_available_languages
from web_scraper import scrape_and_process

# Example usage
query = "sf"
languages_to_translate = ['af', 'sq']  # Italian, French

# Translate the text
translations = translate_text(query, languages_to_translate)
languages=get_available_languages()

# Path to ChromeDriver
chrome_driver_path = r"C:\Users\erikm\Desktop\project_folder\chromedriver-win32\chromedriver.exe"

# Scrape data and process it with Ollama
# You can optionally specify search engines to use
scrape_and_process(query, translations, chrome_driver_path, search_engines=["google"])