import streamlit as st
import pandas as pd
from pathlib import Path
import uuid

st.set_page_config(
    layout="centered", page_icon=":brain:", page_title="Autology"
)

F_CSV = sorted(list(Path("results").glob("*.csv")))
NAMES = set([x.stem.split("_")[0] for x in F_CSV])


def reset_all():
    del st.session_state["current_topic"]
    del st.session_state["hierarchy"]


def button_callback(topic):
    st.session_state["hierarchy"].append(topic)
    st.session_state["current_topic"] = topic


def button_go_back():
    st.session_state["hierarchy"].pop()
    st.session_state["current_topic"] = st.session_state["hierarchy"][-1]


with st.sidebar:
    category = st.selectbox("Category", NAMES, on_change=reset_all)

    DEPTHS = sorted(
        [
            int(x.stem.split("_")[1])
            for x in F_CSV
            if x.stem.split("_")[0] == category
        ]
    )[::-1]

    hidden = """
    k_depth = st.selectbox(
        "Depth (larger numbers take longer to load)", DEPTHS, on_change=reset_all, 
    )
    """
    k_depth = DEPTHS[0]

    f_csv = Path("results") / f"{category}_{k_depth:03d}.csv"


@st.cache_resource
def load_data(f_csv):

    df = pd.read_csv(f_csv)
    main_topic = df[df.depth < 2].parent.values[0]

    missing_cols = ["definition", "examples", "emoji"]
    for col in missing_cols:
        if col not in df:
            df[col] = ""

    return df, main_topic


df, main_topic = load_data(f_csv)

if "current_topic" not in st.session_state:
    st.session_state["current_topic"] = main_topic

if "hierarchy" not in st.session_state:
    st.session_state["hierarchy"] = [main_topic]

# Define the app title and description
st.title(f"{main_topic}")

hi = st.session_state["hierarchy"]
if len(hi) > 1:
    subtitle = " : ".join(hi[1:])
    st.write(f"### {subtitle}")


current_topic = st.session_state["current_topic"]

if len(hi) > 1:
    parent = hi[-2]
    subs = df[(df.topic == current_topic) & (df.parent == parent)]
    desc = subs["definition"].values[0]
    if desc:
        st.markdown(f"*{desc}*")

cols = st.columns(4)
current_col = 0

df_sorted = df[df.parent == current_topic].sort_values("topic")


for row in df_sorted.itertuples(index=False):
    header = row.topic
    emoji = row.emoji

    kwargs = {"on_click": button_callback, "key": uuid.uuid4()}
    text = f"{emoji} {header}"

    # if (df.parent==header).sum() > 0:
    #    text = f":star2: {text}"

    cols[current_col].button(text, args=(header,), **kwargs)

    current_col = current_col + 1
    if current_col >= len(cols):
        current_col = 0


if len(hi) > 1:
    st.button(":arrow_left: Go back", type="secondary", on_click=button_go_back)
    row = df[(df.topic == current_topic) & (df.parent == parent)]
    example_text = row["examples"].values[0]
    st.markdown(example_text)
