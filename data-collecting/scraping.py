import aiohttp
import asyncio
import csv
import logging
from bs4 import BeautifulSoup

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def fetch_article_data(session, url, retries=3):
    for attempt in range(retries):
        try:
            logger.info(f"Scraping URL: {url} (Attempt {attempt + 1}/{retries})")
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as response:
                if response.status != 200:
                    logger.error(f"Non-200 status code {response.status} for URL: {url}")
                    return {
                        'url': url,
                        'category': None,
                        'title': None,
                        'date': None,
                        'content': None
                    }

                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')

                # Ambil kategori
                category_element = soup.find('div', class_='flex', attrs={'data-v-85901760': True})
                category = (category_element.find('span', class_='capitalize text-sm font-medium text-primary-main').text.strip()
                            if category_element else None)

                # Ambil title
                title_element = soup.find('h1', class_='text-[26px] font-bold leading-[122%] text-neutral-1200', attrs={'data-v-85901760': True})
                title = title_element.text.strip() if title_element else None

                # Ambil tanggal
                date_element = soup.find('p', class_='text-neutral-900 text-sm', attrs={'data-v-85901760': True})
                date = date_element.text.strip() if date_element else None

                # Ambil semua content p di dalam content-wrapper
                content_element = soup.find('div', id='content-wrapper')
                content = None
                if content_element:
                    paragraphs = content_element.find_all('p')
                    content = '\n'.join([p.text.strip() for p in paragraphs]) if paragraphs else None

                logger.info(f"Successfully scraped URL: {url}")
                return {
                    'category': category,
                    'title': title,
                    'date': date,
                    'content': content
                }
        
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.warning(f"Network error on {url}: {e}")
        except Exception as e:
            logger.warning(f"Unexpected error on {url}: {e}")

        await asyncio.sleep(2)  # Delay antara retry

    logger.error(f"Max retries reached for URL: {url}")
    return {
        'category': None,
        'title': None,
        'date': None,
        'content': None
    }

async def scrape_articles_from_file(filename):
    try:
        # Membaca URL dari file articles.txt
        with open(filename, 'r') as file:
            urls = file.readlines()

        logger.info(f"Found {len(urls)} URLs in {filename}")

        async with aiohttp.ClientSession() as session:
            tasks = [fetch_article_data(session, url.strip()) for url in urls]
            results = await asyncio.gather(*tasks)

        logger.info(f"Scraped {len(results)} articles")
        return results

    except Exception as e:
        logger.error(f"Error reading file {filename}: {e}")
        return []

def save_to_csv(data, filename):
    try:
        # Menyimpan data ke file CSV
        with open(filename, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=['category', 'title', 'date', 'content'])
            writer.writeheader()  # Menulis header
            writer.writerows(data)  # Menulis data artikel

        logger.info(f"Successfully saved {len(data)} articles to {filename}")
    
    except Exception as e:
        logger.error(f"Error saving data to {filename}: {e}")

# Menjalankan skrip scraping dan menyimpan hasil ke CSV
async def main():
    logger.info("Starting article scraping process")
    results = await scrape_articles_from_file('articles.txt')
    
    if results:
        # Menyimpan hasil ke CSV
        save_to_csv(results, 'articles.csv')
    else:
        logger.warning("No articles scraped. Please check the input URLs or the scraping process.")

# Menjalankan event loop untuk async scraping
if __name__ == '__main__':
    asyncio.run(main())
