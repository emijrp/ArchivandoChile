import time

import config


def add_use(user_id):
    """
    Counts an extra use to the system for a user ID
    :param user_id: User ID.
    :return:
    """
    # If first user
    if not str(user_id) in config.config["users"]:
        config.config["users"][str(user_id)] = {
            "last_use": 0,
            "uses": 0,
            "tries": 0,
            "banned": False
        }
    # if is not banned
    if config.config["users"][str(user_id)]["banned"]:
        return None

    elif can_use(user_id):
        config.config["users"][str(user_id)]["uses"] += 1
        config.config["users"][str(user_id)]["last_use"] = time.time()
        return True
    else:
        config.config["users"][str(user_id)]["tries"] += 1
        if config.config["users"][str(user_id)]["tries"] >= config.MAX_TRIES:
            config.config["users"][str(user_id)]["banned"] = True
            return None
        return False


def ban(user_id):
    """
    Allows to ban an user
    :param user_id: User ID
    :return: None
    """
    if not str(user_id) in config.config["users"]:
        config.config["users"][str(user_id)] = {
            "last_use": 0,
            "uses": 0,
            "tries": 0,
            "banned": False
        }
    config.config["users"][str(user_id)]["banned"] = True
    config.save_config()


def unban(user_id):
    """
    allows to unban an user
    :param user_id:
    :return:
    """
    if str(user_id) in config.config["users"]:
        del config.config["users"][str(user_id)]
        config.save_config()


def can_use(user_id):
    """
    Checks if a user can use the system.
    :param user_id:
    :return:
    """
    if config.config["users"][str(user_id)]["banned"]:
        return False
    elif time.time() - config.config["users"][str(user_id)]["last_use"] > config.TIME_LIMIT * 60:
        config.config["users"][str(user_id)]["uses"] = 0
        config.config["users"][str(user_id)]["tries"] = 0
        return True
    elif config.config["users"][str(user_id)]["uses"] < config.MAX_USES:
        return True
    else:
        return False
