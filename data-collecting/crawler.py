import logging
import requests
from bs4 import BeautifulSoup
import time
import concurrent.futures

# Setup logging to file and terminal
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.StreamHandler(),  # Output ke terminal
                        logging.FileHandler('crawler.log', mode='a', encoding='utf-8')  # Output ke file
                    ])

# Function to crawl articles from a single page for a given date
def crawl_articles(start_date, end_date, page_num=1, max_pages=100):
    url = f"https://www.tempo.co/indeks?page={page_num}&category=date&start_date={start_date}&end_date={end_date}"
    articles = []
    
    logging.info(f"Starting to crawl page {page_num} from {start_date} to {end_date}...")

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Will raise an error for bad responses (e.g., 404 or 500)
    except requests.exceptions.RequestException as e:
        logging.error(f"    [ERROR] Failed to fetch page {page_num}: {e}")
        return articles
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Extract article links from the given HTML structure
    article_containers = soup.find_all('figure', class_='flex flex-row gap-3 py-4 container lg:mx-0 lg:px-0')
    if not article_containers:
        logging.info(f"    [INFO] No articles found on page {page_num}.")
        return articles
    
    for container in article_containers:
        article_link = container.find('a', href=True)
        
        if article_link:
            article_url = "https://www.tempo.co" + article_link['href']
            articles.append({'url': article_url})
            logging.info(f"    [INFO] Found article URL: {article_url}")
    
    # Check if there is a next page button (pagination)
    next_page_button = soup.find('button', {'aria-label': 'Next Page'})
    if next_page_button:
        next_page_value = next_page_button.get('value')
        if next_page_value and int(next_page_value) > page_num and page_num < max_pages:
            page_num += 1
            articles.extend(crawl_articles(start_date, end_date, page_num, max_pages))  # Recursive call to crawl the next page
    
    time.sleep(1)  # Sleep between requests
    return articles

# Function to save URLs to a text file
def save_urls_to_txt(articles, filename="articles.txt"):
    logging.info(f"[INFO] Saving {len(articles)} URLs to {filename}...")
    try:
        with open(filename, mode='a', encoding='utf-8') as file:
            for article in articles:
                file.write(f"{article['url']}\n")  # Save only the URL
    except Exception as e:
        logging.error(f"[ERROR] Failed to save URLs to {filename}: {e}")

# Function to crawl n months back, from today moving backward day by day
def crawl_n_months_back(n_months):
    from datetime import datetime, timedelta
    today = datetime.today()
    start_date = today - timedelta(days=n_months * 30)
    
    # Loop through each day from the start date to today (backwards)
    date = today
    total_articles = 0

    logging.info(f"Starting crawl for the last {n_months} months, from {start_date.strftime('%Y-%m-%d')} to {today.strftime('%Y-%m-%d')}.")

    articles_to_save = []
    
    # Use ThreadPoolExecutor to crawl articles concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_date = {executor.submit(crawl_articles, date.strftime("%Y-%m-%d"), date.strftime("%Y-%m-%d")): date for date in (today - timedelta(days=i) for i in range((today - start_date).days + 1))}
        
        for future in concurrent.futures.as_completed(future_to_date):
            date = future_to_date[future]
            try:
                articles = future.result()
                if articles:
                    articles_to_save.extend(articles)
                    total_articles += len(articles)
                logging.info(f"Found {len(articles)} articles for {date.strftime('%Y-%m-%d')}. Total articles so far: {total_articles}")
            except Exception as e:
                logging.error(f"Error processing date {date.strftime('%Y-%m-%d')}: {e}")
    
    # After crawling, save the collected article URLs
    if articles_to_save:
        save_urls_to_txt(articles_to_save, filename="articles.txt")
    logging.info(f"Finished crawling. Total articles found: {total_articles}")

# Crawl articles for the past 12 months and save to txt
crawl_n_months_back(12)
