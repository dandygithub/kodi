import re
import base64

BK_SEP = '//_//'
BK_BLOCKS = [
    'JCQhIUAkJEBeIUAjJCRA',
    'QEBAQEAhIyMhXl5e',
    'IyMjI14hISMjIUBA',
    'Xl5eIUAjIyEhIyM=',
    'JCQjISFAIyFAIyM='
]


def parse_streams(salted):
    for bk in BK_BLOCKS:
        salted = salted.replace(BK_SEP + bk, '')
    return re.sub(r'http[^,]+m3u8 or ', '', base64.b64decode(salted[2:]).decode('utf-8'))
