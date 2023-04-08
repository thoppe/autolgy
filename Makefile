topic = "Music genres"
all:
	python P0_build_ontolog.py --topic $(topic)

lint:
	black *.py --line-length 80
	flake8 *.py --ignore=E203
