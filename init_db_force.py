import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from itertools import combinations

PRIMES = {2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43}
FIRST_DRAW_DATE = datetime(2002, 12, 7)  # 1회차 추첨일 기준

def calculate_ac(numbers):
    diffs = set()
    for a, b in combinations(numbers, 2):
        diffs.add(abs(a - b))
    return len(diffs) - (len(numbers) - 1)

def get_max_consecutive(numbers):
    sorted_nums = sorted(numbers)
    max_len = 1
    current_len = 1
    for i in range(len(sorted_nums) - 1):
        if sorted_nums[i+1] == sorted_nums[i] + 1:
            current_len += 1
            max_len = max(max_len, current_len)
        else:
            current_len = 1
    return max_len

def build_db_from_excel(excel_path="lotto.xlsx", db_path="lotto_analyzer.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lotto_episodes (
            draw_no INTEGER PRIMARY KEY, draw_date TEXT NOT NULL,
            num1 INTEGER, num2 INTEGER, num3 INTEGER, num4 INTEGER, num5 INTEGER, num6 INTEGER,
            bonus_num INTEGER, num_sum INTEGER NOT NULL, ac_value INTEGER NOT NULL,
            odd_count INTEGER NOT NULL, even_count INTEGER NOT NULL,
            high_count INTEGER NOT NULL, low_count INTEGER NOT NULL,
            prime_count INTEGER NOT NULL, multiple3_count INTEGER NOT NULL,
            last_digit_sum INTEGER NOT NULL, max_consecutive INTEGER NOT NULL
        )
    """)
    
    try:
        df = pd.read_excel(excel_path)
        print(f">>> {len(df)}개 회차 데이터를 엑셀에서 읽어왔습니다. DB 가공 시작...")

        for _, row in df.iterrows():
            draw_no = int(row['회차'])
            
            # 추첨일 컬럼이 없으므로 회차 기반 자동 날짜 생성
            calc_date = FIRST_DRAW_DATE + timedelta(weeks=(draw_no - 1))
            draw_date = calc_date.strftime("%Y-%m-%d")

            nums = sorted([int(row[f'번호{i}']) for i in range(1, 7)])
            bonus = int(row['보너스'])

            cursor.execute("""
                INSERT OR REPLACE INTO lotto_episodes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                draw_no, draw_date, *nums, bonus,
                sum(nums), calculate_ac(nums),
                sum(1 for n in nums if n % 2 != 0), 6 - sum(1 for n in nums if n % 2 != 0),
                sum(1 for n in nums if n >= 23), 6 - sum(1 for n in nums if n >= 23),
                sum(1 for n in nums if n in PRIMES), sum(1 for n in nums if n % 3 == 0),
                sum(n % 10 for n in nums), get_max_consecutive(nums)
            ))

        conn.commit()
        print("🎉 엑셀 데이터 기반 DB 구축 완료!")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        print("💡 엑셀의 열 이름이 ['회차', '번호1', '번호2', '번호3', '번호4', '번호5', '번호6', '보너스'] 인지 확인해 주세요.")

    finally:
        conn.close()

if __name__ == "__main__":
    build_db_from_excel()