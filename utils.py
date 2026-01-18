from hydrogram.errors import UserNotParticipant, FloodWait
from info import LONG_IMDB_DESCRIPTION, ADMINS, IS_PREMIUM, TIME_ZONE, TMDB_API_KEY
from imdb import Cinemagoer
import asyncio
from hydrogram.types import InlineKeyboardButton
from hydrogram import enums
import re
from datetime import datetime
from database.users_chats_db import db
import requests, pytz
import aiohttp

imdb = Cinemagoer() 

class temp(object):
    START_TIME = 0
    BANNED_USERS = []
    BANNED_CHATS = []
    ME = None
    CANCEL = False
    U_NAME = None
    B_NAME = None
    SETTINGS = {}
    VERIFICATIONS = {}
    FILES = {}
    USERS_CANCEL = False
    GROUPS_CANCEL = False
    BOT = None
    PREMIUM = {}

async def is_subscribed(bot, query):
    btn = []
    try:
        if query.from_user.id in ADMINS:
            return btn
        if IS_PREMIUM and await is_premium(query.from_user.id, bot):
            return btn
    except:
        pass
    
    stg = db.get_bot_sttgs()
    if not stg or not stg.get('FORCE_SUB_CHANNELS'):
        return btn
    
    for channel_id in stg.get('FORCE_SUB_CHANNELS').split(' '):
        try:
            channel_id = int(channel_id.strip())
            chat = await bot.get_chat(channel_id)
            member = await bot.get_chat_member(channel_id, query.from_user.id)
            # Check if user is actually a member (not left/kicked/banned)
            if member.status.name in ['LEFT', 'BANNED', 'RESTRICTED']:
                btn.append(
                    [InlineKeyboardButton(f'🔔 Join : {chat.title}', url=chat.invite_link or f'https://t.me/{chat.username}')]
                )
        except UserNotParticipant:
            try:
                chat = await bot.get_chat(channel_id)
                invite_link = chat.invite_link or f'https://t.me/{chat.username}'
                btn.append(
                    [InlineKeyboardButton(f'🔔 Join : {chat.title}', url=invite_link)]
                )
            except Exception as e:
                print(f"Error getting chat {channel_id}: {e}")
        except Exception as e:
            print(f"Force sub check error for {channel_id}: {e}")
    
    # Request force sub (for channels with join requests)
    if stg and stg.get('REQUEST_FORCE_SUB_CHANNELS') and not db.find_join_req(query.from_user.id):
        try:
            req_id = int(stg.get('REQUEST_FORCE_SUB_CHANNELS'))
            chat = await bot.get_chat(req_id)
            await bot.get_chat_member(req_id, query.from_user.id)
        except UserNotParticipant:
            try:
                url = await bot.create_chat_invite_link(req_id, creates_join_request=True)
                btn.append(
                    [InlineKeyboardButton(f'📩 Request : {chat.title}', url=url.invite_link)]
                )
            except Exception as e:
                print(f"Error creating invite link: {e}")
        except Exception as e:
            print(f"Request force sub error: {e}")
    
    return btn


def upload_image(file_path):
    with open(file_path, 'rb') as f:
        files = {'files[]': f}
        response = requests.post("https://uguu.se/upload", files=files)

    if response.status_code == 200:
        try:
            data = response.json()
            return data['files'][0]['url'].replace('\\/', '/')
        except Exception as e:
            return None
    else:
        return None


async def get_poster_tmdb(query, file=None):
    """Get movie/TV info from TMDB API"""
    if not TMDB_API_KEY:
        return None
    
    query = (query.strip()).lower()
    title = query
    year = re.findall(r'[1-2]\d{3}$', query, re.IGNORECASE)
    if year:
        year = year[0]
        title = (query.replace(year, "")).strip()
    elif file is not None:
        year_match = re.findall(r'[1-2]\d{3}', file, re.IGNORECASE)
        if year_match:
            year = year_match[0]
        else:
            year = None
    else:
        year = None
    
    base_url = "https://api.themoviedb.org/3"
    
    async with aiohttp.ClientSession() as session:
        # Search for movie/TV show
        search_url = f"{base_url}/search/multi"
        params = {
            'api_key': TMDB_API_KEY,
            'query': title,
            'include_adult': 'false'
        }
        if year:
            params['year'] = year
        
        try:
            async with session.get(search_url, params=params, timeout=10) as resp:
                if resp.status != 200:
                    print(f"TMDB search failed with status: {resp.status}")
                    return None
                data = await resp.json()
        except Exception as e:
            print(f"TMDB search error: {e}")
            return None
        
        results = data.get('results', [])
        if not results:
            print(f"TMDB search returned no results for: {title}")
            return None
        
        # Filter to movies and TV shows only
        filtered = [r for r in results if r.get('media_type') in ['movie', 'tv']]
        if not filtered:
            filtered = results
        
        # Get the best match
        item = filtered[0]
        media_type = item.get('media_type', 'movie')
        item_id = item.get('id')
        
        # Get detailed info
        detail_url = f"{base_url}/{media_type}/{item_id}"
        params = {
            'api_key': TMDB_API_KEY,
            'append_to_response': 'credits'
        }
        
        try:
            async with session.get(detail_url, params=params, timeout=10) as resp:
                if resp.status != 200:
                    print(f"TMDB detail failed with status: {resp.status}")
                    return None
                details = await resp.json()
        except Exception as e:
            print(f"TMDB detail error: {e}")
            return None
        
        # Extract poster URL
        poster_path = details.get('poster_path')
        poster = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None
        
        # Extract cast
        credits = details.get('credits', {})
        cast = credits.get('cast', [])[:5]
        cast_names = [c.get('name') for c in cast if c.get('name')]
        
        # Extract crew
        crew = credits.get('crew', [])
        directors = [c.get('name') for c in crew if c.get('job') == 'Director']
        writers = [c.get('name') for c in crew if c.get('department') == 'Writing'][:3]
        producers = [c.get('name') for c in crew if c.get('job') == 'Producer'][:3]
        composers = [c.get('name') for c in crew if c.get('job') == 'Original Music Composer'][:2]
        cinematographers = [c.get('name') for c in crew if c.get('job') == 'Director of Photography'][:2]
        
        # Get title based on media type
        title = details.get('title') or details.get('name') or 'N/A'
        original_title = details.get('original_title') or details.get('original_name') or title
        
        # Get release date
        release_date = details.get('release_date') or details.get('first_air_date') or 'N/A'
        year_val = release_date[:4] if release_date and release_date != 'N/A' else 'N/A'
        
        # Get runtime
        runtime = details.get('runtime')
        if not runtime and media_type == 'tv':
            episode_runtime = details.get('episode_run_time', [])
            runtime = episode_runtime[0] if episode_runtime else None
        
        # Get genres
        genres = [g.get('name') for g in details.get('genres', [])]
        
        # Get languages
        languages = [l.get('english_name') or l.get('name') for l in details.get('spoken_languages', [])]
        
        # Get countries
        countries = [c.get('name') for c in details.get('production_countries', [])]
        
        # Get plot
        plot = details.get('overview', 'N/A')
        if plot and len(plot) > 800:
            plot = plot[:800] + "..."
        
        # Get rating
        rating = details.get('vote_average')
        rating_str = f"{rating:.1f}" if rating else 'N/A'
        
        # Get number of seasons for TV shows
        seasons = details.get('number_of_seasons') if media_type == 'tv' else None
        
        tmdb_id = details.get('id')
        url = f"https://www.themoviedb.org/{media_type}/{tmdb_id}"
        
        print(f"TMDB found: {title}, poster: {poster[:50] if poster else 'None'}...")
        
        return {
            'title': title,
            'votes': details.get('vote_count', 'N/A'),
            'aka': original_title if original_title != title else 'N/A',
            'seasons': seasons,
            'box_office': details.get('revenue', 'N/A') if details.get('revenue') else 'N/A',
            'localized_title': title,
            'kind': 'tv series' if media_type == 'tv' else 'movie',
            'imdb_id': f"tmdb{tmdb_id}",
            'cast': list_to_str(cast_names),
            'runtime': str(runtime) if runtime else 'N/A',
            'countries': list_to_str(countries),
            'certificates': 'N/A',
            'languages': list_to_str(languages),
            'director': list_to_str(directors),
            'writer': list_to_str(writers),
            'producer': list_to_str(producers),
            'composer': list_to_str(composers),
            'cinematographer': list_to_str(cinematographers),
            'music_team': 'N/A',
            'distributors': 'N/A',
            'release_date': release_date,
            'year': year_val,
            'genres': list_to_str(genres),
            'poster': poster,
            'plot': plot,
            'rating': rating_str,
            'url': url
        }


async def get_poster_imdb(query, bulk=False, id=False, file=None):
    """Get movie/TV info from IMDB (original implementation)"""
    import asyncio
    from concurrent.futures import ThreadPoolExecutor
    
    loop = asyncio.get_event_loop()
    executor = ThreadPoolExecutor(max_workers=1)
    
    if not id:
        query = (query.strip()).lower()
        title = query
        year = re.findall(r'[1-2]\d{3}$', query, re.IGNORECASE)
        if year:
            year = list_to_str(year[:1])
            title = (query.replace(year, "")).strip()
        elif file is not None:
            year = re.findall(r'[1-2]\d{3}', file, re.IGNORECASE)
            if year:
                year = list_to_str(year[:1]) 
        else:
            year = None
        
        # Run blocking IMDB search in thread executor
        try:
            movieid = await loop.run_in_executor(executor, lambda: imdb.search_movie(title.lower(), results=10))
        except Exception as e:
            print(f"IMDB search_movie failed: {e}")
            return None
            
        if not movieid:
            print(f"IMDB search returned no results for: {title}")
            return None
        if year:
            filtered=list(filter(lambda k: str(k.get('year')) == str(year), movieid))
            if not filtered:
                filtered = movieid
        else:
            filtered = movieid
        movieid=list(filter(lambda k: k.get('kind') in ['movie', 'tv series'], filtered))
        if not movieid:
            movieid = filtered
        if bulk:
            return movieid
        movieid = movieid[0].movieID
    else:
        movieid = query
    
    # Run blocking IMDB get_movie in thread executor
    try:
        movie = await loop.run_in_executor(executor, lambda: imdb.get_movie(movieid))
    except Exception as e:
        print(f"IMDB get_movie failed: {e}")
        return None
        
    if movie.get("original air date"):
        date = movie["original air date"]
    elif movie.get("year"):
        date = movie.get("year")
    else:
        date = "N/A"
    plot = ""
    if not LONG_IMDB_DESCRIPTION:
        plot = movie.get('plot')
        if plot and len(plot) > 0:
            plot = plot[0]
    else:
        plot = movie.get('plot outline')
    if plot and len(plot) > 800:
        plot = plot[0:800] + "..."
    
    poster = movie.get('full-size cover url')
    print(f"IMDB found: {movie.get('title')}, poster: {poster[:50] if poster else 'None'}...")
    
    return {
        'title': movie.get('title'),
        'votes': movie.get('votes'),
        "aka": list_to_str(movie.get("akas")),
        "seasons": movie.get("number of seasons"),
        "box_office": movie.get('box office'),
        'localized_title': movie.get('localized title'),
        'kind': movie.get("kind"),
        "imdb_id": f"tt{movie.get('imdbID')}",
        "cast": list_to_str(movie.get("cast")),
        "runtime": list_to_str(movie.get("runtimes")),
        "countries": list_to_str(movie.get("countries")),
        "certificates": list_to_str(movie.get("certificates")),
        "languages": list_to_str(movie.get("languages")),
        "director": list_to_str(movie.get("director")),
        "writer":list_to_str(movie.get("writer")),
        "producer":list_to_str(movie.get("producer")),
        "composer":list_to_str(movie.get("composer")) ,
        "cinematographer":list_to_str(movie.get("cinematographer")),
        "music_team": list_to_str(movie.get("music department")),
        "distributors": list_to_str(movie.get("distributors")),
        'release_date': date,
        'year': movie.get('year'),
        'genres': list_to_str(movie.get("genres")),
        'poster': poster,
        'plot': plot,
        'rating': str(movie.get("rating")),
        'url':f'https://www.imdb.com/title/tt{movieid}'
    }


async def get_poster(query, bulk=False, id=False, file=None):
    """Get movie/TV poster - uses TMDB if API key is set, otherwise falls back to IMDB"""
    # Try TMDB first if API key is configured
    if TMDB_API_KEY and not bulk and not id:
        result = await get_poster_tmdb(query, file=file)
        if result:
            return result
        print("TMDB failed, falling back to IMDB...")
    
    # Fall back to IMDB
    return await get_poster_imdb(query, bulk=bulk, id=id, file=file)

async def is_check_admin(bot, chat_id, user_id):
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]
    except:
        return False

async def get_verify_status(user_id):
    verify = temp.VERIFICATIONS.get(user_id)
    if not verify:
        verify = await db.get_verify_status(user_id)
        temp.VERIFICATIONS[user_id] = verify
    return verify

async def update_verify_status(user_id, verify_token="", is_verified=False, link="", expire_time=0):
    current = await get_verify_status(user_id)
    current['verify_token'] = verify_token
    current['is_verified'] = is_verified
    current['link'] = link
    current['expire_time'] = expire_time
    temp.VERIFICATIONS[user_id] = current
    await db.update_verify_status(user_id, current)

    
async def is_premium(user_id, bot):
    return False
    if user_id in ADMINS:
        return True
    mp = db.get_plan(user_id)
    if mp['premium']:
        if mp['expire'] < datetime.now():
            await bot.send_message(user_id, f"Your premium {mp['plan']} plan is expired in {mp['expire'].strftime('%Y.%m.%d %H:%M:%S')}, use /plan to activate new plan again")
            mp['expire'] = ''
            mp['plan'] = ''
            mp['premium'] = False
            db.update_plan(user_id, mp)
            return False
        return True
    else:
        return False


async def check_premium(bot):
    while True:
        pr = [i for i in db.get_premium_users() if i['status']['premium']]
        for p in pr:
            mp = p['status']
            if mp['expire'] < datetime.now():
                try:
                    await bot.send_message(
                        p['id'],
                        f"Your premium {mp['plan']} plan is expired in {mp['expire'].strftime('%Y.%m.%d %H:%M:%S')}, use /plan to activate new plan again"
                    )
                except Exception:
                    pass
                mp['expire'] = ''
                mp['plan'] = ''
                mp['premium'] = False
                db.update_plan(p['id'], mp)
        await asyncio.sleep(1200)


async def broadcast_messages(user_id, message, pin):
    try:
        m = await message.copy(chat_id=user_id)
        if pin:
            await m.pin(both_sides=True)
        return "Success"
    except FloodWait as e:
        await asyncio.sleep(e.value)
        return await broadcast_messages(user_id, message, pin)
    except Exception as e:
        await db.delete_user(int(user_id))
        return "Error"

async def groups_broadcast_messages(chat_id, message, pin):
    try:
        k = await message.copy(chat_id=chat_id)
        if pin:
            try:
                await k.pin()
            except:
                pass
        return "Success"
    except FloodWait as e:
        await asyncio.sleep(e.value)
        return await groups_broadcast_messages(chat_id, message, pin)
    except Exception as e:
        await db.delete_chat(chat_id)
        return "Error"

async def get_settings(group_id):
    settings = temp.SETTINGS.get(group_id)
    if not settings:
        settings = await db.get_settings(group_id)
        temp.SETTINGS.update({group_id: settings})
    return settings
    
async def save_group_settings(group_id, key, value):
    current = await get_settings(group_id)
    current.update({key: value})
    temp.SETTINGS.update({group_id: current})
    await db.update_settings(group_id, current)

def get_size(size):
    units = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB"]
    size = float(size)
    i = 0
    while size >= 1024.0 and i < len(units):
        i += 1
        size /= 1024.0
    return "%.2f %s" % (size, units[i])

def list_to_str(k):
    if not k:
        return "N/A"
    elif len(k) == 1:
        return str(k[0])
    else:
        return ', '.join(f'{elem}' for elem in k)

def clean_ascii(text):
    """Remove non-ASCII characters (Sinhala, etc.) and keep only English characters"""
    if not text:
        return text
    # Keep only ASCII printable characters (English letters, numbers, punctuation)
    cleaned = re.sub(r'[^\x00-\x7F]+', '', str(text))
    # Clean up multiple spaces and trim
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned if cleaned else text

def remove_urls(text):
    """Remove URLs from text while keeping all other characters including Sinhala"""
    if not text:
        return text
    
    cleaned = str(text)
    
    # Remove full URLs (http, https, www, t.me links)
    cleaned = re.sub(r'https?://\S+', '', cleaned)
    cleaned = re.sub(r'www\.\S+', '', cleaned)
    cleaned = re.sub(r't\.me/\S+', '', cleaned)
    
    # Remove partial URLs from known subtitle sites (zoom.lk, subz.lk, baiscope.lk)
    cleaned = re.sub(r'zoom\.?lk[/\S]*', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'subz\.?lk[/\S]*', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'baiscope\.?lk[/\S]*', '', cleaned, flags=re.IGNORECASE)
    
    # Remove URL-encoded strings (like %e0%b7%83%e0%b7%92...)
    cleaned = re.sub(r'%[0-9a-fA-F]{2}[%0-9a-fA-F/-]*', '', cleaned)
    
    # Remove "Source:", "Link:", "Zoom lk", etc. labels
    cleaned = re.sub(r'Source:\s*', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'Link:\s*', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'Zoom\s*lk\s*', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'Subz\s*lk\s*', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'Baiscope\s*lk\s*', '', cleaned, flags=re.IGNORECASE)
    
    # Clean up multiple newlines, spaces, and trailing slashes
    cleaned = re.sub(r'\n\s*\n', '\n', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    cleaned = re.sub(r'/+$', '', cleaned).strip()
    
    return cleaned if cleaned else text
    


def get_readable_time(seconds):
    periods = [('d', 86400), ('h', 3600), ('m', 60), ('s', 1)]
    result = ''
    for period_name, period_seconds in periods:
        if seconds >= period_seconds:
            period_value, seconds = divmod(seconds, period_seconds)
            result += f'{int(period_value)}{period_name}'
    return result

def get_wish():
    time = datetime.now(pytz.timezone(TIME_ZONE))
    now = time.strftime("%H")
    if now < "12":
        status = "ɢᴏᴏᴅ ᴍᴏʀɴɪɴɢ 🌞"
    elif now < "18":
        status = "ɢᴏᴏᴅ ᴀꜰᴛᴇʀɴᴏᴏɴ 🌗"
    else:
        status = "ɢᴏᴏᴅ ᴇᴠᴇɴɪɴɢ 🌘"
    return status
    
async def get_seconds(time_string):
    def extract_value_and_unit(ts):
        value = ""
        unit = ""
        index = 0
        while index < len(ts) and ts[index].isdigit():
            value += ts[index]
            index += 1
        unit = ts[index:]
        if value:
            value = int(value)
        return value, unit
    value, unit = extract_value_and_unit(time_string)
    if unit == 's':
        return value
    elif unit == 'min':
        return value * 60
    elif unit == 'hour':
        return value * 3600
    elif unit == 'day':
        return value * 86400
    elif unit == 'month':
        return value * 86400 * 30
    elif unit == 'year':
        return value * 86400 * 365
    else:
        return 0
