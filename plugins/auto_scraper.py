import asyncio
import aiohttp
import os
import re
from bs4 import BeautifulSoup
from hydrogram import Client
from hydrogram.types import Message
from info import BIN_CHANNEL, ADMINS
from database.users_chats_db import db
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Scraper configuration
SCRAPE_INTERVAL = 3600  # Check every 1 hour (in seconds)
MAX_SUBS_PER_RUN = 10   # Maximum subtitles to process per run

class SubtitleScraper:
    def __init__(self, bot: Client):
        self.bot = bot
        self.session = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
    
    async def init_session(self):
        if not self.session:
            self.session = aiohttp.ClientSession(headers=self.headers)
    
    async def close_session(self):
        if self.session:
            await self.session.close()
            self.session = None
    
    def is_processed(self, url: str) -> bool:
        """Check if URL has already been processed"""
        return db.is_scraped_url(url)
    
    def mark_processed(self, url: str, title: str):
        """Mark URL as processed"""
        db.add_scraped_url(url, title)
    
    async def download_file(self, url: str, filename: str) -> str:
        """Download a file and return local path"""
        await self.init_session()
        try:
            async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=60)) as response:
                if response.status == 200:
                    # Create temp directory if not exists
                    os.makedirs('temp_subs', exist_ok=True)
                    filepath = f'temp_subs/{filename}'
                    with open(filepath, 'wb') as f:
                        f.write(await response.read())
                    return filepath
        except Exception as e:
            logger.error(f"Download failed for {url}: {e}")
        return None
    
    async def upload_to_channel(self, filepath: str, caption: str) -> bool:
        """Upload file to BIN_CHANNEL"""
        try:
            await self.bot.send_document(
                chat_id=BIN_CHANNEL,
                document=filepath,
                caption=caption
            )
            logger.info(f"Uploaded: {caption}")
            return True
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            return False
        finally:
            # Clean up temp file
            if os.path.exists(filepath):
                os.remove(filepath)
    
    # ============== SUBZ.LK SCRAPER ==============
    async def scrape_subz_lk(self) -> list:
        """Scrape latest subtitles from subz.lk"""
        await self.init_session()
        subtitles = []
        
        try:
            async with self.session.get('https://subz.lk/', timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status != 200:
                    return subtitles
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Find subtitle entries - adjust selectors based on actual site structure
                for item in soup.select('.post-item, .subtitle-item, article')[:MAX_SUBS_PER_RUN]:
                    try:
                        link = item.find('a', href=True)
                        if not link:
                            continue
                        
                        url = link.get('href', '')
                        if not url.startswith('http'):
                            url = 'https://subz.lk' + url
                        
                        title = link.get_text(strip=True) or item.get_text(strip=True)[:100]
                        
                        if url and not self.is_processed(url):
                            subtitles.append({
                                'url': url,
                                'title': title,
                                'source': 'subz.lk'
                            })
                    except Exception as e:
                        logger.debug(f"Error parsing subz.lk item: {e}")
                        
        except Exception as e:
            logger.error(f"Error scraping subz.lk: {e}")
        
        return subtitles
    
    # ============== ZOOM.LK SCRAPER ==============
    async def scrape_zoom_lk(self) -> list:
        """Scrape latest subtitles from zoom.lk"""
        await self.init_session()
        subtitles = []
        
        try:
            async with self.session.get('https://zoom.lk/subtitles/', timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status != 200:
                    return subtitles
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Find subtitle entries
                for item in soup.select('.post, .entry, article, .subtitle-entry')[:MAX_SUBS_PER_RUN]:
                    try:
                        link = item.find('a', href=True)
                        if not link:
                            continue
                        
                        url = link.get('href', '')
                        if not url.startswith('http'):
                            url = 'https://zoom.lk' + url
                        
                        title = link.get_text(strip=True) or item.get_text(strip=True)[:100]
                        
                        if url and 'subtitle' in url.lower() and not self.is_processed(url):
                            subtitles.append({
                                'url': url,
                                'title': title,
                                'source': 'zoom.lk'
                            })
                    except Exception as e:
                        logger.debug(f"Error parsing zoom.lk item: {e}")
                        
        except Exception as e:
            logger.error(f"Error scraping zoom.lk: {e}")
        
        return subtitles
    
    # ============== BISCOPE.LK SCRAPER ==============
    async def scrape_biscope_lk(self) -> list:
        """Scrape latest subtitles from biscope.lk"""
        await self.init_session()
        subtitles = []
        
        try:
            async with self.session.get('https://biscope.lk/', timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status != 200:
                    return subtitles
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Find subtitle entries
                for item in soup.select('.post, .entry, article, .movie-item')[:MAX_SUBS_PER_RUN]:
                    try:
                        link = item.find('a', href=True)
                        if not link:
                            continue
                        
                        url = link.get('href', '')
                        if not url.startswith('http'):
                            url = 'https://biscope.lk' + url
                        
                        title = link.get_text(strip=True) or item.get_text(strip=True)[:100]
                        
                        if url and not self.is_processed(url):
                            subtitles.append({
                                'url': url,
                                'title': title,
                                'source': 'biscope.lk'
                            })
                    except Exception as e:
                        logger.debug(f"Error parsing biscope.lk item: {e}")
                        
        except Exception as e:
            logger.error(f"Error scraping biscope.lk: {e}")
        
        return subtitles

    async def get_download_link(self, page_url: str, source: str) -> tuple:
        """Get actual download link from subtitle page"""
        await self.init_session()
        
        try:
            async with self.session.get(page_url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status != 200:
                    return None, None
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Look for download links
                download_link = None
                filename = None
                
                # Common download button patterns
                for selector in ['a[href*="download"]', 'a[href*=".srt"]', 'a[href*=".zip"]', 
                                '.download-btn', '.btn-download', 'a.download']:
                    link = soup.select_one(selector)
                    if link and link.get('href'):
                        download_link = link.get('href')
                        if not download_link.startswith('http'):
                            base_url = '/'.join(page_url.split('/')[:3])
                            download_link = base_url + download_link
                        break
                
                # Extract filename from title or link
                title_tag = soup.find('h1') or soup.find('title')
                if title_tag:
                    title = title_tag.get_text(strip=True)
                    # Clean filename
                    filename = re.sub(r'[^\w\s\-\.]', '', title)[:80] + '.srt'
                else:
                    filename = f"subtitle_{datetime.now().strftime('%Y%m%d%H%M%S')}.srt"
                
                return download_link, filename
                
        except Exception as e:
            logger.error(f"Error getting download link from {page_url}: {e}")
        
        return None, None

    async def process_subtitle(self, sub_info: dict) -> bool:
        """Process a single subtitle: get download link, download, and upload"""
        url = sub_info['url']
        title = sub_info['title']
        source = sub_info['source']
        
        logger.info(f"Processing: {title} from {source}")
        
        # Get download link
        download_url, filename = await self.get_download_link(url, source)
        
        if not download_url:
            logger.warning(f"No download link found for: {url}")
            self.mark_processed(url, title)  # Mark as processed to avoid retrying
            return False
        
        # Download file
        filepath = await self.download_file(download_url, filename)
        
        if not filepath:
            logger.warning(f"Failed to download: {download_url}")
            return False
        
        # Upload to channel
        caption = f"📁 {title}\n🌐 Source: {source}\n📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        success = await self.upload_to_channel(filepath, caption)
        
        if success:
            self.mark_processed(url, title)
            return True
        
        return False

    async def run_scrape_cycle(self):
        """Run one complete scrape cycle for all sources"""
        logger.info("Starting scrape cycle...")
        
        all_subtitles = []
        
        # Scrape all sources
        try:
            subz_subs = await self.scrape_subz_lk()
            all_subtitles.extend(subz_subs)
            logger.info(f"Found {len(subz_subs)} new subtitles from subz.lk")
        except Exception as e:
            logger.error(f"subz.lk scrape failed: {e}")
        
        try:
            zoom_subs = await self.scrape_zoom_lk()
            all_subtitles.extend(zoom_subs)
            logger.info(f"Found {len(zoom_subs)} new subtitles from zoom.lk")
        except Exception as e:
            logger.error(f"zoom.lk scrape failed: {e}")
        
        try:
            biscope_subs = await self.scrape_biscope_lk()
            all_subtitles.extend(biscope_subs)
            logger.info(f"Found {len(biscope_subs)} new subtitles from biscope.lk")
        except Exception as e:
            logger.error(f"biscope.lk scrape failed: {e}")
        
        # Process found subtitles
        processed = 0
        for sub in all_subtitles[:MAX_SUBS_PER_RUN]:
            try:
                if await self.process_subtitle(sub):
                    processed += 1
                await asyncio.sleep(2)  # Rate limiting
            except Exception as e:
                logger.error(f"Error processing subtitle: {e}")
        
        logger.info(f"Scrape cycle complete. Processed {processed}/{len(all_subtitles)} subtitles")
        await self.close_session()


# Global scraper instance
scraper = None

async def start_auto_scraper(bot: Client):
    """Start the auto scraper background task"""
    global scraper
    scraper = SubtitleScraper(bot)
    
    logger.info("Auto-scraper started! Will check for new subtitles every hour.")
    
    while True:
        try:
            await scraper.run_scrape_cycle()
        except Exception as e:
            logger.error(f"Scraper error: {e}")
        
        # Wait for next cycle
        await asyncio.sleep(SCRAPE_INTERVAL)


# Admin command to manually trigger scrape
from hydrogram import filters

@Client.on_message(filters.command('scrape') & filters.user(ADMINS))
async def manual_scrape(client: Client, message: Message):
    """Manually trigger a scrape cycle"""
    global scraper
    
    msg = await message.reply("🔄 Starting manual scrape...")
    
    if not scraper:
        scraper = SubtitleScraper(client)
    
    try:
        await scraper.run_scrape_cycle()
        await msg.edit("✅ Scrape cycle complete! Check the logs for details.")
    except Exception as e:
        await msg.edit(f"❌ Scrape failed: {e}")


@Client.on_message(filters.command('scrape_status') & filters.user(ADMINS))
async def scrape_status(client: Client, message: Message):
    """Check scraper status"""
    total_scraped = db.get_scraped_count()
    await message.reply(f"📊 **Scraper Status**\n\n"
                       f"📁 Total URLs processed: {total_scraped}\n"
                       f"⏱ Scrape interval: {SCRAPE_INTERVAL // 60} minutes\n"
                       f"🔢 Max subs per run: {MAX_SUBS_PER_RUN}")
