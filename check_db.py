import sqlite3

def check_lotto_db(db_path="lotto_analyzer.db"):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 1. 전체 저장된 회차 수 및 최신 회차 조회
        cursor.execute("SELECT COUNT(*), MIN(draw_no), MAX(draw_no) FROM lotto_episodes")
        total_cnt, min_draw, max_draw = cursor.fetchone()

        if total_cnt == 0:
            print("❌ DB에 데이터가 전혀 없습니다. main.py에서 3번(DB 최신화)을 실행하세요.")
            return

        print("=" * 60)
        print(f" DataBase 정상 작동 중")
        print(f" • 총 저장된 회차 수 : {total_cnt:,}개")
        print(f" • 데이터 범위       : {min_draw}회 ~ {max_draw}회")
        print("=" * 60)

        # 2. 가장 최근 데이터 3건 출력 (데이터 정확성 확인)
        print("\n [최신 3개 회차 상세 데이터 확인]")
        cursor.execute("""
            SELECT draw_no, draw_date, num1, num2, num3, num4, num5, num6, bonus_num, num_sum, ac_value
            FROM lotto_episodes 
            ORDER BY draw_no DESC 
            LIMIT 3
        """)
        rows = cursor.fetchall()

        for r in rows:
            print(f" [{r[0]}회차 | {r[1]}] 번호: {list(r[2:8])} + 보너스({r[8]}) | 합계: {r[9]} | AC값: {r[10]}")

        print("=" * 60)
        conn.close()

    except sqlite3.OperationalError:
        print("❌ DB 테이블이 생성되지 않았습니다. main.py를 실행하여 3번 메뉴를 먼저 누르세요.")

if __name__ == "__main__":
    check_lotto_db()