from dspipe import Pipe
import pandas as pd
import diskcache as dc
from utils import query
from wasabi import msg as MSG
from pathlib import Path
from slugify import slugify

# topic = "Music styles"
# topic = "Superpowers"
topic = "human feelings"
topic = "weather events"
topic = "emotions"
topic = "sensations"
topic = "meta"
topic = "fantasy creatures"

name = slugify(topic)
f_csv = sorted(list(Path("results").glob(f"{name}*.csv")))[-1]
df = pd.read_csv(f_csv)

cache = dc.Cache(f"cache_def/{slugify(topic)}")


def gather_parents(name, known_parents=None):
    if known_parents is None:
        known_parents = []

    try:
        p = df[df.topic == name].parent.values[0]
        known_parents.append(p)
        return gather_parents(p, known_parents)
    except:
        pass

    return known_parents


@cache.memoize()
def call(msg, topic):
    result = query(msg, n=1, max_tokens=300)

    token_cost = result["usage"]["total_tokens"]
    MSG.warn(f"'{topic}' TOKENS USED {token_cost}")
    return result


def craft_message(topic):
    parents = gather_parents(topic)
    link = ", a subset of ".join(parents)
    msg = f"In a few lines, describe {topic}. It is {link}."
    result = call(msg, topic)
    desc = result["choices"][0]["message"]["content"]
    print(desc)
    return desc


Pipe(df["topic"])(craft_message, 20)

extended_defs = []
for k, topic in enumerate(df["topic"]):
    x = craft_message(topic)
    extended_defs.append(x)

df["definition"] = extended_defs
df.to_csv(f_csv, index=False)
