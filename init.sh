#!/bin/sh 
# Initialize resources for BlueLines alias if needed. 
# Try processing some documents.
do_dev_login()
{
    curl http://iris:8080/_ah/login \
        -F email="test@localhost" \
        -F admin=True \
        -F continue='' \
        -F action=Login \
        -c .cookie.jar;
    echo "Logged in. "        
}
do_ga_login()
{
    if test ! -e .cookie.jar; then
        curl $CURL/user/auth \
            -F Email="berend.van.berkum@gmail.com" \
            -F Passwd="MassiveGMail" \
            -c .cookie.jar;
        echo "Logged in at GA. "
    fi;        
}
init_build_config()
{
    curl $CURL/config/bl
    if test $? -ge 1; then
       curl $CURL/config/bl \
           -F title="Blue Lines shared build-configuration " \
           -F builder="bluelines.Document" 
       echo "Initialized config:bl"
    fi;        
}
init_proc_config()
{
    curl $CURL/config/bl/process/bluelines
    if test $? -ge 1; then
        curl $CURL/config/bl/process/bluelines \
            -F title="Blue Lines" 
        echo "Initialized config:bl:bluelines"        
    fi;
}
init_pub_config()
{
    curl $CURL/config/bl/publish/html
    if test $? -ge 1; then
        curl $CURL/config/bl/publish/html \
            -F title="Blue Lines HTML" \
            -F writer="dotmpe-html" \
            -F template="var/du-html-template.txt" 
        echo "Initialized config:bl:html"
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
        -F "proc-config"="bl,bluelines" \
        -F "default-page"=welcome \
        -F "default-leaf"=main \
        -F "remote-path"="http://blue-lines.appspot.com" 
#        -F "remote-path"="http://iris:8088" 
#    -F default-pub-config="blue-lines-html" \
    echo "Initialized alias:Blue Lines"
#fi;        
}

#CURL="-b .cookie.jar -f -o /dev/null http://iris:8080/0.1/dubl"
if test "$1" == 'dev'; then
    CURL_="-b .cookie.jar http://iris:8080/0.1/dubl"
    CURL=" --fail --silent -o /dev/null "$CURL_
    do_dev_login
    do_dev_login # first-run bug in GAE-dev, module not loaded
else
    CURL_="-b .cookie.jar http://blue-lines.appspot.com/0.1/dubl"
    CURL=" --fail --silent -o /dev/null "$CURL_
    do_ga_login
fi;
#curl $CURL/alias/_/Blue%20Lines
#curl $CURL_/alias/_/Blue%20Lines -X DELETE
#curl $CURL/config/bl/process/bluelines -X DELETE
#curl $CURL/config/bl/publish/html -X DELETE
#curl $CURL/config/bl -X DELETE
#init_build_config
#init_proc_config
#init_pub_config
#init_alias
curl $CURL/process \
    -F unid="~Blue Lines/ReadMe" 
#    --data-urlencode rst@"ReadMe.rst" \
#
#curl $CURL/publish \
#    -F unid="~Blue Lines/ReadMe" \
#    -F format=bl-html
#curl $CURL/alias \
#    -F handle="Blue Lines" \
#    -F "default-title"="Blue Lines" \
#    -F public=True \
#    -F "proc-config"="bl-build,bluelines" \
#    -F "default-page"=welcome \
#    -F "default-leaf"=main \
#    -F "remote-path"="http://iris:8088" 
rm .cookie.jar
