#!/bin/sh 
# Initialize resources for BlueLines alias if needed. 
# Try processing some documents.

#curl $CURL/alias \
#    -F handle="Blue Lines" \
#    -F "default-title"="Blue Lines" \
#    -F public=True \
#    -F "proc-config"="bl-build,bluelines" \
#    -F "default-page"=welcome \
#    -F "default-leaf"=main \
#    -F "remote-path"="http://iris:8088" 

do_dev_login()
{
    #curl http://blue-lines.appspot.com/0.1/dubl/user
    if test ! -e .cookie.jar; then
        curl $CURL/user/auth \
            -F email="test@localhost" \
            -F admin=True \
            -F continue='' \
            -F action=Login \
            -c .cookie.jar;
        #curl http://blue-lines.appspot.com/_ah/login \
        #    -F email="test@localhost" \
        #    -F admin=True \
        #    -F continue='' \
        #    -F action=Login \
        #    -c .cookie.jar;
        echo "Logged in. "        
    fi;        
}
do_ga_login()
{
    curl $CURL/user/auth \
        -F Email="berend.van.berkum@gmail.com" \
        -F Passwd="MassiveGMail" \
        -c .cookie.jar;
    echo "Logged in at GA. "
}
init_build_config()
{
#    curl $CURL/config/builder/bl-build
#    if test $? -ge 1; then
        curl $CURL/config/builder/bl-build \
            -F title="Blue Lines shared build-configuration " \
            -F builder="bluelines.Document" 
        echo "Initialized config:build:bl-build"        
#    fi;        
}
init_proc_config()
{
    # TODO: fix to use ancestor
#    curl $CURL/config/processor/bluelines
#    if test $? -ge 1; then
        curl $CURL/config/processor/bluelines \
            -F title="Blue Lines" \
            -F builder_config="bl-build" 
        echo "Initialized config:proc:bluelines"        
#    fi;
}

init_pub_config()
{
#    curl $CURL/config/publisher/bl-html
#    if test $? -ge 1; then
        curl $CURL/config/publisher/bl-html \
            -F title="Blue Lines HTML" \
            -F builder_config="bl-build" \
            -F writer="dotmpe-html" \
            -F template="var/du-html-template.txt" 
        echo "Initialized config:pub:bl-html"
#    fi;
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
        -F "remote-path"="http://blue-lines.appspot.com" 
#        -F "remote-path"="http://iris:8088" 
#    -F default-pub-config="blue-lines-html" \
    echo "Initialized alias:Blue Lines"
#fi;        
}

if test $1 == 'dev'; then
    CURL="-b .cookie.jar --fail --silent -o /dev/null http://iris:8080/0.1/dubl"
    do_dev_login
    init_build_config
    init_proc_config
    init_pub_config
    init_alias
else
    CURL="-b .cookie.jar --fail --silent -o /dev/null http://blue-lines.appspot.com/0.1/dubl"
    #CURL="-b .cookie.jar -v http://blue-lines.appspot.com/0.1/dubl"
    do_ga_login
    init_build_config
    init_proc_config
    init_pub_config
    init_alias
fi;


curl $CURL/process \
    -F unid="~Blue Lines/ReadMe" 
#    --data-urlencode rst@"ReadMe.rst" \
#
#curl $CURL/publish \
#    -F unid="~Blue Lines/ReadMe" \
#    -F format=bl-html


