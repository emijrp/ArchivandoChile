from datetime import datetime
import logging

import admin
import tweets

import config
import decorators


@decorators.check_admin
def ban_callback(update, context):
    """
    Callback to ban a Twitter user
    :param update: Telegram Update
    :param context: Telegram Context
    :return: None
    """
    logging.info("Update from id: {}".format(update.effective_user.id))
    if len(context.args) != 1:
        update.message.reply_text("/ban <twitter_screen_name>")
    user = tweets.get_twitter_user_by_name(context.args[0])
    if user is not None:
        admin.ban(user.id)
        update.message.reply_text("User banned! id={}, screen_name={}".format(user.id, user.screen_name))
    else:
        update.message.reply_text("User with screen_name={} not found".format(user.screen_name))


@decorators.check_admin
def unban_callback(update, context):
    """
    Callback that unbans an user from the system
    :param update: Telegram Update
    :param context: Telegram Context
    :return: None
    """
    logging.info("Update from id: {}".format(update.effective_user.id))
    if len(context.args) != 1:
        update.message.reply_text("/unban <twitter_screen_name>")
    user = tweets.get_twitter_user_by_name(context.args[0])
    if user is not None:
        admin.unban(user.id)
        update.message.reply_text("User unbanned! id={}, screen_name={}".format(user.id, user.screen_name))
    else:
        update.message.reply_text("User with screen_name={} not found".format(user.screen_name))


def myid_callback(update, _):
    """
    Callback that returns users ID
    :param update: Telegram Update
    :param _: Telegram Context, unused.
    :return:  None
    """
    update.message.reply_text("Your id is {}".format(update.effective_user.id))


@decorators.check_admin
def status_callback(update, context):
    """
    Callback to send an admin a user status report
    :param update: Telegram Update
    :param context: Telegram Context
    :return: None
    """
    logging.info("Update from id: {}".format(update.effective_user.id))
    if len(context.args) != 1:
        update.message.reply_text("/unban <twitter_screen_name>")
    user = tweets.get_twitter_user_by_name(context.args[0])
    if user is not None and str(user.id) in config.config["users"]:
        c = config.config["users"][str(user.id)]
        status = """User Status:
        id={}
        screen_name={}
        banned={}
        last_use={}
        uses={}
        tries={}
        time_threshold={}
        max_uses={}
        max_tries={}
        """.format(user.id,
                   user.screen_name,
                   c["banned"],
                   datetime.fromtimestamp(c["last_use"]).strftime('%Y-%m-%d %H:%M:%S'),
                   c["uses"],
                   c["tries"],
                   config.TIME_LIMIT,
                   config.MAX_USES,
                   config.MAX_TRIES)
        update.message.reply_text(status)
    else:
        update.message.reply_text("User with screen_name={} not found".format(user.screen_name))


@decorators.check_admin
def mentions_callback(update, _):
    """
    Callback used to send to an admin mentions file
    :param update: Telegram Update.
    :param _: Telegram Context, unused.
    :return: None
    """
    logging.info("Update from id: {}".format(update.effective_user.id))
    with open("mentions.json", 'rb') as x:
        update.message.reply_document(document=x)


@decorators.check_admin
def deltweet_callback(update, context):
    """
    Callback used for deleting a tweet
    :param update:  Telegram Update
    :param context:  Telegram Context
    :return: None
    """
    if len(context.args) != 1:
        update.message.reply_text("/deltweet <twitter_status_id>")
    status_id = context.args[0]
    if "twitter.com" in status_id or "http" in status_id:
        status_id = status_id.strip("/").split("/")[-1]
    if status_id.isdigit():
        config.api.DestroyStatus(status_id)
        update.message.reply_text("Tweet deleted successfully!")
    else:
        update.message.reply_text("status_id is not a number or URL")


@decorators.check_admin
def authorize_callback(update, context):
    """
    Callback used for authorizing a user as admin.
    :param update: Telegram Update
    :param context: Telegram Context
    :return: None
    """
    logging.info("Update from id: {}".format(update.effective_user.id))
    if len(context.args) != 1 or not context.args[0].isdigit():
        update.message.reply_text("/authorize <telegram_user_id>")
    user_id = int(context.args[0])
    if user_id not in config.config["admins"]:
        config.config["admins"].append(user_id)
        config.save_config()
        update.message.reply_text("user {} added as admin successfully!".format(user_id))
    else:
        update.message.reply_text("user {} is already an admin!".format(user_id))


@decorators.check_admin
def deauthorize_callback(update, context):
    """
    Callback used for deauthorising a user as admin.
    :param update: Telegram Update
    :param context: Telegram Context
    :return: None
    """
    logging.info("Update from id: {}".format(update.effective_user.id))
    if len(context.args) != 1 or not context.args[0].isdigit():
        update.message.reply_text("/deauthorize <telegram_user_id>")
    user_id = int(context.args[0])
    if user_id in config.config["admins"]:
        config.config["admins"].remove(user_id)
        config.save_config()
        update.message.reply_text("user {} removed as admin successfully!".format(user_id))
    else:
        update.message.reply_text("user {} is not an admin!".format(user_id))


@decorators.check_admin
def logs_callback(update, _):
    """
    Callback that sends logs to an admin
    :param update: Telegram Update
    :param _: Telegram Context, unused
    :return: None
    """
    logging.info("Update from id: {}".format(update.effective_user.id))
    with open("bot.log", 'rb') as x:
        update.message.reply_document(document=x)
