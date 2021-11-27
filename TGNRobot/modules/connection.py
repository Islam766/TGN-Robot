import time
import re

from telegram import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton, Update, Bot
from telegram.error import BadRequest, Unauthorized
from telegram.ext import CommandHandler, CallbackQueryHandler, run_async

import TGNRobot.modules.sql.connection_sql as sql
from TGNRobot import dispatcher, DRAGONS, DEV_USERS
from TGNRobot.modules.helper_funcs import chat_status
from TGNRobot.modules.helper_funcs.alternate import send_message, typing_action

user_admin = chat_status.user_admin


@user_admin
@run_async
@typing_action
def allow_connections(update, context) -> str:

    chat = update.effective_chat
    args = context.args

    if chat.type != chat.PRIVATE:
        if len(args) >= 1:
            var = args[0]
            if var == "no":
                sql.set_allow_connect_to_chat(chat.id, False)
                send_message(
                    update.effective_message,
                    "Connection has been disabled for this chat",
                )
            elif var == "yes":
                sql.set_allow_connect_to_chat(chat.id, True)
                send_message(
                    update.effective_message,
                    "Подключение к этому чату разрешено",
                )
            else:
                send_message(
                    update.effective_message,
                    "Please enter `yes` or `no`!",
                    parse_mode=ParseMode.MARKDOWN,
                )
        else:
            get_settings = sql.allow_connect_to_chat(chat.id)
            if get_settings:
                send_message(
                    update.effective_message,
                    "Подключения к этой группе *Разрешен* для членов!",
                    parse_mode=ParseMode.MARKDOWN,
                )
            else:
                send_message(
                    update.effective_message,
                    "Подключение к этой группе *запрещено* для участников!",
                    parse_mode=ParseMode.MARKDOWN,
                )
    else:
        send_message(
            update.effective_message, "Эта команда предназначена только для группы. Не в личку!"
        )


@run_async
@typing_action
def connection_chat(update, context):

    chat = update.effective_chat
    user = update.effective_user

    conn = connected(context.bot, update, chat, user.id, need_admin=True)

    if conn:
        chat = dispatcher.bot.getChat(conn)
        chat_name = dispatcher.bot.getChat(conn).title
    else:
        if update.effective_message.chat.type != "private":
            return
        chat = update.effective_chat
        chat_name = update.effective_message.chat.title

    if conn:
        message = "В настоящее время вы подключены к {}.\n".format(chat_name)
    else:
        message = "В настоящее время вы не состоите ни в одной группе.\n"
    send_message(update.effective_message, message, parse_mode="markdown")


@run_async
@typing_action
def connect_chat(update, context):

    chat = update.effective_chat
    user = update.effective_user
    args = context.args

    if update.effective_chat.type == "private":
        if args and len(args) >= 1:
            try:
                connect_chat = int(args[0])
                getstatusadmin = context.bot.get_chat_member(
                    connect_chat, update.effective_message.from_user.id
                )
            except ValueError:
                try:
                    connect_chat = str(args[0])
                    get_chat = context.bot.getChat(connect_chat)
                    connect_chat = get_chat.id
                    getstatusadmin = context.bot.get_chat_member(
                        connect_chat, update.effective_message.from_user.id
                    )
                except BadRequest:
                    send_message(update.effective_message, "Invalid Chat ID!")
                    return
            except BadRequest:
                send_message(update.effective_message, "Invalid Chat ID!")
                return

            isadmin = getstatusadmin.status in ("administrator", "creator")
            ismember = getstatusadmin.status in ("member")
            isallow = sql.allow_connect_to_chat(connect_chat)

            if (isadmin) or (isallow and ismember) or (user.id in DRAGONS):
                connection_status = sql.connect(
                    update.effective_message.from_user.id, connect_chat
                )
                if connection_status:
                    conn_chat = dispatcher.bot.getChat(
                        connected(context.bot, update, chat, user.id, need_admin=False)
                    )
                    chat_name = conn_chat.title
                    send_message(
                        update.effective_message,
                        "Successfully connected to *{}*. \nUse /helpconnect to check available commands.".format(
                            chat_name
                        ),
                        parse_mode=ParseMode.MARKDOWN,
                    )
                    sql.add_history_conn(user.id, str(conn_chat.id), chat_name)
                else:
                    send_message(update.effective_message, "Connection failed!")
            else:
                send_message(
                    update.effective_message, "Connection to this chat is not allowed!"
                )
        else:
            gethistory = sql.get_history_conn(user.id)
            if gethistory:
                buttons = [
                    InlineKeyboardButton(
                        text="❎ Кнопка закрытия", callback_data="connect_close"
                    ),
                    InlineKeyboardButton(
                        text="🧹 Чистая история", callback_data="connect_clear"
                    ),
                ]
            else:
                buttons = []
            conn = connected(context.bot, update, chat, user.id, need_admin=False)
            if conn:
                connectedchat = dispatcher.bot.getChat(conn)
                text = "You are currently connected to *{}* (`{}`)".format(
                    connectedchat.title, conn
                )
                buttons.append(
                    InlineKeyboardButton(
                        text="🔌 Отключить", callback_data="connect_disconnect"
                    )
                )
            else:
                text = "Write the chat ID or tag to connect!"
            if gethistory:
                text += "\n\n*Connection history:*\n"
                text += "╒═══「 *Info* 」\n"
                text += "│  Sorted: `Newest`\n"
                text += "│\n"
                buttons = [buttons]
                for x in sorted(gethistory.keys(), reverse=True):
                    htime = time.strftime("%d/%m/%Y", time.localtime(x))
                    text += "╞═「 *{}* 」\n│   `{}`\n│   `{}`\n".format(
                        gethistory[x]["chat_name"], gethistory[x]["chat_id"], htime
                    )
                    text += "│\n"
                    buttons.append(
                        [
                            InlineKeyboardButton(
                                text=gethistory[x]["chat_name"],
                                callback_data="connect({})".format(
                                    gethistory[x]["chat_id"]
                                ),
                            )
                        ]
                    )
                text += "╘══「 Total {} Chats 」".format(
                    str(len(gethistory)) + " (max)"
                    if len(gethistory) == 5
                    else str(len(gethistory))
                )
                conn_hist = InlineKeyboardMarkup(buttons)
            elif buttons:
                conn_hist = InlineKeyboardMarkup([buttons])
            else:
                conn_hist = None
            send_message(
                update.effective_message,
                text,
                parse_mode="markdown",
                reply_markup=conn_hist,
            )

    else:
        getstatusadmin = context.bot.get_chat_member(
            chat.id, update.effective_message.from_user.id
        )
        isadmin = getstatusadmin.status in ("administrator", "creator")
        ismember = getstatusadmin.status in ("member")
        isallow = sql.allow_connect_to_chat(chat.id)
        if (isadmin) or (isallow and ismember) or (user.id in DRAGONS):
            connection_status = sql.connect(
                update.effective_message.from_user.id, chat.id
            )
            if connection_status:
                chat_name = dispatcher.bot.getChat(chat.id).title
                send_message(
                    update.effective_message,
                    "Successfully connected to *{}*.".format(chat_name),
                    parse_mode=ParseMode.MARKDOWN,
                )
                try:
                    sql.add_history_conn(user.id, str(chat.id), chat_name)
                    context.bot.send_message(
                        update.effective_message.from_user.id,
                        "You are connected to *{}*. \nUse `/helpconnect` to check available commands.".format(
                            chat_name
                        ),
                        parse_mode="markdown",
                    )
                except BadRequest:
                    pass
                except Unauthorized:
                    pass
            else:
                send_message(update.effective_message, "Ошибка подключения!")
        else:
            send_message(
                update.effective_message, "Подключение к этому чату запрещено!"
            )


def disconnect_chat(update, context):

    if update.effective_chat.type == "private":
        disconnection_status = sql.disconnect(update.effective_message.from_user.id)
        if disconnection_status:
            sql.disconnected_chat = send_message(
                update.effective_message, "Отключен от чата!"
            )
        else:
            send_message(update.effective_message, "Вы не связаны! ")
    else:
        send_message(update.effective_message, "Эта команда доступна только в личке.")


def connected(bot: Bot, update: Update, chat, user_id, need_admin=True):
    user = update.effective_user

    if chat.type == chat.PRIVATE and sql.get_connected_chat(user_id):

        conn_id = sql.get_connected_chat(user_id).chat_id
        getstatusadmin = bot.get_chat_member(
            conn_id, update.effective_message.from_user.id
        )
        isadmin = getstatusadmin.status in ("administrator", "creator")
        ismember = getstatusadmin.status in ("member")
        isallow = sql.allow_connect_to_chat(conn_id)

        if (
            (isadmin)
            or (isallow and ismember)
            or (user.id in DRAGONS)
            or (user.id in DEV_USERS)
        ):
            if need_admin is True:
                if (
                    getstatusadmin.status in ("administrator", "creator")
                    or user_id in DRAGONS
                    or user.id in DEV_USERS
                ):
                    return conn_id
                else:
                    send_message(
                        update.effective_message,
                        "Вы должны быть администратором подключенной группы!",
                    )
            else:
                return conn_id
        else:
            send_message(
                update.effective_message,
                "Группа изменила права на подключение или вы больше не админ.\nЯ отключил тебя.",
            )
            disconnect_chat(update, bot)
    else:
        return False


CONN_HELP = """
 Доступны действия с подключенными группами:
 • Просмотр и редактирование заметок.
 • Просмотр и редактирование фильтров.
 • Получить инвайт-ссылку чата.
 • Устанавливайте и управляйте настройками AntiFlood.
 • Установка и управление настройками черного списка.
 • Установите блокировки и разблокировки в чате.
 • Включение и отключение команд в чате.
 • Экспорт и импорт резервной копии чата.
 • Больше"""


@run_async
def help_connect_chat(update, context):

    args = context.args

    if update.effective_message.chat.type != "private":
        send_message(update.effective_message, "PM me with that command to get help.")
        return
    else:
        send_message(update.effective_message, CONN_HELP, parse_mode="markdown")


@run_async
def connect_button(update, context):

    query = update.callback_query
    chat = update.effective_chat
    user = update.effective_user

    connect_match = re.match(r"connect\((.+?)\)", query.data)
    disconnect_match = query.data == "connect_disconnect"
    clear_match = query.data == "connect_clear"
    connect_close = query.data == "connect_close"

    if connect_match:
        target_chat = connect_match.group(1)
        getstatusadmin = context.bot.get_chat_member(target_chat, query.from_user.id)
        isadmin = getstatusadmin.status in ("administrator", "creator")
        ismember = getstatusadmin.status in ("member")
        isallow = sql.allow_connect_to_chat(target_chat)

        if (isadmin) or (isallow and ismember) or (user.id in DRAGONS):
            connection_status = sql.connect(query.from_user.id, target_chat)

            if connection_status:
                conn_chat = dispatcher.bot.getChat(
                    connected(context.bot, update, chat, user.id, need_admin=False)
                )
                chat_name = conn_chat.title
                query.message.edit_text(
                    "Successfully connected to *{}*. \nUse `/helpconnect` to check available commands.".format(
                        chat_name
                    ),
                    parse_mode=ParseMode.MARKDOWN,
                )
                sql.add_history_conn(user.id, str(conn_chat.id), chat_name)
            else:
                query.message.edit_text("Connection failed!")
        else:
            context.bot.answer_callback_query(
                query.id, "Подключение к этому чату запрещено!", show_alert=True
            )
    elif disconnect_match:
        disconnection_status = sql.disconnect(query.from_user.id)
        if disconnection_status:
            sql.disconnected_chat = query.message.edit_text("Disconnected from chat!")
        else:
            context.bot.answer_callback_query(
                query.id, "Вы не подключены!", show_alert=True
            )
    elif clear_match:
        sql.clear_history_conn(query.from_user.id)
        query.message.edit_text("Связанная история удалена!")
    elif connect_close:
        query.message.edit_text("Закрыто.\nЧтобы снова открыть, введите /connect")
    else:
        connect_chat(update, context)


__mod_name__ = "Connect"

__help__ = """
 Иногда вы просто хотите добавить некоторые заметки и фильтры в групповой чат, но не хотите, чтобы все видели; Это где подключения приходят...
  Это позволяет вам подключаться к базе данных чата и добавлять в нее вещи без команд, появляющихся в чате! По понятным причинам, вы должны быть администратором, чтобы добавлять вещи; но любой член группы может просматривать ваши данные.\n
  Действия доступные с подключенными группами:
  • Просмотр и редактирование заметок
  • Просмотр и редактирование фильтров
  • просматривать и редактировать черные списки
  • Повышать/понижать пользователей
  • см. Админлист, см. ссылку-приглашение
  • Откл/вкл команды в чате
  • Откл/вкл пользователей в чате
  • Ограничить/неограничить пользователей в чате
  • Больше в будущем!\n
  - Введите /connect или /connection в группе, к которой вы хотите подключиться.
  - /connection or /connect <chatid>: Подключиться к удаленному чату
  - /disconnect: Отключиться от чата
  - /allowconnect on/yes/off/no: Разрешить подключать пользователей к группе\n
  Вы можете получить идентификатор чата с помощью команды /id в вашем чате. Не удивляйтесь, если идентификатор отрицательный; все супер группы имеют отрицательные идентификаторы.
"""

CONNECT_CHAT_HANDLER = CommandHandler("connect", connect_chat, pass_args=True)
CONNECTION_CHAT_HANDLER = CommandHandler("connection", connection_chat)
DISCONNECT_CHAT_HANDLER = CommandHandler("disconnect", disconnect_chat)
ALLOW_CONNECTIONS_HANDLER = CommandHandler(
    "allowconnect", allow_connections, pass_args=True
)
HELP_CONNECT_CHAT_HANDLER = CommandHandler("helpconnect", help_connect_chat)
CONNECT_BTN_HANDLER = CallbackQueryHandler(connect_button, pattern=r"connect")

dispatcher.add_handler(CONNECT_CHAT_HANDLER)
dispatcher.add_handler(CONNECTION_CHAT_HANDLER)
dispatcher.add_handler(DISCONNECT_CHAT_HANDLER)
dispatcher.add_handler(ALLOW_CONNECTIONS_HANDLER)
dispatcher.add_handler(HELP_CONNECT_CHAT_HANDLER)
dispatcher.add_handler(CONNECT_BTN_HANDLER)
