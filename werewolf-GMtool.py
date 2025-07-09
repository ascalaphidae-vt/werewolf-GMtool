 (cd "$(git rev-parse --show-toplevel)" && git apply --3way <<'EOF' 
diff --git a//dev/null b/werewolf_gm_tool.py
index 0000000000000000000000000000000000000000..c3603625def28054f22a08770fc5ea1e1b1833c8 100644
--- a//dev/null
+++ b/werewolf_gm_tool.py
@@ -0,0 +1,195 @@
+"""Streamlit app for assigning roles in a Werewolf game."""
+
+import random
+import json
+import pandas as pd
+import streamlit as st
+import streamlit.components.v1 as components
+
+st.set_page_config(page_title="人狼GM補助ツール", layout="wide")
+
+# --- ステート初期化 ---
+DEFAULT_NUM_PLAYERS = 9
+
+def init_state():
+    if "num_players" not in st.session_state:
+        st.session_state.num_players = DEFAULT_NUM_PLAYERS
+    if "roles" not in st.session_state:
+        st.session_state.roles = []
+    if "players" not in st.session_state:
+        st.session_state.players = ["" for _ in range(13)]
+    if "table" not in st.session_state:
+        st.session_state.table = []
+    if "prophecy" not in st.session_state:
+        st.session_state.prophecy = ""
+    if "bulk_names" not in st.session_state:
+        st.session_state.bulk_names = ""
+
+init_state()
+
+st.title("人狼GM補助ツール")
+
+# --- 入力内容の初期化 ---
+if st.button("入力内容の初期化"):
+    st.session_state.num_players = DEFAULT_NUM_PLAYERS
+    st.session_state.roles = []
+    st.session_state.players = ["" for _ in range(13)]
+    st.session_state.table = []
+    st.session_state.prophecy = ""
+    st.session_state.bulk_names = ""
+    if hasattr(st, "rerun"):
+        st.rerun()
+    else:
+        st.experimental_rerun()
+
+# --- 1. 参加者数入力 ---
+st.subheader("1. 参加者数の入力 (9～11人)")
+st.session_state.num_players = st.number_input(
+    "参加者数",
+    min_value=9,
+    max_value=11,
+    step=1,
+    value=st.session_state.num_players,
+)
+
+# --- 2. 役職テーブル決定 ---
+def set_role_table(num):
+    if num == 9:
+        return [
+            "人狼A",
+            "人狼B",
+            "狂人",
+            "占い",
+            "霊媒",
+            "騎士",
+            "村人A",
+            "村人B",
+            "村人C",
+        ]
+    if num == 10:
+        return [
+            "人狼A",
+            "人狼B",
+            "狂人",
+            "占い",
+            "霊媒",
+            "騎士",
+            "村人A",
+            "村人B",
+            "村人C",
+            "村人D",
+        ]
+    if num == 11:
+        return [
+            "人狼A",
+            "人狼B",
+            "人狼C",
+            "狂人",
+            "占い",
+            "霊媒",
+            "二丁拳銃",
+            "村人A",
+            "村人B",
+            "村人C",
+            "村人D",
+        ]
+    return []
+
+if st.button("役職テーブル決定"):
+    st.session_state.roles = set_role_table(st.session_state.num_players)
+
+if st.session_state.roles:
+    st.write("### 役職テーブル")
+    st.write(st.session_state.roles)
+
+# --- 3. 参加者名の一括入力 ---
+st.subheader("3. 参加者名を一括入力")
+st.session_state.bulk_names = st.text_input(
+    "カンマ区切りで入力",
+    value=st.session_state.bulk_names,
+)
+if st.button("反映"):
+    names = [n.strip() for n in st.session_state.bulk_names.split(",") if n.strip()]
+    for idx, name in enumerate(names):
+        if idx < len(st.session_state.players):
+            st.session_state.players[idx] = name
+
+# --- 4. 参加者名入力 ---
+st.subheader("4. 参加者名の入力")
+for i in range(13):
+    label = f"参加者{i+1}"
+    st.session_state.players[i] = st.text_input(
+        label,
+        value=st.session_state.players[i],
+        key=f"player_{i}",
+    )
+
+# --- 5. 発言順割り当て ---
+if st.button("発言順割り当て"):
+    selected = st.session_state.players[: st.session_state.num_players]
+    table = []
+    for name in selected:
+        rand_a = random.randint(1, 1000)
+        table.append({"name": name, "rand_a": rand_a})
+    table.sort(key=lambda x: x["rand_a"])
+    for idx, row in enumerate(table, 1):
+        row["order"] = f"{idx:02}"
+        row["rand_b"] = None
+        row["role"] = None
+    st.session_state.table = table
+
+# --- 6. 役職割り当て ---
+if st.button("役職割り当て") and st.session_state.roles and st.session_state.table:
+    table = st.session_state.table
+    for row in table:
+        row["rand_b"] = random.randint(1, 2000)
+    table.sort(key=lambda x: x["rand_b"])
+    for idx, row in enumerate(table):
+        row["role"] = st.session_state.roles[idx]
+    st.session_state.table = table
+
+# --- 7. お告げ決定 ---
+if st.button("お告げ決定") and st.session_state.roles:
+    choices = [r for r in st.session_state.roles if not r.startswith("人狼") and r != "占い"]
+    st.session_state.prophecy = random.choice(choices) if choices else ""
+
+if st.session_state.table:
+    copy_col1, copy_col2 = st.columns(2)
+    with copy_col1:
+        if st.button("発言順をコピーする"):
+            text = "\n".join(f"{row['order']}.{row['name']}" for row in st.session_state.table)
+            components.html(
+                f"<script>navigator.clipboard.writeText({json.dumps(text)});</script>",
+                height=0,
+            )
+            st.success("発言順をコピーしました")
+    with copy_col2:
+        if st.button("役職をコピーする"):
+            text = "\n".join(
+                f"{row['order']}.{row['name']}-{row.get('role')}" for row in st.session_state.table
+            )
+            components.html(
+                f"<script>navigator.clipboard.writeText({json.dumps(text)});</script>",
+                height=0,
+            )
+            st.success("役職をコピーしました")
+
+# --- 表示 ---
+if st.session_state.table:
+    df = pd.DataFrame(
+        [
+            {
+                "発言順": row.get("order"),
+                "参加者名": row.get("name"),
+                "役職": row.get("role"),
+                "乱数A": row.get("rand_a"),
+                "乱数B": row.get("rand_b"),
+            }
+            for row in st.session_state.table
+        ]
+    )
+    st.dataframe(df, use_container_width=True)
+
+if st.session_state.prophecy:
+    st.write("### お告げ先")
+    st.write(st.session_state.prophecy)
 
EOF
)