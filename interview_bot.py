"""
マイストーリー インタビューBot
電子書籍出版プロデューサー向け：クライアントのヒアリングを自動化するチャットアプリ
"""

import streamlit as st
from anthropic import Anthropic
import json
import datetime

# ─────────────────────────────────────────────
# 定数・設定
# ─────────────────────────────────────────────
client = Anthropic()
MODEL = "claude-opus-4-7"

# 章の構成定義
CHAPTER_STRUCTURE = [
    {
        "id": "basic_info",
        "title": "📋 基本情報",
        "icon": "📋",
        "sections": ["基本情報・テーマ設定"],
        "key_questions": [
            "お名前（ペンネーム可）",
            "年齢・生年月日・生誕地",
            "現在のお仕事・役職",
            "電子書籍のタイトル（仮）",
            "執筆の目的・ゴール",
            "どんな読者に読んでほしいか",
        ]
    },
    {
        "id": "hajimeni",
        "title": "✨ はじめに",
        "icon": "✨",
        "sections": [
            "① 簡単なプロフィール",
            "② 実績",
            "③ 上梓しようと思った背景・理由",
            "④ 本書のターゲット",
            "⑤ 本書を読んで得られるベネフィット",
        ],
    },
    {
        "id": "chapter1",
        "title": "第1章 幼少期〜社会人",
        "icon": "🌱",
        "sections": [
            "① 生まれ育った環境【幼少期・原体験】",
            "② 学生時代の思い出【青春時代・葛藤と成長】",
            "③ 青春の葛藤と目覚め",
            "④ 社会人としての第一歩",
            "⑤ 自分らしさの芽生え",
        ],
    },
    {
        "id": "chapter2",
        "title": "第2章 違和感と変化",
        "icon": "⚡",
        "sections": [
            "① 日常から冒険に出るまで【転機・覚悟の瞬間】",
            "② 恐怖と迷い、そして覚悟",
        ],
    },
    {
        "id": "chapter3",
        "title": "第3章 失敗の連続",
        "icon": "🔥",
        "sections": [
            "① メンターとの出会い",
            "② 困難や失敗の連続にめげそうになったこと",
        ],
    },
    {
        "id": "chapter4",
        "title": "第4章 試練と成功体験",
        "icon": "💪",
        "sections": [
            "① 支えてくれた仲間の存在",
            "② 裏切りや喪失",
            "③ 変化・成長",
        ],
    },
    {
        "id": "chapter5",
        "title": "第5章 最大の試練",
        "icon": "🏔️",
        "sections": [
            "① ラスボス（最大の壁）",
            "② 突破と成功",
        ],
    },
    {
        "id": "chapter6",
        "title": "第6章 これからの未来",
        "icon": "🌟",
        "sections": [
            "① この経験を経て、どんな未来を生きたいですか？",
            "② どんな人にあなたの経験を伝えていきたいですか？",
        ],
    },
    {
        "id": "owari",
        "title": "おわりに",
        "icon": "🎉",
        "sections": [
            "① 読者への感謝",
            "② 自分の成功には再現性があることを強調",
            "③ 「次はあなたの番」と励ましのエンディング",
        ],
    },
]

TOTAL_SECTIONS = sum(len(ch["sections"]) for ch in CHAPTER_STRUCTURE)


# ─────────────────────────────────────────────
# システムプロンプト生成
# ─────────────────────────────────────────────
def build_system_prompt():
    return """あなたは、電子書籍出版プロデューサーのアシスタントとして、クライアントの「マイストーリー」を引き出す優秀なインタビュアーです。

## あなたの役割
クライアントの人生経験・感情・価値観を丁寧に聞き出し、電子書籍の原稿に使える豊かなエピソードを収集します。

## インタビューの進め方（厳守）
1. **一度に聞く質問は1〜2個まで**。たくさん質問を並べずに、会話のキャッチボールを大切にしてください。
2. **答えが薄い場合は深掘り**する。「もう少し具体的に教えていただけますか？」「その時の気持ちはどんな感じでしたか？」など。
3. **答えが十分に得られたら次のセクションへ**。「ありがとうございます。では次に〇〇について聞かせてください」と自然に移行する。
4. **共感と承認を大切に**。「それは大変でしたね」「素晴らしい経験ですね」など、人間らしい反応を忘れずに。
5. **日本語のみで会話する**。
6. **例文やヒントを適宜示す**。答えにくそうな場合は「例えば〜のような感じでしょうか？」と例を出す。

## 章の構成（この順番で進める）
1. 基本情報（名前・生年月日・現在の仕事・書籍タイトルなど）
2. はじめに（プロフィール・実績・執筆理由・ターゲット・ベネフィット）
3. 第1章：幼少期〜社会人になるまで
4. 第2章：違和感を感じて変化の必要性が迫る
5. 第3章：失敗の連続（自己流で事故る）
6. 第4章：大小さまざまな試練を経て成功体験も味わう
7. 第5章：最大の試練を乗り越え、成功を手にする
8. 第6章：まだ志半ば → これからの未来
9. おわりに

## 各セクションで収集すべき内容
### はじめに
- ①プロフィール：経歴・専門性・これまでの成果の概要
- ②実績：数字や具体的成果（人数・売上・年数など）
- ③執筆背景：なぜ今この本を書くのか
- ④ターゲット：誰に読んでほしいか（年齢・状況・悩みなど）
- ⑤ベネフィット：読んで得られる具体的な変化・気づき

### 第1章
- ①幼少期：家庭環境・親との関係・印象的な出来事・地元の雰囲気
- ②学生時代：夢・部活・友人・挫折・乗り越えた経験
- ③青春の葛藤：進路の悩み・親との衝突・自分探し
- ④社会人の第一歩：初めての職場・現実とのギャップ・学び
- ⑤自分らしさの芽生え：自分の強みや価値観に気づいたきっかけ

### 第2章
- ①転機：「このままではダメだ」と感じた出来事・出会い・衝撃
- ②覚悟：迷い・不安・それでも進む決意とその理由

### 第3章
- ①メンター：出会いの状況・受け取った言葉や教え・今への影響
- ②失敗の連続：うまくいかなかったこと・孤独・自信喪失・立ち直り方

### 第4章
- ①仲間：苦境で支えてくれた人・忘れられない言葉や行動
- ②裏切り・喪失：信頼崩壊・感情・そこから学んだこと
- ③変化・成長：手放したもの・得たもの・価値観の変容

### 第5章
- ①ラスボス：人生最大の壁・その時の感情・誰にも言えなかった気持ち
- ②突破と成功：乗り越えた行動・得た成果・自分の必殺技

### 第6章
- ①未来像：これから挑戦したいこと・10年後のビジョン
- ②伝えたい相手：かつての自分のような人へのメッセージ

### おわりに
- ①読者への感謝：心を込めた言葉
- ②再現性：自分の成功は誰でも真似できることの根拠
- ③励まし：「次はあなたの番」というエンディングメッセージ

## 重要な注意事項
- ユーザーが現在どのセクションにいるかは、システムが管理しています。
- 「[SECTION_COMPLETE]」というメッセージが来たら、次のセクションへ移行してください。
- 会話の冒頭では必ず温かく自己紹介してから、基本情報の収集を始めてください。
"""


# ─────────────────────────────────────────────
# セッション状態の初期化
# ─────────────────────────────────────────────
def init_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "chapter_idx" not in st.session_state:
        st.session_state.chapter_idx = 0
    if "section_idx" not in st.session_state:
        st.session_state.section_idx = 0
    if "completed_sections" not in st.session_state:
        st.session_state.completed_sections = []
    if "collected_data" not in st.session_state:
        st.session_state.collected_data = {}
    if "interview_started" not in st.session_state:
        st.session_state.interview_started = False
    if "interview_complete" not in st.session_state:
        st.session_state.interview_complete = False


def get_current_position():
    """現在の章・セクション情報を返す"""
    idx = st.session_state.chapter_idx
    sec_idx = st.session_state.section_idx
    if idx >= len(CHAPTER_STRUCTURE):
        return None, None, None, None
    chapter = CHAPTER_STRUCTURE[idx]
    sections = chapter["sections"]
    if sec_idx >= len(sections):
        return None, None, None, None
    section = sections[sec_idx]
    # 全体の進捗計算
    completed = sum(
        len(CHAPTER_STRUCTURE[i]["sections"]) for i in range(idx)
    ) + sec_idx
    return chapter, section, idx, completed


def advance_section():
    """次のセクションへ進む"""
    chapter = CHAPTER_STRUCTURE[st.session_state.chapter_idx]
    st.session_state.section_idx += 1
    if st.session_state.section_idx >= len(chapter["sections"]):
        st.session_state.chapter_idx += 1
        st.session_state.section_idx = 0
    if st.session_state.chapter_idx >= len(CHAPTER_STRUCTURE):
        st.session_state.interview_complete = True


# ─────────────────────────────────────────────
# Claude API 呼び出し（ストリーミング）
# ─────────────────────────────────────────────
def stream_claude_response(messages):
    """Claude APIをストリーミングで呼び出してレスポンスを返す"""
    with client.messages.stream(
        model=MODEL,
        max_tokens=2048,
        system=build_system_prompt(),
        messages=messages,
        thinking={"type": "adaptive"},
    ) as stream:
        for text in stream.text_stream:
            yield text


# ─────────────────────────────────────────────
# サイドバー：進捗表示
# ─────────────────────────────────────────────
def render_sidebar():
    with st.sidebar:
        st.title("📚 インタビュー進捗")
        st.markdown("---")

        chapter, section, chapter_idx, completed_count = get_current_position()
        progress = completed_count / TOTAL_SECTIONS if not st.session_state.interview_complete else 1.0
        st.progress(progress)
        st.caption(f"進捗: {completed_count}/{TOTAL_SECTIONS} セクション完了")

        st.markdown("---")

        for i, ch in enumerate(CHAPTER_STRUCTURE):
            if i < st.session_state.chapter_idx:
                # 完了済み章
                st.markdown(f"✅ **{ch['icon']} {ch['title']}**")
            elif i == st.session_state.chapter_idx and not st.session_state.interview_complete:
                # 現在の章
                st.markdown(f"▶️ **{ch['icon']} {ch['title']}** ← 現在")
                for j, sec in enumerate(ch["sections"]):
                    if j < st.session_state.section_idx:
                        st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;✅ {sec}")
                    elif j == st.session_state.section_idx:
                        st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;▶️ **{sec}**")
                    else:
                        st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;⬜ {sec}")
            else:
                # 未着手の章
                st.markdown(f"⬜ {ch['icon']} {ch['title']}")

        st.markdown("---")

        # 操作ボタン
        if st.session_state.interview_started:
            col1, col2 = st.columns(2)
            with col1:
                if st.button("⏭ 次へ進む", use_container_width=True,
                             help="現在のセクションを完了して次へ進みます",
                             disabled=st.session_state.interview_complete):
                    advance_section()
                    # 次セクション移行をメッセージに追加
                    chapter, section, _, _ = get_current_position()
                    if chapter and section:
                        system_msg = f"[SECTION_COMPLETE] 次のセクション：「{chapter['title']} - {section}」について聞いてください。"
                        st.session_state.messages.append(
                            {"role": "user", "content": system_msg}
                        )
                    st.rerun()
            with col2:
                if st.button("💾 保存", use_container_width=True,
                             help="会話履歴をJSONファイルに保存します"):
                    save_conversation()

        if st.session_state.interview_complete:
            st.success("🎉 インタビュー完了！")
            if st.button("📄 テキスト出力", use_container_width=True):
                export_as_text()

        st.markdown("---")
        if st.button("🔄 最初からやり直す", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()


# ─────────────────────────────────────────────
# ファイル保存・エクスポート
# ─────────────────────────────────────────────
def save_conversation():
    """会話履歴をJSONで保存"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"interview_{timestamp}.json"
    data = {
        "timestamp": timestamp,
        "messages": st.session_state.messages,
        "chapter_idx": st.session_state.chapter_idx,
        "section_idx": st.session_state.section_idx,
    }
    st.sidebar.download_button(
        label="📥 JSONダウンロード",
        data=json.dumps(data, ensure_ascii=False, indent=2),
        file_name=filename,
        mime="application/json",
    )


def export_as_text():
    """会話をテキスト形式でエクスポート"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    lines = ["# マイストーリー ヒアリング記録\n"]
    lines.append(f"収録日時: {timestamp}\n\n")
    for msg in st.session_state.messages:
        role = "【クライアント】" if msg["role"] == "user" else "【インタビュアー】"
        content = msg["content"]
        # [SECTION_COMPLETE] のシステムメッセージはスキップ
        if content.startswith("[SECTION_COMPLETE]"):
            continue
        lines.append(f"{role}\n{content}\n\n")
    text_content = "\n".join(lines)
    st.sidebar.download_button(
        label="📥 テキストダウンロード",
        data=text_content.encode("utf-8"),
        file_name=f"interview_{timestamp}.txt",
        mime="text/plain",
    )


# ─────────────────────────────────────────────
# メインチャット UI
# ─────────────────────────────────────────────
def render_chat():
    # チャット履歴の表示（[SECTION_COMPLETE]メッセージは非表示）
    for msg in st.session_state.messages:
        content = msg["content"]
        if content.startswith("[SECTION_COMPLETE]"):
            continue
        role = msg["role"]
        if role == "assistant":
            with st.chat_message("assistant", avatar="🎙️"):
                st.markdown(content)
        else:
            with st.chat_message("user", avatar="🙂"):
                st.markdown(content)


def handle_user_input():
    """ユーザー入力の処理"""
    user_input = st.chat_input("ここに入力してください...")

    if user_input:
        # ユーザーメッセージを追加
        st.session_state.messages.append({"role": "user", "content": user_input})

        # ユーザーメッセージを表示
        with st.chat_message("user", avatar="🙂"):
            st.markdown(user_input)

        # Claude応答をストリーミング
        with st.chat_message("assistant", avatar="🎙️"):
            response_placeholder = st.empty()
            full_response = ""

            # APIメッセージ（[SECTION_COMPLETE]含む全メッセージ）を送る
            api_messages = [
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ]

            try:
                for chunk in stream_claude_response(api_messages):
                    full_response += chunk
                    response_placeholder.markdown(full_response + "▌")
                response_placeholder.markdown(full_response)
            except Exception as e:
                full_response = f"エラーが発生しました: {str(e)}\n\nAPIキーが設定されているか確認してください。"
                response_placeholder.error(full_response)

        # アシスタントのメッセージを履歴に追加
        st.session_state.messages.append(
            {"role": "assistant", "content": full_response}
        )


# ─────────────────────────────────────────────
# 初回起動：インタビュー開始
# ─────────────────────────────────────────────
def start_interview():
    """インタビューを開始する（初回のみ）"""
    if not st.session_state.interview_started:
        st.session_state.interview_started = True

        # 開始プロンプト
        start_message = (
            "インタビューを開始してください。"
            "まず温かく自己紹介してから、基本情報の収集を始めてください。"
            "最初の質問はお名前から始めてください。"
        )
        st.session_state.messages.append({"role": "user", "content": start_message})

        # 初回レスポンスを取得
        with st.chat_message("assistant", avatar="🎙️"):
            response_placeholder = st.empty()
            full_response = ""

            api_messages = [{"role": "user", "content": start_message}]

            try:
                for chunk in stream_claude_response(api_messages):
                    full_response += chunk
                    response_placeholder.markdown(full_response + "▌")
                response_placeholder.markdown(full_response)
            except Exception as e:
                full_response = (
                    "⚠️ APIの接続でエラーが発生しました。\n\n"
                    "ANTHROPIC_API_KEY が正しく設定されているか確認してください。\n\n"
                    f"エラー詳細: {str(e)}"
                )
                response_placeholder.error(full_response)

        st.session_state.messages.append(
            {"role": "assistant", "content": full_response}
        )


# ─────────────────────────────────────────────
# メイン
# ─────────────────────────────────────────────
def main():
    st.set_page_config(
        page_title="マイストーリー インタビューBot",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # カスタムCSS
    st.markdown("""
    <style>
    .stChatMessage { padding: 0.5rem 0; }
    .stChatInput { border-radius: 20px; }
    h1 { font-size: 1.5rem !important; }
    </style>
    """, unsafe_allow_html=True)

    init_session_state()
    render_sidebar()

    # ─── メインエリア ───
    st.title("📚 マイストーリー インタビューBot")

    chapter, section, chapter_idx, completed = get_current_position()
    if not st.session_state.interview_complete and chapter:
        st.info(
            f"**現在のセクション：{chapter['icon']} {chapter['title']} — {section}**　"
            f"（全体 {completed}/{TOTAL_SECTIONS} 完了）"
        )
    elif st.session_state.interview_complete:
        st.success("🎉 全セクションのヒアリングが完了しました！サイドバーからテキストをダウンロードしてください。")

    st.markdown("---")

    # チャット履歴を表示
    render_chat()

    # インタビュー開始（初回）
    if not st.session_state.interview_started:
        start_interview()
        st.rerun()

    # ユーザー入力処理
    if not st.session_state.interview_complete:
        handle_user_input()


if __name__ == "__main__":
    main()
