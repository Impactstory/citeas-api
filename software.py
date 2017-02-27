import requests
import re
import os
from io import StringIO
from HTMLParser import HTMLParser
from citeproc.source.json import CiteProcJSON
from citeproc import CitationStylesStyle
from citeproc import CitationStylesBibliography
from citeproc import formatter
from citeproc import Citation
from citeproc import CitationItem
from citeproc_styles import get_style_filepath

from bibtex import BibTeX  # use local patched version instead of citeproc.source.bibtex
from nameparser import HumanName


class NotFoundException(Exception):
    pass

def get_nonempty_contents(filename_list, github_base_url):
    for filename in filename_list:
        url = u"{}/raw/master/{}".format(github_base_url, filename)
        print "looking for filename", url
        r = requests.get(url, timeout=5)
        print "done"
        if r.status_code == 200:
            return r.text
    return None

def get_concatenation(filename_list, github_base_url):
    response = ""
    for filename in filename_list:
        url = u"{}/raw/master/{}".format(github_base_url, filename)
        print u"getting {}".format(url)
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            response += u"\n{}".format(r.text)
    return response

def extract_bibtex(text):
    try:
        result = re.findall(ur"(@.+{.+})", text, re.MULTILINE | re.DOTALL)[0]
    except IndexError:
        result = None
    return result


def get_readme_and_citation_concat(github_base_url):
    readme = None
    readme = get_concatenation(["README", "README.md", "CITATION", "CITATION.md"], github_base_url)
    return readme


def author_name_as_dict(literal_name):
    if len(literal_name.split(" ")) > 1:
        name_dict = HumanName(literal_name).as_dict()
        response_dict = {
            "family": name_dict["last"],
            "given": name_dict["first"],
            "suffix": name_dict["suffix"]
        }
    else:
        response_dict = {"family": literal_name}

    return response_dict

def get_bib_source_from_dict(data):
    data["id"] = "ITEM-1"
    id = "ITEM-1"

    if "bibtex" in data:
        del data["bibtex"]

    for k, v in data.iteritems():
        if k=="author":
            author_list = []
            for name_dict in v:
                new_name_dict = {}
                for name_k, name_v in name_dict.iteritems():
                    if name_k == "literal":
                        new_name_dict = author_name_as_dict(name_v)
                    else:
                        new_name_dict[name_k] = name_v
                author_list.append(new_name_dict)
            data["author"] = author_list

    bib_source = CiteProcJSON([data])

    return bib_source



def find_zenodo_doi(text):
    if text and "zenodo" in text:
        try:
            text = text.lower()
            return re.findall("://zenodo.org/badge/doi/(.+?).svg", text, re.MULTILINE)[0]
        except IndexError:
            pass
    return None



class Software(object):
    def __init__(self):
        self.url = None
        self.doi = None
        self.metadata = {}
        self.bib_source = None
        self.github_api_raw = None
        self.github_user_api_raw = None
        self.citation_style = "harvard1"


    @property
    def doi_url(self):
        if self.doi:
            return u"http://doi.org/{}".format(self.doi)
        return None

    @property
    def display_url(self):
        if self.url:
            return self.url
        if self.doi_url:
            return self.doi_url
        return None


    @property
    def has_github_url(self):
        return self.url and "github.com" in self.url

    @property
    def owner_login(self):
        if not self.has_github_url:
            return
        if not self.github_api_raw:
            self.set_github_api_raw()
        return self.github_api_raw["owner"]["login"]

    @property
    def owner_name(self):
        if not self.has_github_url:
            return
        if not self.github_user_api_raw:
            self.set_github_user_api_raw()
        return self.github_user_api_raw["name"]

    @property
    def repo_name(self):
        if not self.has_github_url:
            return
        if not self.github_api_raw:
            self.set_github_api_raw()
        return self.github_api_raw["name"]

    @property
    def year(self):
        if not self.has_github_url:
            return
        if not self.github_api_raw:
            self.set_github_api_raw()
        return self.github_api_raw["created_at"][0:4]


    def find_doi(self):
        if self.doi:
            return
        if self.has_github_url:
            self.doi = find_zenodo_doi(get_readme_and_citation_concat(self.url))


    def find_citeas_request_in_github_repo(self):
        request_text = None
        if self.has_github_url:
            request_text = get_readme_and_citation_concat(self.url)
            return extract_bibtex(request_text)
        return None

    def get_github_token_tuple(self):
        tokens_str = os.environ["GITHUB_TOKENS"]
        tokens = [t.split(":") for t in tokens_str.split(",")]
        (login, token) = tokens[0]
        return (login, token)

    def set_github_api_raw(self):
        if not self.has_github_url:
            return
        api_url = self.url.replace("github.com/", "api.github.com/repos/")
        h = {"User-Agent": "CiteAs"}
        (login, token) = self.get_github_token_tuple()
        r = requests.get(api_url, auth=(login, token), headers=h)
        self.github_api_raw = r.json()

    def set_github_user_api_raw(self):
        if not self.has_github_url:
            return
        api_url = "https://api.github.com/users/{}".format(self.owner_login)
        h = {"User-Agent": "CiteAs"}
        (login, token) = self.get_github_token_tuple()
        r = requests.get(api_url, auth=(login, token), headers=h)
        self.github_user_api_raw = r.json()

    def set_metadata(self):
        if self.doi_url:
            self.set_metadata_from_doi()
        elif self.has_github_url:
            bibtex = self.find_citeas_request_in_github_repo()
            if bibtex:
                self.set_metadata_from_bibtex(bibtex)
            else:
                self.set_metadata_from_github_biblio()

        if not self.metadata:
            self.metadata = {}
            self.metadata["type"] = "misc"
            self.metadata["URL"] = self.url

    def set_metadata_from_bibtex(self, bibtex):
        bibtext_string = u"{}".format(bibtex)
        bib_dict = BibTeX(StringIO(bibtext_string))
        id = bib_dict.keys()[0]
        if "month" in bib_dict[id]:
            del bib_dict[id]["month"]
        self.metadata = dict(bib_dict[id].items())
        self.metadata["bibtex"] = bibtex


    def set_metadata_from_doi(self):
        headers = {'Accept': 'application/rdf+xml;q=0.5, application/vnd.citationstyles.csl+json;q=1.0'}
        r = requests.get(self.doi_url, headers=headers)
        self.metadata = r.json()


    def set_metadata_from_github_biblio(self):
        self.metadata = {}
        self.metadata["title"] = self.repo_name
        self.metadata["author"] = [author_name_as_dict(self.owner_name)]
        self.metadata["publisher"] = "GitHub repository"
        self.metadata["URL"] = self.url
        self.metadata["issued"] = {"date-parts": [[self.year]]}
        self.metadata["type"] = "software"


    def set_bib_source(self):
        self.find_doi()
        self.set_metadata()
        self.bib_source = get_bib_source_from_dict(self.metadata)


    def display_citation(self, bib_stylename):
        # valid style names: plos, apa, pnas, nature, bmj, harvard1
        # full list is here: https://github.com/citation-style-language/styles

        style_path = get_style_filepath(bib_stylename)
        bib_style = CitationStylesStyle(style_path, validate=False)

        bibliography = CitationStylesBibliography(bib_style, self.bib_source, formatter.html) #could be formatter.html
        id = "ITEM-1"
        citation = Citation([CitationItem(id)])
        bibliography.register(citation)

        try:
            citation_parts = u"".join(bibliography.bibliography()[0])
            citation_text = u"".join(citation_parts)
        except Exception:
            print "Error parsing bibliography, so no bibliography for now"
            citation_text = str(self.bib_source["bibtex"])

        html_parser = HTMLParser()
        citation_text = html_parser.unescape(citation_text)

        return citation_text


    def __repr__(self):
        return u"<Software ({})>".format(self.url)

    def to_dict(self):
        response = {
            "url": self.display_url,
            "doi": self.doi,
            "citation": self.display_citation(self.citation_style),
            "metadata": self.metadata
        }
        return response



