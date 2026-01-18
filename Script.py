class script(object):

    START_TXT = """<b>ʜᴇʏ {}, <i>{}</i>

ඕනෑම ෆිල්ම් එකක සබ්ටයිටල් (Subtitles) දැන් ලේසියෙන්ම හොයාගන්න. චිත්‍රපටයේ හෝ කතාමාලාවේ නම එවන්න විතරයි තියෙන්නේ! 🎬
    
ɪ ᴀᴍ ᴘᴏᴡᴇʀғᴜʟ ꜱᴜʙᴛɪᴛʟᴇ ꜰɪɴᴅᴇʀ ʙᴏᴛ. ʏᴏᴜ ᴄᴀɴ ꜱᴇᴀʀᴄʜ ᴀɴʏ ꜱᴜʙᴛɪᴛʟᴇ ꜰɪʟᴇꜱ ɪɴ ᴍʏ ᴅᴀᴛᴀʙᴀꜱᴇ. ᴊᴜꜱᴛ ꜱᴇɴᴅ ᴛʜᴇ ᴍᴏᴠɪᴇ ɴᴀᴍᴇ ɪ ᴡɪʟʟ ᴘʀᴏᴠɪᴅᴇ ᴛʜᴇ ꜱᴜʙᴛɪᴛʟᴇꜱ! ♻️</b>"""

    MY_ABOUT_TXT = """★ Server: <a href=https://www.heroku.com>Heroku</a>
★ Database: <a href=https://www.mongodb.com>MongoDB</a>
★ Language: <a href=https://www.python.org>Python</a>
★ Library: <a href=https://t.me/HydrogramNews>Hydrogram</a>"""

    MY_OWNER_TXT = """★ Name: Sinhala Subs Project
★ Username: @sinhalasubsproject
★ Country: Sri Lanka 🇱🇰"""

    STATUS_TXT = """👤 Total Users: <code>{}</code>
👥 Total Chats: <code>{}</code>
🗳 Data database used: <code>{}</code>

🗂 1st database Files: <code>{}</code>
🗳 1st files database used: <code>{}</code>

🗂 2nd database Files: <code>{}</code>
🗳 2nd files database used: <code>{}</code>

🚀 Bot Uptime: <code>{}</code>"""

    NEW_GROUP_TXT = """#NewGroup
Title - {}
ID - <code>{}</code>
Username - {}
Total - <code>{}</code>"""

    NEW_USER_TXT = """#NewUser
★ Name: {}
★ ID: <code>{}</code>"""

    NOT_FILE_TXT = """👋 Hello {},

I can't find the <b>{}</b> in my database! 🥲

👉 Google Search and check your spelling is correct.
👉 Please read the Instructions to get better results.
👉 Or not been released yet."""
    
    IMDB_TEMPLATE = """✅ I Found: <code>{query}</code>

🏷 Title: <a href={url}>{title}</a>
🎭 Genres: {genres}
📆 Year: <a href={url}/releaseinfo>{year}</a>
🌟 Rating: <a href={url}/ratings>{rating} / 10</a>
☀️ Languages: {languages}
📀 RunTime: {runtime} Minutes

🗣 Requested by: {message.from_user.mention}
©️ Powered by: <b>{message.chat.title}</b>"""

    FILE_CAPTION = """<b>{file_name}</b>

<b>{file_caption}</b>

Powered by @slbotdevs"""

    WELCOME_TEXT = """👋 Hello {mention}, Welcome to {title} group! 💞"""

    HELP_TXT = """👋 Hello {},
    
ɪ ᴄᴀɴ ꜰɪɴᴅ ꜱᴜʙᴛɪᴛʟᴇꜱ ꜰᴏʀ ʏᴏᴜ 
ᴊᴜꜱᴛ ᴛʏᴘᴇ ᴛʜᴇ ɴᴀᴍᴇ ᴏꜰ ᴛʜᴇ ᴍᴏᴠɪᴇ ᴏʀ ꜱᴇʀɪᴇꜱ ɪɴ ᴍʏ ᴘᴍ ᴏʀ ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ.
ɪ ʜᴀᴠᴇ ᴀ ʟᴀʀɢᴇ ᴅᴀᴛᴀʙᴀꜱᴇ ᴏꜰ ꜱᴜʙᴛɪᴛʟᴇ ꜰɪʟᴇꜱ."""

    ADMIN_COMMAND_TXT = """<b>Here is bot admin commands 👇


/index_channels - to check how many index channel id added
/stats - to get bot status
/delete - to delete files using query
/delete_all - to delete all indexed file
/broadcast - to send message to all bot users
/grp_broadcast - to send message to all groups
/pin_broadcast - to send message as pin to all bot users.
/pin_grp_broadcast - to send message as pin to all groups.
/restart - to restart bot
/leave - to leave your bot from particular group
/users - to get all users details
/chats - to get all groups
/invite_link - to generate invite link
/index - to index bot accessible channels
/add_prm - to add new premium user
/rm_prm - to add remove premium user
/delreq - to delete join request in db (if change REQUEST_FORCE_SUB_CHANNELS using /set_req_fsub then must need use this command)
/set_req_fsub - to set request force subscribe channel
/set_fsub - to set force subscribe channels</b>"""
    
    PLAN_TXT = """Activate any premium plan to get exclusive features.

You can activate any premium plan and then you can get exclusive features.

- INR {} for pre day -

Basic premium features:
Ad free experience
Fastest response
No need joined channels
No need verify
Ad-free direct files
Premium community access
And more...

Support: {}"""

    USER_COMMAND_TXT = """<b>Here is bot user commands 👇

/start - to check bot alive or not
/settings - to change group settings as your wish
/connect - to connect group settings to PM
/id - to check group or channel id</b>"""
    
    SOURCE_TXT = """<b>ʙᴏᴛ ɢɪᴛʜᴜʙ ʀᴇᴘᴏsɪᴛᴏʀʏ -

- ᴛʜɪꜱ ʙᴏᴛ ɪꜱ ᴀɴ ᴏᴘᴇɴ ꜱᴏᴜʀᴄᴇ ᴘʀᴏᴊᴇᴄᴛ.

- ꜱᴏᴜʀᴄᴇ - <a href=https://github.com/HA-Bots/Auto-Filter-Bot>ʜᴇʀᴇ</a>

- ᴅᴇᴠʟᴏᴘᴇʀ - @sinhalasubsproject"""

