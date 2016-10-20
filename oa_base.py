import os
import requests
from time import time
from collections import defaultdict

import oa_local
from util import elapsed
from util import normalize

def base_url_sort_score(url):
    # sometimes base returns just this.  don't use this url.
    if url=="http://www.ncbi.nlm.nih.gov/pmc/articles/PMC":
        return 10

    # sometimes the base doi isn't actually open, like in this record:
    # https://www.base-search.net/Record/9b574f9768c8c25d9ed6dd796191df38a865f870fde492ee49138c6100e31301/
    # so sort doi down in the list
    if "doi.org" in url:
        return 1

    # pmc results are better than IR results, if we've got them
    if "/pmc/" in url:
        return -2

    # otherwise whatever we've got
    return -1


def pick_best_base_url(urls):
    return sorted(urls, key=lambda x:base_url_sort_score(x))[0]

def call_base(products):
    if not products:
        print "empty product list so not calling base"
        return

    titles = []
    # may be more than one product for a given title, so is a dict of lists
    titles_to_products = defaultdict(list)

    for p in products:
        p.license_string = ""
        p.base_dcoa = None
        p.repo_urls = {"urls": []}

        title = p.best_title
        titles_to_products[normalize(title)].append(p)

        title = title.lower()
        # can't just replace all punctuation because ' replaced with ? gets no hits
        title = title.replace('"', "?")
        title = title.replace('#', "?")
        title = title.replace('=', "?")
        title = title.replace('&', "?")
        title = title.replace('%', "?")
        title = title.replace('-', "*")

        # only bother looking up titles that are at least 3 words long
        title_words = title.split()
        if len(title_words) >= 3:
            # only look up the first 12 words
            title_to_query = u" ".join(title_words[0:12])
            titles.append(title_to_query)

    # now do the lookup in base
    titles_string = u"%20OR%20".join([u'%22{}%22'.format(title) for title in titles])
    # print u"{}: calling base with query string of length {}, utf8 bits {}".format(self.id, len(titles_string), 8*len(titles_string.encode('utf-8')))
    url_template = u"https://api.base-search.net/cgi-bin/BaseHttpSearchInterface.fcgi?func=PerformSearch&query=(dcoa:1%20OR%20dcoa:2)%20AND%20dctitle:({titles_string})&fields=dctitle,dccreator,dcyear,dcrights,dcprovider,dcidentifier,dcoa,dclink&hits=100000&format=json"
    url = url_template.format(titles_string=titles_string)

    # print u"calling base with {}".format(url)

    start_time = time()
    proxy_url = os.getenv("STATIC_IP_PROXY")
    proxies = {"https": proxy_url}
    r = None
    try:
        r = requests.get(url, proxies=proxies, timeout=6)
        # print u"** querying with {} titles took {}s".format(len(titles), elapsed(start_time))
    except requests.exceptions.ConnectionError:
        print u"connection error in set_fulltext_urls, skipping."
    except requests.Timeout:
        print u"timeout error in set_fulltext_urls, skipping."

    if r != None and r.status_code != 200:
        print u"problem searching base! status_code={}".format(r.status_code)
        for p in products:
            p.base_dcoa = u"base query error: status_code={}".format(r.status_code)

    else:
        try:
            data = r.json()["response"]
            # print "number found:", data["numFound"]
            for doc in data["docs"]:
                base_dcoa = str(doc["dcoa"])
                try:
                    matching_products = titles_to_products[normalize(doc["dctitle"])]
                except KeyError:
                    matching_products = []
                for p in matching_products:
                    if base_dcoa == "1":
                        # got a 1 hit.  yay!  overwrite no matter what.
                        p.fulltext_url = pick_best_base_url(doc["dcidentifier"])
                        p.open_step = "oa repository (via base-search.net oa url)"
                        p.repo_urls["urls"] = {}
                        p.base_dcoa = base_dcoa
                        if "dcrights" in doc:
                            p.license_string += u"{};".format(doc["dcrights"])
                    elif base_dcoa == "2" and p.base_dcoa != "1":
                        # got a 2 hit.  use only if we don't already have a 1.
                        p.repo_urls["urls"] += doc["dcidentifier"]
                        p.base_dcoa = base_dcoa
        except ValueError:  # includes simplejson.decoder.JSONDecodeError
            print u'decoding JSON has failed base response'
            for p in products:
                p.base_dcoa = u"base lookup error: json response parsing"
        except AttributeError:  # no json
            # print u"no hit with title {}".format(doc["dctitle"])
            # print u"normalized: {}".format(normalize(doc["dctitle"]))
            pass

    for p in products:
        if p.license_string:
            p.license = oa_local.find_normalized_license(p.license_string)


    print u"finished base step of set_fulltext_urls with {} titles in {}s".format(
        len(titles_to_products), elapsed(start_time, 2))
