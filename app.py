import streamlit as st
import pandas as pd
from core_generator import LottoCoreGenerator
from db_pipeline import sync_lotto_database

st.set_page_config(page_title="AI 로또 번호 생성기", layout="centered")

st.title("🎲 데이터 기반 AI 로또 번호 생성기")
st.caption("SQLite DB 및 고차원 필터링 알고리즘 적용")

# DB 동기화 버튼
if st.button("🔄 lotto.xlsx 데이터 최신화"):
    sync_lotto_database()
    st.success("데이터베이스 동기화 완료!")

# 생성기 로드
generator = LottoCoreGenerator()

# 생성 옵션 UI
game_count = st.slider("생성할 게임 수", min_value=1, max_value=10, value=5)

if st.button("✨ 최적 조합 생성하기"):
    with st.spinner("가중치 및 필터 체인 검증 중..."):
        games, attempts = generator.generate_combinations(count=game_count)
    
    st.subheader(f"🎯 추천 조합 ({game_count}게임)")
    st.info(f"필터 검증 완료 (총 {attempts:,}회 무작위 시도 수행)")

    for idx, game in enumerate(games, 1):
        # 로또 번호 출력 (알록달록한 뱃지 형태)
        st.write(f"**{idx}게임:** " + " ".join([f"`{n:02d}`" for n in game]))