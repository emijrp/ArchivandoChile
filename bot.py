import json
import archiveis
import requests
import time
from datetime import datetime

import twitter
import telegram
from telegram.ext import Updater, CommandHandler

import logging
import sys

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

api = None
config = None

TIME_LIMIT = 2
MAX_USES = 5
MAX_TRIES = 5

m = open("mentions.json", 'a')
media_hash = set()


def load_media_hash_set():
    try:
        return pickle.load(open("media_hash.pickle", "rb"))
    except (OSError, IOError) as e:
        return set()


def save_media_hash_set():
    try:
        return pickle.dump(open("media_hash.pickle", "wb"))
    except (OSError, IOError) as e:
        return


def add_use(userid):
    '''
    Counts an extra use to the system for a user ID
    :param userid: User ID.
    :return:
    '''
    global config
    # If first user
    if not str(userid) in config["users"]:
        config["users"][str(userid)] = {
            "last_use": 0,
            "uses": 0,
            "tries": 0,
            "banned": False
        }
    # if is not banned
    if config["users"][str(userid)]["banned"]:
        return None

    elif can_use(userid):
        config["users"][str(userid)]["uses"] += 1
        config["users"][str(userid)]["last_use"] = time.time()
        return True
    else:
        config["users"][str(userid)]["tries"] += 1
        if config["users"][str(userid)]["tries"] >= MAX_TRIES:
            config["users"][str(userid)]["banned"] = True
            return None
        return False


def ban(userid):
    '''
    Allows to ban an user
    :param userid: User ID
    :return: None
    '''
    global config
    if not str(userid) in config["users"]:
        config["users"][str(userid)] = {
            "last_use": 0,
            "uses": 0,
            "tries": 0,
            "banned": False
        }
    config["users"][str(userid)]["banned"] = True
    save_config()


def unban(userid):
    '''
    allows to unban an user
    :param userid:
    :return:
    '''
    global config
    if str(userid) in config["users"]:
        del config["users"][str(userid)]
        save_config()


def can_use(userid):
    '''
    Checks if a user can use the system.
    :param userid:
    :return:
    '''
    global config
    if config["users"][str(userid)]["banned"]:
        return False
    elif time.time() - config["users"][str(userid)]["last_use"] > TIME_LIMIT * 60:
        config["users"][str(userid)]["uses"] = 0
        config["users"][str(userid)]["tries"] = 0
        return True
    elif config["users"][str(userid)]["uses"] < MAX_USES:
        return True
    else:
        return False


def save_in_archive(url):
    '''
    Saves an URL in archive.is
    :param url: URL to save
    :return: URL in archive.is
    '''
    return archiveis.capture(url)


def get_twitter_user_by_name(name):
    '''
    Returns a twitter user by its screen_name or URL.
    :param name: screen name
    :return: None or a User object
    '''
    global api, config
    screen_name = name
    if "twitter.com" in screen_name or "http" in screen_name:
        screen_name = screen_name.strip("/").split("/")[-1]
    user = api.GetUser(screen_name=screen_name)
    return user


def get_commented_retweet(msg):
    '''
    Returns a retweeted tweet if it exists.
    :param msg: the message
    :return: None if the retweet doesn't exist, the retweet if it exists
    '''
    global api
    if msg.urls is not None:
        for url in msg.urls:
            if "twitter.com" in url.expanded_url and "status" in url.expanded_url:
                status_id = url.expanded_url.strip("/").split("/")[-1]
                if status_id.isdigit():
                    return api.GetStatus(int(status_id))
    return None


def ban_callback(update, context):
    """
    Callback to ban a Twitter user
    :param update: Telegram Update
    :param context: Telegram Context
    :return: None
    """
    global api, config
    if update.effective_user.id not in config["admins"]:
        return
    logging.info("Update from id: {}".format(update.effective_user.id))
    if len(context.args) != 1:
        update.message.reply_text("/ban <twitter_screen_name>")
    user = get_twitter_user_by_name(context.args[0])
    if user is not None:
        ban(user.id)
        update.message.reply_text("User banned! id={}, screen_name={}".format(user.id, user.screen_name))
    else:
        update.message.reply_text("User with screen_name={} not found".format(user.screen_name))


def unban_callback(update, context):
    """
    Callback that unbans an user from the system
    :param update: Telegram Update
    :param context: Telegram Context
    :return: None
    """
    global config
    if update.effective_user.id not in config["admins"]:
        return
    logging.info("Update from id: {}".format(update.effective_user.id))
    if len(context.args) != 1:
        update.message.reply_text("/unban <twitter_screen_name>")
    user = get_twitter_user_by_name(context.args[0])
    if user is not None:
        unban(user.id)
        update.message.reply_text("User unbanned! id={}, screen_name={}".format(user.id, user.screen_name))
    else:
        update.message.reply_text("User with screen_name={} not found".format(user.screen_name))


def myid_callback(update, context):
    '''
    Callback that returns users ID
    :param update: Telegram Update
    :param context: Telegram Context
    :return:  None
    '''
    update.message.reply_text("Your id is {}".format(update.effective_user.id))


def status_callback(update, context):
    '''
    Callback to send an admin a user status report
    :param update: Telegram Update
    :param context: Telegram Context
    :return: None
    '''
    global config
    if update.effective_user.id not in config["admins"]:
        return
    logging.info("Update from id: {}".format(update.effective_user.id))
    if len(context.args) != 1:
        update.message.reply_text("/unban <twitter_screen_name>")
    user = get_twitter_user_by_name(context.args[0])
    if user is not None and str(user.id) in config["users"]:
        c = config["users"][str(user.id)]
        status = '''User Status:
        id={}
        screen_name={}
        banned={}
        last_use={}
        uses={}
        tries={}
        time_threshold={}
        max_uses={}
        max_tries={}
        '''.format(user.id,
                   user.screen_name,
                   c["banned"],
                   datetime.fromtimestamp(c["last_use"]).strftime('%Y-%m-%d %H:%M:%S'),
                   c["uses"],
                   c["tries"],
                   TIME_LIMIT,
                   MAX_USES,
                   MAX_TRIES)
        update.message.reply_text(status)
    else:
        update.message.reply_text("User with screen_name={} not found".format(user.screen_name))


def mentions_callback(update, context):
    '''
    Callback used to send to an admin mentions file
    :param update: Telegram Update
    :param context: Telegram Context
    :return: None
    '''
    global config
    if update.effective_user.id not in config["admins"]:
        return
    logging.info("Update from id: {}".format(update.effective_user.id))
    with open("mentions.json", 'rb') as x:
        update.message.reply_document(document=x)


def deltweet_callback(update, context):
    '''
    Callback used for deleting a tweet
    :param update:  Telegram Update
    :param context:  Telegram Context
    :return: None
    '''
    global api, config
    if update.effective_user.id not in config["admins"]:
        return
    if len(context.args) != 1:
        update.message.reply_text("/deltweet <twitter_status_id>")
    status_id = context.args[0]
    if "twitter.com" in status_id or "http" in status_id:
        status_id = status_id.strip("/").split("/")[-1]
    if status_id.isdigit():
        api.DestroyStatus(status_id)
        update.message.reply_text("Tweet deleted successfully!")
    else:
        update.message.reply_text("status_id is not a number or URL")


def authorize_callback(update, context):
    '''
    Callback used for authorizing a user as admin.
    :param update: Telegram Update
    :param context: Telegram Context
    :return: None
    '''
    global config
    if update.effective_user.id not in config["admins"]:
        return
    logging.info("Update from id: {}".format(update.effective_user.id))
    if len(context.args) != 1 or not context.args[0].isdigit():
        update.message.reply_text("/authorize <telegram_user_id>")
    user_id = int(context.args[0])
    if user_id not in config["admins"]:
        config["admins"].append(user_id)
        save_config()
        update.message.reply_text("user {} added as admin successfully!".format(user_id))
    else:
        update.message.reply_text("user {} is already an admin!".format(user_id))


def deauthorize_callback(update, context):
    '''
    Callback used for deauthorising a user as admin.
    :param update: Telegram Update
    :param context: Telegram Context
    :return: None
    '''
    global config
    if update.effective_user.id not in config["admins"]:
        return
    logging.info("Update from id: {}".format(update.effective_user.id))
    if len(context.args) != 1 or not context.args[0].isdigit():
        update.message.reply_text("/deauthorize <telegram_user_id>")
    user_id = int(context.args[0])
    if user_id in config["admins"]:
        config["admins"].remove(user_id)
        save_config()
        update.message.reply_text("user {} removed as admin successfully!".format(user_id))
    else:
        update.message.reply_text("user {} is not an admin!".format(user_id))


def logs_callback(update, context):
    '''
    Callback that sends logs to an admin
    :param update: Telegram Update
    :param context: Telegram Context
    :return: None
    '''
    global config
    if update.effective_user.id not in config["admins"]:
        return
    logging.info("Update from id: {}".format(update.effective_user.id))
    with open("bot.log", 'rb') as x:
        update.message.reply_document(document=x)


def main_job(context):
    '''
    Handles the operation with mentions on Twitter, and answers "Saved!" with a tg link.
    :param context: TG bot context
    :return: nothing
    '''
    global config, api
    last_id = config["lastID"]
    mentions = api.GetMentions(count=200, since_id=last_id, )
    while len(mentions) != 0:
        for mention in mentions:
            last_id = mention.id
            config["lastID"] = last_id
            use = add_use(mention.user.id)
            save_config()
            if use:
                # trying to save the reply if exists
                if mention.in_reply_to_status_id is not None:
                    msg = api.GetStatus(mention.in_reply_to_status_id)
                else:
                    msg = mention
                # trying to save the commented RT if this tweet has no media
                commented_retweet = get_commented_retweet(msg)
                if msg.media is None and commented_retweet is not None:
                    msg = commented_retweet
                # saving tweet for debugging
                json.dump(msg.AsDict(), m)
                m.flush()
                tg = save_in_telegram(msg, context)
                if tg is None:
                    logging.info("error saving in telegram")
                    continue
                confirm_save(mention.id, tg.link)
            elif use is False:
                confirm_error(mention.id,
                              "Hiciste muchos intentos en muy poco tiempo. "
                              "Intenta de nuevo en unos minutos o dile a otro usuario que "
                              "archive el video.")
        mentions = api.GetMentions(count=200, since_id=last_id)


def get_best_variant(variants):
    '''
    Returns the best variant for a video
    :param variants: Array with video variants
    :return: A URL with the best variant
    '''
    bitrate = 0
    url = ""
    for v in variants:
        if ("bitrate" not in v and bitrate == 0) or ("bitrate" in v and v["bitrate"] > bitrate):
            bitrate = v["bitrate"] if "bitrate" in v else 0
            url = v["url"]
    if len(url) > 0:
        r = requests.get(url, stream=True)
        if r.status_code < 400:
            return r.raw
    return None


def confirm_save(original_id, tg_url):
    '''
    Post into Twitter the link to Telegram, replying to original message
    :param tg_url:
    :return:
    '''
    global api
    try:
        api.PostUpdate("¡Guardado! 👍 {}".format(tg_url), in_reply_to_status_id=original_id,
                       auto_populate_reply_metadata=True)
    except Exception as e:
        logging.info(e)


def confirm_error(original_id, msg):
    '''
    Reply to message when an error has occured.
    :param original_id: status id to reply
    :param msg: error message
    :return:
    '''
    global api
    try:
        api.PostUpdate("Lo siento, no pude guardar esto. {}".format(msg), in_reply_to_status_id=original_id,
                       auto_populate_reply_metadata=True)
    except Exception as e:
        logging.info(e)


def get_geo(twitter_msg):
    '''
    Generates GoogleMap link if msg has location data.
    :param twitter_msg: Twitter Status Object
    :return: string with gm link if possible or empty string otherwise
    '''
    try:
        x, y = twitter_msg.place["bounding_box"]["coordinates"][0][0]
        return "https://www.google.com/maps/place/{},{}".format(y, x)
    except Exception as e:
        return ""


def save_in_telegram(twitter_msg, context):
    '''
    Saves a tweet and video in Telegram (with a archive.is link)
    :param twitter_msg: Twitter Status Object
    :param context: Telegram bot context
    :return: nothing
    '''
    save_media_hash_set()
    
    tweet_url = "https://www.twitter.com/{}/status/{}".format(
        twitter_msg.user.screen_name, twitter_msg.id)
    logging.info("Saving tweet {}".format(tweet_url))
    if twitter_msg.media is not None:
        saved_url = save_in_archive(tweet_url)
        location = get_geo(twitter_msg)
        caption = "{} {}".format(saved_url, location)
        if saved_url is not None:
            # Individual file
            if len(twitter_msg.media) == 1:
                m = twitter_msg.media[0]
                if m.id not in media_hash:
                    media_hash.add(m.id)
                    if m.type == "photo":
                        return context.bot.send_photo(config["telegram"]["chatid"],
                                                    m.media_url_https,
                                                    disable_notification=True,
                                                    caption=caption)
                    elif m.type == "video":
                        best_variant = get_best_variant(m.video_info["variants"])
                        if best_variant is not None:
                            return context.bot.send_video(config["telegram"]["chatid"],
                                                        best_variant,
                                                        disable_notification=True,
                                                        caption=saved_url)

            elif len(twitter_msg.media) > 1:
                mediaArr = []
                for m in twitter_msg.media:
                    if m.id not in media_hash:
                        media_hash.add(m.id)
                        if m.type == "photo":
                            mediaArr.append(telegram.InputMediaPhoto(media=m.media_url_https,
                                                                    caption=saved_url))
                        elif m.type == "video":
                            best_variant = get_best_variant(
                                m.video_info["variants"])
                            if best_variant is not None:
                                mediaArr.append(telegram.InputMediaVideo(media=best_variant,
                                                                        caption=saved_url))
                resps = context.bot.send_media_group(config["telegram"]["chatid"],
                                                     mediaArr,
                                                     disable_notification=True)
                if len(resps) > 0:
                    return resps[0]
        else:
            logging.info("error saving tweet {}")


def load_config():
    '''
    Loads the config on a global var from config.json
    :return: nothing
    '''
    global config
    try:
        config = json.load(open("config.json"))
        if "lastID" not in config:
            config["lastID"] = 1
        if "users" not in config:
            config["users"] = {}
        if "admins" not in config:
            config["admins"] = []
    except Exception as e:
        logging.info("config.json not found")
        exit(1)


def save_config():
    '''
    Saves global config into config.json file
    :return:
    '''
    global config
    try:
        json.dump(config, open("config.json", 'w'))
    except Exception as e:
        logging.info("cannot save config.json", e)
        exit(1)


commands = {
    'ban': ban_callback,
    'unban': unban_callback,
    'myid': myid_callback,
    'deltweet': deltweet_callback,
    'mentions': mentions_callback,
    'status': status_callback,
    'authorize': authorize_callback,
    'deauthorize': deauthorize_callback,
    'logs': logs_callback,
}
if __name__ == "__main__":
    load_config()
    api = twitter.Api(consumer_key=config["twitter"]["consumerKey"],
                      consumer_secret=config["twitter"]["consumerSecret"],
                      access_token_key=config["twitter"]["accessTokenKey"],
                      access_token_secret=config["twitter"]["accessTokenSecret"], tweet_mode="extended")
    updater = Updater(config["telegram"]["token"], use_context=True)
    media_hash = load_media_hash_set()
    queue = updater.job_queue
    queue.run_repeating(main_job, interval=60, first=0)
    for cmd, callback in commands.items():
        handler = CommandHandler(cmd, callback)
        updater.dispatcher.add_handler(handler)
    updater.start_polling()
