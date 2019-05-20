SETUP = python3 setup.py

release: clean
	$(SETUP) sdist bdist_wheel
	twine upload dist/* --verbose

clean:
	-rm -r build/ dist/ *.egg-info/
