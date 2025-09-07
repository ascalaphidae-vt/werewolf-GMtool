import streamlit as st
import pandas as pd
from secrets import SystemRandom

# ──────────────────────────────────────────────────────────
#  人狼GMアシストツール  ver.0.3.4
#   - 役職編集（B案：各行 TextInput + お告げ除外）
#   - 参加者名の一括入力（カンマ区切り）＋個別入力
#   - 発言順コピー／役職コピー用テキストの改行修正
#   - コピー生成ボタンで順番・割当が変化しないようスナップショット固定
# ──────────────────────────────────────────────────────────

rng = SystemRandom()

ROLE_TABLES = {
    9: ["人狼A", "人狼B", "狂人", "占い", "霊媒", "騎士", "村人A", "村人B", "村人C"],
    10: ["人狼A", "人狼B", "狂人", "占い", "霊媒", "騎士", "村人A", "村人B", "村人C", "村人D"],
    11: ["人狼A", "人狼B", "人狼C", "狂人", "占い", "霊媒", "二丁拳銃", "村人A", "村人B", "村人C", "村人D"],
}

# ─────────────────────
# SessionState 初期化
# ─────────────────────
if "count" not in st.session_state:
    st.session_state.count = 9
if "roles" not in st.session_state:
    st.session_state.roles = []
if "editable_roles" not in st.session_state:
    st.session_state.editable_roles = []  # [{No, role, omen_exclude}]
if "names" not in st.session_state:
    st.session_state.names = []
if "df" not in st.session_state:
    st.session_state.df = pd.DataFrame()
if "df_initialized" not in st.session_state:
    st.session_state.df_initialized = False  # 不用意な再生成を防ぐ
if "omen" not in st.session_state:
    st.session_state.omen = ""
if "bulk_names" not in st.session_state:
    st.session_state.bulk_names = ""
if "order_copy_text" not in st.session_state:
    st.session_state.order_copy_text = ""
if "role_copy_text" not in st.session_state:
    st.session_state.role_copy_text = ""
if "order_snapshot" not in st.session_state:
    st.session_state.order_snapshot = None  # ['01','02',...] を保持してコピー時に使用

# ─────────────────────
# UI レイアウト
# ─────────────────────
st.set_page_config(page_title="人狼GMアシストツール", layout="wide")
st.title("🐺 人狼GMアシストツール")
st.markdown(
    '<div style="font-size:0.9rem; opacity:0.8; margin-top:-0.6rem;">by <a href="https://x.com/Ascalaphidae" target="_blank">あすとらふぃーだ</a></div>',
    unsafe_allow_html=True,
)

# 初期化ボタン
if st.button("入力内容の初期化", type="secondary"):
    st.session_state.count = 9
    st.session_state.roles = []
    st.session_state.editable_roles = []
    st.session_state.names = []
    st.session_state.df = pd.DataFrame()
    st.session_state.df_initialized = False
    st.session_state.omen = ""
    st.session_state.bulk_names = ""
    st.session_state.order_copy_text = ""
    st.session_state.role_copy_text = ""
    st.session_state.order_snapshot = None
    st.rerun()

# ① 参加者数入力
st.subheader("① 参加者数を入力")
count = st.number_input("参加者数 (9〜11)", 9, 11, value=st.session_state.count, key="count")

# ② 役職テーブル決定 → 編集
st.subheader("② 役職テーブル決定 → 編集")
if st.button("役職テーブル決定（プリセット読込）", key="set_roles"):
    st.session_state.roles = ROLE_TABLES[count]
    def _default_excluded(r: str) -> bool:
        return r in {"人狼A", "人狼B", "人狼C", "占い"}
    st.session_state.editable_roles = [
        {"No": i + 1, "role": r, "omen_exclude": _default_excluded(r)}
        for i, r in enumerate(st.session_state.roles)
    ]
    st.success("役職テーブルを読み込みました")

# 編集UI（B案：行ごと TextInput + Checkbox）
if st.session_state.editable_roles:
    st.caption("※ 各行を編集できます（役職名／お告げ除外）")
    new_list = []
    for i, row in enumerate(st.session_state.editable_roles):
        c1, c2, c3 = st.columns([0.5, 2.5, 1.2])
        with c1:
            st.number_input(" ", value=row["No"], disabled=True, label_visibility="hidden", key=f"er_no_{i}")
        with c2:
            role_val = st.text_input(" ", value=row["role"], label_visibility="hidden", key=f"er_role_{i}")
        with c3:
            ex_val = st.checkbox(" ", value=row["omen_exclude"], key=f"er_ex_{i}")
        new_list.append({"No": i + 1, "role": role_val.strip(), "omen_exclude": ex_val})
    st.session_state.editable_roles = new_list
    st.dataframe(pd.DataFrame(st.session_state.editable_roles), use_container_width=True)

# ③-1 参加者名一括入力
st.subheader("③-1 参加者名を一括入力（カンマ区切り）")
st.session_state.bulk_names = st.text_input(
    "例： あおはだ,いしがけ,うすばき,えさきもんつの,おお,からす,きべり,くだまき,けぶか",
    value=st.session_state.bulk_names,
    key="bulk_names_input",
)
if st.button("一括反映", key="apply_bulk_names"):
    names = [n.strip() for n in st.session_state.bulk_names.split(",") if n.strip()]
    st.session_state.names = []
    for i in range(count):
        st.session_state.names.append(names[i] if i < len(names) else f"プレイヤー{i+1}")
        st.session_state[f"name_{i}"] = st.session_state.names[i]
    st.success("一括入力を反映しました")

# ③-2 個別入力
st.subheader("③-2 参加者名を個別入力")
name_cols = st.columns((1, 1))
st.session_state.names = []
for i in range(count):
    with name_cols[i % 2]:
        default_name = st.session_state.get(f"name_{i}", f"プレイヤー{i+1}")
        name = st.text_input(f"参加者 {i+1}", value=default_name, key=f"name_{i}")
        st.session_state.names.append(name.strip() if name.strip() else f"プレイヤー{i+1}")

# DataFrame 確保（順番保護／最小変更）
if not st.session_state.df_initialized:
    st.session_state.df = pd.DataFrame({
        "発言順": [""] * count,
        "参加者名": st.session_state.names if st.session_state.names else [f"プレイヤー{i+1}" for i in range(count)],
        "役職": [""] * count,
        "乱数A": [0] * count,
        "乱数B": [0] * count,
    })
    st.session_state.df_initialized = True
else:
    df = st.session_state.df.copy()
    cur = len(df)
    if cur < count:
        add = pd.DataFrame({
            "発言順": [""] * (count - cur),
            "参加者名": [f"プレイヤー{i+1}" for i in range(cur, count)],
            "役職": [""] * (count - cur),
            "乱数A": [0] * (count - cur),
            "乱数B": [0] * (count - cur),
        })
        df = pd.concat([df, add], ignore_index=True)
    elif cur > count:
        df = df.iloc[:count].copy().reset_index(drop=True)
    # 名前だけ最新に（行順は維持）
    if st.session_state.names:
        new_names = st.session_state.names + [f"プレイヤー{i+1}" for i in range(len(st.session_state.names), count)]
        df.loc[:count-1, "参加者名"] = new_names[:count]
    st.session_state.df = df

# ④ 発言順を決める（乱数A 昇順→01,02…）
st.subheader("④ 発言順を決める")
if st.button("発言順割り当て", key="set_order"):
    randA = [rng.randrange(1, 1001) for _ in range(count)]
    df = st.session_state.df.copy()
    df["乱数A"] = randA
    df = df.sort_values("乱数A").reset_index(drop=True)
    df["発言順"] = df.index.map(lambda x: f"{x + 1:02}")
    st.session_state.df = df
    st.session_state.order_snapshot = df["発言順"].tolist()  # 並びを固定
    st.success("発言順を更新しました！")

# ⑤ 役職を配る（乱数B 昇順→編集後テーブル順で配布→表示は発言順に戻す）
st.subheader("⑤ 役職を配る")
if st.button("役職割り当て", key="set_roles_to_players"):
    if not st.session_state.editable_roles:
        st.error("役職テーブルを決定してください")
    else:
        blanks = [r["No"] for r in st.session_state.editable_roles if not r["role"]]
        if blanks:
            st.error("未入力の役職があります: " + ", ".join(map(str, blanks)))
        else:
            randB = [rng.randrange(1, 2001) for _ in range(count)]
            df = st.session_state.df.copy()
            df["乱数B"] = randB
            df = df.sort_values("乱数B").reset_index(drop=True)
            assigned_roles = [row["role"] for row in st.session_state.editable_roles]
            df["役職"] = assigned_roles
            # 表示順を発言順スナップショットに合わせて戻す
            if st.session_state.order_snapshot is not None:
                snap = st.session_state.order_snapshot
                if "発言順" not in df.columns or df["発言順"].eq("").any():
                    df["発言順"] = df.index.map(lambda x: f"{x + 1:02}")
                df = df.set_index("発言順").reindex(snap).reset_index()
            else:
                df = df.sort_values("発言順").reset_index(drop=True)
            st.session_state.df = df
            st.success("役職を割り当てました！")

# ⑥ お告げ（チェックONは候補から除外）
st.subheader("⑥ お告げを決定")
if st.button("お告げ決定", key="set_omen"):
    if not st.session_state.editable_roles:
        st.error("役職リストがありません")
    else:
        candidates = [r["role"] for r in st.session_state.editable_roles if not r["omen_exclude"]]
        if not candidates:
            st.error("候補がありません")
        else:
            st.session_state.omen = rng.choice(candidates)
            st.success("お告げ先を決定しました！")
if st.session_state.omen:
    st.info(f"**お告げ先（役職）** : {st.session_state.omen}")

# ⑦ 最終テーブル & コピー用テキスト（コピー時は読み取り専用でDFを変更しない）
st.subheader("最終テーブル")
if not st.session_state.df.empty:
    if st.session_state.order_snapshot is not None and "発言順" in st.session_state.df.columns:
        snap = st.session_state.order_snapshot
        df_view = st.session_state.df.set_index("発言順").reindex(snap).reset_index()
    else:
        df_view = st.session_state.df.copy()
        if (df_view["発言順"] != "").any():
            df_view = df_view.sort_values("発言順").reset_index(drop=True)
        else:
            df_view = df_view.reset_index(drop=True)
    st.dataframe(df_view, use_container_width=True)

# コピー用テキストの生成（順番・割当は一切変更しない）
if not st.session_state.df.empty and st.session_state.order_snapshot is not None:
    snap = st.session_state.order_snapshot
    df_sorted = st.session_state.df.set_index("発言順").reindex(snap).reset_index()
    order_text = "
".join(
        f"{row['発言順']}.{row['参加者名']}" for _, row in df_sorted.iterrows()
    )
    role_text = "
".join(
        f"{row['発言順']}.{row['参加者名']}-{row['役職'] if row['役職'] else ''}" for _, row in df_sorted.iterrows()
    )
    c1, c2 = st.columns(2)
    with c1:
        if st.button("発言順をコピー用に生成"):
            st.session_state.order_copy_text = order_text
    with c2:
        if st.button("役職をコピー用に生成"):
            st.session_state.role_copy_text = role_text
    if st.session_state.order_copy_text:
        st.text_area("発言順コピー用テキスト", st.session_state.order_copy_text, height=150)
    if st.session_state.role_copy_text:
        st.text_area("役職コピー用テキスト", st.session_state.role_copy_text, height=200)
