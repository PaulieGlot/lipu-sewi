#!/bin/sh
let line_number=0
rm full.md
while read -r line; do
    let line_number+=1
    # Ignore empty or commented lines.
    [[ $line == "" || $line =~ ^\/\/.* ]] && continue

    # Recognise section titles, which are preceded by a hash.
    [[ $line =~ ^#(.*)$ ]] && {
        section=${BASH_REMATCH[1]}
        [[ ! -d "./$section" ]] && mkdir "./$section"
        printf "# $section\n\n" >> full.md
        continue
    }
    # Recognise book titles and chapter counts, which are separated by a comma (with no following space).
    [[ $line =~ ^([^,]*),([0-9]+)$ ]] && {
        book=${BASH_REMATCH[1]}
        let chapters=${BASH_REMATCH[2]}
        echo "In $section: $book, $chapters chapters"
        printf "## $book\n\n" >> full.md
        [[ ! -d "./$section/$book" ]] && mkdir "./$section/$book"
        let chapter=1
        while [[ $chapter -le $chapters ]]; do
            file="./$section/$book/$chapter.txt"
            touch "$file"
            printf "### $book $chapter\n\n" >> full.md
            while read -r verse; do
                printf "$verse\n\n" >> full.md
            done <"$file"
            echo >> full.md
            let chapter+=1
        done
        continue
    }

    # This is only reachable if the line is not of a known format.
    echo "Error: unrecognised line format: line $line_number: \`$line\`"
done <chapters.txt