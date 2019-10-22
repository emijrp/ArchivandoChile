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
    last_id = config.config["lastID"]
    mentions = config.api.GetMentions(count=200, since_id=last_id, )
    while len(mentions) != 0:
        for mention in mentions:
            last_id = mention.id
            config.config["lastID"] = last_id
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
                # saving tweet for debugging
                json.dump(msg.AsDict(), config.m)
                config.m.flush()
                tg = save_in_telegram(msg, context)
                if tg is None:
                    logging.info("error saving in telegram")
                else:
                    confirm_save(mention.id, tg.link)
            elif use is False:
                confirm_error(mention.id,
                              "Hiciste muchos intentos en muy poco tiempo. "
                              "Intenta de nuevo en unos minutos o dile a otro usuario que "
                              "archive el video.")
        mentions = config.api.GetMentions(count=200, since_id=last_id)
