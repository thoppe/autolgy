# topic = "Colors"
# topic = "Emotions"
# topic = "Sensations"
# topic = "Superpowers"
# topic = "Music styles"
# topic = "Weather events"
# topic = "Human feelings"
# topic = "meta"
# topic = "reasons why she left you"
# topic = "fantasy creatures"
# topic = "scifi biomes"
# topic = "reasons why you are a dumbass"
topic = "Music genres"

all:
	python P0_build_ontolog.py --topic $(topic)
	python P1_gather_defs.py --topic $(topic) --mode definition
	python P1_gather_defs.py --topic $(topic) --mode emoji
	python P1_gather_defs.py --topic $(topic) --mode examples
lint:
	black *.py --line-length 80
	flake8 *.py --ignore=E203
