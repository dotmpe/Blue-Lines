#!/bin/sh 
# Initialize resources for BlueLines alias if needed. 
# Try processing some documents.
print_result()
{
    if test $1 -ge 1; then echo $3; else echo $2; fi;        
}
do_dev_login()
{
    curl http://iris:8080/_ah/login \
        -F email="test@localhost" \
        -F admin=True \
        -F continue='' \
        -F action=Login \
        -c .cookie.jar;
    print_result $? "Logged in at dev-server. " "Error logging in at dev-server."
}
do_ga_login()
{
    if test ! -e .cookie.jar; then
        curl $CURL/user/auth \
            --data @/home/berend/project/dotmpe-com/var/phpbl/post-credentials.txt \
            -c .cookie.jar;
            #-F passwd=MassiveGMail -F email=berend.van.berkum@gmail.com \
        print_result $? "Logged in at GA. " "Error logging in at GA. "
    fi;        
}
init_build_config()
{
#    curl $CURL/config/bl
#    if test $? -ge 1; then
        curl $CURL/config/bl \
            -F title="Blue Lines shared build-configuration " \
            -F builder="bluelines.Document" \
            -F breadcrumb=yes
        print_result $? "Initialized config:bl" "Error initializing config:bl"
#    fi;        
}
init_proc_config()
{
#    curl $CURL/config/bl/process/bluelines
#    if test $? -ge 1; then
        curl $CURL/config/bl/process/bluelines \
            -F title="Blue Lines" \
            -F breadcrumb=no
        print_result $? "Initialized config:bl:bluelines" "Error initializing config:bl:bluelines"
#    fi;
}
init_pub_config()
{
    curl $CURL/config/bl/publish/html
    if test $? -ge 1; then
        curl $CURL/config/bl/publish/html \
            -F title="Blue Lines HTML" \
            -F writer="dotmpe-html" \
            -F template="var/du-html-template.txt" 
        print_result $? "Initialized config:bl:html" "Error initializing config:bl:html"
    fi;
    curl $CURL/config/bl/publish/xml
    if test $? -ge 1; then
        curl $CURL/config/bl/publish/xml \
            -F title="Docutils XML" \
            -F writer="xml" 
        print_result $? "Initialized config:bl:xml" "Error initializing config:bl:xml"
    fi;
}
init_alias()
{
curl $CURL/alias/BL%20Dev
if test $? -ge 1; then
    curl $CURL/alias \
        -F handle="BL Dev" \
        -F "default-title"="Blue Lines (dev)" \
        -F public=True \
        -F "proc-config"="bl,bluelines" \
        -F "default-page"=welcome \
        -F "default-leaf"=main \
        -F "remote-path"="http://iris:8088" 
    print_result $? "Initialized alias:BL Dev" "Error initializing alias:BL Dev"
fi;        
curl $CURL/alias/Blue%20Lines
if test $? -ge 1; then
    curl $CURL/alias \
        -F handle="Blue Lines" \
        -F "default-title"="Blue Lines" \
        -F public=True \
        -F "proc-config"="bl,bluelines" \
        -F "default-page"=welcome \
        -F "default-leaf"=main \
        -F "remote-path"="http://blue-lines.appspot.com" 
    print_result $? "Initialized alias:Blue Lines" "Error initializing alias:Blue Lines"
fi;        
curl $CURL/alias/Sandbox
if test $? -ge 1; then
    curl $CURL/alias \
        -F handle="Sandbox" \
        -F "default-title"="Sandbox" \
        -F public=True \
        -F "proc-config"="bl,bluelines" \
        -F "default-page"=welcome \
        -F "default-leaf"=main 
    print_result $? "Initialized alias:Sandbox" "Error initializing alias:Sandbox"
fi;        
}
delete_all()
{
    curl $CURL_/alias/_/Sandbox -X DELETE
    curl $CURL_/alias/_/Blue%20Lines -X DELETE
    curl $CURL/config/bl/process/bluelines -X DELETE
    curl $CURL/config/bl/publish/html -X DELETE
    curl $CURL/config/bl -X DELETE
}
test_fetch()
{
    curl $CURL_/alias/_/Sandbox
    curl $CURL_/alias/_/Blue%20Lines
    curl $CURL_/config/bl/process/bluelines 
    curl $CURL_/config/bl/publish/html 
    curl $CURL_/config/bl 
}
#CURL="-b .cookie.jar -f -o /dev/null http://iris:8080/0.1/dubl"
#rm .cookie.jar
if test "$1" == 'dev'; then
    CURL_="-b .cookie.jar http://iris:8080/0.1/dubl"
    CURL=" --fail --silent -o /dev/null "$CURL_
    do_dev_login # first-run bug in GAE-SDK, module not loaded
    do_dev_login
else
    CURL_="-b .cookie.jar http://blue-lines.appspot.com/0.1/dubl"
    CURL=" --fail --silent -o /dev/null "$CURL_
    do_ga_login
fi;
#delete_all
#test_fetch
#init_build_config
init_proc_config
#init_pub_config
#init_alias
#test_fetch
#curl $CURL/process \
#    -F unid="~Blue Lines/ReadMe" 
#curl $CURL/process \
#    -F unid="~BL Dev/ReadMe" 
#curl $CURL/publish \
#    -F unid="~Blue Lines/ReadMe" \
#    -F format=html
#curl $CURL_/process \
#    --data unid="~Sandbox/Test1" \
#    --data-urlencode rst@"ReadMe.rst" 
#curl $CURL_/publish \
#    --data unid="~Sandbox/Test1" 
#curl $CURL/alias \
#    -F handle="Blue Lines" \
#    -F "default-title"="Blue Lines" \
#    -F public=True \
#    -F "proc-config"="bl-build,bluelines" \
#    -F "default-page"=welcome \
#    -F "default-leaf"=main \
#    -F "remote-path"="http://iris:8088" 
