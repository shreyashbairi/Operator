#!/usr/bin/env bash

SOURCE="$1"
DEST="$2"

mv "$SOURCE" "$DEST"
echo "Moved '$SOURCE' to '$DEST'"
