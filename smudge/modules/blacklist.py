#    SmudgeLord (A telegram bot project)
#    Copyright (C) 2017-2019 Paul Larsen
#    Copyright (C) 2019-2021 A Haruka Aita and Intellivoid Technologies project
#    Copyright (C) 2021 Renatoh

#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.

import html
import re
from typing import Optional, List

from telegram import Message, Chat, Update, Bot, ParseMode
from telegram.error import BadRequest
from telegram.ext import CommandHandler, MessageHandler, Filters, run_async

import smudge.modules.sql.blacklist_sql as sql
from smudge import dispatcher, LOGGER, CallbackContext
from smudge.modules.disable import DisableAbleCommandHandler
from smudge.helper_funcs.chat_status import user_admin, user_not_admin
from smudge.helper_funcs.extraction import extract_text
from smudge.helper_funcs.misc import split_message

from smudge.modules.connection import connected

from smudge.modules.translations.strings import tld

BLACKLIST_GROUP = 11


def blacklist(update: Update, context: CallbackContext):
    bot = context.bot
    args = context.args
    msg = update.effective_message  # type: Optional[Message]
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]

    conn = connected(update, context, chat, user.id, need_admin=False)
    if conn:
        chat_id = conn
        chat_name = dispatcher.bot.getChat(conn).title
    else:
        if chat.type == "private":
            return
        chat_id = update.effective_chat.id
        chat_name = chat.title

    filter_list = tld(chat.id, "blacklist_active_list").format(chat_name)

    all_blacklisted = sql.get_chat_blacklist(chat_id)

    if len(args) > 0 and args[0].lower() == 'copy':
        for trigger in all_blacklisted:
            filter_list += "<code>{}</code>\n".format(html.escape(trigger))
    else:
        for trigger in all_blacklisted:
            filter_list += " • <code>{}</code>\n".format(html.escape(trigger))

    split_text = split_message(filter_list)
    for text in split_text:
        if filter_list == tld(chat.id, "blacklist_active_list").format(
                chat_name):  # We need to translate
            msg.reply_text(tld(chat.id, "blacklist_no_list").format(chat_name),
                           parse_mode=ParseMode.HTML)
            return
        msg.reply_text(text, parse_mode=ParseMode.HTML)


@user_admin
def add_blacklist(update: Update, context: CallbackContext):
    bot = context.bot
    msg = update.effective_message  # type: Optional[Message]
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    words = msg.text.split(None, 1)

    conn = connected(update, context, chat, user.id, need_admin=False)
    if conn:
        chat_id = conn
        chat_name = dispatcher.bot.getChat(conn).title
    else:
        chat_id = update.effective_chat.id
        if chat.type == "private":
            return
        chat_name = chat.title

    if len(words) > 1:
        text = words[1]
        to_blacklist = list(
            {trigger.strip() for trigger in text.split("\n")
                if trigger.strip()})
        for trigger in to_blacklist:
            sql.add_to_blacklist(chat_id, trigger.lower())

        if len(to_blacklist) == 1:
            msg.reply_text(tld(chat.id, "blacklist_add").format(
                html.escape(to_blacklist[0]), chat_name),
                parse_mode=ParseMode.HTML)

        else:
            msg.reply_text(tld(chat.id,
                               "blacklist_add").format(len(to_blacklist)),
                           chat_name,
                           parse_mode=ParseMode.HTML)

    else:
        msg.reply_text(tld(chat.id, "blacklist_err_add_no_args"))


@user_admin
def unblacklist(update: Update, context: CallbackContext):
    bot = context.bot
    msg = update.effective_message  # type: Optional[Message]
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    words = msg.text.split(None, 1)

    conn = connected(update, context, chat, user.id, need_admin=False)
    if conn:
        chat_id = conn
        chat_name = dispatcher.bot.getChat(conn).title
    else:
        chat_id = update.effective_chat.id
        if chat.type == "private":
            return
        chat_name = chat.title

    if len(words) > 1:
        text = words[1]
        to_unblacklist = list(
            {trigger.strip() for trigger in text.split("\n")
                if trigger.strip()})
        successful = 0
        for trigger in to_unblacklist:
            success = sql.rm_from_blacklist(chat_id, trigger.lower())
            if success:
                successful += 1

        if len(to_unblacklist) == 1:
            if successful:
                msg.reply_text(tld(chat.id, "blacklist_del").format(
                    html.escape(to_unblacklist[0]), chat_name),
                    parse_mode=ParseMode.HTML)
            else:
                msg.reply_text(
                    tld(chat.id, "This isn't a blacklisted trigger!"))

        elif successful == len(to_unblacklist):
            msg.reply_text(tld(chat.id, "blacklist_multi_del").format(
                successful, chat_name),
                parse_mode=ParseMode.HTML)

        elif not successful:
            msg.reply_text(tld(chat.id,
                               "blacklist_err_multidel_no_trigger").format(
                                   successful,
                                   len(to_unblacklist) - successful),
                           parse_mode=ParseMode.HTML)

        else:
            msg.reply_text(tld(
                chat.id, "blacklist_err_multidel_some_no_trigger").format(
                    successful, chat_name,
                    len(to_unblacklist) - successful),
                parse_mode=ParseMode.HTML)
    else:
        msg.reply_text(tld(chat.id, "blacklist_err_del_no_args"))


@user_not_admin
def del_blacklist(update: Update, context: CallbackContext):
    bot = context.bot
    chat = update.effective_chat  # type: Optional[Chat]
    message = update.effective_message  # type: Optional[Message]
    to_match = extract_text(message)
    if not to_match:
        return

    chat_filters = sql.get_chat_blacklist(chat.id)
    for trigger in chat_filters:
        pattern = r"( |^|[^\w])" + re.escape(trigger) + r"( |$|[^\w])"
        if re.search(pattern, to_match, flags=re.IGNORECASE):
            try:
                message.delete()
            except BadRequest as excp:
                if excp.message == "Message to delete not found":
                    pass
                else:
                    LOGGER.exception("Error while deleting blacklist message.")
            break


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __stats__():
    return "• `{}` blacklist triggers, across `{}` chats.".format(
        sql.num_blacklist_filters(), sql.num_blacklist_filter_chats())


def __import_data__(chat_id, data):
    # set chat blacklist
    blacklist = data.get('blacklist', {})
    for trigger in blacklist:
        sql.add_to_blacklist(chat_id, trigger)


__help__ = True

# TODO: Add blacklist alternative modes: warn, ban, kick, or mute.

BLACKLIST_HANDLER = DisableAbleCommandHandler(
    "blacklist", blacklist, pass_args=True, admin_ok=True, run_async=True)
ADD_BLACKLIST_HANDLER = CommandHandler(
    "addblacklist", add_blacklist, filters=Filters.chat_type.groups, run_async=True)
UNBLACKLIST_HANDLER = CommandHandler(
    ["unblacklist", "rmblacklist"], unblacklist)
BLACKLIST_DEL_HANDLER = MessageHandler(
    (Filters.text | Filters.command | Filters.sticker | Filters.photo)
    & Filters.chat_type.groups,
    del_blacklist,
    run_async=True)

dispatcher.add_handler(BLACKLIST_HANDLER)
dispatcher.add_handler(ADD_BLACKLIST_HANDLER)
dispatcher.add_handler(UNBLACKLIST_HANDLER)
dispatcher.add_handler(BLACKLIST_DEL_HANDLER, group=BLACKLIST_GROUP)
