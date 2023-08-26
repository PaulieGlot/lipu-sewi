def get_verse(section, book, chapter, verse):
    filename = "%s/%s/%s.txt" % (section, book, f"{chapter:04}")
    try: file = open(filename)
    except FileNotFoundError: return "error fetching verse: chapter file `%s` does not exist.\n\tcheck chapters.txt to see if it should!\n" % filename
    for line in file:
        prefix = "%i: " % verse
        if line.startswith(prefix):
            return line
    return "error fetching verse: chapter file `%s` contains no verse numbered %i.\n\tbe sure you are using the same numbering system as this version, and that a translation has been supplied for the requested verse.\n" % (filename, verse)


# pull all completed verses and errors when requested verses aren't found (somewhat slower)
def check_verse_range(section, book, chapter, start_verse, end_verse):
    text = ""
    for verse in range(start_verse, end_verse+1):
        text += get_verse(section, book, chapter, verse)
    return text


# quickly pull all completed verses within a chapter
def get_chapter(section, book, chapter):
    filename = "%s/%s/%s.txt" % (section, book, f"{chapter:04}")
    try: file = open(filename)
    except FileNotFoundError: return "error fetching chapter: chapter file `%s` does not exist.\n\tcheck chapters.txt to see if it should!\n" % filename
    text = ""
    for line in file:
        text += line
    return text


# quickly pull all completed verses within a range
def get_verse_range(section, book, chapter, start_verse, end_verse):
    filename = "%s/%s/%s.txt" % (section, book, f"{chapter:04}")
    try: file = open(filename)
    except FileNotFoundError: return "error fetching verse range: chapter file `%s` does not exist.\n\tcheck chapters.txt to see if it should!\n" % filename
    text = ""
    current_verse = start_verse
    for line in file:
        prefix = int(line.split(":")[0])
        if prefix >= start_verse:
            text += line
        if prefix > end_verse:
            break
    if text == "":
        return "error fetching verse range: chapter file `%s` contains no verses within the range %i - %i.\n\tbe sure you are using the same numbering system as this version, and that translations have been supplied for verses in the requested range.\n" % (filename, start_verse, end_verse)
    return text


print(check_verse_range("Old Testament", "Genesis", 1, 1, 40))