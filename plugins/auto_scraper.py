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
                    logger.warning(f"subz.lk returned status {response.status}")
                    return subtitles
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Find all links that contain "sinhala-subtitle" in the URL
                for link in soup.find_all('a', href=True):
                    href = link.get('href', '')
                    
                    # Filter subtitle pages - they contain "sinhala-subtitle" in URL
                    if 'subz.lk/' in href and 'sinhala-subtitle' in href.lower():
                        url = href if href.startswith('http') else f'https://subz.lk{href}'
                        
                        # Get title from link text
                        title = link.get_text(strip=True)
                        if not title or len(title) < 3:
                            continue
                        
                        # Skip navigation/category links
                        if title.lower() in ['see more', 'movies', 'tv shows', 'category']:
                            continue
                        
                        if url and not self.is_processed(url):
                            subtitles.append({
                                'url': url,
                                'title': title[:100],
                                'source': 'subz.lk'
                            })
                
                # Remove duplicates
                seen = set()
                unique_subtitles = []
                for sub in subtitles:
                    if sub['url'] not in seen:
                        seen.add(sub['url'])
                        unique_subtitles.append(sub)
                
                return unique_subtitles[:MAX_SUBS_PER_RUN]
                        
        except Exception as e:
            logger.error(f"Error scraping subz.lk: {e}")
        
        return subtitles
    
    # ============== ZOOM.LK SCRAPER ==============
    async def scrape_zoom_lk(self) -> list:
        """Scrape latest subtitles from zoom.lk"""
        await self.init_session()
        subtitles = []
        
        try:
            async with self.session.get('https://zoom.lk/', timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status != 200:
                    logger.warning(f"zoom.lk returned status {response.status}")
                    return subtitles
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Find all links that contain subtitle info
                for link in soup.find_all('a', href=True):
                    href = link.get('href', '')
                    
                    # Filter subtitle pages
                    if 'zoom.lk/' in href and ('sinhala-subtitle' in href.lower() or 'subtitle' in href.lower()):
                        url = href if href.startswith('http') else f'https://zoom.lk{href}'
                        
                        # Get title from link text
                        title = link.get_text(strip=True)
                        if not title or len(title) < 3:
                            continue
                        
                        if url and not self.is_processed(url):
                            subtitles.append({
                                'url': url,
                                'title': title[:100],
                                'source': 'zoom.lk'
                            })
                
                # Remove duplicates
                seen = set()
                unique_subtitles = []
                for sub in subtitles:
                    if sub['url'] not in seen:
                        seen.add(sub['url'])
                        unique_subtitles.append(sub)
                
                return unique_subtitles[:MAX_SUBS_PER_RUN]
                        
        except Exception as e:
            logger.error(f"Error scraping zoom.lk: {e}")
        
        return subtitles
    
    # ============== BAISCOPE.LK SCRAPER ==============
    async def scrape_baiscope_lk(self) -> list:
        """Scrape latest subtitles from baiscope.lk"""
        await self.init_session()
        subtitles = []
        
        try:
            async with self.session.get('https://www.baiscope.lk/', timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status != 200:
                    logger.warning(f"baiscope.lk returned status {response.status}")
                    return subtitles
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Find all links that contain subtitle info
                for link in soup.find_all('a', href=True):
                    href = link.get('href', '')
                    
                    # Filter subtitle pages - baiscope uses "sinhala-subtitles" in URL
                    if 'baiscope.lk/' in href and ('sinhala-subtitle' in href.lower() or 'subtitles' in href.lower()):
                        url = href if href.startswith('http') else f'https://www.baiscope.lk{href}'
                        
                        # Skip category pages
                        if '/category/' in url:
                            continue
                        
                        # Get title from link text
                        title = link.get_text(strip=True)
                        if not title or len(title) < 3:
                            continue
                        
                        # Skip navigation links
                        if 'ලබාගන්න' in title or 'සියලුම' in title:
                            continue
                        
                        if url and not self.is_processed(url):
                            subtitles.append({
                                'url': url,
                                'title': title[:100],
                                'source': 'baiscope.lk'
                            })
                
                # Remove duplicates
                seen = set()
                unique_subtitles = []
                for sub in subtitles:
                    if sub['url'] not in seen:
                        seen.add(sub['url'])
                        unique_subtitles.append(sub)
                
                return unique_subtitles[:MAX_SUBS_PER_RUN]
                        
        except Exception as e:
            logger.error(f"Error scraping baiscope.lk: {e}")
        
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
                
                download_link = None
                filename = None
                
                # Common download button patterns for these sites
                download_selectors = [
                    'a[href*=".srt"]',
                    'a[href*=".zip"]', 
                    'a[href*=".rar"]',
                    'a[href*="download"]',
                    'a[href*="drive.google"]',
                    'a[href*="mediafire"]',
                    'a[href*="mega.nz"]',
                    '.download-link a',
                    '.btn-download',
                    'a.download',
                    'a[download]'
                ]
                
                for selector in download_selectors:
                    link = soup.select_one(selector)
                    if link and link.get('href'):
                        download_link = link.get('href')
                        if not download_link.startswith('http'):
                            base_url = '/'.join(page_url.split('/')[:3])
                            download_link = base_url + download_link
                        break
                
                # Extract filename from title
                title_tag = soup.find('h1') or soup.find('title')
                if title_tag:
                    title = title_tag.get_text(strip=True)
                    # Clean filename - keep only alphanumeric, spaces, and basic punctuation
                    filename = re.sub(r'[^\w\s\-\.\(\)]', '', title)[:80]
                    # Add extension based on download link
                    if download_link:
                        if '.zip' in download_link.lower():
                            filename += '.zip'
                        elif '.rar' in download_link.lower():
                            filename += '.rar'
                        else:
                            filename += '.srt'
                    else:
                        filename += '.srt'
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
            baiscope_subs = await self.scrape_baiscope_lk()
            all_subtitles.extend(baiscope_subs)
            logger.info(f"Found {len(baiscope_subs)} new subtitles from baiscope.lk")
        except Exception as e:
            logger.error(f"baiscope.lk scrape failed: {e}")
        
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
                       f"🔢 Max subs per run: {MAX_SUBS_PER_RUN}\n\n"
                       f"🌐 Sources:\n"
                       f"• subz.lk\n"
                       f"• zoom.lk\n"
                       f"• baiscope.lk")


@Client.on_message(filters.command('seed_scraper') & filters.user(ADMINS))
async def seed_scraper(client: Client, message: Message):
    """
    Seed the scraper database by marking all EXISTING subtitles as processed.
    This prevents downloading old subtitles - only NEW ones will be downloaded.
    Run this ONCE before starting regular scraping.
    """
    global scraper
    
    msg = await message.reply("🌱 **Seeding scraper database...**\n\nThis will mark all existing subtitles as 'processed' WITHOUT downloading them.\nOnly truly NEW subtitles will be downloaded in the future.")
    
    if not scraper:
        scraper = SubtitleScraper(client)
    
    await scraper.init_session()
    seeded_count = 0
    
    try:
        # Seed subz.lk
        await msg.edit("🌱 Seeding subz.lk...")
        try:
            async with scraper.session.get('https://subz.lk/', timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    for link in soup.find_all('a', href=True):
                        href = link.get('href', '')
                        if 'subz.lk/' in href and 'sinhala-subtitle' in href.lower():
                            url = href if href.startswith('http') else f'https://subz.lk{href}'
                            title = link.get_text(strip=True)[:100] or 'Unknown'
                            db.add_scraped_url(url, f"[SEEDED] {title}")
                            seeded_count += 1
        except Exception as e:
            logger.error(f"Error seeding subz.lk: {e}")
        
        # Seed zoom.lk
        await msg.edit(f"🌱 Seeding zoom.lk... ({seeded_count} done)")
        try:
            async with scraper.session.get('https://zoom.lk/', timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    for link in soup.find_all('a', href=True):
                        href = link.get('href', '')
                        if 'zoom.lk/' in href and ('sinhala-subtitle' in href.lower() or 'subtitle' in href.lower()):
                            url = href if href.startswith('http') else f'https://zoom.lk{href}'
                            title = link.get_text(strip=True)[:100] or 'Unknown'
                            db.add_scraped_url(url, f"[SEEDED] {title}")
                            seeded_count += 1
        except Exception as e:
            logger.error(f"Error seeding zoom.lk: {e}")
        
        # Seed baiscope.lk  
        await msg.edit(f"🌱 Seeding baiscope.lk... ({seeded_count} done)")
        try:
            async with scraper.session.get('https://www.baiscope.lk/', timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    for link in soup.find_all('a', href=True):
                        href = link.get('href', '')
                        if 'baiscope.lk/' in href and ('sinhala-subtitle' in href.lower() or 'subtitles' in href.lower()):
                            if '/category/' not in href:
                                url = href if href.startswith('http') else f'https://www.baiscope.lk{href}'
                                title = link.get_text(strip=True)[:100] or 'Unknown'
                                db.add_scraped_url(url, f"[SEEDED] {title}")
                                seeded_count += 1
        except Exception as e:
            logger.error(f"Error seeding baiscope.lk: {e}")
        
        await scraper.close_session()
        
        await msg.edit(f"✅ **Seeding complete!**\n\n"
                      f"📁 Marked {seeded_count} URLs as processed\n"
                      f"🆕 Only NEW subtitles will be downloaded now\n\n"
                      f"Total in database: {db.get_scraped_count()}")
        
    except Exception as e:
        await msg.edit(f"❌ Seeding failed: {e}")


@Client.on_message(filters.command('reset_scraper') & filters.user(ADMINS))
async def reset_scraper(client: Client, message: Message):
    """Reset the scraper database - clears all processed URLs"""
    if len(message.command) < 2 or message.command[1] != 'confirm':
        return await message.reply(
            "⚠️ **Warning!**\n\n"
            "This will clear ALL processed URLs from the database.\n"
            "The scraper will treat ALL subtitles as new and try to download them!\n\n"
            "To confirm, use: `/reset_scraper confirm`"
        )
    
    result = db.clear_scraped_urls()
    await message.reply(f"🗑 **Scraper database reset!**\n\n"
                       f"Deleted {result.deleted_count} processed URLs.\n"
                       f"Run `/seed_scraper` to mark existing URLs before scraping.")
