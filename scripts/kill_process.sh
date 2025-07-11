#!/bin/bash
# Usage: kill_process.sh <process_name_or_pid>
if [[ $1 =~ ^[0-9]+$ ]]; then
    kill -9 $1
else
    pkill -x "$1"
fi
