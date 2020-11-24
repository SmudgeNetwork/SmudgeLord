import html
import wikipedia
import re
from datetime import datetime
from typing import Optional, List
from covid import Covid

import requests
import urllib.request
from telegram import Message, Chat, Update, Bot, MessageEntity
from telegram import ParseMode, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CommandHandler, run_async, Filters
from telegram.utils.helpers import escape_markdown, mention_html
from telegram.error import BadRequest

from smudge import dispatcher, OWNER_ID, SUDO_USERS, SUPPORT_USERS, WHITELIST_USERS, sw, SCREENSHOT_API_KEY
from smudge.__main__ import GDPR
from smudge.__main__ import STATS, USER_INFO
from smudge.modules.disable import DisableAbleCommandHandler
from smudge.helper_funcs.extraction import extract_user

from smudge.modules.translations.strings import tld

from requests import get

cvid = Covid(source="worldometers")


@run_async
def screenshot(bot: Bot, update: Update, args):
    chat_id = update.effective_chat.id
    chat = update.effective_chat
    txt = " ".join(args)
    filename = "screencapture.png"

    image_url = f"https://api.screenshotlayer.com/api/capture?access_key={SCREENSHOT_API_KEY}&url={txt}&fullpage=1&viewport=2560x1440&format=PNG&force=1"
    if not SCREENSHOT_API_KEY:
        msg.reply_text(tld(chat.id, "lastfm_usernotset"))
        return
    urllib.request.urlretrieve(image_url, filename)
    bot.send_document(chat_id=chat.id,  document=open(
        'screencapture.png', 'rb'), caption=txt)


@run_async
def get_bot_ip(bot: Bot, update: Update):
    res = requests.get("http://ipinfo.io/ip")
    update.message.reply_text(res.text)


@run_async
def get_id(bot: Bot, update: Update, args: List[str]):
    user_id = extract_user(update.effective_message, args)
    chat = update.effective_chat  # type: Optional[Chat]
    if user_id:
        if update.effective_message.reply_to_message and update.effective_message.reply_to_message.forward_from:
            user1 = update.effective_message.reply_to_message.from_user
            user2 = update.effective_message.reply_to_message.forward_from
            update.effective_message.reply_markdown(tld(chat.id, "misc_get_id_1").format(escape_markdown(user2.first_name), user2.id,
                                                                                         escape_markdown(user1.first_name), user1.id))
        else:
            user = bot.get_chat(user_id)
            update.effective_message.reply_markdown(tld(chat.id, "misc_get_id_2").format(escape_markdown(user.first_name),
                                                                                         user.id))
    else:
        chat = update.effective_chat  # type: Optional[Chat]
        if chat.type == "private":
            update.effective_message.reply_markdown(
                tld(chat.id, "misc_id_1").format(chat.id))

        else:
            update.effective_message.reply_markdown(
                tld(chat.id, "misc_id_2").format(chat.id))


@run_async
def info(bot: Bot, update: Update, args: List[str]):
    msg = update.effective_message  # type: Optional[Message]
    user_id = extract_user(update.effective_message, args)
    chat = update.effective_chat  # type: Optional[Chat]

    if user_id:
        user = bot.get_chat(user_id)

    elif not msg.reply_to_message and not args:
        user = msg.from_user

    elif not msg.reply_to_message and (
            not args or
        (len(args) >= 1 and not args[0].startswith("@")
         and not args[0].isdigit()
         and not msg.parse_entities([MessageEntity.TEXT_MENTION]))):
        msg.reply_text(tld(chat.id, "misc_info_extract_error"))
        return

    else:
        return

    text = tld(chat.id, "misc_info_1")
    text += tld(chat.id, "misc_info_id").format(user.id)
    text += tld(chat.id,
                "misc_info_first").format(html.escape(user.first_name))

    if user.last_name:
        text += tld(chat.id,
                    "misc_info_name").format(html.escape(user.last_name))

    if user.username:
        text += tld(chat.id,
                    "misc_info_username").format(html.escape(user.username))

    text += tld(chat.id,
                "misc_info_user_link").format(mention_html(user.id, "link"))

    try:
        spamwatch = sw.get_ban(int(user.id))
        if spamwatch:
            text += tld(chat.id, "misc_info_swban1")
            text += tld(chat.id, "misc_info_swban2").format(spamwatch.reason)
            text += tld(chat.id, "misc_info_swban3")
        else:
            pass
    except:
        pass

    if user.id == OWNER_ID:
        text += tld(chat.id, "misc_info_is_owner")
    else:
        if user.id == int(254318997):
            text += tld(chat.id, "misc_info_is_original_owner")

        if user.id in SUDO_USERS:
            text += tld(chat.id, "misc_info_is_sudo")
        else:
            if user.id in SUPPORT_USERS:
                text += tld(chat.id, "misc_info_is_support")

            if user.id in WHITELIST_USERS:
                text += tld(chat.id, "misc_info_is_whitelisted")

    for mod in USER_INFO:
        mod_info = mod.__user_info__(user.id, chat.id).strip()
        if mod_info:
            text += "\n\n" + mod_info

    update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)


@run_async
def echo(bot: Bot, update: Update):
    message = update.effective_message
    message.delete()
    args = update.effective_message.text.split(None, 1)
    if message.reply_to_message:
        message.reply_to_message.reply_text(args[1])
    else:
        message.reply_text(args[1], quote=False)


@run_async
def reply_keyboard_remove(bot: Bot, update: Update):
    reply_keyboard = []
    reply_keyboard.append([ReplyKeyboardRemove(remove_keyboard=True)])
    reply_markup = ReplyKeyboardRemove(remove_keyboard=True)
    old_message = bot.send_message(
        chat_id=update.message.chat_id,
        text='trying',  # This text will not get translated
        reply_markup=reply_markup,
        reply_to_message_id=update.message.message_id)
    bot.delete_message(chat_id=update.message.chat_id,
                       message_id=old_message.message_id)


@run_async
def gdpr(bot: Bot, update: Update):
    update.effective_message.reply_text(
        tld(update.effective_chat.id, "misc_gdpr"))
    for mod in GDPR:
        mod.__gdpr__(update.effective_user.id)

    update.effective_message.reply_text(tld(update.effective_chat.id,
                                            "send_gdpr"),
                                        parse_mode=ParseMode.MARKDOWN)


@run_async
def markdown_help(bot: Bot, update: Update):
    chat = update.effective_chat  # type: Optional[Chat]
    update.effective_message.reply_text(tld(chat.id, "misc_md_list"),
                                        parse_mode=ParseMode.HTML)
    update.effective_message.reply_text(
        tld(chat.id, "misc_md_try"))
    update.effective_message.reply_text(
        tld(
            chat.id, "misc_md_help"))


@run_async
def stats(bot: Bot, update: Update):
    update.effective_message.reply_text(
        # This text doesn't get translated as it is internal message.
        "*Current Stats:*\n" + "\n".join([mod.__stats__() for mod in STATS]),
        parse_mode=ParseMode.MARKDOWN)


@run_async
def github(bot: Bot, update: Update):
    message = update.effective_message
    text = message.text[len('/git '):]
    usr = get(f'https://api.github.com/users/{text}').json()
    if usr.get('login'):
        text = f"*Username:* [{usr['login']}](https://github.com/{usr['login']})"

        whitelist = [
            'name', 'id', 'type', 'location', 'blog', 'bio', 'followers',
            'following', 'hireable', 'public_gists', 'public_repos', 'email',
            'company', 'updated_at', 'created_at'
        ]

        difnames = {
            'id': 'Account ID',
            'type': 'Account type',
            'created_at': 'Account created at',
            'updated_at': 'Last updated',
            'public_repos': 'Public Repos',
            'public_gists': 'Public Gists'
        }

        goaway = [None, 0, 'null', '']

        for x, y in usr.items():
            if x in whitelist:
                if x in difnames:
                    x = difnames[x]
                else:
                    x = x.title()

                if x == 'Account created at' or x == 'Last updated':
                    y = datetime.strptime(y, "%Y-%m-%dT%H:%M:%SZ")

                if y not in goaway:
                    if x == 'Blog':
                        x = "Website"
                        y = f"[Here!]({y})"
                        text += ("\n*{}:* {}".format(x, y))
                    else:
                        text += ("\n*{}:* `{}`".format(x, y))
        reply_text = text
    else:
        reply_text = "User not found. Make sure you entered valid username!"
    message.reply_text(reply_text,
                       parse_mode=ParseMode.MARKDOWN,
                       disable_web_page_preview=True)


@run_async
def repo(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message
    text = message.text[len('/repo '):]
    usr = get(f'https://api.github.com/users/{text}/repos?per_page=40').json()
    reply_text = "*Repo*\n"
    for i in range(len(usr)):
        reply_text += f"[{usr[i]['name']}]({usr[i]['html_url']})\n"
    message.reply_text(reply_text,
                       parse_mode=ParseMode.MARKDOWN,
                       disable_web_page_preview=True)


@run_async
def ud(bot: Bot, update: Update):
    message = update.effective_message
    text = message.text[len('/ud '):]
    results = get(
        f'http://api.urbandictionary.com/v0/define?term={text}').json()
    reply_text = f'Word: {text}\nDefinition: {results["list"][0]["definition"]}'
    message.reply_text(reply_text)


@run_async
def wiki(bot: Bot, update: Update):
    msg = update.effective_message

    msg.reply_text("🇧🇷Para pesquisar no wikipedia em português use /wikipt e em Ingles use /wikien\n \n🇺🇸To search wikipedia in Portuguese use /wikipt and in English use /wikien")


@run_async
def wikien(bot: Bot, update: Update):
    kueri = re.split(pattern="wikien", string=update.effective_message.text)
    wikipedia.set_lang("en")
    if len(str(kueri[1])) == 0:
        update.effective_message.reply_text("Enter keywords!")
    else:
        try:
            pertama = update.effective_message.reply_text("🔄 Loading...")
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton(text="🔧 More Info...",
                                     url=wikipedia.page(kueri).url)
            ]])
            bot.editMessageText(chat_id=update.effective_chat.id,
                                message_id=pertama.message_id,
                                text=wikipedia.summary(kueri, sentences=3),
                                reply_markup=keyboard)
        except wikipedia.PageError as e:
            update.effective_message.reply_text("⚠ Error: {}".format(e))
        except BadRequest as et:
            update.effective_message.reply_text("⚠ Error: {}".format(et))
        except wikipedia.exceptions.DisambiguationError as eet:
            update.effective_message.reply_text(
                "⚠ Error\n There are too many query! Express it more!\nPossible query result:\n{}".format(
                    eet)
            )


@run_async
def wikipt(bot: Bot, update: Update):
    kueri = re.split(pattern="wikipt", string=update.effective_message.text)
    wikipedia.set_lang("pt")
    if len(str(kueri[1])) == 0:
        update.effective_message.reply_text(
            "Escreva o que você quer procurar no Wikipedia!")
    else:
        try:
            pertama = update.effective_message.reply_text("🔄 Carregando...")
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton(text="🔧 Mais Informações...",
                                     url=wikipedia.page(kueri).url)
            ]])
            bot.editMessageText(chat_id=update.effective_chat.id,
                                message_id=pertama.message_id,
                                text=wikipedia.summary(kueri, sentences=3),
                                reply_markup=keyboard)
        except wikipedia.PageError as e:
            update.effective_message.reply_text("⚠ Erro: {}".format(e))
        except BadRequest as et:
            update.effective_message.reply_text("⚠ Erro: {}".format(et))
        except wikipedia.exceptions.DisambiguationError as eet:
            update.effective_message.reply_text(
                "⚠ Error\n Há muitas coisa! Expresse melhor para achar o resultado!\nPossíveis resultados da consulta:\n{}".format(
                    eet)
            )


@run_async
def covid(bot: Bot, update: Update):
    message = update.effective_message
    chat = update.effective_chat
    country = str(message.text[len('/covid '):])
    if country == '':
        country = "world"
    if country.lower() in ["south korea", "korea"]:
        country = "s. korea"
    try:
        c_case = cvid.get_status_by_country_name(country)
    except Exception:
        message.reply_text(tld(chat.id, "misc_covid_error"))
        return
    active = format_integer(c_case["active"])
    confirmed = format_integer(c_case["confirmed"])
    country = c_case["country"]
    critical = format_integer(c_case["critical"])
    deaths = format_integer(c_case["deaths"])
    new_cases = format_integer(c_case["new_cases"])
    new_deaths = format_integer(c_case["new_deaths"])
    recovered = format_integer(c_case["recovered"])
    total_tests = c_case["total_tests"]
    if total_tests == 0:
        total_tests = "N/A"
    else:
        total_tests = format_integer(c_case["total_tests"])
    reply = tld(chat.id,
                "misc_covid").format(country, confirmed, new_cases, active,
                                     critical, deaths, new_deaths, recovered,
                                     total_tests)
    message.reply_markdown(reply)


def format_integer(number, thousand_separator=','):
    def reverse(string):
        string = "".join(reversed(string))
        return string

    s = reverse(str(number))
    count = 0
    result = ''
    for char in s:
        count = count + 1
        if count % 3 == 0:
            if len(s) == count:
                result = char + result
            else:
                result = thousand_separator + char + result
        else:
            result = char + result
    return result


__help__ = True

ID_HANDLER = DisableAbleCommandHandler("id",
                                       get_id,
                                       pass_args=True,
                                       admin_ok=True)
IP_HANDLER = CommandHandler("ip",
                            get_bot_ip,
                            filters=Filters.chat(OWNER_ID))

INFO_HANDLER = DisableAbleCommandHandler("info",
                                         info,
                                         pass_args=True,
                                         admin_ok=True)
GITHUB_HANDLER = DisableAbleCommandHandler("git", github, admin_ok=True)
REPO_HANDLER = DisableAbleCommandHandler("repo",
                                         repo,
                                         pass_args=True,
                                         admin_ok=True)

ECHO_HANDLER = CommandHandler("echo", echo, filters=Filters.user(OWNER_ID))
MD_HELP_HANDLER = CommandHandler("markdownhelp",
                                 markdown_help,
                                 filters=Filters.private)

STATS_HANDLER = CommandHandler("stats", stats, filters=Filters.user(OWNER_ID))
GDPR_HANDLER = CommandHandler("gdpr", gdpr, filters=Filters.private)
UD_HANDLER = DisableAbleCommandHandler("ud", ud)
WIKI_HANDLER = DisableAbleCommandHandler("wiki", wiki)
WIKIEN_HANDLER = DisableAbleCommandHandler("wikien", wikien)
WIKIPT_HANDLER = DisableAbleCommandHandler("wikipt", wikipt)
COVID_HANDLER = DisableAbleCommandHandler("covid", covid, admin_ok=True)
SCREENSHOT_HANDLER = DisableAbleCommandHandler(
    ["screenshot", "print", "ss", "screencapture"], screenshot, pass_args=True)

dispatcher.add_handler(SCREENSHOT_HANDLER)
dispatcher.add_handler(UD_HANDLER)
dispatcher.add_handler(ID_HANDLER)
dispatcher.add_handler(IP_HANDLER)
dispatcher.add_handler(INFO_HANDLER)
dispatcher.add_handler(ECHO_HANDLER)
dispatcher.add_handler(MD_HELP_HANDLER)
dispatcher.add_handler(STATS_HANDLER)
dispatcher.add_handler(GDPR_HANDLER)
dispatcher.add_handler(GITHUB_HANDLER)
dispatcher.add_handler(REPO_HANDLER)
dispatcher.add_handler(
    DisableAbleCommandHandler("removebotkeyboard", reply_keyboard_remove))
dispatcher.add_handler(WIKI_HANDLER)
dispatcher.add_handler(WIKIPT_HANDLER)
dispatcher.add_handler(WIKIEN_HANDLER)
dispatcher.add_handler(COVID_HANDLER)
