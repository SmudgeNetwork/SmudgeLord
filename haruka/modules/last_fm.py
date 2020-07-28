# Last.fm module by @TheRealPhoenix - https://github.com/rsktg

import requests

from telegram import Bot, Update, Message, Chat, ParseMode, User
from telegram.ext import run_async, CommandHandler

from haruka import dispatcher, LASTFM_API_KEY
from haruka.modules.disable import DisableAbleCommandHandler

import haruka.modules.sql.last_fm_sql as sql
from haruka.modules.translations.strings import tld


@run_async
def set_user(bot: Bot, update: Update, args):
    msg = update.effective_message
    chat = update.effective_chat
    if args:
        user = update.effective_user.id
        username = " ".join(args)
        sql.set_user(user, username)
        msg.reply_text(tld(chat.id, "setuser_lastfm").format(username))
    else:
        msg.reply_text(
            tld(chat.id, "setuser_lastfm_error"))


@run_async
def clear_user(bot: Bot, update: Update):
    user = update.effective_user.id
    chat = update.effective_chat
    sql.set_user(user, "")
    update.effective_message.reply_text(
        tld(chat.id, "learuser_lastfm"))


@run_async
def last_fm(bot: Bot, update: Update):
    msg = update.effective_message
    user = update.effective_user.first_name
    user_id = update.effective_user.id
    username = sql.get_user(user_id)
    chat = update.effective_chat
    if not username:
        msg.reply_text(tld(chat.id, "lastfm_usernotset"))
        return

    base_url = "http://ws.audioscrobbler.com/2.0"
    res = requests.get(
        f"{base_url}?method=user.getrecenttracks&limit=3&extended=1&user={username}&api_key={LASTFM_API_KEY}&format=json")
    if not res.status_code == 200:
        msg.reply_text(tld(chat.id, "lastfm_userwrong"))
        return

    try:
        first_track = res.json().get("recenttracks").get("track")[0]
    except IndexError:
        msg.reply_text(tld(chat.id, "lastfm_nonetracks"))
        return
    if first_track.get("@attr"):
        # Ensures the track is now playing
        image = first_track.get("image")[3].get("#text")  # Grab URL of 300x300 image
        artist = first_track.get("artist").get("name")
        song = first_track.get("name")
        loved = int(first_track.get("loved"))
        rep = tld(chat.id, "lastfm_listening").format(user)
        if not loved:
            rep += tld(chat.id, "lastfm_scrb").format(artist, song)
        else:
            rep += tld(chat.id, "lastfm_scrb_loved").format(artist, song)
        if image:
            rep += f"<a href='{image}'>\u200c</a>"
    else:
        tracks = res.json().get("recenttracks").get("track")
        track_dict = {tracks[i].get("artist").get("name"): tracks[i].get("name") for i in range(3)}
        rep = f"{user} was listening to:\n"
        for artist, song in track_dict.items():
            rep += tld(chat.id, "lastfm_scrr").format(artist, song)
        last_user = requests.get(
            f"{base_url}?method=user.getinfo&user={username}&api_key={LASTFM_API_KEY}&format=json").json().get("user")
        scrobbles = last_user.get("playcount")
        rep += tld(chat.id, "lastfm_scr").format(scrobbles)

    msg.reply_text(rep, parse_mode=ParseMode.HTML)

@run_async
def top_tracks(bot: Bot, update: Update):
    msg = update.effective_message
    user = update.effective_user.first_name
    user_id = update.effective_user.id
    username = sql.get_user(user_id)
    if not username:
        msg.reply_text("🇺🇸You haven't set your username yet!\n🇧🇷Você não colocou seu username")
        return
    
    base_url = "http://ws.audioscrobbler.com/2.0"
    res = requests.get(f"{base_url}?method=user.gettoptracks&limit=3&extended=1&user={username}&api_key={LASTFM_API_KEY}&format=json")
    if not res.status_code == 200:
        msg.reply_text("Hmm... something went wrong.\nPlease ensure that you've set the correct username!")
        return
        
    else:
        tracks = res.json().get("toptracks").get("track")
        track_dict = {tracks[i].get("artist").get("name"): tracks[i].get("name") for i in range(1)}
        track_dict2 = {tracks[i].get("artist").get("name"): tracks[i].get("name") for i in range(2)}
        track_dict3 = {tracks[i].get("artist").get("name"): tracks[i].get("name") for i in range(3)}

        rep = f"{user} Top tracks :\n\n"
        for artist, song in track_dict.items():
            rep += f"🥇  <code>{artist} - {song}</code>\n"
        for artist, song in track_dict2.items():
            rep += f"🥈  <code>{artist} - {song}</code>\n"
        for artist, song in track_dict3.items():
            rep += f"🥉  <code>{artist} - {song}</code>\n"
        last_user = requests.get(f"{base_url}?method=user.getinfo&user={username}&api_key={LASTFM_API_KEY}&format=json").json().get("user")
        scrobbles = last_user.get("playcount")
        rep += f"\n(<code>{scrobbles}</code> scrobbles so far)"
        
    msg.reply_text(rep, parse_mode=ParseMode.HTML)
    
    
__help__ = """
Share what you're what listening to with the help of this module!

*Available commands:*
 - /setuser <username>: sets your last.fm username.
 - /clearuser: removes your last.fm username from the bot's database.
 - /lastfm: returns what you're scrobbling on last.fm.
"""

__mod_name__ = "Last.FM"
    

SET_USER_HANDLER = CommandHandler("setuser", set_user, pass_args=True)
CLEAR_USER_HANDLER = CommandHandler("clearuser", clear_user)
LASTFM_HANDLER = DisableAbleCommandHandler(["lastfm", "lt", "last", "l"], last_fm)
TOPTRACKS_HANDLER = CommandHandler(["lasttop", "top", "lastop", "toplast", "overall","t"], top_tracks)


dispatcher.add_handler(SET_USER_HANDLER)
dispatcher.add_handler(CLEAR_USER_HANDLER)
dispatcher.add_handler(LASTFM_HANDLER)
dispatcher.add_handler(TOPTRACKS_HANDLER)
