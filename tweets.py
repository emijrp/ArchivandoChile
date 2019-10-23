import logging

import requests

import config


def confirm_save(original_id, tg_url):
    """
    Post into Twitter the link to Telegram, replying to original message
    :param original_id: Original Status ID. Used to answer that status.
    :param tg_url: Telegram URL, where the media was backed up
    :return: None
    """
    '''
        try:
            config.api.PostUpdate("¡Guardado! 👍 {}".format(tg_url), in_reply_to_status_id=original_id,
                                  auto_populate_reply_metadata=True)
        except Exception as e:
            logging.info(e)
    '''
    pass


def confirm_error(original_id, msg):
    """
    Reply to message when an error has occured.
    :param original_id: status id to reply
    :param msg: error message
    :return:
    """
    try:
        config.api.PostUpdate("Lo siento, no pude guardar esto. {}".format(msg),
                              in_reply_to_status_id=original_id,
                              auto_populate_reply_metadata=True)
    except Exception as e:
        logging.info(e)


def get_twitter_user_by_name(name):
    """
    Returns a twitter user by its screen_name or URL.
    :param name: screen name
    :return: None or a User object
    """
    screen_name = name
    if "twitter.com" in screen_name or "http" in screen_name:
        screen_name = screen_name.strip("/").split("/")[-1]
    user = config.api.GetUser(screen_name=screen_name)
    return user


def get_commented_retweet(msg):
    """
    Returns a retweeted tweet if it exists.
    :param msg: the message
    :return: None if the retweet doesn't exist, the retweet if it exists
    """
    if msg.urls is not None:
        for url in msg.urls:
            if "twitter.com" in url.expanded_url and "status" in url.expanded_url:
                status_id = url.expanded_url.strip("/").split("/")[-1]
                if status_id.isdigit():
                    return config.api.GetStatus(int(status_id))
    return None


def get_best_variant(variants):
    """
    Returns the best variant for a video
    :param variants: Array with video variants
    :return: A URL with the best variant
    """
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


def get_geo(twitter_msg):
    """
    Generates GoogleMap link if msg has location data.
    :param twitter_msg: Twitter Status Object
    :return: string with gm link if possible or empty string otherwise
    """
    try:
        x, y = twitter_msg.place["bounding_box"]["coordinates"][0][0]
        return "https://www.google.com/maps/place/{},{}".format(y, x)
    except Exception as e:
        return ""
