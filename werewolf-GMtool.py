#!/usr/bin/env python3
# coding: utf-8
"""
人狼GMアシストツール（堅牢版 / テーブル完全保持）
- 参加者数（9〜11）
- 役職テーブル（プリセット）→ 行ごと編集（テキスト＋お告げ除外チェック）
- 参加者名：一括入力（カンマ区切り）＋個別入力（各行は一意IDで管理）
- 発言順：乱数A(1-1000)で決定。リスト自体を並べ替え → “その順” を常に保持
- 役職割当：乱数B(1-2000)で決定。**並び替えず**「割り当てだけ」行う（順は不変）
- お告げ：チェックONは除外、候補からランダム
- コピー用テキスト：**完全に読み取り専用**（ボタン押下で順／割当は一切変化しない）
- 乱数は SystemRandom を使用
"""

import copy
import pandas as pd
import streamlit as st
from secrets import SystemRandom

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
    ss.setdefault("next_id", 1)             # 新規行に付与する一意ID
    ss.setdefault("table", [])              # list[dict]: id, name, order, role, randA, randB
    ss.setdefault("roles_base", [])         # プリセット原本
    ss.setdefault("roles_edit", [])         # [{No, role, omen_exclude}]
    ss.setdefault("bulk_names", "")
    ss.setdefault("omen", "")
    ss.setdefault("order_copy_text", "")
    ss.setdefault("role_copy_text", "")

    # 初回テーブル構築
    if not ss["table"]:
        for i in range(ss["count"]):
            ss["table"].append({
                "id": ss["next_id"],
                "name": f"プレイヤー{i+1}",
                "order": "",   # "01"..
                "role": "",
                "randA": 0,
                "randB": 0,
            })
            ss["next_id"] += 1

def _ensure_row_count(new_count: int):
    """行数を new_count に調整（順・割当は不変／末尾追加・末尾切り詰めのみ）"""
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
        # 末尾から切り詰め（順番は維持）
        ss["table"] = ss["table"][:new_count]

def _assign_order():
    """乱数A→昇順に**リストそのもの**を並べ替え＆order採番（以降の表示／コピーはこの順を使用）"""
    ss = st.session_state
    # 現在の範囲のみ（将来拡張しやすいように）
    rows = ss["table"]
    # 乱数Aを付与
    for r in rows:
        r["randA"] = rng.randrange(1, 1001)
    # 小さい順に並べ替え
    rows.sort(key=lambda r: r["randA"])
    # 01,02...を付与
    for idx, r in enumerate(rows, 1):
        r["order"] = f"{idx:02}"
    # ss["table"] は参照で書き換わっている（並び確定）

def _assign_roles():
    """乱数B→昇順に“割当順”を決定して、編集テーブルの上から役職を配布。
       **テーブルの順は変えない**（リストの並びは _assign_order で決まったまま）。
    """
    ss = st.session_state
    rows = ss["table"]
    if not ss["roles_edit"] or len(ss["roles_edit"]) != len(rows):
        st.error("役職テーブルの行数が参加者数と一致していません。『役職テーブル決定』から再設定してください。")
        return
    # 必須バリデーション
    blanks = [e["No"] for e in ss["roles_edit"] if not e["role"]]
    if blanks:
        st.error("未入力の役職があります → No: " + ", ".join(map(str, blanks)))
        return

    # 各行に乱数B
    for r in rows:
        r["randB"] = rng.randrange(1, 2001)

    # 割当順（乱数B昇順）のインデックス列を作る（並べ替えは**しない**）
    idx_sorted_by_B = sorted(range(len(rows)), key=lambda i: rows[i]["randB"])
    # 編集後の役職リスト（配布順）
    assign_roles = [e["role"] for e in ss["roles_edit"]]

    # 乱数B順に役職を付与するだけ
    for pos, row_idx in enumerate(idx_sorted_by_B):
        rows[row_idx]["role"] = assign_roles[pos]
    # 並びは不変（コピーや表示で順が変わらない）

def _current_df():
    """現在のテーブル順のまま DataFrame を作る（ソートしない）"""
    ss = st.session_state
    rows = ss["table"]
    return pd.DataFrame([{
        "発言順": r["order"],
        "参加者名": r["name"],
        "役職": r["role"],
        "乱数A": r["randA"],
        "乱数B": r["randB"],
    } for r in rows])

def _copy_texts():
    """コピー用テキストを生成（読み取り専用：テーブルは一切変更しない）"""
    ss = st.session_state
    rows = ss["table"]
    # エッジ：発言順が未割当なら弾く
    if not rows or any(r["order"] == "" for r in rows):
        st.warning("先に『発言順割り当て』を実行してね。")
        return

    # 堅牢化：念のためスナップショットを取ってから生成（復元は不要だが安全のため残せる）
    snapshot = copy.deepcopy(rows)

    order_text = "\n".join(f"{r['order']}.{r['name']}" for r in rows)
    role_text  = "\n".join(f"{r['order']}.{r['name']}-{r['role']}" for r in rows)

    ss["order_copy_text"] = order_text
    ss["role_copy_text"] = role_text

    # rows は一切変更していないので、順／割当は不変（snapshot未使用）

# ──────────────────────────────────────────────────────────
# UI 開始
# ──────────────────────────────────────────────────────────
st.set_page_config(page_title="人狼GMアシストツール", layout="wide")
_init_state()

st.title("🐺 人狼GMアシストツール")
st.markdown(
    '<div style="font-size:0.9rem; opacity:0.8; margin-top:-0.6rem;">by '
    '<a href="https://x.com/Ascalaphidae" target="_blank">あすとらふぃーだ</a></div>',
    unsafe_allow_html=True,
)

# 初期化ボタン
if st.button("入力内容の初期化", type="secondary"):
    st.session_state.clear()
    _init_state()
    st.rerun()

# ① 参加者数
st.subheader("① 参加者数を入力")
count = st.number_input("参加者数 (9〜11)", 9, 11, value=st.session_state.count, key="count")
if count != len(st.session_state.table):
    _ensure_row_count(count)

# ② 役職テーブル決定 → 編集
st.subheader("② 役職テーブル決定 → 編集")
if st.button("役職テーブル決定（プリセット読込）", key="set_roles"):
    st.session_state.roles_base = ROLE_TABLES[count]
    st.session_state.roles_edit = [
        {"No": i + 1, "role": r, "omen_exclude": _default_excluded(r)}
        for i, r in enumerate(st.session_state.roles_base)
    ]
    st.success("役職テーブルを読み込みました")

# 編集UI
if st.session_state.roles_edit:
    st.caption("※ 各行を編集できます（役職名／お告げ除外）")
    new_edit = []
    for i, row in enumerate(st.session_state.roles_edit):
        c1, c2, c3 = st.columns([0.5, 2.5, 1.2])
        with c1:
            st.number_input(" ", value=row["No"], disabled=True, label_visibility="hidden", key=f"er_no_{i}")
        with c2:
            role_val = st.text_input(" ", value=row["role"], label_visibility="hidden", key=f"er_role_{i}")
        with c3:
            ex_val = st.checkbox(" ", value=row["omen_exclude"], key=f"er_ex_{i}")
        new_edit.append({"No": i + 1, "role": role_val.strip(), "omen_exclude": ex_val})
    st.session_state.roles_edit = new_edit
    st.dataframe(pd.DataFrame(st.session_state.roles_edit), use_container_width=True)

# ③-1 参加者名を一括入力
st.subheader("③-1 参加者名を一括入力（カンマ区切り）")
st.session_state.bulk_names = st.text_input(
    "例： あおはだ,いしがけ,うすばき,えさきもんつの,おお,からす,きべり,くだまき,けぶか",
    value=st.session_state.bulk_names,
    key="bulk_names_input",
)
if st.button("一括反映", key="apply_bulk_names"):
    names = [n.strip() for n in st.session_state.bulk_names.split(",") if n.strip()]
    for i in range(len(st.session_state.table)):
        if i < len(names):
            st.session_state.table[i]["name"] = names[i]
        else:
            st.session_state.table[i]["name"] = f"プレイヤー{i+1}"
    st.success("一括入力を反映しました")

# ③-2 参加者名を個別入力（行は一意IDで固定）
st.subheader("③-2 参加者名を個別入力")
cols = st.columns((1, 1))
for i, row in enumerate(st.session_state.table):
    with cols[i % 2]:
        key = f"name_{row['id']}"  # 並び替え後もキーがズレない
        default = st.session_state.get(key, row["name"])
        st.session_state[key] = st.text_input(f"参加者 {i+1}", value=default, key=key)
        row["name"] = st.session_state[key].strip() if st.session_state[key].strip() else f"プレイヤー{i+1}"

# ④ 発言順（乱数A→昇順→リストそのものを並べ替え）
st.subheader("④ 発言順を決める")
if st.button("発言順割り当て", key="set_order"):
    _assign_order()
    st.success("発言順を更新しました！（この順は以降も保持されます）")

# ⑤ 役職割り当て（乱数B→昇順で配布のみ／並びは不変）
st.subheader("⑤ 役職を配る")
if st.button("役職割り当て", key="set_roles_to_players"):
    if not st.session_state.roles_edit:
        st.error("役職テーブルを決定してください")
    else:
        _assign_roles()
        st.success("役職を割り当てました！（発言順の並びは変わりません）")

# ⑥ お告げ
st.subheader("⑥ お告げを決定")
if st.button("お告げ決定", key="set_omen"):
    if not st.session_state.roles_edit:
        st.error("役職テーブルがありません")
    else:
        candidates = [r["role"] for r in st.session_state.roles_edit if not r["omen_exclude"]]
        if not candidates:
            st.error("候補がありません（お告げ除外にチェックを入れすぎていませんか？）")
        else:
            st.session_state.omen = rng.choice(candidates)
            st.success("お告げ先を決定しました！")
if st.session_state.omen:
    st.info(f"**お告げ先（役職）** : {st.session_state.omen}")

# ⑦ 最終テーブル（常に“現在の並び”のまま表示） & コピー用
st.subheader("最終テーブル")
df_view = _current_df()
st.dataframe(df_view, use_container_width=True)

# コピー用テキストの生成（**読み取り専用**で順や割当は一切変更しない）
c1, c2 = st.columns(2)
with c1:
    if st.button("発言順をコピー用に生成"):
        _copy_texts()
with c2:
    if st.button("役職をコピー用に生成"):
        _copy_texts()

if st.session_state.order_copy_text:
    st.text_area("発言順コピー用テキスト", st.session_state.order_copy_text, height=150)
if st.session_state.role_copy_text:
    st.text_area("役職コピー用テキスト", st.session_state.role_copy_text, height=200)
