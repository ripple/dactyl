def include_code(filename, lines="", mark_disjoint="", language=""):
    #TO-DO: Add "start_after" and "end_before" as an alternative to lines
    with open(filename, encoding="utf-8") as f:
        s = f.read()

    # mark_disjoint
    if mark_disjoint == True:
        mark_disjoint = "..."

    if lines:
        use_lines = parse_range(lines)
        s2 = ""
        file_lines = s.split("\n")
        old_i = None
        for i in use_lines:
            if i < 1 or i > len(file_lines):
                raise ValueError("include_code: requested line is out of range: '%s'" % i)
            if old_i != None and mark_disjoint:
                if old_i+1 != i:
                    s2 += mark_disjoint + "\n"
            s2 += file_lines[i-1] + "\n"
            old_i = i
        s = s2

    return "```%s\n%s\n```" % (language, s)

def parse_range(range_string):
    range_list = []
    for x in range_string.split(","):
        part = x.split("-")
        if len(part) == 1:
            range_list.append(int(part[0]))
        elif len(part) == 2:
            range_list += [i for i in range(int(part[0]), int(part[1])+1)]
        else:
            raise ValueError("invalid range: '%s'" % range_string)
    return range_list

export = {
    "include_code": include_code
}
