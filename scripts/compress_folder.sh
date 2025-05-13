#!/bin/bash
folder="$1"
archive="$2"
if [ -z "$archive" ]; then
    archive="${folder%/}.zip"
fi
zip -r "$archive" "$folder"