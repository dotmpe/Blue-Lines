.PHONY: default update update-app update-docs clean clean-pyc test dev loc

default:

srv:
	dev_appserver.py ./ -a iris --datastore_path=.tmp/dev_appserver.datastore

srv2:
	dev_appserver.py ./ -a iris -p 8088 --datastore_path=.tmp/dev_appserver.datastore

dev:
	dev_appserver.py ./ -a iris -d --datastore_path=.tmp/dev_appserver.datastore

dev2:
	dev_appserver.py ./ -a iris -p 8088 -d --datastore_path=.tmp/dev_appserver.datastore

test:
	python test/main.py

clean: clean-pyc 

clean-pyc:
	find ./ -iname '*.pyc'|while read f; do rm $$f; done;

update: update-app update-docs

update-app:
	appcfg.py update ./ --verbose

update-docs:
	var/media/nabu *.rst --server-url https://blue-lines.appspot.com/~blue/.xmlrpc
	var/media/nabu doc/ -r --server-url https://blue-lines.appspot.com/~blue/.xmlrpc
	# TODO: nabu has no --quiet option

loc: loc.txt
	@echo Project has `cat $@.txt|grep total -|sed 's/total//'` Lines of Python Code.

loc.txt: ./*.py */*.py
	@wc -l *.py {extractor,decorator,model,tag}/*.py > $@


TODO.txt: * 
	@rgrep -n --colour=auto TODO * {decorator,doc,extractor,model,tag,var}/* > $@


# vim:noet: 
