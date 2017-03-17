import requests
import parsing
from globalvars import GlobalVars
import time
import HTMLParser
from classes import Post


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

    item = response['items'][0]
    h = HTMLParser.HTMLParser()
    post_struct = {'question_id': post_id, 'link': parsing.url_to_shortlink(item['link']), 'post_type': post_type,
                   'title': h.unescape(item['title']), 'site': site, 'body': item['body'], 'score': item['score'],
                   'up_vote_count': item['up_vote_count'], 'down_vote_count': item['down_vote_count']}

    if 'owner' in item and 'link' in item['owner']:
        post_struct['owner'] = {'display_name': h.unescape(item['owner']['display_name']),
                                'link': item['owner']['link'],
                                'reputation': item['owner']['reputation']}
    if post_type == "answer":
        post_struct['question_id'] = item['question_id']

    return Post(api_response=post_struct)
