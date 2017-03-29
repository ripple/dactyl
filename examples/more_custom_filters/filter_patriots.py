## 'Patriots' custom filter v2

def filter_markdown(md, **kwargs):
    s = md.replace("patriots", "la-li-lu-le-lo")
    return s.replace("Patriots", "La-Li-Lu-Le-Lo")
