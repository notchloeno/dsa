import hashlib
import logging
import time

clock = time.time()


def check_time():
    logging.debug("{}s since last clock reset")


def start_stopwatch():
    logging.debug("Starting timing...")


def get_file_md5_hash(filename: str) -> bytes:
    """
    Returns digest of the MD5 hash of the given file
    :param filename: Name of the file to be hashed
    :return: A bytes object, which the is the digest of the MD5 of the file
    """
    with open(filename, "r") as file:
        data = file.read()
        return hashlib.md5(data).digest()


def confirm_files_equal(filename_one: str, filename_two: str) -> bool:
    """
    Checks if file one and file two have the same MD5 hash
    :param filename_one: Name of the first file
    :param filename_two: Name of the second file
    :return: True if the files have the same MD5 hash, else False
    """
    a = get_file_md5_hash(filename_one)
    b = get_file_md5_hash(filename_two)
    return True if a == b else False
