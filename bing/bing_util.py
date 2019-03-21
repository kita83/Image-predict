import os
import re

def make_dir(path):
    if not os.path.isdir(path):
        os.mkdir(path)

def search_term2file_name(search_term):
    return re.sub('\s+', '_', search_term)
