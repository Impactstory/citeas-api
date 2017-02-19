#!/usr/bin/python
 # -*- coding: utf-8 -*-

import unittest
from nose.tools import nottest
from nose.tools import assert_equals
from nose.tools import assert_not_equals
from nose.tools import assert_true
import requests
from ddt import ddt, data
import requests_cache

from software import Software

requests_cache.install_cache('my_requests_cache', expire_after=60*60*24*7)  # expire_after is in seconds

test_urls = [
    ("http://cnn.com", "", u'Anon, Available at: http://cnn.com.'),
    ("https://github.com/pvlib/pvlib-python", "10.5281/zenodo.50141", "Holmgren, W. et al., 2016. pvlib-python: 0.3.1. Available at: https://doi.org/10.5281/zenodo.50141."),
    ("https://github.com/gcowan/hyperk", "10.5281/zenodo.160400", "Cowan, G., 2016. Gcowan/Hyperk: Mcp Data Processing Code. Available at: https://doi.org/10.5281/zenodo.160400."),
    ("https://github.com/NSLS-II-XPD/xpdView", "10.5281/zenodo.60479", "Duff, C. & Kaming-Thanassi, J., 2016. xpdView: xpdView initial release. Available at: https://doi.org/10.5281/zenodo.60479."),
    ("https://github.com/impactstory/depsy", "", "Impactstory, 2015. depsy. Available at: https://github.com/impactstory/depsy."),
    ("https://github.com/abianchetti/blick", "", u'Bianchetti, A., 2012. Determinaci\xf3n del di\xe1metro pupilar ocular en tiempo real.'),
    ("https://github.com/jasonpriem/FeedVis", "", u"Priem, J., 2011. FeedVis. Available at: https://github.com/jasonpriem/FeedVis."),
    ("https://github.com/vahtras/loprop", "", u'Vahtras, O., 2014. LoProp for Dalton.'),
    ("https://github.com/cvitolo/r_BigDataAnalytics", "", u'Vitolo, C., 2015. r_BigDataAnalytics v.0.0.1. Available at: https://doi.org/10.5281/zenodo.15722.'),
    ("https://github.com/nicholasricci/DDM_Framework", "", u"Marzolla, M., D'Angelo, G. & Mandrioli, M., 2013. A Parallel Data Distribution Management Algorithm. In Proc. IEEE/ACM International Symposium on Distributed Simulation and Real Time Applications (DS-RT 2013).  Delft, the Netherlands."),
    ("https://github.com/alvarag/LSH-IS", "", u'Arnaiz-Gonz\xe1lez, \xc1. et al., 2016. Instance selection of linear complexity for big data. Knowledge-Based Systems, 107, pp.83\u201395.'),
    # ("https://github.com/sanger-pathogens/mlst_check", "", """"Multilocus sequence typing by blast from de novo assemblies against PubMLST", Andrew J. Page, Ben Taylor, Jacqueline A. Keane, The Journal of Open Source Software, (2016). doi: http://dx.doi.org/10.21105/joss.00118"""),
    # ("https://github.com/AndrasHartmann/rtfractools", "", "Hartmann, A., Mukli, P., Nagy, Z., Kocsis, L., Hermán, P., & Eke, A. (2013). Real-time fractal signal processing in the time domain. Physica A: Statistical Mechanics and Its Applications, 392(1), 89–102. doi:10.1016/j.physa.2012.08.002"),
    # ("https://github.com/magitz/1001", "", "Mavrodiev EV. (2015) 1001 - A tool for binary representations of unordered multistate characters (with examples from genomic data) PeerJ PrePrints 3:e1403 https://dx.doi.org/10.7287/peerj.preprints.1153v1"),
    # ("https://github.com/gregmacfarlane/trucksim_disagg", "", """Macfarlane, G. and Donnelly, R. (2014). A national simulation of freight truck flows."""),
    # ("https://github.com/aimalz/chippr", "", "alz et al, in preparation\footnote{\texttt{https://github.com/aimalz/chippr}}"),
    # ("https://github.com/happynotes/NLDAS2TS", "", """PIHM Analysis Suite developed by Lele Shu, contributions by PIHM and http://www.pihm.psu.edu"""),
    ]

# We request that applications and derivative work cite this as:
# Cite this as
# If you end up using any of the code or ideas you find here in your academic research, please cite me as
# How to cite this software
# To cite this software please use the following BibTex information
# Please cite this software as
# To cite this software:
# To cite this software use:
# Please cite this software:
# Cite this software as:
# If you use this software please, cite the following paper:
# Citation: if you want to cite this software use the following bibtex entry.

@ddt
class MyTestCase(unittest.TestCase):
    _multiprocess_can_split_ = True

    @data(*test_urls)
    def test_the_urls(self, test_data):
        (url, doi, expected) = test_data
        my_software = Software()
        my_software.url = url
        my_software.set_citation()
        assert_equals(my_software.citation, expected)

    @data(*test_urls)
    def test_the_dois(self, test_data):
        (url, doi, expected) = test_data
        if doi:
            my_software = Software()
            my_software.doi = doi
            my_software.set_citation()
            assert_equals(my_software.citation, expected)
