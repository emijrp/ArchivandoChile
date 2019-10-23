import json
import logging

import admin
import config
import tweets
from tg import save_in_telegram
from tweets import confirm_save, confirm_error


def main_job(context):
    """
    Detects mentions in twitter and saves them in Telegram.
    :param context: TG bot context
    :return: nothing
    """
    mentions = config.api.GetMentions(count=200, since_id=config.config["lastID"])
    while len(mentions) != 0:
        for mention in mentions:
            config.config["lastID"] = mention.id
            use = admin.add_use(mention.user.id)
            config.save_config()
            if use:
                # trying to save the reply if exists
                if mention.in_reply_to_status_id is not None:
                    msg = config.api.GetStatus(mention.in_reply_to_status_id)
                else:
                    msg = mention
                # trying to save the commented RT if this tweet has no media
                commented_retweet = tweets.get_commented_retweet(msg)
                if msg.media is None and commented_retweet is not None:
                    msg = commented_retweet
                msg_dict = msg.AsDict()
                if str(msg.id) in config.config["cached"]:
                    msg_dict["archive_url"] = "cached"
                    logging.info("tweet {} is cached! sending cached link".format(msg.id))
                    confirm_save(mention.id, config.config["cached"][str(msg.id)])
                else:
                    tg = save_in_telegram(msg, context)
                    if tg is None:
                        msg_dict["archive_url"] = None
                        logging.info("error saving in telegram")
                    else:
                        msg_dict["archive_url"] = tg.link
                        confirm_save(mention.id, tg.link)
                # saving tweet for debugging
                json.dump(msg_dict, config.m)
                config.m.flush()
            elif use is False:
                confirm_error(mention.id,
                              "Hiciste muchos intentos en muy poco tiempo. "
                              "Intenta de nuevo en unos minutos o dile a otro usuario que "
                              "archive el video.")
        mentions = config.api.GetMentions(count=200, since_id=config.config["lastID"])
