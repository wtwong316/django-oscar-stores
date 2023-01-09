.PHONY: install sandbox css

install:
	pip install -e . -r requirements.txt django-oscar

sandbox: install
	-rm -rf sandbox/public/media/cache sandbox/public/media/uploads
	./sandbox/manage.py migrate
	./sandbox/manage.py loaddata sandbox/fixtures/auth.json
	./sandbox/manage.py loaddata sandbox/fixtures/countries.json
	./sandbox/manage.py loaddata sandbox/fixtures/sdfs.json
	./sandbox/manage.py thumbnail clear

css:
	lessc sdfs/static/sdfs/less/sdfs.less > sdfs/static/sdfs/css/sdfs.css
