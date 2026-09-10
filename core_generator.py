import sqlite3
import numpy as np

class LottoCoreGenerator:
    def __init__(self, db_path="lotto_analyzer.db"):
        self.db_path = db_path
        self.reload_engine()

    def reload_engine(self):
        """DB 최신화 이후 가중치 및 필터 파라미터 재계산"""
        self.weights = np.ones(46)
        self.hot_numbers = set()
        self.cold_numbers = set()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 테이블 존재 여부 확인
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='lotto_episodes'")
        if not cursor.fetchone():
            conn.close()
            self.probs = [0] + [1.0 / 45.0] * 45
            return

        cursor.execute("SELECT draw_no, num1, num2, num3, num4, num5, num6 FROM lotto_episodes ORDER BY draw_no DESC")
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            self.probs = [0] + [1.0 / 45.0] * 45
            return

        latest_draw = rows[0][0]
        recent_10 = rows[:10]
        recent_counts = {i: 0 for i in range(1, 46)}
        for r in recent_10:
            for n in r[1:7]:
                recent_counts[n] += 1

        last_appeared = {i: 0 for i in range(1, 46)}
        for r in rows:
            for n in r[1:7]:
                if last_appeared[n] == 0:
                    last_appeared[n] = r[0]

        for n in range(1, 46):
            gap = latest_draw - last_appeared[n] if last_appeared[n] > 0 else len(rows)
            if gap <= 5:
                self.hot_numbers.add(n)
            elif gap > 10:
                self.cold_numbers.add(n)

            omission_score = 1.5 if 5 <= gap <= 10 else (0.8 if gap > 15 else 1.0)
            recent_score = 1.0 + (recent_counts[n] * 0.1)
            self.weights[n] = omission_score * recent_score

        prob_sum = sum(self.weights[1:])
        self.probs = [0] + [self.weights[i] / prob_sum for i in range(1, 46)]

    def passes_filters(self, numbers):
        sorted_nums = sorted(numbers)
        # 1. 합계 (100~175)
        if not (100 <= sum(sorted_nums) <= 175):
            return False
        # 2. AC값 (>= 7)
        diffs = set(abs(sorted_nums[i] - sorted_nums[j]) for i in range(6) for j in range(i + 1, 6))
        if len(diffs) - 5 < 7:
            return False
        # 3. 홀짝 (2:4, 3:3, 4:2)
        if sum(1 for n in sorted_nums if n % 2 != 0) not in (2, 3, 4):
            return False
        # 4. 고저 (2:4, 3:3, 4:2)
        if sum(1 for n in sorted_nums if n >= 23) not in (2, 3, 4):
            return False
            
        # 5. Hot/Cold 비율 (DB 데이터가 수집된 경우에만 검증하도록 수정)
        if self.hot_numbers or self.cold_numbers:
            cold_cnt = sum(1 for n in sorted_nums if n in self.cold_numbers)
            hot_cnt = sum(1 for n in sorted_nums if n in self.hot_numbers)
            if cold_cnt > 2 or (self.hot_numbers and hot_cnt < 1):
                return False

        return True

    def generate_combinations(self, count=5):
        results = []
        attempts = 0
        while len(results) < count and attempts < 100000:
            attempts += 1
            candidate = sorted(np.random.choice(range(1, 46), size=6, replace=False, p=self.probs[1:]).tolist())
            if self.passes_filters(candidate) and candidate not in results:
                results.append(candidate)
        return results, attempts