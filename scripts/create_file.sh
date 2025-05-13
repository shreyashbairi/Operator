#!/bin/bash
path="$1"
content="$2"
if [ -z "$content" ]; then
    touch "$path"
else
    echo "$content" > "$path"
fi