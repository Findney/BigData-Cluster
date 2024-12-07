import aiohttp
import asyncio
import csv
import logging
from bs4 import BeautifulSoup

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def fetch_article_data(session, url):
    try:
        logger.info(f"Scraping URL: {url}")
        async with session.get(url) as response:
            html = await response.text()
            soup = BeautifulSoup(html, 'html.parser')

            # Ambil kategori
            category_element = soup.find('div', class_='flex', attrs={'data-v-85901760': True})
            category = category_element.find('span', class_='capitalize text-sm font-medium text-primary-main').text if category_element else None

            # Ambil title
            title_element = soup.find('h1', class_='text-[26px] font-bold leading-[122%] text-neutral-1200', attrs={'data-v-85901760': True})
            title = title_element.text.strip() if title_element else None

            # Ambil tanggal
            date_element = soup.find('p', class_='text-neutral-900 text-sm', attrs={'data-v-85901760': True})
            date = date_element.text.strip() if date_element else None

            # Ambil semua content p di dalam content-wrapper
            content = ""
            content_elements = soup.find_all('div', id='content-wrapper')
            for content_element in content_elements:
                # Pastikan div memiliki tag <p> di dalamnya
                paragraphs = content_element.find_all('p')
                if paragraphs:
                    content += '\n'.join([p.text.strip() for p in paragraphs]) + '\n'

            if not content:
                content = None

            logger.info(f"Successfully scraped URL: {url}")
            return {
                'url': url,
                'category': category,
                'title': title,
                'date': date,
                'content': content
            }

    except Exception as e:
        logger.error(f"Error scraping {url}: {e}")
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

def clean_content(content):
    # Menghapus tanda kutip ganda dan menggantinya dengan tanda kutip tunggal
    if content:
        content = content.replace('"', "'")
        # Mengganti baris baru dengan spasi atau simbol lain
        content = content.replace('\n', ' ').replace('\r', '')
    return content

def save_to_csv(data, filename):
    try:
        # Menyimpan data ke file CSV
        with open(filename, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=['url', 'category', 'title', 'date', 'content'])
            writer.writeheader()  # Menulis header
            # Bersihkan konten sebelum menulis ke CSV
            for article in data:
                article['content'] = clean_content(article['content'])
            writer.writerows(data)  # Menulis data artikel

        logger.info(f"Successfully saved {len(data)} articles to {filename}")
    
    except Exception as e:
        logger.error(f"Error saving data to {filename}: {e}")


# Menjalankan skrip scraping dan menyimpan hasil ke CSV
async def main():
    logger.info("Starting article scraping process")
    results = await scrape_articles_from_file('articles1.txt')
    
    if results:
        # Menyimpan hasil ke CSV
        save_to_csv(results, 'articles.csv')
    else:
        logger.warning("No articles scraped. Please check the input URLs or the scraping process.")

# Menjalankan event loop untuk async scraping
if __name__ == '__main__':
    asyncio.run(main())
