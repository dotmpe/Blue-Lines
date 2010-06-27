if test -n "$1";
    git commit -m "$1";
    bzr gi -m "$1";
    bzr push;
    git push;
else
    echo "Need commit message."
    exit 2
fi;
