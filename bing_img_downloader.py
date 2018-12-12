# coding: utf-8
import requests
import os
import sys
import re
import hashlib
import json

import bing_util

def get_target(line):
    matchObj=re.match(r"date=(\d{14}), search_term=([^,]+)", line)
    return [matchObj.group(1), matchObj.group(2)]

def download_image(url, timeout=10):
    response = requests.get(url, allow_redirects=True, timeout=timeout)
    if response.status_code != 200:
        error = Exception("HTTP status: %d" % response.status_code)
        raise error

    content_type = response.headers["content-type"]
    if 'image' not in content_type:
        error = Exception("Content-Type: %s" % content_type)
        raise error

    return response.content

def gen_image_md5(image_data):
    return hashlib.md5(image_data).hexdigest()

def save_image_file(img_save_dir, content):
    filename = "%s.jpg" % (gen_image_md5(content))
    filepath = os.path.join(img_save_dir, filename)
    with open(filepath, "wb") as fout:
        fout.write(content)
    return filename

if __name__ == '__main__':

    filepath = sys.argv[1]
    save_dir_path = './bing'
    bing_util.make_dir(save_dir_path)

    file = open(filepath)
    lines = file.readlines()
    file.close()

    [target_date, search_term] =get_target(lines[0].rstrip())
    print (search_term)
    img_save_dir=os.path.join(save_dir_path, '%s_%s' % (bing_util.search_term2file_name(search_term), target_date))

    bing_util.make_dir(img_save_dir)

    correspondence_table = {}

    for url in lines[1:]:
        try:
            url = url.rstrip()
            content = download_image(url)
            filename = save_image_file(img_save_dir, content)
            correspondence_table[url] = filename
            print ("filename:%s" % filename)

        except KeyboardInterrupt:
            break
        except Exception as err:
            print("%s : %s" % (err, url))

    with open(os.path.join(img_save_dir, 'corr_table.json'), mode='w') as f:
        json.dump(correspondence_table, f)
