from __future__ import annotations

import html

import streamlit as st

PUBLIC_URL = "https://fctokyo.xyz/calendar/"

st.set_page_config(
    page_title="FC東京 試合日程カレンダー",
    page_icon="🗓️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

safe_url = html.escape(PUBLIC_URL, quote=True)

# 旧Streamlit URLに来た利用者を新サイトへ自動転送する。
st.markdown(
    f'''
    <meta http-equiv="refresh" content="0; url={safe_url}">
    <script>
      window.location.replace({PUBLIC_URL!r});
    </script>
    <div style="padding:2rem 0;text-align:center;font-family:sans-serif;">
      <h2>FC東京 試合日程カレンダーは移転しました</h2>
      <p>新しいURLへ移動します。</p>
      <p><a href="{safe_url}" target="_self">{safe_url}</a></p>
    </div>
    ''',
    unsafe_allow_html=True,
)

st.link_button("新しい試合日程カレンダーを開く", PUBLIC_URL)
st.stop()
