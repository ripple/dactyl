################################################################################
## Demote Headers filter                                                      ##
## Author: Rome Reginelli                                                     ##
## Copyright: Ripple Labs, Inc. 2017                                          ##
##                                                                            ##
## Demote all headers one level. This can be useful to make PDF docs render   ##
## a nice link hierarchy if your templates provide category headers at h1 but ##
## your docs individually start at the h1 level.                              ##
################################################################################

DEMOTE_FIELD = "demote_headers_pdf_only"

def filter_html(html, mode="html", target={}, **kwargs):
    if (mode == "html" and
        DEMOTE_FIELD in target and
        target[DEMOTE_FIELD]):
        # Don't bother then
        return html

    html = html.replace("<h5", "<h6")
    html = html.replace("<h4", "<h5")
    html = html.replace("<h3", "<h4")
    html = html.replace("<h2", "<h3")
    html = html.replace("<h1", "<h2")
    return html
