#!/bin/sh 
# Initialize resources for BlueLines alias if needed. 
# Try processing some documents.

CURL="-b .cookie.jar --fail --silent -o /dev/null http://iris:8080/0.1/dubl"
#CURL="-b .cookie.jar http://iris:8080/0.1/dubl"
#curl $CURL/alias \
#    -F handle="Blue Lines" \
#    -F "default-title"="Blue Lines" \
#    -F public=True \
#    -F "proc-config"="bl-build,bluelines" \
#    -F "default-page"=welcome \
#    -F "default-leaf"=main \
#    -F "remote-path"="http://iris:8088" 

do_login()
{
    #curl http://iris:8080/0.1/dubl/user
    if test ! -e .cookie.jar; then
        curl http://iris:8080/_ah/login \
            -F email="test@localhost" \
            -F admin=True \
            -F continue='' \
            -F action=Login \
            -c .cookie.jar;
        echo "Logged in. "        
    fi;        
}

init_build_config()
{
    curl $CURL/config/builder/bl-build
    if test $? -ge 1; then
        curl $CURL/config/builder/bl-build \
            -F title="Blue Lines shared build-configuration " \
            -F builder="bluelines.Document" 
        echo "Initialized config:build:bl-build"        
    fi;        
}

init_proc_config()
{
    # TODO: fix to use ancestor
    curl $CURL/config/processor/bluelines
    if test $? -ge 1; then
        curl $CURL/config/processor/bluelines \
            -F title="Blue Lines" \
            -F builder_config="bl-build" 
        echo "Initialized config:proc:bluelines"        
    fi;
}

init_pub_config()
{
    curl $CURL/config/publisher/bl-html
    if test $? -ge 1; then
        curl $CURL/config/publisher/bl-html \
            -F title="Blue Lines HTML" \
            -F builder_config="bl-build" \
            -F writer="dotmpe-html" \
            -F template="var/du-html-template.txt" 
        echo "Initialized config:pub:bl-html"
    fi;
}

init_alias()
{
#curl $CURL/alias -F handle="Blue Lines" 
#if test $? -ge 1; then
    curl $CURL/alias \
        -F handle="Blue Lines" \
        -F "default-title"="Blue Lines" \
        -F public=True \
        -F "proc-config"="bl-build,bluelines" \
        -F "default-page"=welcome \
        -F "default-leaf"=main \
        -F "remote-path"="http://iris:8088" 
#    -F default-pub-config="blue-lines-html" \
#    -F remote-path=http://blue-lines.appspot.com/ \
    echo "Initialized alias:Blue Lines"
#fi;        
}

init_pub_config

#curl $CURL/process \
#    -F unid="~Blue Lines/ReadMe" 
##    --data-urlencode rst@"ReadMe.rst" \
#
#curl $CURL/publish \
#    -F unid="~Blue Lines/ReadMe" \
#    -F format=bl-html


