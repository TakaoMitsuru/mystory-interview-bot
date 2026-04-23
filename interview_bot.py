"""
マイストーリー インタビューBot v2
ホロスコープ完全統合版
"""

import streamlit as st
from anthropic import Anthropic
import json
import datetime

# ── ライブラリチェック ──────────────────────────────────────
try:
    from kerykeion import AstrologicalSubject
    from kerykeion.aspects import NatalAspects
    KERYKEION_OK = True
except Exception:
    KERYKEION_OK = False

try:
    from geopy.geocoders import Nominatim
    GEOPY_OK = True
except Exception:
    GEOPY_OK = False

# ── 定数 ───────────────────────────────────────────────────
client = Anthropic()
MODEL  = "claude-opus-4-7"

SIGN_JP = {
    "Aries":"牡羊座","Taurus":"牡牛座","Gemini":"双子座",
    "Cancer":"蟹座","Leo":"獅子座","Virgo":"乙女座",
    "Libra":"天秤座","Scorpio":"蠍座","Sagittarius":"射手座",
    "Capricorn":"山羊座","Aquarius":"水瓶座","Pisces":"魚座",
}
HOUSE_NUM = {
    "First_House":1,"Second_House":2,"Third_House":3,
    "Fourth_House":4,"Fifth_House":5,"Sixth_House":6,
    "Seventh_House":7,"Eighth_House":8,"Ninth_House":9,
    "Tenth_House":10,"Eleventh_House":11,"Twelfth_House":12,
}
ASPECT_JP = {
    "conjunction":"コンジャンクション(0°)",
    "sextile":"セクスタイル(60°)",
    "square":"スクエア(90°)",
    "trine":"トライン(120°)",
    "opposition":"オポジション(180°)",
    "quincunx":"クインカンクス(150°)",
}
PLANET_JP = {
    "Sun":"太陽","Moon":"月","Mercury":"水星","Venus":"金星",
    "Mars":"火星","Jupiter":"木星","Saturn":"土星",
    "Uranus":"天王星","Neptune":"海王星","Pluto":"冥王星",
    "True_Node":"ノース・ノード","Mean_Node":"ノース・ノード",
    "Chiron":"カイロン",
}
TZ_OPTIONS = {
    "日本 (JST, UTC+9)": "Asia/Tokyo",
    "中国・台湾 (CST, UTC+8)": "Asia/Shanghai",
    "インド (IST, UTC+5:30)": "Asia/Kolkata",
    "中欧 (CET, UTC+1)": "Europe/Berlin",
    "UK (GMT, UTC+0)": "Europe/London",
    "米東部 (EST, UTC-5)": "America/New_York",
    "米中部 (CST, UTC-6)": "America/Chicago",
    "米西部 (PST, UTC-8)": "America/Los_Angeles",
    "ブラジル (BRT, UTC-3)": "America/Sao_Paulo",
}

# ── 章の構成 ───────────────────────────────────────────────
CHAPTER_STRUCTURE = [
    {
        "id": "hajimeni", "title": "✨ はじめに", "icon": "✨",
        "sections": [
            "① 簡単なプロフィール", "② 実績",
            "③ 上梓しようと思った背景・理由",
            "④ 本書のターゲット", "⑤ 本書を読んで得られるベネフィット",
        ],
    },
    {
        "id": "chapter1", "title": "第1章 幼少期〜社会人", "icon": "🌱",
        "sections": [
            "① 生まれ育った環境【幼少期・原体験】",
            "② 学生時代の思い出【青春時代・葛藤と成長】",
            "③ 青春の葛藤と目覚め",
            "④ 社会人としての第一歩",
            "⑤ 自分らしさの芽生え",
        ],
    },
    {
        "id": "chapter2", "title": "第2章 違和感と変化", "icon": "⚡",
        "sections": [
            "① 日常から冒険に出るまで【転機・覚悟の瞬間】",
            "② 恐怖と迷い、そして覚悟",
        ],
    },
    {
        "id": "chapter3", "title": "第3章 失敗の連続", "icon": "🔥",
        "sections": [
            "① メンターとの出会い",
            "② 困難や失敗の連続にめげそうになったこと",
        ],
    },
    {
        "id": "chapter4", "title": "第4章 試練と成功体験", "icon": "💪",
        "sections": [
            "① 支えてくれた仲間の存在",
            "② 裏切りや喪失",
            "③ 変化・成長",
        ],
    },
    {
        "id": "chapter5", "title": "第5章 最大の試練", "icon": "🏔️",
        "sections": [
            "① ラスボス（最大の壁）",
            "② 突破と成功",
        ],
    },
    {
        "id": "chapter6", "title": "第6章 これからの未来", "icon": "🌟",
        "sections": [
            "① この経験を経て、どんな未来を生きたいですか？",
            "② どんな人にあなたの経験を伝えていきたいですか？",
        ],
    },
    {
        "id": "owari", "title": "おわりに", "icon": "🎉",
        "sections": [
            "① 読者への感謝",
            "② 自分の成功には再現性があることを強調",
            "③ 「次はあなたの番」と励ましのエンディング",
        ],
    },
]
TOTAL_SECTIONS = sum(len(ch["sections"]) for ch in CHAPTER_STRUCTURE)


# ── ホロスコープ計算 ───────────────────────────────────────
def geocode_city(city_name):
    if not GEOPY_OK:
        return None, None
    try:
        geo = Nominatim(user_agent="mystory_interview_bot_v2", timeout=10)
        loc = geo.geocode(city_name)
        if loc:
            return round(loc.latitude, 4), round(loc.longitude, 4)
    except Exception:
        pass
    return None, None


def _safe(planet, attr, default="—"):
    try:
        return getattr(planet, attr)
    except Exception:
        return default


def build_horoscope_text(subject, city_name, birth_str):
    lines = []
    lines.append("═" * 48)
    lines.append("【ホロスコープデータ】")
    lines.append(f"出生：{birth_str}　出生地：{city_name}")
    lines.append("═" * 48)

    # 主要ポイント
    lines.append("\n【主要ポイント】")
    for label, planet in [
        ("太陽", subject.sun), ("月", subject.moon),
    ]:
        sign = SIGN_JP.get(_safe(planet, "sign", ""), _safe(planet, "sign", ""))
        pos  = _safe(planet, "position", 0)
        h    = HOUSE_NUM.get(str(_safe(planet, "house", "")), _safe(planet, "house", ""))
        lines.append(f"  {label}：{sign} {pos:.1f}°（第{h}ハウス）")

    for label, house_obj in [
        ("ASC（上昇点）", subject.first_house),
        ("MC（中天）",   subject.tenth_house),
    ]:
        sign = SIGN_JP.get(_safe(house_obj, "sign", ""), _safe(house_obj, "sign", ""))
        pos  = _safe(house_obj, "position", 0)
        lines.append(f"  {label}：{sign} {pos:.1f}°")

    try:
        nn = subject.true_node
        sign = SIGN_JP.get(_safe(nn, "sign", ""), _safe(nn, "sign", ""))
        pos  = _safe(nn, "position", 0)
        h    = HOUSE_NUM.get(str(_safe(nn, "house", "")), _safe(nn, "house", ""))
        lines.append(f"  ノース・ノード：{sign} {pos:.1f}°（第{h}ハウス）")
    except Exception:
        pass

    # 全天体
    lines.append("\n【全天体の位置】")
    planet_map = [
        ("太陽",   subject.sun),
        ("月",     subject.moon),
        ("水星",   subject.mercury),
        ("金星",   subject.venus),
        ("火星",   subject.mars),
        ("木星",   subject.jupiter),
        ("土星",   subject.saturn),
        ("天王星", subject.uranus),
        ("海王星", subject.neptune),
        ("冥王星", subject.pluto),
    ]
    try:
        planet_map.append(("ノース・ノード", subject.true_node))
    except Exception:
        pass
    try:
        planet_map.append(("カイロン", subject.chiron))
    except Exception:
        pass

    for name_jp, planet in planet_map:
        try:
            sign  = SIGN_JP.get(_safe(planet, "sign", ""), _safe(planet, "sign", ""))
            pos   = _safe(planet, "position", 0)
            h     = HOUSE_NUM.get(str(_safe(planet, "house", "")), _safe(planet, "house", ""))
            retro = "（逆行）" if _safe(planet, "retrograde", False) else ""
            lines.append(f"  {name_jp}：{sign} {pos:.1f}°　第{h}ハウス{retro}")
        except Exception:
            lines.append(f"  {name_jp}：データなし")

    # ハウスカスプ
    lines.append("\n【ハウスカスプ（Placidus）】")
    house_objs = [
        subject.first_house, subject.second_house, subject.third_house,
        subject.fourth_house, subject.fifth_house, subject.sixth_house,
        subject.seventh_house, subject.eighth_house, subject.ninth_house,
        subject.tenth_house, subject.eleventh_house, subject.twelfth_house,
    ]
    h_labels = [
        "Ⅰ(ASC)","Ⅱ","Ⅲ","Ⅳ(IC)","Ⅴ","Ⅵ",
        "Ⅶ(DSC)","Ⅷ","Ⅸ","Ⅹ(MC)","Ⅺ","Ⅻ"
    ]
    for i, (ho, lbl) in enumerate(zip(house_objs, h_labels), 1):
        try:
            sign = SIGN_JP.get(_safe(ho, "sign", ""), _safe(ho, "sign", ""))
            pos  = _safe(ho, "position", 0)
            lines.append(f"  第{i}ハウス {lbl}：{sign} {pos:.1f}°")
        except Exception:
            lines.append(f"  第{i}ハウス：データなし")

    # アスペクト
    lines.append("\n【主要アスペクト】")
    try:
        natal = NatalAspects(subject)
        aspects = natal.relevant_aspects
        for asp in aspects[:25]:
            p1 = PLANET_JP.get(str(asp.p1_name), str(asp.p1_name))
            p2 = PLANET_JP.get(str(asp.p2_name), str(asp.p2_name))
            asp_jp = ASPECT_JP.get(str(asp.aspect), str(asp.aspect))
            orb = abs(float(asp.orbit)) if hasattr(asp, "orbit") else 0
            lines.append(f"  {p1} ☽ {asp_jp} ☽ {p2}（オーブ {orb:.1f}°）")
    except Exception as e:
        lines.append(f"  アスペクト計算エラー: {e}")

    lines.append("═" * 48)
    return "\n".join(lines)


def calculate_horoscope(name, year, month, day, hour, minute, lat, lon, tz_str, city_name):
    if not KERYKEION_OK:
        return None, "kerykeionライブラリが必要です。requirements.txtを確認してください。"
    try:
        subject = AstrologicalSubject(
            name, year, month, day, hour, minute,
            lat=lat, lng=lon, tz_str=tz_str
        )
        birth_str = f"{year}年{month}月{day}日 {hour:02d}:{minute:02d}"
        text = build_horoscope_text(subject, city_name, birth_str)
        return text, None
    except Exception as e:
        return None, f"計算エラー: {e}"


# ── システムプロンプト ────────────────────────────────────
def build_system_prompt(horoscope_text=None):
    prompt = "あなたは電子書籍出版プロデューサーのインタビュアーです。クライアントの「マイストーリー」を引き出す優秀なヒアリングの専門家です。\n"

    if horoscope_text:
        prompt += f"""
{horoscope_text}

【ホロスコープの活用方針】
このホロスコープデータを常に参照しながらインタビューを進めてください。

■ 各天体の意味：
- 太陽星座：核となる自己・人生の目的・意志の方向性
- 月星座：感情パターン・幼少期の記憶・家族との絆・安心の源
- ASC（上昇点）：外向きの自己表現・人生のスタイル・第一印象
- MC（中天）：キャリア・社会的役割・天職・目標
- 水星：コミュニケーション・思考スタイル・学習傾向
- 金星：愛情表現・価値観・美意識・人間関係
- 火星：行動力・情熱・競争心・怒りの表れ方
- 木星：拡大・幸運・信念・成長のテーマ
- 土星：試練・責任・制約・遅い成功・構造化
- 天王星：変革・革新・突然の変化・自由への欲求
- 海王星：霊性・直感・夢・幻想・犠牲
- 冥王星：変容・権力・再生・深い変化
- ノース・ノード：魂の成長方向・今世のテーマ

■ ハウスの意味：
1H=自己 2H=財産・価値観 3H=コミュ・兄弟 4H=家庭・ルーツ
5H=創造・恋愛 6H=仕事・健康 7H=パートナー 8H=変容・遺産
9H=哲学・海外 10H=キャリア・社会 11H=仲間・夢 12H=潜在意識・試練

■ インタビューへの活用例：
- 土星が第10ハウス → キャリアでの試練・遅い成功を深掘り
- 月が蟹座 → 家族・ルーツへの感情的な絆を丁寧に質問
- 冥王星が第1ハウス → 人生の大きな変容体験を探る
- ノース・ノードの配置 → 魂の成長テーマに関連した体験を聞く
- アスペクトの緊張（スクエア・オポジション）→ 葛藤・試練の具体的エピソードを促す

各章で「星が示すテーマ」と「実際の人生体験」の対応を見つけながら進めてください。
"""

    prompt += """
【インタビューの進め方（厳守）】
1. 一度に聞く質問は1〜2個まで。会話のキャッチボールを大切に。
2. 答えが薄い場合は深掘りする。「もう少し具体的に教えていただけますか？」
3. 十分な答えが得られたら次のセクションへ自然に移行する。
4. 共感と承認を忘れない。「それは大変でしたね」「素晴らしい経験ですね」
5. 日本語のみで会話する。
6. 例文やヒントを適宜示す。

【章の順番】
1. はじめに（プロフィール・実績・執筆理由・ターゲット・ベネフィット）
2. 第1章：幼少期〜社会人になるまで
3. 第2章：転機・覚悟の瞬間
4. 第3章：メンターとの出会い・失敗の連続
5. 第4章：仲間・裏切り・成長
6. 第5章：最大の試練と突破
7. 第6章：これからの未来
8. おわりに

まず温かく自己紹介してから、「はじめに①：簡単なプロフィール」から始めてください。
ホロスコープデータがある場合は、「〇〇座の太陽をお持ちのあなたは〜」などと自然に織り交ぜながら進めてください。
"""
    return prompt


# ── セッション状態 ────────────────────────────────────────
def init_session():
    defaults = {
        "messages": [],
        "chapter_idx": 0,
        "section_idx": 0,
        "interview_started": False,
        "interview_complete": False,
        "horoscope_text": None,
        "client_name": "",
        "birth_data_ready": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def get_current_position():
    idx = st.session_state.chapter_idx
    sec = st.session_state.section_idx
    if idx >= len(CHAPTER_STRUCTURE):
        return None, None, 0
    ch = CHAPTER_STRUCTURE[idx]
    if sec >= len(ch["sections"]):
        return None, None, 0
    completed = sum(len(CHAPTER_STRUCTURE[i]["sections"]) for i in range(idx)) + sec
    return ch, ch["sections"][sec], completed


def advance_section():
    ch = CHAPTER_STRUCTURE[st.session_state.chapter_idx]
    st.session_state.section_idx += 1
    if st.session_state.section_idx >= len(ch["sections"]):
        st.session_state.chapter_idx += 1
        st.session_state.section_idx = 0
    if st.session_state.chapter_idx >= len(CHAPTER_STRUCTURE):
        st.session_state.interview_complete = True


# ── Claude API ────────────────────────────────────────────
def stream_claude(messages):
    with client.messages.stream(
        model=MODEL,
        max_tokens=2048,
        system=build_system_prompt(st.session_state.horoscope_text),
        messages=messages,
        thinking={"type": "adaptive"},
    ) as stream:
        for text in stream.text_stream:
            yield text


# ── サイドバー ────────────────────────────────────────────
def render_sidebar():
    with st.sidebar:
        st.title("📚 インタビュー進捗")

        # ホロスコープステータス
        if st.session_state.horoscope_text:
            st.success(f"🔮 ホロスコープ: {st.session_state.client_name}さん")
        else:
            st.warning("🔮 ホロスコープ: 未設定")

        st.markdown("---")

        ch, sec, completed = get_current_position()
        progress = completed / TOTAL_SECTIONS if not st.session_state.interview_complete else 1.0
        st.progress(progress)
        st.caption(f"進捗: {completed}/{TOTAL_SECTIONS} セクション完了")
        st.markdown("---")

        for i, chapter in enumerate(CHAPTER_STRUCTURE):
            if i < st.session_state.chapter_idx:
                st.markdown(f"✅ **{chapter['icon']} {chapter['title']}**")
            elif i == st.session_state.chapter_idx and not st.session_state.interview_complete:
                st.markdown(f"▶️ **{chapter['icon']} {chapter['title']}** ← 現在")
                for j, s in enumerate(chapter["sections"]):
                    if j < st.session_state.section_idx:
                        st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;✅ {s}")
                    elif j == st.session_state.section_idx:
                        st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;▶️ **{s}**")
                    else:
                        st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;⬜ {s}")
            else:
                st.markdown(f"⬜ {chapter['icon']} {chapter['title']}")

        st.markdown("---")

        if st.session_state.interview_started:
            if st.button("⏭ 次のセクションへ", use_container_width=True,
                         disabled=st.session_state.interview_complete):
                advance_section()
                ch2, sec2, _ = get_current_position()
                if ch2 and sec2:
                    msg = f"[SECTION_COMPLETE] 次のセクション：「{ch2['title']} - {sec2}」について質問してください。"
                    st.session_state.messages.append({"role": "user", "content": msg})
                st.rerun()

            if st.button("💾 会話を保存", use_container_width=True):
                ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                data = {
                    "timestamp": ts,
                    "client_name": st.session_state.client_name,
                    "horoscope": st.session_state.horoscope_text,
                    "messages": st.session_state.messages,
                }
                st.sidebar.download_button(
                    "📥 JSONダウンロード",
                    json.dumps(data, ensure_ascii=False, indent=2),
                    f"interview_{ts}.json",
                    "application/json",
                )

        if st.session_state.interview_complete:
            st.success("🎉 インタビュー完了！")
            if st.button("📄 テキスト出力", use_container_width=True):
                ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                lines = [f"# マイストーリー ヒアリング記録\n収録日時: {ts}\n"]
                if st.session_state.horoscope_text:
                    lines.append(st.session_state.horoscope_text + "\n")
                for msg in st.session_state.messages:
                    if msg["content"].startswith("[SECTION_COMPLETE]"):
                        continue
                    role = "【クライアント】" if msg["role"] == "user" else "【インタビュアー】"
                    lines.append(f"{role}\n{msg['content']}\n")
                st.sidebar.download_button(
                    "📥 テキストダウンロード",
                    "\n".join(lines).encode("utf-8"),
                    f"interview_{ts}.txt",
                    "text/plain",
                )

        st.markdown("---")
        if st.button("🔄 最初からやり直す", use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()


# ── ホロスコープ入力フォーム ──────────────────────────────
def render_horoscope_form():
    st.markdown("### 🔮 クライアントの出生データを入力")
    st.caption("ホロスコープを計算してClaudeのインタビューに自動反映させます")

    with st.form("horoscope_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("お名前（ペンネーム可）", placeholder="例：田中 花子")
        with col2:
            tz_label = st.selectbox("タイムゾーン", list(TZ_OPTIONS.keys()), index=0)

        col3, col4, col5 = st.columns(3)
        with col3:
            birth_date = st.date_input("生年月日", value=datetime.date(1980, 1, 1),
                                       min_value=datetime.date(1900, 1, 1))
        with col4:
            birth_hour = st.number_input("出生時刻（時）", min_value=0, max_value=23, value=12)
        with col5:
            birth_min = st.number_input("（分）", min_value=0, max_value=59, value=0)

        birthplace = st.text_input("出生地（地名）", placeholder="例：東京、大阪市、New York")

        col6, col7 = st.columns(2)
        with col6:
            lat_manual = st.number_input("緯度（地名検索できない場合）", value=0.0, step=0.0001, format="%.4f")
        with col7:
            lon_manual = st.number_input("経度（地名検索できない場合）", value=0.0, step=0.0001, format="%.4f")

        submitted = st.form_submit_button("🔮 ホロスコープを計算してインタビュー開始", use_container_width=True)

    if submitted:
        if not name:
            st.error("お名前を入力してください")
            return

        tz_str = TZ_OPTIONS[tz_label]
        lat, lon = lat_manual, lon_manual

        # 地名からジオコーディング
        if birthplace:
            with st.spinner(f"「{birthplace}」の位置情報を取得中..."):
                g_lat, g_lon = geocode_city(birthplace)
            if g_lat and g_lon:
                lat, lon = g_lat, g_lon
                st.success(f"📍 {birthplace} → 緯度{lat}, 経度{lon}")
            else:
                if lat == 0.0 and lon == 0.0:
                    st.warning("地名の検索に失敗しました。緯度・経度を手動入力してください。")
                    return

        if lat == 0.0 and lon == 0.0:
            st.error("出生地または緯度・経度を入力してください")
            return

        # ホロスコープ計算
        with st.spinner("ホロスコープを計算中..."):
            horo_text, error = calculate_horoscope(
                name,
                birth_date.year, birth_date.month, birth_date.day,
                birth_hour, birth_min,
                lat, lon, tz_str,
                birthplace or f"緯度{lat}/経度{lon}"
            )

        if error:
            st.error(f"計算エラー: {error}")
            return

        # 結果を保存してインタビュー開始
        st.session_state.horoscope_text = horo_text
        st.session_state.client_name = name
        st.session_state.birth_data_ready = True

        with st.expander("📊 計算されたホロスコープデータを確認", expanded=False):
            st.code(horo_text)

        st.success(f"✅ {name}さんのホロスコープ計算完了！インタビューを開始します。")
        st.rerun()

    # スキップオプション
    st.markdown("---")
    if st.button("ホロスコープなしでインタビューを開始する", use_container_width=False):
        name = st.text_input("お名前だけ入力", key="name_only", placeholder="例：田中 花子")
        if name:
            st.session_state.client_name = name
            st.session_state.birth_data_ready = True
            st.rerun()


# ── チャット UI ───────────────────────────────────────────
def render_chat():
    for msg in st.session_state.messages:
        if msg["content"].startswith("[SECTION_COMPLETE]"):
            continue
        avatar = "🙂" if msg["role"] == "user" else "🔮"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])


def start_interview():
    st.session_state.interview_started = True
    horo_info = ""
    if st.session_state.horoscope_text:
        horo_info = f"クライアントは{st.session_state.client_name}さんです。ホロスコープデータを参照しながら、"
    start_msg = f"{horo_info}インタビューを開始してください。まず温かく自己紹介してから「はじめに①簡単なプロフィール」の質問を1つ始めてください。"
    st.session_state.messages.append({"role": "user", "content": start_msg})

    with st.chat_message("assistant", avatar="🔮"):
        placeholder = st.empty()
        full = ""
        try:
            for chunk in stream_claude([{"role": "user", "content": start_msg}]):
                full += chunk
                placeholder.markdown(full + "▌")
            placeholder.markdown(full)
        except Exception as e:
            full = f"⚠️ APIエラー: {e}"
            placeholder.error(full)

    st.session_state.messages.append({"role": "assistant", "content": full})


def handle_input():
    user_input = st.chat_input("ここに入力してください...")
    if not user_input:
        return

    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="🙂"):
        st.markdown(user_input)

    api_msgs = [{"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages]

    with st.chat_message("assistant", avatar="🔮"):
        placeholder = st.empty()
        full = ""
        try:
            for chunk in stream_claude(api_msgs):
                full += chunk
                placeholder.markdown(full + "▌")
            placeholder.markdown(full)
        except Exception as e:
            full = f"⚠️ APIエラー: {e}"
            placeholder.error(full)

    st.session_state.messages.append({"role": "assistant", "content": full})


# ── メイン ────────────────────────────────────────────────
def main():
    st.set_page_config(
        page_title="マイストーリー インタビューBot",
        page_icon="🔮", layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown("""
    <style>
    .stChatMessage { padding: 0.5rem 0; }
    </style>
    """, unsafe_allow_html=True)

    init_session()
    render_sidebar()

    st.title("🔮 マイストーリー インタビューBot")
    st.markdown("*ホロスコープ完全統合版*")

    # フェーズ1：出生データ入力
    if not st.session_state.birth_data_ready:
        render_horoscope_form()
        return

    # フェーズ2：インタビュー
    ch, sec, completed = get_current_position()
    if not st.session_state.interview_complete and ch:
        if st.session_state.horoscope_text:
            st.info(f"🔮 **{st.session_state.client_name}さん** | 現在のセクション：{ch['icon']} {ch['title']} — {sec}　（{completed}/{TOTAL_SECTIONS}）")
        else:
            st.info(f"現在のセクション：{ch['icon']} {ch['title']} — {sec}　（{completed}/{TOTAL_SECTIONS}）")
    elif st.session_state.interview_complete:
        st.success("🎉 全セクション完了！サイドバーからダウンロードできます。")

    st.markdown("---")
    render_chat()

    if not st.session_state.interview_started:
        start_interview()
        st.rerun()

    if not st.session_state.interview_complete:
        handle_input()


if __name__ == "__main__":
    main()
