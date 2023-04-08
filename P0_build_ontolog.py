import pandas as pd
import json
from tqdm import tqdm
import diskcache as dc
from utils import query
from wasabi import msg as MSG
import itertools
import math
from pathlib import Path
from slugify import slugify

topic = "Colors"
MAX_DEPTH = 3

topic = "Emotions"
MAX_DEPTH = 4

# topic = "Sensations"
# MAX_DEPTH = 3

topic = "Superpowers"
MAX_DEPTH = 4

#topic = "Music styles"
#MAX_DEPTH = 4

#topic = "Weather events"
#MAX_DEPTH = 4

#topic = "Human feelings"
#MAX_DEPTH = 3

topic = "meta"
topic = "reasons why she left you"
topic = "fantasy creatures"
topic = "scifi biomes"
topic = "reasons why you are a dumbass"

MAX_DEPTH = 3
cache = dc.Cache(f"cache/{slugify(topic)}")
N = 7
max_tokens = 300

save_dest = Path("results")
save_dest.mkdir(exist_ok=True, parents=True)

pd.set_option("display.max_rows", 200)


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


def filter_df(df, result, depth, parent, keep_fraction=0.5):
    dx = clean_categories(result, depth, parent)
    dx = dx[dx["count"] >= math.floor(N * keep_fraction)]

    bad_keys = pd.merge(
        df[df.depth < dx.depth.max()], dx, left_on="topic", right_on="topic"
    )["topic"].unique()

    # if bad_keys.any():
    #    MSG.fail(f"Removing previously found {bad_keys.tolist()}")

    dx = dx[~dx["topic"].isin(bad_keys)]

    return dx


df = pd.DataFrame([{"topic": topic, "count": N, "depth": 0, "parent": ""}])
result = top_level_cats(topic, n=N)
df = filter_df(df, result, depth=1, parent=topic)
print(df)

for k_depth in range(2, MAX_DEPTH + 1):
    df_at_depth = df[df.depth == k_depth - 1]

    for subtopic, parent in zip(df_at_depth.topic, df_at_depth.parent):

        result = next_level_cats(topic, subtopic, parent, n=N)
        dx = filter_df(df, result, k_depth, subtopic)
        df = pd.concat([df, dx]).reset_index(drop=True)
        print(dx)

    f_save = save_dest / (slugify(topic) + f"_{k_depth:03d}.csv")
    df.to_csv(f_save, index=False)

    MSG.good(f"Saved to {f_save}")
