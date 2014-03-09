""" Utilities. """
import sys
import hashlib
import os
import struct
import termios
import fcntl
from urllib.request import urlretrieve
from math import ceil


def levenshtein(x, y):
    """ Get the levenshtein edit distance between y strings. """
    if len(x) < len(y):
        return levenshtein(y, x)
    if len(y) == 0:
        return len(x)
    previous_row = range(len(y) + 1)
    for i, k in enumerate(x):
        current_row = [i + 1]
        for j, l in enumerate(y):
            insertions = previous_row[
                j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (k != l)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]


def list_names(array, word=', ', last_word=' and '):
    """ Human readable list of the names.

    This function displays the array in a human readable form. It will separate
    the first elements by the `word`, and the last element will have the
    `last_word` before it.

    Example returned string:
        one, two and three

    """
    if len(array) > 1:
        return (word.join([str(i) for i in array[:-1]]) + last_word +
                str(array[-1]))
    elif len(array) == 1:
        return array[0]


def download(url, file_name=None, checksum=None, prefix='',
             display_name=None):
    """ Download with progressbar. """
    if file_name is None:
        file_name = url.split('/')[-1]
    if display_name is None:
        display_name = file_name

    term_width = get_term_width()
    pprefix = prefix + display_name
    progress = create_progress_bar(prefix=pprefix, width=term_width)
    urlretrieve(url, filename=file_name, reporthook=progress)

    if checksum is not None and len(checksum) > 0:
        print('\n' + ' ' * len(prefix) + 'Checking checksum...', end=' ')
        actual_checksum = checksum_file(file_name)
        if actual_checksum == checksum:
            print('Sucess')
        else:
            os.remove(file_name)
            print('The checksums did not match! The file was deleted.')


def create_progress_bar(width, prefix=None):
    """ Create a progress bar. """
    left = ceil(width/2)
    right = width-left
    net_bar_size = right-8
    char_size = net_bar_size/100
    frmt = '{{prefix:<{}}}[{{bar_left}}{{bar_right}}] {{prc}}%\r'.format(left)
    last_percent = -1

    def progress_hook(count, blocksize, totalsize):
        """ Progress hook. """
        percent = min(ceil(count*blocksize*100/totalsize), 100)
        nonlocal last_percent
        if percent == last_percent:
            return
        else:
            last_percent = percent
        fill_size = int(char_size*percent)
        empty_size = net_bar_size-fill_size
        text = frmt.format(prefix=prefix,
                           bar_left=('='*(fill_size-1)+'>' if percent < 100
                                     else '='*fill_size),
                           bar_right=' '*empty_size,
                           prc=percent)

        sys.stdout.write(text)
        sys.stdout.flush()
    return progress_hook


def checksum_file(file_name):
    """ MD5 Checksum of file with name `file_name`. """
    return hashlib.md5(open(file_name, 'rb').read()).hexdigest()


def replace_last(string, old, new):
    """ Replace the last occurance of `old` in `string` with `new`. """
    string = string.rsplit(old, 1)
    return new.join(string)


def get_term_width(term=1):
    """ Get the width of the terminal.

    This tries to exctract the width with fcntl.ioctl. If that failes the
    standard width 80 is returned.

    """
    try:
        return struct.unpack('hh', fcntl.ioctl(term,
                                               termios.TIOCGWINSZ,
                                               '1234'))[1]
    except BaseException:
        return 80


def extract_file(zipped, file, dest):
    """ Extract file from ZipFile archive to file.

    This function takes three arguments:
        zipped    The ZipFile to extract the file from.
        file      The path in the ZipFile to the file to extract.
        dest      The path in the filesystem to the destination.

    This function will extract the file in `file` in the zip archive to the
    file in `dest` in the filesystem. Folders are handled correctly, too.

    """
    if file.endswith('/'):
        if os.path.exists(dest):
            if not os.path.isdir(dest):
                os.remove(dest)
            else:
                return
        os.makedirs(dest)
    else:
        content = zipped.read(file)
        with open(dest, 'wb') as dest:
            dest.write(content)