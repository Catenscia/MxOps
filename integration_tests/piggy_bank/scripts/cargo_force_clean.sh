#!/bin/bash

# fail first cargo clean
echo "launching cargo clean"
cargo clean
if [ $? == 0 ]
then
    echo "cargo clean succeeded, exiting script"
    exit 0
else
    echo "cargo clean failed, launching forced cleaning"
fi

# force cargo clean

# retrieve one of the remanent files
file=$(ls -t -a target/debug/deps| tail -n +3 | head -1)
if [ -z "$file" ]
then
    echo "Failed to get a remanent file"
    exit 1
fi

# get the headers and the values for the command lsof
pid_headers=$(lsof target/debug/deps/$file | grep PID)
pid_row=$(lsof target/debug/deps/$file | grep deps)

# get the column number for PID
tokens=$(echo $pid_headers | sed 's/[\\\/;?!:]//g')
header_pos=0
for token in $tokens
do
    header_pos=$(($header_pos + 1))
    if [ "$token" == "PID" ]
    then
        break
    fi
done

if [ $header_pos == 0 ]
then
    echo "Failed to find PID column"
    exit 1
fi

# retrieve the PID value and kill it
tokens=$(echo $pid_row | sed 's/[\\\/;?!:]//g')
value_pos=0
for token in $tokens
do
    value_pos=$(($value_pos + 1))
    if [ $value_pos == $header_pos ]
    then
        kill $token
        break
    fi
done

# relaunch cargo clean
sleep 1
cargo clean

echo "Cleaning done"
