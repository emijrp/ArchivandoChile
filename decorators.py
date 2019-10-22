import config


def check_admin(func):
    """
    Checks if user executing a callback is an admin
    :param func: function to execute
    :return: a function which checks the permissions
    """

    def checking(update, context):
        if update.effective_user.id not in config.config["admins"]:
            return
        func(update, context)

    return checking
