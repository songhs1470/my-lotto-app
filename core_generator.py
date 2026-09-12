import pandas as pd
import random
import os
from typing import List, Set, Dict, Any, Tuple

# 1. AC 값 계산 함수
def calculate_ac(numbers: List[int]) -> int:
    sorted_nums = sorted(numbers)
    diffs = set()
    for i in range(len(sorted_nums)):
        for j in range(i + 1, len(sorted_nums)):
            diffs.add(sorted_nums[j] - sorted_nums[i])
    return len(diffs) - (len(numbers) - 1)

# 2. 최근 5회차 데이터 분석 함수 (예외 처리 강화)
def get_recent_5_stats(excel_path: str = "lotto.xlsx") -> Tuple[Set[int], Set[int], List[int]]:
    if not os.path.exists(excel_path):
        return set(), set(range(1, 46)), []
    
    try:
        df = pd.read_excel(excel_path)
        
        # 숫자 데이터만 추출하기 위한 처리
        valid_rows = []
        for _, row in df.iterrows():
            row_nums = []
            for val in row:
                try:
                    num = int(val)
                    row_nums.append(num)
                except (ValueError, TypeError):
                    continue
            # 로또 번호 6개 이상이 포함된 행만 수집
            if len(row_nums) >= 6:
                # 회차 번호를 제외한 6개 당첨번호 추출
                valid_rows.append(row_nums[1:7] if len(row_nums) >= 7 else row_nums[:6])
                
            if len(valid_rows) == 5:
                break
                
        if not valid_rows:
            return set(), set(range(1, 46)), []

        latest_draw = valid_rows[0]
        appeared = set()
        for r in valid_rows:
            appeared.update(r)
            
        all_nums = set(range(1, 46))
        unappeared = all_nums - appeared
        
        return appeared, unappeared, latest_draw
    except Exception:
        return set(), set(range(1, 46)), []

# 3. Level 2 통합 로또 번호 생성기
def generate_lotto_level2(
    count: int = 5,
    min_ac: int = 7,
    allow_3_consecutive: bool = False,
    carry_mode: str = "자동",
    custom_carry_nums: List[int] = None,
    use_neighbor: bool = False,
    use_same_end_limit: bool = True,
    section_ratio_mode: str = "선택 OFF",
    section_counts: Dict[str, int] = None,
    section_skew_mode: str = "선택 OFF",
    skew_target_range: str = None,
    use_recent_5_pattern: bool = False,
    excel_path: str = "lotto.xlsx"
) -> List[List[int]]:
    
    appeared_5, unappeared_5, latest_draw = get_recent_5_stats(excel_path)
    
    neighbors = set()
    if latest_draw:
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
            
            # --- [필터 1: 이월수] ---
            if carry_mode == "0개":
                pass
            elif carry_mode in ["1개", "2개"] and latest_draw:
                k = int(carry_mode[0])
                if len(latest_draw) >= k:
                    cand.update(random.sample(latest_draw, k))
            elif carry_mode == "직접선택" and custom_carry_nums:
                cand.update(custom_carry_nums)
            elif carry_mode == "자동" and latest_draw:
                k = random.choice([0, 1, 2])
                if len(latest_draw) >= k and k > 0:
                    cand.update(random.sample(latest_draw, k))
                    
            if len(cand) > 6:
                continue

            # --- [필터 2: 구간 쏠림] ---
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

            # --- [필터 3: 구간별 비중] ---
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

            # 나머지 무작위 채우기
            rem_pool = [n for n in range(1, 46) if n not in cand]
            if len(cand) < 6:
                cand.update(random.sample(rem_pool, 6 - len(cand)))
                
            nums = sorted(list(cand))
            if len(nums) != 6:
                continue

            # --- [검증 조건들] ---
            if calculate_ac(nums) < min_ac:
                continue

            if not allow_3_consecutive:
                has_3_consec = False
                for i in range(len(nums) - 2):
                    if nums[i+1] == nums[i] + 1 and nums[i+2] == nums[i] + 2:
                        has_3_consec = True; break
                if has_3_consec:
                    continue

            if use_neighbor and neighbors:
                if not any(n in neighbors for n in nums):
                    continue

            if use_same_end_limit:
                ends = [n % 10 for n in nums]
                end_counts = {}
                for e in ends:
                    end_counts[e] = end_counts.get(e, 0) + 1
                if any(cnt >= 4 for cnt in end_counts.values()):
                    continue

            if use_recent_5_pattern and appeared_5:
                cnt_app = sum(1 for n in nums if n in appeared_5)
                cnt_unapp = sum(1 for n in nums if n in unappeared_5)
                if not (2 <= cnt_app <= 3 and 2 <= cnt_unapp <= 3):
                    continue

            # 홀짝 및 합계 기본 안전성
            evens = sum(1 for n in nums if n % 2 == 0)
            if evens not in [2, 3, 4]:
                continue
            if not (100 <= sum(nums) <= 175):
                continue

            results.append(nums)
            break
            
    return results
