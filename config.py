############################################################
# Constants and Globals
############################################################
import json
import logging
import sys

import twitter
from telegram.ext import Updater, CommandHandler
import commands
import jobs

api = None
updater = None
config = None
TIME_LIMIT = 2
MAX_USES = 5
MAX_TRIES = 5
m = open("mentions.json", 'a')

commands = {
    'ban': commands.ban_callback,
    'unban': commands.unban_callback,
    'myid': commands.myid_callback,
    'deltweet': commands.deltweet_callback,
    'mentions': commands.mentions_callback,
    'status': commands.status_callback,
    'authorize': commands.authorize_callback,
    'deauthorize': commands.deauthorize_callback,
    'logs': commands.logs_callback,
}


def load_config():
    """
    Loads the globals.config on a global var from globals.config.json
    :return: nothing
    """
    global config
    try:
        config = json.load(open("config.json"))
        if "lastID" not in config:
            config["lastID"] = 1
        if "users" not in config:
            config["users"] = {}
        if "admins" not in config:
            config["admins"] = []
        if "cached" not in config:
            config["cached"] = {}
    except Exception as e:
        logging.info("globals.config.json not found")
        exit(1)


def save_config():
    """
    Saves global globals.config into globals.config.json file
    :return:
    """
    global config
    try:
        json.dump(config, open("globals.config.json", 'w'))
    except Exception as e:
        logging.info("cannot save globals.config.json", e)
        exit(1)


def init():
    global api, updater, config
    init_logs()
    load_config()
    api = twitter.Api(consumer_key=config["twitter"]["consumerKey"],
                      consumer_secret=config["twitter"]["consumerSecret"],
                      access_token_key=config["twitter"]["accessTokenKey"],
                      access_token_secret=config["twitter"]["accessTokenSecret"],
                      tweet_mode="extended")
    updater = Updater(config["telegram"]["token"], use_context=True)
    queue = updater.job_queue
    queue.run_repeating(jobs.main_job, interval=60, first=0)
    for cmd, callback in commands.items():
        handler = CommandHandler(cmd, callback)
        updater.dispatcher.add_handler(handler)
    updater.start_polling()


def init_logs():
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    root = logging.getLogger()
    root.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(logging.INFO)
    handler.setFormatter(formatter)
    root.addHandler(handler)

    fh = logging.FileHandler('bot.log')
    fh.setLevel(logging.INFO)
    fh.setFormatter(formatter)
    root.addHandler(fh)
