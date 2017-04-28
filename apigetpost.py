# coding=utf-8
import requests
import parsing
from globalvars import GlobalVars
import time
import html


def api_get_post(post_url):
    GlobalVars.api_request_lock.acquire()

    # Respect backoff, if we were given one
    if GlobalVars.api_backoff_time > time.time():
        time.sleep(GlobalVars.api_backoff_time - time.time() + 2)
    d = parsing.fetch_post_id_and_site_from_url(post_url)
    if d is None:
        GlobalVars.api_request_lock.release()
        return None
    post_id, site, post_type = d
    if post_type == "answer":
        api_filter = "!FdmhxNQy0ZXsmxUOvWMVSbuktT"
    else:
        assert post_type == "question"
        api_filter = "!)Ehu.SHRfXhu2eCP4p6wd*Wxyw1XouU5qO83b7X5GQK6ciVat"

    request_url = "http://api.stackexchange.com/2.2/{type}s/{post_id}?site={site}&filter={api_filter}&" \
                  "key=IAkbitmze4B8KpacUfLqkw((".format(type=post_type, post_id=post_id, site=site,
                                                        api_filter=api_filter)
    response = requests.get(request_url).json()
    if "backoff" in response:
        if GlobalVars.api_backoff_time < time.time() + response["backoff"]:
            GlobalVars.api_backoff_time = time.time() + response["backoff"]
    if 'items' not in response or len(response['items']) == 0:
        GlobalVars.api_request_lock.release()
        return False
    GlobalVars.api_request_lock.release()

    post_item = Post(api_response=response['items'][0])
    return post_item
