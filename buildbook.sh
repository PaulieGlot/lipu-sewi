#!/bin/sh
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
    [[ $line =~ ^([^,]*),([0-9]*)$ ]] && {
        book=${BASH_REMATCH[1]}
        let chapter=${BASH_REMATCH[2]}

        echo $section $book $chapter
        [[ ! -d "./$section/$book" ]] && mkdir "./$section/$book"
        while [[ $chapter > 0 ]]; do
            touch "./$section/$book/$chapter.txt"
            let chapter-=1
        done
        continue
    }

    # This is only reachable if the line is not of a known format.
    echo "Error: unrecognised line format: line $line_number: \`$line\`"
done <chapters.txt
