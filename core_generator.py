import sqlite3
import random
from typing import List, Set, Dict, Any, Tuple

# 1. AC 값 계산 함수
def calculate_ac(numbers: List[int]) -> int:
    sorted_nums = sorted(numbers)
    diffs = set()
    for i in range(len(sorted_nums)):
        for j in range(i + 1, len(sorted_nums)):
            diffs.add(sorted_nums[j] - sorted_nums[i])
    return len(diffs) - (len(numbers) - 1)

# 2. 최근 5회차 데이터 분석 함수
def get_recent_5_stats(db_path: str = "lotto.db") -> Tuple[Set[int], Set[int], List[int]]:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT num1, num2, num3, num4, num5, num6 
        FROM lotto_history 
        ORDER BY draw_number DESC LIMIT 5
    """)
    rows = cursor.fetchall()
    
    # 전회차 당첨번호 (가장 최근 1회차)
    latest_draw = list(rows[0]) if rows else []
    
    appeared = set()
    for r in rows:
        appeared.update(r)
        
    all_nums = set(range(1, 46))
    unappeared = all_nums - appeared
    conn.close()
    
    return appeared, unappeared, latest_draw

# 3. Level 2 통합 로또 번호 생성기
def generate_lotto_level2(
    count: int = 5,
    min_ac: int = 7,
    allow_3_consecutive: bool = False,
    carry_mode: str = "자동",  # "자동", "0개", "1개", "2개", "직접선택"
    custom_carry_nums: List[int] = None,
    use_neighbor: bool = False,
    use_same_end_limit: bool = True,
    section_ratio_mode: str = "선택 OFF",  # "선택 OFF", "대역별 개수 지정", "랜덤"
    section_counts: Dict[str, int] = None,  # 예: {"1-9": 1, "10-19": 2, ...}
    section_skew_mode: str = "선택 OFF",   # "선택 OFF", "특정 구간 지정", "랜덤"
    skew_target_range: str = None,         # "1-9", "10-19", "20-29", "30-39", "40-45"
    use_recent_5_pattern: bool = False,
    db_path: str = "lotto.db"
) -> List[List[int]]:
    
    appeared_5, unappeared_5, latest_draw = get_recent_5_stats(db_path)
    
    # 전회차 이웃수 (±1, ±2) 집합
    neighbors = set()
    for num in latest_draw:
        for offset in [-2, -1, 1, 2]:
            cand = num + offset
            if 1 <= cand <= 45 and cand not in latest_draw:
                neighbors.add(cand)

    results = []
    max_attempts = 100000
    
    for _ in range(count):
        attempts = 0
        while attempts < max_attempts:
            attempts += 1
            cand = set()
            
            # --- [필터 1: 전회차 이월수 처리] ---
            if carry_mode == "0개":
                pass
            elif carry_mode in ["1개", "2개"]:
                k = int(carry_mode[0])
                if len(latest_draw) >= k:
                    cand.update(random.sample(latest_draw, k))
            elif carry_mode == "직접선택" and custom_carry_nums:
                cand.update(custom_carry_nums)
            elif carry_mode == "자동":
                k = random.choice([0, 1, 2])
                if len(latest_draw) >= k and k > 0:
                    cand.update(random.sample(latest_draw, k))
                    
            if len(cand) > 6:
                continue

            # --- [필터 2: 구간 쏠림(3~4개) 처리] ---
            if section_skew_mode != "선택 OFF":
                target_range = skew_target_range
                ranges = {
                    "1-9": list(range(1, 10)),
                    "10-19": list(range(10, 20)),
                    "20-29": list(range(20, 30)),
                    "30-39": list(range(30, 40)),
                    "40-45": list(range(40, 46))
                }
                if section_skew_mode == "랜덤" or not target_range:
                    target_range = random.choice(list(ranges.keys()))
                
                skew_count = random.choice([3, 4])
                pool = [n for n in ranges[target_range] if n not in cand]
                needed = skew_count - len([n for n in cand if n in ranges[target_range]])
                if needed > 0 and len(pool) >= needed and len(cand) + needed <= 6:
                    cand.update(random.sample(pool, needed))

            # --- [필터 3: 구간별 비중 지정 처리] ---
            if section_ratio_mode == "대역별 개수 지정" and section_counts:
                ranges = {
                    "1-9": list(range(1, 10)),
                    "10-19": list(range(10, 20)),
                    "20-29": list(range(20, 30)),
                    "30-39": list(range(30, 40)),
                    "40-45": list(range(40, 46))
                }
                valid_spec = True
                for r_key, req_cnt in section_counts.items():
                    curr_cnt = len([n for n in cand if n in ranges[r_key]])
                    diff = req_cnt - curr_cnt
                    if diff < 0:
                        valid_spec = False; break
                    pool = [n for n in ranges[r_key] if n not in cand]
                    if len(pool) < diff:
                        valid_spec = False; break
                    if diff > 0:
                        cand.update(random.sample(pool, diff))
                if not valid_spec or len(cand) > 6:
                    continue

            # --- 나머지 번호 무작위 채우기 ---
            rem_pool = [n for n in range(1, 46) if n not in cand]
            if len(cand) < 6:
                cand.update(random.sample(rem_pool, 6 - len(cand)))
                
            nums = sorted(list(cand))
            if len(nums) != 6:
                continue

            # --- [검증 1: AC값] ---
            if calculate_ac(nums) < min_ac:
                continue

            # --- [검증 2: 연속 번호 제어] ---
            if not allow_3_consecutive:
                has_3_consec = False
                for i in range(len(nums) - 2):
                    if nums[i+1] == nums[i] + 1 and nums[i+2] == nums[i] + 2:
                        has_3_consec = True; break
                if has_3_consec:
                    continue

            # --- [검증 3: 전회차 이웃수] ---
            if use_neighbor:
                if not any(n in neighbors for n in nums):
                    continue

            # --- [검증 4: 동끝수 제한 (2~3개 이하)] ---
            if use_same_end_limit:
                ends = [n % 10 for n in nums]
                end_counts = {}
                for e in ends:
                    end_counts[e] = end_counts.get(e, 0) + 1
                if any(cnt >= 4 for cnt in end_counts.values()):
                    continue

            # --- [검증 5: 최근 5회차 패턴] ---
            if use_recent_5_pattern:
                cnt_app = sum(1 for n in nums if n in appeared_5)
                cnt_unapp = sum(1 for n in nums if n in unappeared_5)
                if not (2 <= cnt_app <= 3 and 2 <= cnt_unapp <= 3):
                    continue

            # 기본 안전성 검증 (홀짝/합계)
            evens = sum(1 for n in nums if n % 2 == 0)
            if evens not in [2, 3, 4]:
                continue
            if not (100 <= sum(nums) <= 175):
                continue

            results.append(nums)
            break
            
    return results
