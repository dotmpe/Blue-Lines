# XXX: undecided: I like github, perhaps leave LP at some point
if test -n "$1";
then    
    git commit -m "$1";
    bzr ci -m "$1";
    if test -n "$2";
    then
        bzr push lp:blue-lines;
        git push;
        echo "Pushed work to master tree. "
    fi;
else
    echo "Need commit message."
    exit 2
fi;
