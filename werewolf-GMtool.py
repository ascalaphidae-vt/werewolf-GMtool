import streamlit as st
import pandas as pd
from secrets import SystemRandom

# ──────────────────────────────────────────────────────────
#  人狼GMアシストツール  ver.0.3（役職編集B案 + 一括名前入力 + コピー用テキスト）
#  author: ChatGPT (o3)
# ──────────────────────────────────────────────────────────
#  機能概要
#  1. 参加者数（9〜11）入力
#  2. 役職テーブル生成（固定3パターン）→ 行ごと編集（B案: 個別 TextInput + Checkbox）
#  3. 参加者名「一括入力」＋「個別入力」
#  4. 発言順割り当て（乱数A: 1〜1000）
#  5. 役職割り当て（乱数B: 1〜2000, 乱数B 昇順で編集後テーブルからロール付与）
#  6. お告げ決定（チェックONの役職を候補から除外してランダム選出）
#  7. 最終テーブル表示 + コピー用テキスト（発言順/役職）
# ──────────────────────────────────────────────────────────

rng = SystemRandom()

ROLE_TABLES = {
    9: [
        "人狼A", "人狼B", "狂人", "占い", "霊媒", "騎士",
        "村人A", "村人B", "村人C",
    ],
    10: [
        "人狼A", "人狼B", "狂人", "占い", "霊媒", "騎士",
        "村人A", "村人B", "村人C", "村人D",
    ],
    11: [
        "人狼A", "人狼B", "人狼C", "狂人", "占い", "霊媒",
        "二丁拳銃", "村人A", "村人B", "村人C", "村人D",
    ],
}

# ─────────────────────
# SessionState 初期化
# ─────────────────────
if "count" not in st.session_state:
    st.session_state.count = 9
if "roles" not in st.session_state:
    st.session_state.roles = []  # プリセット原本
if "editable_roles" not in st.session_state:
    # 編集用: list[dict(No:int, role:str, omen_exclude:bool)]
    st.session_state.editable_roles = []
if "names" not in st.session_state:
    st.session_state.names = []
if "df" not in st.session_state:
    st.session_state.df = pd.DataFrame()
if "omen" not in st.session_state:
    st.session_state.omen = ""
# 追加（旧版から統合）
if "bulk_names" not in st.session_state:
    st.session_state.bulk_names = ""
if "order_copy_text" not in st.session_state:
    st.session_state.order_copy_text = ""
if "role_copy_text" not in st.session_state:
    st.session_state.role_copy_text = ""

# ─────────────────────
# UI レイアウト
# ─────────────────────
st.set_page_config(page_title="人狼GMアシストツール", layout="wide")
st.title("🐺 人狼GMアシストツール")
st.markdown(
    '<div style="font-size:0.9rem; opacity:0.8; margin-top:-0.6rem;">by <a href="https://x.com/Ascalaphidae" target="_blank">あすとらふぃーだ</a></div>',
    unsafe_allow_html=True,
)

# 全消去（旧版の初期化ボタンを統合）
if st.button("入力内容の初期化", type="secondary"):
    st.session_state.count = 9
    st.session_state.roles = []
    st.session_state.editable_roles = []
    st.session_state.names = []
    st.session_state.df = pd.DataFrame()
    st.session_state.omen = ""
    st.session_state.bulk_names = ""
    st.session_state.order_copy_text = ""
    st.session_state.role_copy_text = ""
    st.rerun()

# 1️⃣ 参加者数入力
st.subheader("① 参加者数を入力")
count = st.number_input("参加者数 (9〜11)", 9, 11, value=st.session_state.count, key="count")

# 2️⃣ 役職テーブル決定（プリセット→編集用へ展開）
st.subheader("② 役職テーブル決定 → 編集")
col2a, col2b = st.columns([1,1])
with col2a:
    if st.button("役職テーブル決定（プリセット読込）", key="set_roles"):
        st.session_state.roles = ROLE_TABLES[count]
        # 既定のお告げ除外: 人狼A/B/C と 占い
        def _default_excluded(r: str) -> bool:
            return r in {"人狼A", "人狼B", "人狼C", "占い"}
        st.session_state.editable_roles = [
            {"No": i + 1, "role": r, "omen_exclude": _default_excluded(r)}
            for i, r in enumerate(st.session_state.roles)
        ]
        st.success("役職テーブルを読み込み、編集用リストを初期化しました！")
with col2b:
    if st.button("役職テーブルを既定に戻す", key="reset_roles_default") and st.session_state.roles:
        base = ROLE_TABLES[count]
        def _default_excluded(r: str) -> bool:
            return r in {"人狼A", "人狼B", "人狼C", "占い"}
        st.session_state.editable_roles = [
            {"No": i + 1, "role": r, "omen_exclude": _default_excluded(r)}
            for i, r in enumerate(base)
        ]
        st.success("編集用リストを既定の内容に戻しました。")

# 編集 UI（B案：行ごとに TextInput + Checkbox）
if st.session_state.editable_roles:
    st.caption("※ 各行を個別に編集できます（役職名／お告げ除外）。行数は人数に固定されます。")
    cols = st.columns([0.5, 2.5, 1.2])  # No / 役職 / お告げ除外
    with cols[0]:
        st.markdown("**No**")
    with cols[1]:
        st.markdown("**役職（編集可）**")
    with cols[2]:
        st.markdown("**お告げ除外**")

    new_list = []
    for i in range(len(st.session_state.editable_roles)):
        row = st.session_state.editable_roles[i]
        c1, c2, c3 = st.columns([0.5, 2.5, 1.2])
        with c1:
            st.number_input(" ", value=row["No"], label_visibility="hidden", disabled=True, key=f"er_no_{i}")
        with c2:
            role_val = st.text_input(" ", value=row["role"], label_visibility="hidden", key=f"er_role_{i}")
        with c3:
            ex_val = st.checkbox(" ", value=row["omen_exclude"], key=f"er_ex_{i}")
        new_list.append({"No": i + 1, "role": role_val.strip(), "omen_exclude": ex_val})
    st.session_state.editable_roles = new_list

    # 現在の編集内容のプレビュー
    st.dataframe(
        pd.DataFrame(st.session_state.editable_roles),
        use_container_width=True,
    )
else:
    if st.session_state.roles:
        st.dataframe(
            pd.DataFrame({"No": range(1, len(st.session_state.roles) + 1), "役職": st.session_state.roles}),
            use_container_width=True,
        )

# 3️⃣-1 参加者名を一括入力（旧版機能を統合：カンマ区切り）
st.subheader("③-1 参加者名を一括入力（カンマ区切り）")
st.session_state.bulk_names = st.text_input(
    "例： あす, らふぃ, テレみ, はろ, しらつゆ",
    value=st.session_state.bulk_names,
    key="bulk_names_input",
)
if st.button("一括反映", key="apply_bulk_names"):
    names = [n.strip() for n in st.session_state.bulk_names.split(",") if n.strip()]
    # names を現在の人数に収まる範囲で適用
    st.session_state.names = []
    for i in range(count):
        if i < len(names):
            st.session_state.names.append(names[i])
        else:
            st.session_state.names.append(f"プレイヤー{i + 1}")
    # 個別入力フィールドにも反映されるよう、既存の name_i に直接代入
    for i, nm in enumerate(st.session_state.names):
        st.session_state[f"name_{i}"] = nm
    st.success("一括入力を反映しました。")

# 3️⃣-2 参加者名の個別入力（人数ぶん生成）
st.subheader("③-2 参加者名を個別入力")
name_cols = st.columns((1, 1))
st.session_state.names = []
for i in range(count):
    with name_cols[i % 2]:
        # 既に name_i に値がある場合はそれを初期値に使う
        default_name = st.session_state.get(f"name_{i}", f"プレイヤー{i + 1}")
        name = st.text_input(f"参加者 {i + 1}", value=default_name, key=f"name_{i}")
        st.session_state.names.append(name.strip() if name.strip() else f"プレイヤー{i + 1}")

# DataFrame を確保（人数変化にも追随）
if st.session_state.df.empty or len(st.session_state.df) != count:
    st.session_state.df = pd.DataFrame(
        {
            "発言順": [""] * count,
            "参加者名": st.session_state.names,
            "役職": [""] * count,
            "乱数A": [0] * count,
            "乱数B": [0] * count,
        }
    )
else:
    # 名前は最新入力で常に更新
    st.session_state.df["参加者名"] = st.session_state.names

# 4️⃣ 発言順割り当て（乱数A → 昇順 → 01,02…）
st.subheader("④ 発言順を決める")
if st.button("発言順割り当て", key="set_order"):
    randA = [rng.randrange(1, 1001) for _ in range(count)]
    df = pd.DataFrame({"参加者名": st.session_state.names, "乱数A": randA})
    df = df.sort_values("乱数A").reset_index(drop=True)
    df["発言順"] = df.index.map(lambda x: f"{x + 1:02}")
    # 既存の役職・乱数B は保持
    if "役職" in st.session_state.df.columns:
        df["役職"] = st.session_state.df["役職"]
    else:
        df["役職"] = [""] * count
    if "乱数B" in st.session_state.df.columns:
        df["乱数B"] = st.session_state.df["乱数B"]
    else:
        df["乱数B"] = [0] * count
    st.session_state.df = df
    st.success("発言順を更新しました！")

# 5️⃣ 役職割り当て（乱数B → 昇順 → 編集後テーブル上から配る）
st.subheader("⑤ 役職を配る")
if st.button("役職割り当て", key="set_roles_to_players"):
    if not st.session_state.editable_roles:
        st.error("先に『役職テーブル決定（プリセット読込）』で編集用リストを用意してね！")
    else:
        # 役職名のバリデーション（空文字の検出）
        blanks = [r["No"] for r in st.session_state.editable_roles if not r["role"]]
        if blanks:
            st.error(f"役職名が未入力の行があります → No: {', '.join(map(str, blanks))}")
        elif len(st.session_state.editable_roles) != count:
            st.error("編集用役職リストの行数が参加者数と一致していません。プリセットの再読み込みを行ってください。")
        else:
            randB = [rng.randrange(1, 2001) for _ in range(count)]
            df = st.session_state.df.copy()
            df["乱数B"] = randB
            # 乱数Bの小さい順に並べる
            df = df.sort_values("乱数B").reset_index(drop=True)
            assigned_roles = [row["role"] for row in st.session_state.editable_roles]
            df["役職"] = assigned_roles  # 昇順で割付
            # 表示は発言順に戻す
            df = df.sort_values("発言順").reset_index(drop=True)
            st.session_state.df = df
            st.success("役職を割り当てました！")

# 6️⃣ お告げ決定（チェックONは候補から除外）
st.subheader("⑥ お告げを決定")
if st.button("お告げ決定", key="set_omen"):
    if not st.session_state.editable_roles:
        st.error("編集用役職リストがありません。先に役職テーブルを用意してね！")
    else:
        candidates = [r["role"] for r in st.session_state.editable_roles if not r["omen_exclude"]]
        if not candidates:
            st.error("お告げ候補がありません（除外にチェックを入れすぎていませんか？）")
        else:
            st.session_state.omen = rng.choice(candidates)
            st.success("お告げ先を決定しました！")

if st.session_state.omen:
    st.info(f"**お告げ先（役職）** : {st.session_state.omen}")

# 7️⃣ 最終テーブル & コピー用テキスト
st.subheader("最終テーブル")
st.dataframe(st.session_state.df, use_container_width=True)

if not st.session_state.df.empty and st.session_state.df["発言順"].iloc[0] != "":
    # 現在の並び（発言順昇順）でコピー文面を作成
    df_sorted = st.session_state.df.sort_values("発言順").reset_index(drop=True)
    order_text = "\\n".join(
        f"{row['発言順']}.{row['参加者名']}" for _, row in df_sorted.iterrows()
    )
    role_text = "\\n".join(
        f"{row['発言順']}.{row['参加者名']}-{row['役職'] if row['役職'] else ''}"
        for _, row in df_sorted.iterrows()
    )
    copy_col1, copy_col2 = st.columns(2)
    with copy_col1:
        if st.button("発言順をコピー用に生成"):
            st.session_state.order_copy_text = order_text
    with copy_col2:
        if st.button("役職をコピー用に生成"):
            st.session_state.role_copy_text = role_text

    if st.session_state.order_copy_text:
        st.text_area("発言順コピー用テキスト", st.session_state.order_copy_text, height=150)
    if st.session_state.role_copy_text:
        st.text_area("役職コピー用テキスト", st.session_state.role_copy_text, height=200)

