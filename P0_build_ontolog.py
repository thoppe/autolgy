from dspipe import Pipe
import argparse
import pandas as pd
import diskcache as dc
from utils import query
from wasabi import msg as MSG
import itertools
from pathlib import Path
from slugify import slugify

parser = argparse.ArgumentParser(
    description="Generate an ontology from a root topic."
)
parser.add_argument("--topic", type=str, help="Root topic")
parser.add_argument(
    "--N",
    type=int,
    default=7,
    help="Number of queries",
)
parser.add_argument(
    "--K_THRESHOLD",
    type=int,
    default=3,
    help="Min number of votes to keep an item",
)
parser.add_argument(
    "--MAX_DEPTH",
    type=int,
    default=3,
    help="Number of levels to build the ontology",
)

parser.add_argument(
    "--MAX_TOKENS",
    type=int,
    default=300,
    help="Limit on number of tokens to use",
)

# Parse the arguments
args = parser.parse_args()

topic = args.topic
MAX_DEPTH = args.MAX_DEPTH
N = args.N
K_THRESHOLD = args.K_THRESHOLD
max_tokens = args.MAX_TOKENS
NUM_QUERY_THREADS = 15


cache = dc.Cache(f"cache/{slugify(topic)}/ontology")

save_dest = Path("results")
save_dest.mkdir(exist_ok=True, parents=True)


@cache.memoize()
def top_level_cats(main_topic, n=2):

    textq = f"""You are an expert knowledge engine and are constructing an ontology. The topic is "{main_topic}". Enumerate the major categories under {main_topic} in a bulleted list. Do not include a description."""

    js = query(textq, max_tokens=max_tokens, n=n)

    token_cost = js["usage"]["total_tokens"]

    MSG.warn(f"'{main_topic}' TOKENS USED {token_cost}")
    return js


@cache.memoize()
def next_level_cats(main_topic, sub_topic, parent, n=2):

    MSG.warn(f"{main_topic} : {parent} : {sub_topic}")

    textq = f"""You are an expert knowledge engine and are constructing an ontology. The topic is "{main_topic}" and you are in the subheading of {parent}. Enumerate only the direct subcategories of {sub_topic} in a bulleted list. Do not include a description."""

    js = query(textq, max_tokens=max_tokens, n=n)

    token_cost = js["usage"]["total_tokens"]

    MSG.info(f"TOKENS USED {token_cost}")
    return js


@cache.memoize()
def check_if_subset(args):
    t0, t1 = args
    textq = f"""Is "{t0}" a subset of "{t1}"? Only answer yes or no"""
    js = query(textq, max_tokens=max_tokens, n=1)
    val = js["choices"][0]["message"]["content"].strip(". ").lower()

    if val == "yes":
        return True
    return False


def clean_categories(js, depth, parent):
    msgs = [x["message"]["content"] for x in js.pop("choices")]

    cats = []
    for msg in msgs:
        cat_set = [x.strip('''+ -'"''') for x in msg.splitlines()]
        cats.append(cat_set)

    key_func = lambda x: x.title()
    groups = itertools.groupby(
        sorted(itertools.chain.from_iterable(cats), key=key_func), key=key_func
    )
    hist = {key: len(list(group)) for key, group in groups}

    df = pd.DataFrame(hist.items(), columns=["topic", "count"])
    df = df.sort_values(["count", "topic"], ascending=False)
    df["depth"] = depth
    df["parent"] = parent

    return df


def filter_df(df, result, depth, parent):
    dx = clean_categories(result, depth, parent)
    dx = dx[dx["count"] >= K_THRESHOLD]

    # Remove keys that appears higher up in the ontology
    bad_keys = pd.merge(
        df[df.depth < dx.depth.max()], dx, left_on="topic", right_on="topic"
    )["topic"].unique()
    dx = dx[~dx["topic"].isin(bad_keys)]

    # Remove keys that are subsets of each other
    ITR = list(itertools.combinations(dx["topic"], r=2))
    bad_keys = []
    for (t0, t1), is_subset in zip(
        ITR, Pipe(ITR)(check_if_subset, NUM_QUERY_THREADS)
    ):
        if is_subset:
            MSG.warn(f"Found {t0} as a subset of {t1}")
            bad_keys.append(t0)
    dx = dx[~dx["topic"].isin(bad_keys)]

    return dx


def analyze_row(row):
    subtopic, parent = row.topic, row.parent
    result = next_level_cats(topic, subtopic, parent, n=N)
    return subtopic, result


# Start the analysis with a top level query

df = pd.DataFrame([{"topic": topic, "count": N, "depth": 0, "parent": ""}])
result = top_level_cats(topic, n=N)
df = filter_df(df, result, depth=1, parent=topic)

for k_depth in range(2, MAX_DEPTH + 1):
    df_at_depth = df[df.depth == k_depth - 1]

    ITR = df_at_depth.itertuples(index=False)
    for (subtopic, result) in Pipe(ITR)(analyze_row, NUM_QUERY_THREADS):

        dx = filter_df(df, result, k_depth, subtopic)
        df = pd.concat([df, dx]).reset_index(drop=True)
        print(dx)

    f_save = save_dest / (slugify(topic) + f"_{k_depth:03d}.csv")
    df.to_csv(f_save, index=False)

    MSG.good(f"Saved to {f_save}")
