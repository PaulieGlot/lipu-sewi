import re
import os
from datetime import date, datetime
import nimi

line_number = 0
verse_count = 0
sealed_count = 0
sealed_pattern = re.compile(r"[0-9]+: !")
cobweb_count = 0
cobweb_pattern = re.compile(r"[0-9]+: \?")
cobweb_files = []
bible_dir = 'bible'
books_file_path = '%s/chapters.txt' % bible_dir
fulltext_file_path = '%s/full.md' % bible_dir
stats_file_path = 'stats/completion.csv'
cobweb_file_path = 'stats/cobwebs.txt'
cobweb_file = open(cobweb_file_path, 'w')
stats_file = open(stats_file_path, 'a')
books_file = open(books_file_path, 'r')
fulltext_file = open(fulltext_file_path, 'w')
book_lines = books_file.readlines()
section = ""
nimifier = nimi.Nimifier()

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
            title_line = "### %s %d\n" % (book, chapter)
            fulltext_file.write(title_line)
            verses = chapter_file.readlines()
            for verse in verses:
                if verse != "":
                    verse = nimifier.replace_names(verse)
                    fulltext_file.write("%s\n" % verse)
                    verse_count += 1
                    if cobweb_pattern.match(verse):
                        cobweb_count += 1
                        cobweb_files.append(chapter_path)
                    elif sealed_pattern.match(verse):
                        sealed_count += 1
                    else:
                        print(chapter_path)
        continue
    print("Error: line %d: unrecognised format" % line_number)
print("regenerated full.md, %d verses completed (%d sealed, %d cobwebs)." % (verse_count, sealed_count, cobweb_count))
csv_summary = "%s, %d, %d, %d\n" % (date.today(), verse_count, sealed_count, cobweb_count)
stats_file.writelines(csv_summary)
seen = []
for file in cobweb_files:
    if file not in seen:
        cobweb_file.writelines("%s\n" % file)
        seen.append(file)