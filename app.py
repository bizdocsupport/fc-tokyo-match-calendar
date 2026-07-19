from __future__ import annotations

import html
import json
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote

import pandas as pd
import requests
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
LOCAL_DATA_PATH = BASE_DIR / "data" / "schedule_sample.csv"

DEFAULT_TICKET_APP_URL = "https://club-ticket-navi-fctokyo-test.streamlit.app/"

PUBLIC_COLUMNS = [
    "match_id",
    "team",
    "competition",
    "round",
    "status",
    "candidate_start",
    "candidate_end",
    "candidate_dates",
    "confirmed_date",
    "kickoff",
    "duration_minutes",
    "home_away",
    "opponent",
    "venue",
    "official_url",
    "ticket_url",
    "note",
    "enabled",
]


def get_secret(name: str, default: str = "") -> str:
    try:
        value = st.secrets.get(name, default)
    except Exception:
        value = default
    return str(value or "").strip()


MASTER_API_URL = get_secret("MASTER_API_URL")
TOP_CALENDAR_ID = get_secret("TOP_CALENDAR_ID")
U21_CALENDAR_ID = get_secret("U21_CALENDAR_ID")
TICKET_APP_URL = get_secret("TICKET_APP_URL", DEFAULT_TICKET_APP_URL)


st.set_page_config(
    page_title="FC東京 試合日程カレンダー",
    page_icon="🗓️",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def inject_css() -> None:
    st.markdown(
        """
<style>
:root {
  --fct-blue:#003b7a;
  --fct-blue-2:#005bac;
  --fct-red:#d7193f;
  --fct-soft:#f4f7fb;
  --fct-border:#d9e2ef;
  --fct-text:#172033;
}
.block-container {
  max-width: 1120px;
  padding-top: 2.1rem;
  padding-bottom: 3rem;
}
.hero {
  position: relative;
  overflow: hidden;
  padding: 30px 32px;
  border-radius: 22px;
  color: white;
  background:
    radial-gradient(circle at 88% 10%, rgba(255,255,255,.20), transparent 26%),
    linear-gradient(125deg, #002d63 0%, #004b98 63%, #b31538 100%);
  box-shadow: 0 14px 38px rgba(0,45,99,.18);
  margin-bottom: 22px;
}
.hero:after {
  content:"";
  position:absolute;
  width:220px;
  height:220px;
  right:-100px;
  bottom:-135px;
  border:28px solid rgba(255,255,255,.10);
  border-radius:50%;
}
.hero-kicker {
  font-size:.82rem;
  letter-spacing:.13em;
  font-weight:800;
  opacity:.86;
}
.hero h1 {
  color:white;
  font-size:clamp(2rem, 5vw, 3.3rem);
  margin:.25rem 0 .45rem;
  line-height:1.12;
}

.no-break {
  white-space: nowrap;
  
.hero p {
  margin:0;
  max-width:720px;
  font-size:1.02rem;
  line-height:1.7;
  opacity:.94;
}
.calendar-card {
  min-height:175px;
  border:1px solid var(--fct-border);
  border-radius:17px;
  padding:20px 20px 16px;
  background:white;
  box-shadow:0 6px 22px rgba(23,32,51,.06);
  margin-bottom:10px;
}
.calendar-card .label {
  display:inline-flex;
  padding:4px 9px;
  border-radius:999px;
  font-size:.75rem;
  font-weight:800;
  background:#eaf2fb;
  color:var(--fct-blue);
}
.calendar-card.u21 .label {
  background:#fff0f3;
  color:#b31538;
}
.calendar-card h3 {
  margin:.65rem 0 .35rem;
  font-size:1.35rem;
}
.calendar-card p {
  color:#5b6577;
  font-size:.91rem;
  line-height:1.55;
  margin-bottom:.2rem;
}
.info-strip {
  border-left:5px solid var(--fct-red);
  background:#fff7f8;
  padding:12px 15px;
  border-radius:8px;
  color:#4c2530;
  margin:8px 0 20px;
}
.match-card {
  border:1px solid var(--fct-border);
  border-radius:14px;
  padding:15px 17px;
  background:white;
  margin:0 0 18px;
  box-shadow:0 3px 13px rgba(23,32,51,.045);
}
.match-top {
  display:flex;
  align-items:center;
  gap:8px;
  flex-wrap:wrap;
}
.badge {
  display:inline-flex;
  align-items:center;
  padding:3px 8px;
  border-radius:999px;
  font-size:.72rem;
  font-weight:800;
}
.badge.confirmed { background:#e8f6ee; color:#187242; }
.badge.tentative { background:#fff4d7; color:#8b5b00; }
.badge.progress { background:#f1eaff; color:#6038a5; }
.badge.home { background:#eaf2ff; color:#1356a4; }
.badge.away { background:#fff0f1; color:#b12235; }
.match-date {
  font-weight:850;
  color:var(--fct-blue);
  font-size:1.1rem;
}
.match-title {
  font-size:1.05rem;
  font-weight:800;
  margin:.55rem 0 .32rem;
  color:var(--fct-text);
}
.match-meta {
  color:#5e6878;
  font-size:.86rem;
  line-height:1.55;
}
.match-note {
  margin-top:.55rem;
  padding-top:.55rem;
  border-top:1px dashed #d9e2ef;
  color:#687385;
  font-size:.82rem;
}
.link-row a {
  display:inline-block;
  margin:7px 13px 0 0;
  font-size:.82rem;
  font-weight:700;
}
.small-muted {
  color:#6b7585;
  font-size:.82rem;
}
[data-testid="stLinkButton"] a {
  font-weight:750;
}
@media (max-width: 700px) {
  .block-container {
    padding-left:1rem;
    padding-right:1rem;
    padding-top:1.25rem;
  }
  .hero {
    padding:23px 20px;
    border-radius:17px;
  }
  .hero h1 { font-size:2rem; }
  .calendar-card { min-height:0; }
}
</style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(ttl=600, show_spinner=False)
def load_remote_schedule(url: str) -> tuple[pd.DataFrame, str]:
    response = requests.get(
        url,
        timeout=18,
        headers={"User-Agent": "fc-tokyo-match-calendar/0.1"},
    )
    response.raise_for_status()

    content_type = response.headers.get("content-type", "").lower()
    if "json" in content_type or response.text.lstrip().startswith("{"):
        payload: dict[str, Any] = response.json()
        records = payload.get("data", payload.get("records", []))
        updated_at = str(payload.get("updated_at", ""))
        return pd.DataFrame(records), updated_at

    from io import StringIO
    return pd.read_csv(StringIO(response.text)), ""


def load_local_schedule() -> tuple[pd.DataFrame, str]:
    if not LOCAL_DATA_PATH.exists():
        return pd.DataFrame(columns=PUBLIC_COLUMNS), ""
    return pd.read_csv(LOCAL_DATA_PATH, dtype=str).fillna(""), "サンプルデータ"


def load_schedule() -> tuple[pd.DataFrame, str, str]:
    if MASTER_API_URL:
        try:
            df, updated_at = load_remote_schedule(MASTER_API_URL)
            return df, updated_at, "Googleスプレッドシート"
        except Exception as exc:
            local_df, _ = load_local_schedule()
            return local_df, "", f"API取得エラーのためサンプル表示：{exc}"

    local_df, updated_at = load_local_schedule()
    return local_df, updated_at, "同梱サンプル"


def normalize_schedule(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    for column in PUBLIC_COLUMNS:
        if column not in result.columns:
            result[column] = ""

    result = result[PUBLIC_COLUMNS].fillna("")
    for column in result.columns:
        result[column] = result[column].astype(str).str.strip()

    enabled = result["enabled"].str.lower()
    result = result[~enabled.isin({"false", "0", "no", "off", "無効"})].copy()

    result["display_start"] = result.apply(
        lambda row: row["confirmed_date"] or row["candidate_start"],
        axis=1,
    )
    result["_sort_date"] = pd.to_datetime(
        result["display_start"], errors="coerce"
    )
    result = result.sort_values(
        ["_sort_date", "team", "match_id"],
        kind="stable",
        na_position="last",
    )
    return result


def google_add_url(calendar_id: str) -> str:
    return (
        "https://calendar.google.com/calendar/u/0/r?cid="
        + quote(calendar_id, safe="")
    )


def ical_url(calendar_id: str) -> str:
    return (
        "https://calendar.google.com/calendar/ical/"
        + quote(calendar_id, safe="")
        + "/public/basic.ics"
    )


def parse_date(value: str) -> datetime | None:
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def format_date(value: str, include_year: bool = True) -> str:
    parsed = parse_date(value)
    if not parsed:
        return value or "未定"
    if include_year:
        return f"{parsed.year}/{parsed.month}/{parsed.day}"
    return f"{parsed.month}/{parsed.day}"


def format_schedule_date(row: pd.Series) -> str:
    if row["status"] == "確定" and row["confirmed_date"]:
        date_text = format_date(row["confirmed_date"])
        if row["kickoff"]:
            date_text += f" {row['kickoff']}"
        else:
            date_text += "（時間未定）"
        return date_text

    start = format_date(row["candidate_start"])
    end = format_date(row["candidate_end"])
    if row["candidate_start"] and row["candidate_end"]:
        if row["candidate_start"] == row["candidate_end"]:
            return f"{start}（候補日）"
        return f"{start}〜{end}（候補期間）"
    return "日時未定"


def status_class(status: str) -> tuple[str, str]:
    if status == "確定":
        return "confirmed", "確定"
    if status in {"進出時", "開催未定"}:
        return "progress", status
    return "tentative", status or "候補日あり"


def safe_link(url: str, label: str) -> str:
    if not url:
        return ""
    return (
        f'<a href="{html.escape(url, quote=True)}" '
        f'target="_blank" rel="noopener noreferrer">{html.escape(label)}</a>'
    )


def render_match_card(row: pd.Series) -> None:
    status_css, status_label = status_class(row["status"])
    side = row["home_away"].upper()
    side_css = "home" if side == "HOME" else "away" if side == "AWAY" else ""
    side_badge = (
        f'<span class="badge {side_css}">{html.escape(side)}</span>'
        if side
        else ""
    )

    team_name = "FC東京" if row["team"].upper() == "TOP" else "FC東京U-21"
    opponent = row["opponent"] or "対戦相手未定"
    title = f"{team_name} vs {opponent}"

    meta_parts = [
        value
        for value in [
            row["competition"],
            row["round"],
            row["venue"],
        ]
        if value
    ]
    meta = " ｜ ".join(html.escape(value) for value in meta_parts)

    candidate_detail = ""
    if row["candidate_dates"] and row["status"] != "確定":
        candidate_detail = (
            f'<div class="match-meta">候補日：'
            f'{html.escape(row["candidate_dates"])}</div>'
        )

    note = (
        f'<div class="match-note">{html.escape(row["note"])}</div>'
        if row["note"]
        else ""
    )

    link_row = ""

    st.markdown(
        f"""
<div class="match-card">
  <div class="match-top">
    <span class="match-date">{html.escape(format_schedule_date(row))}</span>
    <span class="badge {status_css}">{html.escape(status_label)}</span>
    {side_badge}
  </div>
  <div class="match-title">{html.escape(title)}</div>
  <div class="match-meta">{meta}</div>
  {candidate_detail}
  {note}
  {link_row}
</div>
        """,
        unsafe_allow_html=True,
    )


def render_team_schedule(df: pd.DataFrame, team: str) -> None:
    team_df = df[df["team"].str.upper() == team].copy()
    if team_df.empty:
        st.info(
            "このチームの日程はまだマスターに登録されていません。"
            "Googleスプレッドシートへ追加すると表示されます。"
        )
        return

    for _, row in team_df.iterrows():
        render_match_card(row)


inject_css()

st.markdown(
    """
<div class="hero">
  <div class="hero-kicker">FC TOKYO MATCH CALENDAR｜非公式</div>
  <h1>試合日程を、<span class="no-break">いつものカレンダーへ。</span></h1>
  <p>
    FC東京トップチームとFC東京U-21の日程を登録できます。
    日時未定の試合は候補期間を1件で表示し、確定後は同じ予定が正式日時へ更新されます。
  </p>
</div>
    """,
    unsafe_allow_html=True,
)

df_raw, updated_at, data_source = load_schedule()
df = normalize_schedule(df_raw)

if updated_at:
    st.caption(f"データ元：{data_source}｜最終更新：{updated_at}")
else:
    st.caption(f"データ元：{data_source}")

left, right = st.columns(2, gap="large")

with left:
    st.markdown(
        """
<div class="calendar-card">
  <span class="label">TOP TEAM</span>
  <h3>FC東京 トップチーム</h3>
  <p>リーグ戦・カップ戦など。日程変更時は登録済みカレンダーへ反映します。</p>
</div>
        """,
        unsafe_allow_html=True,
    )
    if TOP_CALENDAR_ID:
        st.link_button(
            "Googleカレンダーに追加",
            google_add_url(TOP_CALENDAR_ID),
            use_container_width=True,
            type="primary",
        )
        with st.expander("Appleカレンダー・Outlookで登録"):
            st.code(ical_url(TOP_CALENDAR_ID), language=None)
    else:
        st.button(
            "Googleカレンダーに追加（初期設定後に有効）",
            disabled=True,
            use_container_width=True,
        )

with right:
    st.markdown(
        """
<div class="calendar-card u21">
  <span class="label">U-21</span>
  <h3>FC東京U-21</h3>
  <p>確定日程と候補期間を掲載。複数候補日は、横長の仮予定1件として登録します。</p>
</div>
        """,
        unsafe_allow_html=True,
    )
    if U21_CALENDAR_ID:
        st.link_button(
            "Googleカレンダーに追加",
            google_add_url(U21_CALENDAR_ID),
            use_container_width=True,
            type="primary",
        )
        with st.expander("Appleカレンダー・Outlookで登録"):
            st.code(ical_url(U21_CALENDAR_ID), language=None)
    else:
        st.button(
            "Googleカレンダーに追加（初期設定後に有効）",
            disabled=True,
            use_container_width=True,
        )

st.markdown(
    """
<div class="info-strip">
  <strong>未確定日程の扱い：</strong>
  例として「2/27・2/28・3/1」の場合は、2/27〜3/1の終日予定を1件登録します。
  2/28 14:00に決まったら、その予定を削除せず同じ予定IDのまま更新します。
</div>
    """,
    unsafe_allow_html=True,
)

ticket_col, guide_col = st.columns([1, 1], gap="large")
with ticket_col:
    st.subheader("チケット発売日も確認")
    st.write(
        "トップチームのチケット発売予定は、既存のチケットナビから確認できます。"
    )
    st.link_button(
        "FC東京 チケット発売日ナビを開く",
        TICKET_APP_URL,
        use_container_width=True,
    )

with guide_col:
    st.subheader("登録後の更新")
    st.write(
        "Googleカレンダーを追加した後は、マスター更新に合わせて予定が更新されます。"
        "個別の試合予定をコピーする方式ではありません。"
    )

st.divider()
st.subheader("掲載中の日程")

show_finished = st.checkbox("終了済みの日程も表示", value=False)
view_df = df.copy()
if not show_finished and not view_df.empty:
    today = pd.Timestamp.now(tz="Asia/Tokyo").tz_localize(None).normalize()
    view_df = view_df[
        view_df["_sort_date"].isna() | (view_df["_sort_date"] >= today)
    ].copy()

top_tab, u21_tab = st.tabs(["トップチーム", "FC東京U-21"])
with top_tab:
    render_team_schedule(view_df, "TOP")
with u21_tab:
    render_team_schedule(view_df, "U21")

with st.expander("このサービスについて"):
    st.markdown(
        """
- FC東京公式サービスではありません。
- 日程・会場・キックオフ時刻は必ずクラブ・大会主催者の公式発表をご確認ください。
- Googleカレンダーの公開設定や組織アカウントの制約により、登録できない場合があります。
- 初版ではチケット発売日ナビとはリンク連携です。将来は同じ試合IDを使って情報連携できます。
        """
    )
