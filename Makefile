SETUP = python3 setup.py

release: clean
	$(SETUP) sdist bdist_wheel upload --sign

clean:
	-rm -r build/ dist/ *.egg-info/
