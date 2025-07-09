#!/usr/bin/env python3
# coding: utf-8
"""Streamlit app for assigning roles in a Werewolf game."""

import random
import pandas as pd
import streamlit as st


def main() -> None:
    """Run the Streamlit app."""
    st.set_page_config(page_title="人狼GM補助ツール", layout="wide")

    DEFAULT_NUM_PLAYERS = 9

    def init_state() -> None:
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
        if "bulk_names" not in st.session_state:
            st.session_state.bulk_names = ""
        if "order_copy_text" not in st.session_state:
            st.session_state.order_copy_text = ""
        if "role_copy_text" not in st.session_state:
            st.session_state.role_copy_text = ""

    init_state()

    st.title("人狼GM補助ツール")

    if st.button("入力内容の初期化"):
        st.session_state.num_players = DEFAULT_NUM_PLAYERS
        st.session_state.roles = []
        st.session_state.players = ["" for _ in range(13)]
        st.session_state.table = []
        st.session_state.prophecy = ""
        st.session_state.bulk_names = ""
        st.session_state.order_copy_text = ""
        st.session_state.role_copy_text = ""
        if hasattr(st, "rerun"):
            st.rerun()
        else:
            st.experimental_rerun()

    st.subheader("1. 参加者数の入力 (9～11人)")
    st.session_state.num_players = st.number_input(
        "参加者数",
        min_value=9,
        max_value=11,
        step=1,
        value=st.session_state.num_players,
    )

    def set_role_table(num: int):
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

    st.subheader("3. 参加者名を一括入力")
    st.session_state.bulk_names = st.text_input(
        "カンマ区切りで入力",
        value=st.session_state.bulk_names,
    )
    if st.button("反映"):
        names = [n.strip() for n in st.session_state.bulk_names.split(",") if n.strip()]
        for idx, name in enumerate(names):
            if idx < len(st.session_state.players):
                st.session_state.players[idx] = name

    st.subheader("4. 参加者名の入力")
    for i in range(13):
        label = f"参加者{i+1}"
        st.session_state.players[i] = st.text_input(
            label,
            value=st.session_state.players[i],
            key=f"player_{i}",
        )

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

    if st.button("役職割り当て") and st.session_state.roles and st.session_state.table:
        table = st.session_state.table
        for row in table:
            row["rand_b"] = random.randint(1, 2000)
        table.sort(key=lambda x: x["rand_b"])
        for idx, row in enumerate(table):
            row["role"] = st.session_state.roles[idx]
        st.session_state.table = table

    if st.button("お告げ決定") and st.session_state.roles:
        choices = [r for r in st.session_state.roles if not r.startswith("人狼") and r != "占い"]
        st.session_state.prophecy = random.choice(choices) if choices else ""

    if st.session_state.table:
        order_text = "\n".join(
            f"{row['order']}.{row['name']}" for row in st.session_state.table
        )
        role_text = "\n".join(
            f"{row['order']}.{row['name']}-{row.get('role')}" for row in st.session_state.table
        )

        copy_col1, copy_col2 = st.columns(2)
        with copy_col1:
            if st.button("発言順をコピーする"):
                st.session_state.order_copy_text = order_text
        with copy_col2:
            if st.button("役職をコピーする"):
                st.session_state.role_copy_text = role_text

        if st.session_state.order_copy_text:
            st.text_area("発言順コピー用テキスト", st.session_state.order_copy_text, height=150)
        if st.session_state.role_copy_text:
            st.text_area("役職コピー用テキスト", st.session_state.role_copy_text, height=200)

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


if __name__ == "__main__":
    main()