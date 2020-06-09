import logging
import sys
import yaml
import spamwatch
import os

from telethon import TelegramClient
import telegram.ext as tg

#Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO)

LOGGER = logging.getLogger(__name__)

LOGGER.info("Starting eliana bot...")

# If Python version is < 3.6, stops the bot.
if sys.version_info[0] < 3 or sys.version_info[1] < 8:
    LOGGER.error(
        "You MUST have a python version of at least 3.8! Multiple features depend on this. Bot quitting."
    )
    quit(1)
ENV = bool(os.environ.get('ENV', False))

if ENV:
    TOKEN = os.environ.get('TOKEN', None)
    try:
        OWNER_ID = int(os.environ.get('OWNER_ID', None))
    except ValueError:
        raise Exception("Your OWNER_ID env variable is not a valid integer.")

    MESSAGE_DUMP = os.environ.get('MESSAGE_DUMP', None)
    GBAN_DUMP = os.environ.get('GBAN_DUMP', None)
    OWNER_USERNAME = os.environ.get("OWNER_USERNAME", None)
    API_KEY = os.environ.get('API_KEY', "")
    API_HASH = os.environ.get('API_HASH', "")

    try:
        SUDO_USERS = set(int(x) for x in os.environ.get("SUDO_USERS", "").split())
    except ValueError:
        raise Exception("Your sudo users list does not contain valid integers.")

    try:
        SUPPORT_USERS = set(int(x) for x in os.environ.get("SUPPORT_USERS", "").split())
    except ValueError:
        raise Exception("Your support users list does not contain valid integers.")

    try:
        WHITELIST_USERS = set(int(x) for x in os.environ.get("WHITELIST_USERS", "").split())
    except ValueError:
        raise Exception("Your whitelisted users list does not contain valid integers.")

    
    DEEPFRY_TOKEN = os.environ.get('DEEPFRY_TOKEN', "")
    DB_URI = os.environ.get('DATABASE_URL')
    LOAD = os.environ.get("LOAD", "").split()
    NO_LOAD = os.environ.get("NO_LOAD", "translation").split()
    DEL_CMDS = bool(os.environ.get('DEL_CMDS', False))
    STRICT_ANTISPAM = bool(os.environ.get('STRICT_ANTISPAM', False))
    WORKERS = int(os.environ.get('WORKERS', 8))
    
    # SpamWatch
    spamwatch_api = os.environ.get('SW_API', None)
    if spamwatch_api == "None":
    	sw = None
    	LOGGER.warning("SpamWatch API key is missing! Check your config.env.")
    else:
    	try:
    		sw = spamwatch.Client(spamwatch_api)
    	except Exception:
    		sw = None

else:
	# Load config
	try:
	    CONFIG = yaml.load(open('config.yml', 'r'), Loader=yaml.SafeLoader)
	except FileNotFoundError:
	    print("Are you dumb? C'mon start using your brain!")
	    quit(1)
	except Exception as eee:
	    print(
	        f"Ah, look like there's error(s) while trying to load your config. It is\n!!!! ERROR BELOW !!!!\n {eee} \n !!! ERROR END !!!"
	    )
	    quit(1)
	
	if not CONFIG['is_example_config_or_not'] == "not_sample_anymore":
	    print("Please, use your eyes and stop being blinded.")
	    quit(1)
	
	TOKEN = CONFIG['bot_token']
	API_KEY = CONFIG['api_key']
	API_HASH = CONFIG['api_hash']
	
	try:
	    OWNER_ID = int(CONFIG['owner_id'])
	except ValueError:
	    raise Exception("Your 'owner_id' variable is not a valid integer.")
	
	try:
	    MESSAGE_DUMP = CONFIG['message_dump']
	except ValueError:
	    raise Exception("Your 'message_dump' must be set.")
	
	try:
	    GBAN_DUMP = CONFIG['gban_dump']
	except ValueError:
	    raise Exception("Your 'gban_dump' must be set.")
	
	try:
	    OWNER_USERNAME = CONFIG['owner_username']
	except ValueError:
	    raise Exception("Your 'owner_username' must be set.")
	
	try:
	    SUDO_USERS = set(int(x) for x in CONFIG['sudo_users'] or [])
	except ValueError:
	    raise Exception("Your sudo users list does not contain valid integers.")
	
	try:
	    SUPPORT_USERS = set(int(x) for x in CONFIG['support_users'] or [])
	except ValueError:
	    raise Exception("Your support users list does not contain valid integers.")
	
	try:
	    WHITELIST_USERS = set(int(x) for x in CONFIG['whitelist_users'] or [])
	except ValueError:
	    raise Exception(
	        "Your whitelisted users list does not contain valid integers.")
	
	DB_URI = CONFIG['database_url']
	LOAD = CONFIG['load']
	NO_LOAD = CONFIG['no_load']
	DEL_CMDS = CONFIG['del_cmds']
	STRICT_ANTISPAM = CONFIG['strict_antispam']
	WORKERS = CONFIG['workers']
	DEEPFRY_TOKEN = CONFIG['deepfry_token']
	
	# SpamWatch
	spamwatch_api = CONFIG['sw_api']
	
	if spamwatch_api == "None":
	    sw = None
	    LOGGER.warning("SpamWatch API key is missing! Check your config.env.")
	else:
	    try:
	        sw = spamwatch.Client(spamwatch_api)
	    except Exception:
	        sw = None
	        
SUDO_USERS.add(OWNER_ID)

updater = tg.Updater(TOKEN, workers=WORKERS)

dispatcher = updater.dispatcher

tbot = TelegramClient("eliana", API_KEY, API_HASH)

SUDO_USERS = list(SUDO_USERS)
WHITELIST_USERS = list(WHITELIST_USERS)
SUPPORT_USERS = list(SUPPORT_USERS)

# Load at end to ensure all prev variables have been set
from eliana.modules.helper_funcs.handlers import CustomCommandHandler, CustomRegexHandler

# make sure the regex handler can take extra kwargs
tg.RegexHandler = CustomRegexHandler

tg.CommandHandler = CustomCommandHandler