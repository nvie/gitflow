#!/bin/bash

for cmd in $(./git-flow help | grep '^   ' | awk '{print $1}') ; do
    rm -f flags.doc
    git flow $cmd help 2>&1 | grep "git flow" | sed 's/^usage://' | sed 's/^ *//' | while read cmd ; do
        echo "               " $cmd
        cmd=$(echo $cmd | sed 's/<.*>//' | tr '[]' '  ')
        eval "$cmd -h" 2>&1 | grep '^  ' >> flags.doc
    done

    echo
    echo '                Flags:'
    cat flags.doc | sed 's/^/                /' | sort -u
    echo
    echo
    echo
done
rm -rf flags.doc
