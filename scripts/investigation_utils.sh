#!/bin/bash

# attempting a <.*>.env is probably the most obvious thing people try to do
# just wanted to play with JQ to recreated something homebrewed of what I would
# get if I were using a logging DSL like splunk SPL or grafana.
# If the question is - well, why don't you?, the answer is simple.
#   1) Not paying any licenses in this project - mostly out of fun really
#   2) setting up loki + grafana would require more resources than the machine I'm using has :)
function display_attempts_dotenv(){
  docker-compose -f docker-compose.yml logs frontend  \
    | jq -Rr 'fromjson? | select(.request_uri | test(".*\\.env$"; "i"))' \
    | jq -sr 'group_by(.remote_addr, .status)
             | map({ remote_addr: .[0].remote_addr, status: .[0].status, count: length })
             | .[]
             | [.remote_addr, .status, .count]
             | @csv'
}
