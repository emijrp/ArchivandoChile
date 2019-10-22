import archiveis


def save_in_archive(url):
    """
    Saves an URL in archive.is
    :param url: URL to save
    :return: URL in archive.is
    """
    return archiveis.capture(url)
