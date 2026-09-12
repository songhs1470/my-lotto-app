import streamlit as st
import sqlite3
import pandas as pd
from db_pipeline import update_lotto_database
from core_generator import generate_lotto_level2, get_recent_5_stats

st.set_page_config(page_title="로또 번호 생성기 Level 2", page_icon="🎱", layout="wide")

# DB 최신화
@st.cache_resource
def init_db():
    update_lotto_database()

init_db()

# 전회차 번호 가져오기
appeared_5, unappeared_5, latest_draw = get_recent_5_stats()

st.title("🎱 로또 번호 생성기 (Level 2)")
st.caption("고도화된 통계 필터와 사용자가 직접 제어하는 맞춤형 조합 시스템")

# --- 사이드바: Level 2 필터 설정 ---
st.sidebar.header("🎛️ Level 2 필터 설정")

# 1. AC값 난이도
min_ac = st.sidebar.slider("AC값 최소 난이도 (1~10)", min_value=1, max_value=10, value=7)

# 2. 연속번호 제한
allow_3_consec = st.sidebar.checkbox("3연속 이상 번호 허용 (제한 해제)", value=False)

# 3. 전회차 이월수
carry_mode = st.sidebar.selectbox("전회차 이월수 설정", ["자동", "0개", "1개", "2개", "직접선택"])
custom_carry = []
if carry_mode == "직접선택":
    custom_carry = st.sidebar.multiselect("이월시킬 번호 선택 (최대 2개)", latest_draw, max_selections=2)

# 4. 전회차 이웃수
use_neighbor = st.sidebar.checkbox("전회차 이웃수 (±1, ±2) 포함 필터", value=False)

# 5. 동끝수 제한
use_same_end = st.sidebar.checkbox("동끝수 제한 (동일 끝자리 3개 이하)", value=True)

# 6. 최근 5회차 패턴
use_recent_5 = st.sidebar.checkbox("최근 5회차 패턴 (당첨 2~3개 / 미출현 2~3개)", value=False)

st.sidebar.markdown("---")

# 7. 구간별 비중 지정
section_ratio_mode = st.sidebar.selectbox("구간별 비중 지정", ["선택 OFF", "대역별 개수 지정", "랜덤"])
section_counts = {}
if section_ratio_mode == "대역별 개수 지정":
    st.sidebar.caption("5개 구간의 합이 6이 되도록 설정하세요.")
    c1 = st.sidebar.number_input("단번대(1-9)", 0, 6, 1)
    c2 = st.sidebar.number_input("10번대(10-19)", 0, 6, 1)
    c3 = st.sidebar.number_input("20번대(20-29)", 0, 6, 2)
    c4 = st.sidebar.number_input("30번대(30-39)", 0, 6, 1)
    c5 = st.sidebar.number_input("40번대(40-45)", 0, 6, 1)
    section_counts = {"1-9": c1, "10-19": c2, "20-29": c3, "30-39": c4, "40-45": c5}

# 8. 구간 쏠림 지정
section_skew_mode = st.sidebar.selectbox("구간 쏠림(3~4개) 지정", ["선택 OFF", "특정 구간 지정", "랜덤"])
skew_target = None
if section_skew_mode == "특정 구간 지정":
    skew_target = st.sidebar.selectbox("집중시킬 구간 선택", ["1-9", "10-19", "20-29", "30-39", "40-45"])

# 메인 영역
col1, col2 = st.columns([2, 1])

with col1:
    count = st.slider("생성할 게임 수", 1, 10, 5)
    if st.button("✨ Level 2 최적 조합 생성하기", use_container_width=True):
        # 비중 개수 검증
        if section_ratio_mode == "대역별 개수 지정" and sum(section_counts.values()) != 6:
            st.error("구간별 대역 개수의 총합이 반드시 6개여야 합니다!")
        else:
            games = generate_lotto_level2(
                count=count,
                min_ac=min_ac,
                allow_3_consecutive=allow_3_consec,
                carry_mode=carry_mode,
                custom_carry_nums=custom_carry,
                use_neighbor=use_neighbor,
                use_same_end_limit=use_same_end,
                section_ratio_mode=section_ratio_mode,
                section_counts=section_counts,
                section_skew_mode=section_skew_mode,
                skew_target_range=skew_target,
                use_recent_5_pattern=use_recent_5
            )
            
            st.subheader("🎉 생성된 번호 조합")
            for idx, game in enumerate(games, 1):
                st.markdown(f"**게임 {idx}:** " + " ".join([f"`{n:02d}`" for n in game]))

with col2:
    st.subheader("📊 최근 당첨 정보")
    if latest_draw:
        st.write(f"**전회차 당첨번호:**")
        st.write(" ".join([f"`{n:02d}`" for n in latest_draw]))
    st.markdown("---")
    st.write(f"**최근 5회차 출현수:** {len(appeared_5)}개")
    st.write(f"**최근 5회차 미출현수:** {len(unappeared_5)}개")
