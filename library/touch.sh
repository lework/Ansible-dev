#!/bin/sh

args_file=$1

[ ! -f "$args_file" ] && echo -n '{"failed": true, "msg": "missing required arguments: file"}' && exit 1
args_result=$(cat $args_file | gawk -F'file=' '{print $2}' | gawk -F' ' '{print $1}')

[ ! -n "$args_result" ] && echo -n "{\"failed\": true, \"msg\": \"file () is absent, cannot continue\", \"file\": \"$args_result\"}" && exit 1

touch $args_result && echo -n "{\"changed\": true, \"rc\": $?,\"file\": \"$args_result\"}" || echo -n "{\"failed\": true, \"rc\": $?, \"file\": \"$args_result\"}"
exit $?
