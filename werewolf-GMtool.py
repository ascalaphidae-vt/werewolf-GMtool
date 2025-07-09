"""Streamlit app for assigning roles in a Werewolf game."""

import random
import pandas as pd
import streamlit as st

st.set_page_config(page_title="人狼GM補助ツール", layout="wide")

# --- ステート初期化 ---
DEFAULT_NUM_PLAYERS = 9

def init_state():
    if "num_players" not in st.session_state:
        st.session_state.num_players = DEFAULT_NUM_PLAYERS
    if "roles" not in st.session_state:
        st.session_state.roles = []
    if "players" not in st.session_state:
        st.session_state.players = ["" for _ in range(13)]
    if "table" not in st.session_state:
        st.session_state.table = []
    if "prophecy" not in st.session_state:
        st.session_state.prophecy = ""

init_state()

st.title("人狼GM補助ツール")

# --- 入力内容の初期化 ---
if st.button("入力内容の初期化"):
    st.session_state.num_players = DEFAULT_NUM_PLAYERS
    st.session_state.roles = []
    st.session_state.players = ["" for _ in range(13)]
    st.session_state.table = []
    st.session_state.prophecy = ""
    if hasattr(st, "rerun"):
        st.rerun()
    else:
        st.experimental_rerun()

# --- 1. 参加者数入力 ---
st.subheader("1. 参加者数の入力 (9～11人)")
st.session_state.num_players = st.number_input(
    "参加者数",
    min_value=9,
    max_value=11,
    step=1,
    value=st.session_state.num_players,
)

# --- 2. 役職テーブル決定 ---
def set_role_table(num):
    if num == 9:
        return [
            "人狼A",
            "人狼B",
            "狂人",
            "占い",
            "霊媒",
            "騎士",
            "村人A",
            "村人B",
            "村人C",
        ]
    if num == 10:
        return [
            "人狼A",
            "人狼B",
            "狂人",
            "占い",
            "霊媒",
            "騎士",
            "村人A",
            "村人B",
            "村人C",
            "村人D",
        ]
    if num == 11:
        return [
            "人狼A",
            "人狼B",
            "人狼C",
            "狂人",
            "占い",
            "霊媒",
            "二丁拳銃",
            "村人A",
            "村人B",
            "村人C",
            "村人D",
        ]
    return []

if st.button("役職テーブル決定"):
    st.session_state.roles = set_role_table(st.session_state.num_players)

if st.session_state.roles:
    st.write("### 役職テーブル")
    st.write(st.session_state.roles)

# --- 3. 参加者名入力 ---
st.subheader("3. 参加者名の入力")
for i in range(13):
    label = f"参加者{i+1}"
    st.session_state.players[i] = st.text_input(
        label,
        value=st.session_state.players[i],
        key=f"player_{i}",
    )

# --- 4. 発言順割り当て ---
if st.button("発言順割り当て"):
    selected = st.session_state.players[: st.session_state.num_players]
    table = []
    for name in selected:
        rand_a = random.randint(1, 1000)
        table.append({"name": name, "rand_a": rand_a})
    table.sort(key=lambda x: x["rand_a"])
    for idx, row in enumerate(table, 1):
        row["order"] = f"{idx:02}"
        row["rand_b"] = None
        row["role"] = None
    st.session_state.table = table

# --- 5. 役職割り当て ---
if st.button("役職割り当て") and st.session_state.roles and st.session_state.table:
    table = st.session_state.table
    for row in table:
        row["rand_b"] = random.randint(1, 2000)
    table.sort(key=lambda x: x["rand_b"])
    for idx, row in enumerate(table):
        row["role"] = st.session_state.roles[idx]
    st.session_state.table = table

# --- 6. お告げ決定 ---
if st.button("お告げ決定") and st.session_state.roles:
    choices = [r for r in st.session_state.roles if not r.startswith("人狼") and r != "占い"]
    st.session_state.prophecy = random.choice(choices) if choices else ""

# --- 表示 ---
if st.session_state.table:
    df = pd.DataFrame(
        [
            {
                "発言順": row.get("order"),
                "参加者名": row.get("name"),
                "役職": row.get("role"),
                "乱数A": row.get("rand_a"),
                "乱数B": row.get("rand_b"),
            }
            for row in st.session_state.table
        ]
    )
    st.dataframe(df, use_container_width=True)

if st.session_state.prophecy:
    st.write("### お告げ先")
    st.write(st.session_state.prophecy)