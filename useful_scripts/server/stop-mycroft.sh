#!/usr/bin/env bash

# Copyright 2017 Mycroft AI Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

SOURCE="${BASH_SOURCE[0]}"

script=${0}
script=${script##*/}
cd -P "$( dirname "$SOURCE" )"

function help() {
    echo "${script}:  Mycroft service stopper"
    echo "usage: ${script} [service]"
    echo
    echo "Service:"
    echo "  all       ends core services: bus, audio, skills, voice, hive"
    echo "  (none)    same as \"all\""
    echo "  bus       stop the Mycroft messagebus service"
    echo "  audio     stop the audio playback service"
    echo "  skills    stop the skill service"
    echo "  voice     stop voice capture service"
    echo "  hive      stop hive mind"
    echo "  enclosure stop enclosure (hardware/gui interface) service"
    echo
    echo "Examples:"
    echo "  ${script}"
    echo "  ${script} audio"

    exit 0
}

_module=""
function name-to-script-path() {
    case ${1} in
        "bus")               _module="mycroft.messagebus.service" ;;
        "skills")            _module="mycroft.skills" ;;
        "audio")             _module="mycroft.audio" ;;
        "hive")              _module="jarbas_hive_mind" ;;
        "voice")             _module="mycroft.client.speech" ;;
        "cli")               _module="mycroft.client.text" ;;
        "audiotest")         _module="mycroft.util.audio_test" ;;
        "wakewordtest")      _module="test.wake_word" ;;
        "enclosure")         _module="mycroft.client.enclosure" ;;

        *)
            echo "Error: Unknown name '${1}'"
            exit 1
    esac
}

function process-running() {
    if [[ $( pgrep -f "python3 (.*)-m ${_module}" ) ]] ; then
        return 0
    else
        return 1
    fi
}

function end-process() {
    name-to-script-path ${1}
    if process-running ${_module} ; then
        # Find the process by name, only returning the oldest if it has children
        pid=$( pgrep -o -f "python3 (.*)-m ${_module}" )
        echo -n "Stopping ${_module} (${pid})..."
        kill -SIGINT ${pid}

        # Wait up to 5 seconds (50 * 0.1) for process to stop
        c=1
        while [ $c -le 50 ] ; do
            if process-running ${_module} ; then
                sleep 0.1
                (( c++ ))
            else
                c=999   # end loop
            fi
        done

        if process-running ${_module} ; then
            echo "failed to stop."
            pid=$( pgrep -o -f "python3 (.*)-m ${_module}" )
            echo -n "  Killing ${_module} (${pid})..."
            kill -9 ${pid}
            echo "killed."
            result=120
        else
            echo "stopped."
            if [ $result -eq 0 ] ; then
                result=100
            fi
        fi
    fi
}


result=0  # default, no change


OPT=$1
shift

case ${OPT} in
    "all")
        ;&
    "")
        echo "Stopping all mycroft-core services"
        end-process hive
        end-process enclosure
        end-process speech
        end-process audio
        end-process skills
        end-process messagebus.service
        ;;
    "bus")
        end-process messagebus.service
        ;;
    "audio")
        end-process audio
        ;;
    "skills")
        end-process skills
        ;;
    "voice")
        end-process speech
        ;;
    "hive")
        end-process hive
        ;;
    "enclosure")
        end-process enclosure
        ;;

    *)
        help
        ;;
esac

# Exit codes:
#     0   if nothing changed (e.g. --help or no process was running)
#     100 at least one process was stopped
#     120 if any process had to be killed
exit $result
