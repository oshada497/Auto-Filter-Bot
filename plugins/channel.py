from hydrogram import Client, filters
from info import INDEX_CHANNELS, INDEX_EXTENSIONS, BIN_CHANNEL
from database.ia_filterdb import save_file

media_filter = filters.document | filters.video

# Combine INDEX_CHANNELS and BIN_CHANNEL for auto-indexing
auto_index_channels = list(INDEX_CHANNELS) if INDEX_CHANNELS else []
if BIN_CHANNEL and BIN_CHANNEL not in auto_index_channels:
    auto_index_channels.append(BIN_CHANNEL)

@Client.on_message(filters.chat(auto_index_channels) & media_filter)
async def media(bot, message):
    """Media Handler - Auto index files from INDEX_CHANNELS and BIN_CHANNEL"""
    media = getattr(message, message.media.value, None)
    if media and media.file_name:
        if (str(media.file_name).lower()).endswith(tuple(INDEX_EXTENSIONS)):
            media.caption = message.caption
            result = await save_file(media)
            if result == 'suc':
                print(f"Auto-indexed: {media.file_name}")
            elif result == 'dup':
                print(f"Already indexed: {media.file_name}")
