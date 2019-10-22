import logging

import archive
import telegram

import config
import tweets


def save_in_telegram(twitter_msg, context):
    """
    Saves a tweet and video in Telegram (with a archive.is link)
    :param twitter_msg: Twitter Status Object
    :param context: Telegram bot context
    :return: nothing
    """
    tweet_url = "https://www.twitter.com/{}/status/{}".format(
        twitter_msg.user.screen_name, twitter_msg.id)
    logging.info("Saving tweet {}".format(tweet_url))
    if twitter_msg.media is not None:
        saved_url = archive.save_in_archive(tweet_url)
        location = tweets.get_geo(twitter_msg)
        caption = "{} {}".format(saved_url, location)
        if saved_url is not None:
            # Individual file
            if len(twitter_msg.media) == 1:
                m = twitter_msg.media[0]
                if m.type == "photo":
                    return context.bot.send_photo(config.config["telegram"]["chatid"],
                                                  m.media_url_https,
                                                  disable_notification=True,
                                                  caption=caption)
                elif m.type == "video":
                    best_variant = tweets.get_best_variant(m.video_info["variants"])
                    if best_variant is not None:
                        return context.bot.send_video(config.config["telegram"]["chatid"],
                                                      best_variant,
                                                      disable_notification=True,
                                                      caption=saved_url)

            elif len(twitter_msg.media) > 1:
                mediaArr = []
                for m in twitter_msg.media:
                    if m.type == "photo":
                        mediaArr.append(telegram.InputMediaPhoto(media=m.media_url_https,
                                                                 caption=saved_url))
                    elif m.type == "video":
                        best_variant = tweets.get_best_variant(
                            m.video_info["variants"])
                        if best_variant is not None:
                            mediaArr.append(telegram.InputMediaVideo(media=best_variant,
                                                                     caption=saved_url))
                resps = context.bot.send_media_group(config.config["telegram"]["chatid"],
                                                     mediaArr,
                                                     disable_notification=True)
                if len(resps) > 0:
                    return resps[0]
        else:
            logging.info("error saving tweet {}")
