#!/usr/bin/env python3
# coding: utf-8
"""Streamlit app for assigning roles in a Werewolf game (役職編集つき)."""

import random
import pandas as pd
import streamlit as st


def main() -> None:
    """Run the Streamlit app."""
    st.set_page_config(page_title="人狼GM補助ツール", layout="wide")

    DEFAULT_NUM_PLAYERS = 9

    # ─────────────────────────────────
    # Session State 初期化
    # ─────────────────────────────────
    def init_state() -> None:
        if "num_players" not in st.session_state:
            st.session_state.num_players = DEFAULT_NUM_PLAYERS
        if "roles" not in st.session_state:
            st.session_state.roles = []
        # 役職編集用：[{ "No": 1, "role": "人狼A", "omen_exclude": True }, ...]
        if "editable_roles" not in st.session_state:
            st.session_state.editable_roles = []
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

    # タイトル＋Xリンク（控えめサイズ）
    st.title("人狼GM補助ツール")
    st.markdown(
        '<div style="font-size:0.9rem; opacity:0.8; margin-top:-0.6rem;">by '
        '<a href="https://x.com/Ascalaphidae" target="_blank">あすとらふぃーだ</a></div>',
        unsafe_allow_html=True,
    )

    # 全消し
    if st.button("入力内容の初期化"):
        st.session_state.num_players = DEFAULT_NUM_PLAYERS
        st.session_state.roles = []
        st.session_state.editable_roles = []
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

    # ─────────────────────────────────
    # 1. 参加者数
    # ─────────────────────────────────
    st.subheader("1. 参加者数の入力 (9～11人)")
    st.session_state.num_players = st.number_input(
        "参加者数",
        min_value=9,
        max_value=11,
        step=1,
        value=st.session_state.num_players,
    )

    # ─────────────────────────────────
    # 役職プリセット
    # ─────────────────────────────────
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

    # お告げ除外の初期値ルール
    def default_omen_exclude(role: str) -> bool:
        return role in {"人狼A", "人狼B", "人狼C", "占い"}

    # ─────────────────────────────────
    # 2. 役職テーブル決定 → 編集可能リスト化
    # ─────────────────────────────────
    if st.button("役職テーブル決定"):
        st.session_state.roles = set_role_table(st.session_state.num_players)
        st.session_state.editable_roles = [
            {"No": i + 1, "role": r, "omen_exclude": default_omen_exclude(r)}
            for i, r in enumerate(st.session_state.roles)
        ]

    # プリセットの確認表示
    if st.session_state.roles:
        st.write("### 役職テーブル（プリセット）")
        st.write(st.session_state.roles)

    # 編集可能リストUI（行ごとテキスト＋チェック）
    if st.session_state.editable_roles:
        st.write("### 役職テーブルを編集（行ごと）")
        st.caption("※ 役職名は個別に編集できます。お告げ除外のチェックONは候補から除外します。")
        new_list = []
        for i, row in enumerate(st.session_state.editable_roles):
            c1, c2, c3 = st.columns([0.5, 2.5, 1.5])
            with c1:
                st.number_input("No", value=row["No"], disabled=True, key=f"er_no_{i}")
            with c2:
                role_val = st.text_input("役職名", value=row["role"], key=f"er_role_{i}")
            with c3:
                ex_val = st.checkbox("お告げ除外", value=row["omen_exclude"], key=f"er_ex_{i}")
            new_list.append({"No": i + 1, "role": role_val.strip(), "omen_exclude": ex_val})
        st.session_state.editable_roles = new_list

        # 現在の編集内容プレビュー
        st.dataframe(
            pd.DataFrame(st.session_state.editable_roles),
            use_container_width=True,
        )

    # ─────────────────────────────────
    # 3. 参加者名：一括入力
    # ─────────────────────────────────
    st.subheader("③-1 参加者名を一括入力（カンマ区切り）")
    st.session_state.bulk_names = st.text_input(
        "例： あおはだ,いしがけ,うすばき,えさきもんつの,おお,からす,きべり,くだまき,けぶか",
        value=st.session_state.bulk_names,
        key="bulk_names_input",
    )
    if st.button("反映"):
        names = [n.strip() for n in st.session_state.bulk_names.split(",") if n.strip()]
        for idx, name in enumerate(names):
            if idx < len(st.session_state.players):
                st.session_state.players[idx] = name

    # ─────────────────────────────────
    # 4. 参加者名：個別入力（常時13枠）
    # ─────────────────────────────────
    st.subheader("4. 参加者名の入力")
    for i in range(13):
        label = f"参加者{i+1}"
        st.session_state.players[i] = st.text_input(
            label,
            value=st.session_state.players[i],
            key=f"player_{i}",
        )

    # ─────────────────────────────────
    # 発言順割り当て（乱数A）
    # ─────────────────────────────────
    if st.button("発言順割り当て"):
        selected = st.session_state.players[: st.session_state.num_players]
        table = []
        for name in selected:
            rand_a = random.randint(1, 1000)
            table.append({"name": name if name else "", "rand_a": rand_a})
        table.sort(key=lambda x: x["rand_a"])
        for idx, row in enumerate(table, 1):
            row["order"] = f"{idx:02}"
            row["rand_b"] = None
            row["role"] = None
        st.session_state.table = table

    # ─────────────────────────────────
    # 役職割り当て（編集リストを参照）
    # ─────────────────────────────────
    if st.button("役職割り当て") and st.session_state.table:
        # 役職のソースは「編集可能リスト」。未設定ならプリセットを利用。
        if st.session_state.editable_roles:
            role_source = [r["role"] for r in st.session_state.editable_roles]
        else:
            role_source = st.session_state.roles

        # 行数チェック（人数と役職数のズレ防止）
        if not role_source or len(role_source) != len(st.session_state.table):
            st.error("役職テーブルの行数が参加者数と一致していません。『役職テーブル決定』→必要なら編集を調整してください。")
        else:
            table = st.session_state.table
            for row in table:
                row["rand_b"] = random.randint(1, 2000)
            table.sort(key=lambda x: x["rand_b"])
            for idx, row in enumerate(table):
                row["role"] = role_source[idx]
            st.session_state.table = table

    # ─────────────────────────────────
    # お告げ決定（編集リストのフラグで除外）
    # ─────────────────────────────────
    if st.button("お告げ決定"):
        # 候補リストは編集可能リストの「omen_exclude == False」を採用
        candidates = []
        if st.session_state.editable_roles:
            candidates = [r["role"] for r in st.session_state.editable_roles if not r["omen_exclude"]]
        else:
            # 編集機能が未使用なら、従来の除外ルール
            if st.session_state.roles:
                candidates = [r for r in st.session_state.roles if not (r.startswith("人狼") or r == "占い")]

        st.session_state.prophecy = random.choice(candidates) if candidates else ""
        if not candidates:
            st.warning("お告げ候補がありません（お告げ除外にチェックを入れすぎていないか確認してね）")

    # ─────────────────────────────────
    # コピー用テキスト（読み取りのみ）
    # ─────────────────────────────────
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

    # ─────────────────────────────────
    # 表示
    # ─────────────────────────────────
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
