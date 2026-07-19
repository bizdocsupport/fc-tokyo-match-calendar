# 既存のチケット発売日ナビへカレンダーリンクを追加する

初版では、2つのStreamlitアプリを相互リンクする方法が安全です。

## site_config.py に追加

FC東京版の設定へ次を追加します。

```python
"match_calendar_url": "https://公開後のカレンダーアプリURL.streamlit.app/",
```

## app.py に追加

チケットナビのタイトル直下、または試合一覧の前に追加します。

```python
match_calendar_url = TEAM.get("match_calendar_url", "").strip()

if match_calendar_url:
    st.link_button(
        "試合日程をGoogleカレンダーに追加",
        match_calendar_url,
        use_container_width=True,
    )
```

横並びにする場合：

```python
col1, col2 = st.columns(2)

with col1:
    st.link_button(
        "FC東京公式 チケット情報",
        TEAM["ticket_news_url"],
        use_container_width=True,
    )

with col2:
    st.link_button(
        "試合日程をGoogleカレンダーに追加",
        TEAM["match_calendar_url"],
        use_container_width=True,
    )
```

## 将来のデータ連携

チケットナビの `match_key` と、日程カレンダーの `match_id` を同じ値にします。

これだけ先に合わせておけば、後から日程とチケット発売日を結合しやすくなります。
