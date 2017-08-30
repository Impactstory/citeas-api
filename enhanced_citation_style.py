from citeproc import CitationStylesStyle
from citeproc_styles import get_style_filepath

class EnhancedCitationStyle(CitationStylesStyle):
    def __init__(self, bib_stylename):
        # valid style names: plos, apa, pnas, nature, bmj, harvard1
        # full list is here: https://github.com/citation-style-language/styles

        self.style_path = get_style_filepath(bib_stylename)
        super(EnhancedCitationStyle, self).__init__(self.style_path, validate=False)

    @property
    def name(self):
        info = self.root.find("{http://purl.org/net/xbiblio/csl}info")
        if info:
            title = info.find("{http://purl.org/net/xbiblio/csl}title")
            print title.text
            return title.text
            # print [elem.text for elem in list(info)]
            # short_title = info.find(u"{http://purl.org/net/xbiblio/csl}title-short")
            # if short_title:
            #     print short_title.text
        # print (etree.tostring(bib_style.xml, pretty_print=True))
        # print bib_style.xml
        return self.style_path


def get_style_name(bib_stylename):
    style_obj = EnhancedCitationStyle(bib_stylename)
    return style_obj.name
