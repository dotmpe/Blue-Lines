.PHONY: default link 
default: bl_lib.zip

XMLRPCSERVER := xmlrpcserver-0.99.2.tar.gz

link:
	if test ! -f $(XMLRPCSERVER); then \
		wget http://www.julien-oster.de/projects/xmlrpcserver/dist/$(XMLRPCSERVER); \
		tar xzvf $(XMLRPCSERVER); fi;
	-ln -s xmlrpcserver/xmlrpcserver.py 
	@echo "These may need to be resolved manually:"
	-ln -s /home/berend/src/python-breve/latest/breve
	-ln -s /home/berend/src/nabu/working/lib/python/nabu
	-ln -s /home/berend/src/python-docutils/docutils.svn/trunk/docutils/docutils
	-ln -s /usr/share/pyshared/roman.py
	-ln -s ../../docutils/dotmpe
	-ln -s ../../vestige
	-ln -s ~/src/python-gae-sessions/latest/gaesessions
	-ln -s /home/berend/projects/gate-vc/src/gate
	-ln -s /usr/lib/python2.5/site-packages/zope

clean:
	find -L ./ -iname '*.pyc'|while read f; do sudo rm $$f;done

bl_lib.zip:
	zip $@ -r vestige/ breve/ nabu/ docutils/ dotmpe/ roman.py uriref.py \
        xmlrpcserver.py gaesessions/ gate/ zope/ \
        -x '*/.svn*' -x '*/.bzr*' -x '*.pyc'


