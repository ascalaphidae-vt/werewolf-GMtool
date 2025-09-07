#!/usr/bin/env python3
# coding: utf-8
"""
人狼GMアシストツール（堅牢版 v1.1）
- 参加者数（9〜11）
- 役職テーブル（プリセット）→ 行ごと編集（テキスト＋お告げ除外チェック）
- 参加者名：一括入力（カンマ区切り）＋個別入力（各行は一意IDで管理）
- 発言順：乱数A(1-1000)で決定、リスト順で保持（以後の表示/コピーはこの順）
- 役職割当：乱数B(1-2000)で決定、配布のみ（並びは不変）
- お告げ：チェックONは除外
- コピー用テキスト：読み取り専用（順/割当は不変）
- 乱数は SystemRandom を使用
"""

import copy
import pandas as pd
import streamlit as st
from secrets import SystemRandom

st.set_page_config(page_title="人狼GMアシストツール", layout="wide")

rng = SystemRandom()

ROLE_TABLES = {
    9:  ["人狼A", "人狼B", "狂人", "占い", "霊媒", "騎士", "村人A", "村人B", "村人C"],
    10: ["人狼A", "人狼B", "狂人", "占い", "霊媒", "騎士", "村人A", "村人B", "村人C", "村人D"],
    11: ["人狼A", "人狼B", "人狼C", "狂人", "占い", "霊媒", "二丁拳銃", "村人A", "村人B", "村人C", "村人D"],
}

def _default_excluded(role: str) -> bool:
    return role in {"人狼A", "人狼B", "人狼C", "占い"}

def _init_state():
    ss = st.session_state
    ss.setdefault("count", 9)
    ss.setdefault("table", [])          # list[dict]: id, name, order, role, randA, randB
    ss.setdefault("next_id", 1)
    ss.setdefault("roles_base", [])
    ss.setdefault("roles_edit", [])     # [{No, role, omen_exclude}]
    ss.setdefault("bulk_names", "")
    ss.setdefault("omen", "")
    ss.setdefault("order_copy_text", "")
    ss.setdefault("role_copy_text", "")

    if not ss["table"]:
        for i in range(ss["count"]):
            ss["table"].append({
                "id": ss["next_id"],
                "name": f"プレイヤー{i+1}",
                "order": "",
                "role": "",
                "randA": 0,
                "randB": 0,
            })
            ss["next_id"] += 1

def _ensure_row_count(new_count: int):
    ss = st.session_state
    cur = len(ss["table"])
    if new_count > cur:
        for i in range(cur, new_count):
            ss["table"].append({
                "id": ss["next_id"],
                "name": f"プレイヤー{i+1}",
                "order": "",
                "role": "",
                "randA": 0,
                "randB": 0,
            })
            ss["next_id"] += 1
    elif new_count < cur:
        ss["table"] = ss["table"][:new_count]

def _assign_order():
    ss = st.session_state
    rows = ss["table"]
    for r in rows:
        r["randA"] = rng.randrange(1, 1001)
    rows.sort(key=lambda r: r["randA"])
    for idx, r in enumerate(rows, 1):
        r["order"] = f"{idx:02}"

def _assign_roles():
    ss = st.session_state
    rows = ss["table"]
    if not ss["roles_edit"] or len(ss["roles_edit"]) != len(rows):
        st.error("役職テーブルの行数が参加者数と一致していません。『役職テーブル決定』から再設定してください。")
        return
    blanks = [e["No"] for e in ss["roles_edit"] if not e["role"]]
    if blanks:
        st.error("未入力の役職があります → No: " + ", ".join(map(str, blanks)))
        return

    for r in rows:
        r["randB"] = rng.randrange(1, 2001)
    idx_sorted_by_B = sorted(range(len(rows)), key=lambda i: rows[i]["randB"])
    assign_roles = [e["role"] for e in ss["roles_edit"]]
    for pos, row_idx in enumerate(idx_sorted_by_B):
        rows[row_idx]["role"] = assign_roles[pos]

def _current_df():
    rows = st.session_state["table"]
    return pd.DataFrame([{
        "発言順": r["order"],
        "参加者名": r["name"],
        "役職": r["role"],
        "乱数A": r["randA"],
        "乱数B": r["randB"],
    } for r in rows])

def _copy_texts():
    ss = st.session_state
    rows = ss["table"]
    if not rows or any(r["order"] == "" for r in rows):
        st.warning("先に『発言順割り当て』を実行してね。")
        return
    # 読み取り専用（副作用なし）
    order_text = "\n".join(f"{r['order']}.{r['name']}" for r in rows)
    role_text  = "\n".join(f"{r['order']}.{r['name']}-{r['role']}" for r in rows)
    ss["order_copy_text"] = order_text
    ss["role_copy_text"] = role_text

# ── UI ─────────────────────────────────────────────────────
_init_state()

st.title("🐺 人狼GMアシストツール")
st.markdown(
    '<div style="font-size:0.9rem; opacity:0.8; margin-top:-0.6rem;">by '
    '<a href="https://x.com/Ascalaphidae" target="_blank">あすとらふぃーだ</a></div>',
    unsafe_allow_html=True,
)

if st.button("入力内容の初期化", type="secondary"):
    st.session_state.clear()
    _init_state()
    st.rerun()

# ① 参加者数
st.subheader("① 参加者数を入力")
count = st.number_input("参加者数 (9〜11)", 9, 11, value=st.session_state["count"], key="count")
if count != len(st.session_state["table"]):
    st.session_state["count"] = count
    _ensure_row_count(count)

# ② 役職テーブル決定 → 編集
st.subheader("② 役職テーブル決定 → 編集")
if st.button("役職テーブル決定（プリセット読込）", key="set_roles"):
    st.session_state["roles_base"] = ROLE_TABLES[count]
    st.session_state["roles_edit"] = [
        {"No": i + 1, "role": r, "omen_exclude": _default_excluded(r)}
        for i, r in enumerate(st.session_state["roles_base"])
    ]
    st.success("役職テーブルを読み込みました")

if st.session_state["roles_edit"]:
    st.caption("※ 各行を編集できます（役職名／お告げ除外）")
    new_edit = []
    for i, row in enumerate(st.session_state["roles_edit"]):
        c1, c2, c3 = st.columns([0.5, 2.5, 1.2])
        with c1:
            st.number_input(" ", value=row["No"], disabled=True, label_visibility="hidden", key=f"er_no_{i}")
        with c2:
            role_val = st.text_input(" ", value=row["role"], label_visibility="hidden", key=f"er_role_{i}")
        with c3:
            ex_val = st.checkbox(" ", value=row["omen_exclude"], key=f"er_ex_{i}")
        new_edit.append({"No": i + 1, "role": role_val.strip(), "omen_exclude": ex_val})
    st.session_state["roles_edit"] = new_edit
    st.dataframe(pd.DataFrame(st.session_state["roles_edit"]), use_container_width=True)

# ③-1 一括入力
st.subheader("③-1 参加者名を一括入力（カンマ区切り）")
st.session_state["bulk_names"] = st.text_input(
    "例： あおはだ,いしがけ,うすばき,えさきもんつの,おお,からす,きべり,くだまき,けぶか",
    value=st.session_state["bulk_names"],
    key="bulk_names_input",
)
if st.button("一括反映", key="apply_bulk_names"):
    names = [n.strip() for n in st.session_state["bulk_names"].split(",") if n.strip()]
    for i in range(len(st.session_state["table"])):
        st.session_state["table"][i]["name"] = names[i] if i < len(names) else f"プレイヤー{i+1}"
    st.success("一括入力を反映しました")

# ③-2 個別入力（※ widgetのkey=行ID、session_stateへの直接代入はしない）
st.subheader("③-2 参加者名を個別入力")
cols = st.columns((1, 1))
for i, row in enumerate(st.session_state["table"]):
    with cols[i % 2]:
        key = f"name_{row['id']}"
        default = row["name"]
        val = st.text_input(f"参加者 {i+1}", value=default, key=key)
        row["name"] = val.strip() if val.strip() else f"プレイヤー{i+1}"

# ④ 発言順（乱数A→昇順→リスト順を直接並べ替え）
st.subheader("④ 発言順を決める")
if st.button("発言順割り当て", key="set_order"):
    _assign_order()
    st.success("発言順を更新しました！（この順は以降も保持されます）")

# ⑤ 役職割り当て（乱数B→昇順で配布のみ／並びは不変）
st.subheader("⑤ 役職を配る")
if st.button("役職割り当て", key="set_roles_to_players"):
    if not st.session_state["roles_edit"]:
        st.error("役職テーブルを決定してください")
    else:
        _assign_roles()
        st.success("役職を割り当てました！（発言順の並びは変わりません）")

# ⑥ お告げ
st.subheader("⑥ お告げを決定")
if st.button("お告げ決定", key="set_omen"):
    if not st.session_state["roles_edit"]:
        st.error("役職テーブルがありません")
    else:
        candidates = [r["role"] for r in st.session_state["roles_edit"] if not r["omen_exclude"]]
        if not candidates:
            st.error("候補がありません（お告げ除外にチェックを入れすぎていませんか？）")
        else:
            st.session_state["omen"] = rng.choice(candidates)
            st.success("お告げ先を決定しました！")
if st.session_state["omen"]:
    st.info(f"**お告げ先（役職）** : {st.session_state['omen']}")

# ⑦ 最終テーブル（現在のリスト順のまま） & コピー用
st.subheader("最終テーブル")
st.dataframe(_current_df(), use_container_width=True)

c1, c2 = st.columns(2)
with c1:
    if st.button("発言順をコピー用に生成"):
        _copy_texts()
with c2:
    if st.button("役職をコピー用に生成"):
        _copy_texts()

if st.session_state["order_copy_text"]:
    st.text_area("発言順コピー用テキスト", st.session_state["order_copy_text"], height=150)
if st.session_state["role_copy_text"]:
    st.text_area("役職コピー用テキスト", st.session_state["role_copy_text"], height=200)
