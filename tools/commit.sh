if test -n "$1";
then    
    git commit -m "$1";
    bzr ci -m "$1";
    bzr push lp:blue-lines;
    git push;
else
    echo "Need commit message."
    exit 2
fi;
