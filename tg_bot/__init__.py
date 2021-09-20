import logging
import os
import sys, json
import time
import spamwatch
import telegram.ext as tg
from telethon import TelegramClient
from telethon.sessions import MemorySession
from pyrogram import Client, errors
from pyrogram.errors.exceptions.bad_request_400 import PeerIdInvalid, ChannelInvalid
from pyrogram.types import Chat, User
from configparser import ConfigParser
from rich.logging import RichHandler
from ptbcontrib.postgres_persistence import PostgresPersistence

StartTime = time.time()

def get_user_list(key):
    # Import here to evade a circular import
    from tg_bot.modules.sql import nation_sql
    royals = nation_sql.get_royals(key)
    return [a.user_id for a in royals]

# enable logging
FORMAT = "[Enterprise] %(message)s"
logging.basicConfig(handlers=[RichHandler()], level=logging.INFO, format=FORMAT, datefmt="[%X]")
logging.getLogger("pyrogram").setLevel(logging.WARNING)
log = logging.getLogger("rich")

log.info("[KIGYO] Kigyo is starting. | An Eagle Union Project. | Licensed under GPLv3.")

log.info("[KIGYO] Not affiliated to Azur Lane or Yostar in any way whatsoever.")
log.info("[KIGYO] Project maintained by: github.com/Dank-del (t.me/dank_as_fuck)")

# if version < 3.6, stop bot.
if sys.version_info[0] < 3 or sys.version_info[1] < 7:
    log.error(
        "[KIGYO] You MUST have a python version of at least 3.7! Multiple features depend on this. Bot quitting."
    )
    quit(1)

ENV = bool(os.environ.get('ENV', False))

if ENV:
    TOKEN = os.environ.get('TOKEN', None)

    try:
        OWNER_ID = int(os.environ.get('OWNER_ID', None))
    except ValueError:
        raise Exception("Your OWNER_ID env variable is not a valid integer.")
    
    OWNER_USERNAME = os.environ.get("OWNER_USERNAME", None)

    try:
        SUDO_USERS = {int(x) for x in os.environ.get("SUDO_USERS", "").split()}
        DEV_USERS = {int(x) for x in os.environ.get("DEV_USERS", "").split()}
    except ValueError:
        raise Exception(
            "Your sudo or dev users list does not contain valid integers.")

    try:
        SUPPORT_USERS = {int(x) for x in os.environ.get("SUPPORT_USERS", "").split()}
    except ValueError:
        raise Exception(
            "Your support users list does not contain valid integers.")

    try:
        WHITELIST_USERS = {int(x) for x in os.environ.get("WHITELIST_USERS", "").split()}
    except ValueError:
        raise Exception(
            "Your whitelisted users list does not contain valid integers.")
    try:
        SARDEGNA_USERS = {int(x) for x in os.environ.get("WHITELIST_USERS", "").split()}
    except ValueError:
        raise Exception(
            "Your whitelisted users list does not contain valid integers.")


    OWNER_ID = os.environ.get("OWNER_ID", None)
    OWNER_USERNAME = os.environ.get("OWNER_USERNAME", None)
    APP_ID = os.environ.get("APP_ID", None)
    API_HASH = os.environ.get("API_HASH", None)
    WEBHOOK = bool(os.environ.get("WEBHOOK", False))
    URL = os.environ.get("URL", None)
    CERT_PATH = os.environ.get("CERT_PATH", None)
    PORT = int(os.environ.get("PORT", None))
    INFOPIC = bool(os.environ.get("INFOPIC", False))
    DEL_CMDS = bool(os.environ.get("DEL_CMDS", False))
    STRICT_GBAN = bool(os.environ.get("STRICT_GBAN", False))
    ALLOW_EXCL = bool(os.environ.get("ALLOW_EXCL", False))
    CUSTOM_CMD = os.environ.get('CUSTOM_CMD', ('/', '!'))
    BAN_STICKER = os.environ.get("BAN_STICKER", None)
    TOKEN = os.environ.get("TOKEN", None)
    DB_URI = os.environ.get("SQLALCHEMY_DATABASE_URI", None)
    LOAD = os.environ.get("LOAD", "").split()
    NO_LOAD = os.environ.get("NO_LOAD", "").split()
    MESSAGE_DUMP = os.environ.get("MESSAGE_DUMP", None)
    GBAN_LOGS = os.environ.get("GBAN_LOGS", None)
    WORKERS = int(os.environ.get('WORKERS', 8))
    SUDO_USERS = os.environ.get("SUDO_USERS", None)
    DEV_USERS = os.environ.get("DEV_USERS", None)
    SUPPORT_USERS = os.environ.get("SUPPORT_USERS", None)
    SARDEGNA_USERS = os.environ.get("SARDEGNA_USERS", None)
    WHITELIST_USERS = os.environ.get("WHITELIST_USERS", None)
    SPAMMERS = os.environ.get("spammers", None)
    spamwatch_api = os.environ.get("spamwatch_api", None)
    CASH_API_KEY = os.environ.get("CASH_API_KEY", None)
    TIME_API_KEY = os.environ.get("TIME_API_KEY", None)
    WALL_API = os.environ.get("WALL_API", None)
    LASTFM_API_KEY = os.environ.get("LASTFM_API_KEY", None)
    try:
        CF_API_KEY = os.environ.get("CF_API_KEY", None)
        log.info("[NLP] AI antispam powered by Intellivoid.")
    except:
         log.info("[NLP] No Coffeehouse API key provided.")
         CF_API_KEY = None

# SpamWatch
if spamwatch_api is None:
    sw = None
    log.warning("SpamWatch API key is missing! Check your config.ini")
else:
    try:
        sw = spamwatch.Client(spamwatch_api)
    except:
        sw = None
        log.warning("Can't connect to SpamWatch!")


from tg_bot.modules.sql import SESSION

updater = tg.Updater(TOKEN, workers=WORKERS, use_context=True)
telethn = TelegramClient(MemorySession(), APP_ID, API_HASH)
dispatcher = updater.dispatcher


SUDO_USERS = list(SUDO_USERS) + list(DEV_USERS)
DEV_USERS = list(DEV_USERS)
SUPPORT_USERS = list(SUPPORT_USERS)
WHITELIST_USERS = list(WHITELIST_USERS)
SARDEGNA_USERS = list(SARDEGNA_USERS)



kp = Client(":memory:", api_id=APP_ID, api_hash=API_HASH, bot_token=TOKEN, workers=min(32, os.cpu_count() + 4))
apps = []
apps.append(kp)


async def get_entity(client, entity):
    entity_client = client
    if not isinstance(entity, Chat):
        try:
            entity = int(entity)
        except ValueError:
            pass
        except TypeError:
            entity = entity.id
        try:
            entity = await client.get_chat(entity)
        except (PeerIdInvalid, ChannelInvalid):
            for kp in apps:
                if kp != client:
                    try:
                        entity = await kp.get_chat(entity)
                    except (PeerIdInvalid, ChannelInvalid):
                        pass
                    else:
                        entity_client = kp
                        break
            else:
                entity = await kp.get_chat(entity)
                entity_client = kp
    return entity, entity_client

# Load at end to ensure all prev variables have been set
from tg_bot.modules.helper_funcs.handlers import CustomCommandHandler

if CUSTOM_CMD and len(CUSTOM_CMD) >= 1:
    tg.CommandHandler = CustomCommandHandler


def spamfilters(text, user_id, chat_id):
    # print("{} | {} | {}".format(text, user_id, chat_id))
    if int(user_id) in SPAMMERS:
        print("This user is a spammer!")
        return True
    else:
        return False
