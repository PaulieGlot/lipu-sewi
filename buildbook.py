import re
import os

line_number = 0
verse_count = 0
sealed_count = 0
sealed_pattern = re.compile(r"[0-9]+: !")
cobweb_count = 0
cobweb_pattern = re.compile(r"[0-9]+: \?")
bible_dir = 'bible'
books_file_path = '%s/chapters.txt' % bible_dir
fulltext_file_path = '%s/full.md' % bible_dir
books_file = open(books_file_path, 'r')
fulltext_file = open(fulltext_file_path, 'w')
book_lines = books_file.readlines()
section = ""

for line in book_lines:
    line_number += 1
    comment_regex = re.compile("^\\/\\/.*")
    if line == "" or comment_regex.match(line):
        continue
    section_regex = re.compile("^#(.*)$")
    if section_regex.match(line):
        section = section_regex.search(line).group(1)
        section_path = "%s/%s" % (bible_dir, section)
        if not os.path.isdir(section_path):
            os.makedirs(section_path)
        fulltext_file.write("# %s\n" % section)
        continue
    book_regex = re.compile("^([^,]*),([0-9]+)$")
    if book_regex.match(line):
        book = book_regex.search(line).group(1)
        chapters = int(book_regex.search(line).group(2))
        fulltext_file.write("## %s\n" % book)
        book_path = "%s/%s" % (section_path, book)
        if not os.path.isdir(book_path):
            os.makedirs(book_path)
        for chapter in range(chapters):
            chapter += 1
            chapter_path = "%s/%s.txt" % (book_path, f'{chapter:04}')
            chapter_file = open(chapter_path, 'r')
            # append trailing newline to chapter file if nonexistent
            fulltext_file.write("### %s %d\n" % (book, chapter))
            verses = chapter_file.readlines()
            for verse in verses:
                if verse != "":
                    fulltext_file.write("%s\n" % verse)
                    verse_count += 1
                    if cobweb_pattern.match(verse):
                        cobweb_count += 1
                    elif sealed_pattern.match(verse):
                        sealed_count += 1
        continue
    print("Error: line %d: unrecognised format" % line_number)
print("regenerated full.md, %d verses completed (%d sealed, %d cobwebs)." % (verse_count, sealed_count, cobweb_count))