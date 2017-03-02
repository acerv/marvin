install:
	pip install --no-cache-dir -r requirements.txt
	python setup.py install --record files.txt

uninstall:
	cat files.txt | xargs rm -vrf
