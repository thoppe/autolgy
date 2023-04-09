# topic = "Colors"
# topic = "Emotions"
# topic = "Sensations"
# topic = "Music styles"
# topic = "Weather events"
# topic = "Human feelings"
# topic = "meta"
# topic = "reasons why you are a dumbass"

#topic = "Music genres"
#topic = "Ways to propose"
#topic = "Types of presents to buy for people"
#topic = "reasons why she left you"
#topic = "why are men"
#topic = "fantasy creatures"
#topic = "Superpowers"
#topic = "sci-fi and fantasy biomes"
#topic = "Liminal spaces"
#topic = "How to be a bad bitch"
#topic = "outrageous shit your mother in law says"
topic = "weird phobias"


all:
	python P0_build_ontolog.py --topic $(topic)
	python P1_gather_defs.py --topic $(topic) --mode definition
	python P1_gather_defs.py --topic $(topic) --mode emoji
	python P1_gather_defs.py --topic $(topic) --mode examples
lint:
	black *.py --line-length 80
	flake8 *.py --ignore=E501

streamlit:
	streamlit run streamlit_app.py
