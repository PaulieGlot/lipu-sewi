#!/bin/sh

# This file pads chapter titles so wimpy humings can read them without bursting into flames
let line_number=0
while read -r line; do
    let line_number+=1
    # Ignore empty or commented lines.
    [[ $line == "" || $line =~ ^\/\/.* ]] && continue

    # Recognise section titles, which are preceded by a hash.
    [[ $line =~ ^#(.*)$ ]] && {
        section=${BASH_REMATCH[1]}
        [[ ! -d "./$section" ]] && mkdir "./$section"
        continue
    }
    # Recognise book titles and chapter counts, which are separated by a comma (with no following space).
    [[ $line =~ ^([^,]*),([0-9]+)$ ]] && {
        book=${BASH_REMATCH[1]}
        let chapters=${BASH_REMATCH[2]}
        echo "In $section: $book, $chapters chapters"
        [[ ! -d "./$section/$book" ]] && mkdir "./$section/$book"
        let oldname=1
        for chapter in $(seq -f "%04g" 1 $chapters); do
            file="./$section/$book/$chapter.txt"
            oldfile="./$section/$book/$oldname.txt"
            echo "renaming '$oldfile' to '$file'"
            mv "$oldfile" "$file"
            let oldname+=1
        done
        continue
    }

    # This is only reachable if the line is not of a known format.
    echo "Error: unrecognised line format: line $line_number: \`$line\`"
done <chapters.txt
echo "$verse_count verses completed."
