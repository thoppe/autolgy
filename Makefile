lint:
	black *.py --line-length 80
	flake8 *.py --ignore=E203
