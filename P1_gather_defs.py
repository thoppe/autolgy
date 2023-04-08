import argparse
from dspipe import Pipe
import pandas as pd
import diskcache as dc
from utils import query
from wasabi import msg as MSG
from pathlib import Path
from slugify import slugify

parser = argparse.ArgumentParser(
    description="Generate a description for each entry in the ontology."
)
parser.add_argument("--topic", type=str, help="Root topic")
parser.add_argument(
    "--N",
    type=int,
    default=7,
    help="Number of queries",
)
parser.add_argument(
    "--MAX_TOKENS",
    type=int,
    default=300,
    help="Limit on number of tokens to use",
)
parser.add_argument(
    "--mode",
    type=str,
    help="One of definition, emoji, examples",
)

# Parse the arguments
args = parser.parse_args()

target_column = args.mode
topic = args.topic
MAX_TOKENS = args.MAX_TOKENS
NUM_QUERY_THREADS = 15

if target_column not in ["definition", "emoji", "examples"]:
    raise KeyError(f"--mode argument not valid")

if target_column == "definition":
    msg_core = """Briefly in a few lines define "{topic}". It is {link}, but you don't need to repeat that. Do not give examples."""
elif target_column == "emoji":
    msg_core = """Return a single emoji that best exemplifies "{topic}". Only return one emoji and no other text. {definition}"""
elif target_column == "examples":
    msg_core = """Return a few examples that best exemplifies "{topic}". Return the items as a bulleted list. {definition}"""

name = slugify(topic)

# Grab the deepest ontology
f_csv = sorted(list(Path("results").glob(f"{name}*.csv")))[-1]
df = pd.read_csv(f_csv)


cache = dc.Cache(f"cache/{slugify(topic)}/{target_column}")


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
    result = query(msg, n=1, max_tokens=MAX_TOKENS)

    token_cost = result["usage"]["total_tokens"]
    MSG.warn(f"'{topic}' TOKENS USED {token_cost}")
    return result


def craft_message(row):
    topic = row.topic
    parents = gather_parents(topic)
    link = ", a subset of ".join(parents)

    kwargs = row._asdict()
    kwargs["link"] = link
    msg = msg_core.format(**kwargs)

    result = call(msg, topic)
    desc = result["choices"][0]["message"]["content"]
    print(desc)
    return desc


ITR = list(df.itertuples(index=False))
Pipe(ITR)(craft_message, NUM_QUERY_THREADS)

extended_defs = []
for k, row in enumerate(ITR):
    extended_defs.append(craft_message(row))

df[target_column] = extended_defs
df.to_csv(f_csv, index=False)
