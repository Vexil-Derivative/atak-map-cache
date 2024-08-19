import json
import os
import requests
import warnings
from requests.packages.urllib3.exceptions import InsecureRequestWarning

debug_enabled = True
warnings.simplefilter('ignore',InsecureRequestWarning)


def debug(message):
  if debug_enabled:
    print('[DEBUG] ' + message)


def progress_bar(msg, current, total):
    term_length = os.get_terminal_size().columns
    bar_length = term_length - 20
    progress = int(round(current / total * bar_length, 0))

    # \x1b[K = clear to end of line
    print(msg, end='\x1b[K')
    print()
    # \x1b[1A\r = go up 1 line and to the beginning
    print(f'[{current:<4} of {total}] [' + "-" * progress + ' ' * (bar_length - progress) + ']', end='\x1b[1A\r')


def dl_with_retry(url, max_tries=3):
    success = False
    tries = 1
    # TODO: Create get_with_retry method in utils
    while not success:
        try:
            r = requests.get(url, verify=False)
            if (r.status_code == 200):
                success = True
                return r.content
            elif tries == max_tries:
                print("File could not be downloaded after {max_tries} attempts")
                raise RuntimeError
            else:
                tries = tries + 1
        except SSLError:
            tries = tries + 1
    return r.content


class JSONWithCommentsDecoder(json.JSONDecoder):
    def __init__(self, **kw):
        super().__init__(**kw)

    def decode(self, s: str):
        s = '\n'.join(l for l in s.split('\n') if not l.lstrip(' ').startswith('//'))
        return super().decode(s)
