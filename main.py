import sys
from db_pipeline import sync_lotto_database
from core_generator import LottoCoreGenerator
from backtester import LottoBacktester

def render_dashboard(game, idx):
    num_sum = sum(game)
    odd_cnt = sum(1 for n in game if n % 2 != 0)
    high_cnt = sum(1 for n in game if n >= 23)
    
    diffs = set(abs(game[i] - game[j]) for i in range(6) for j in range(i + 1, 6))
    ac_val = len(diffs) - 5

    grid = ["."] * 45
    for n in game:
        grid[n - 1] = "█"
    vis_bar = "".join(grid)

    print(f"║ 게임 {idx:02d} ║ {str(game):<26} ║ 합계: {num_sum:3d} ║ AC: {ac_val:2d} ║ 홀짝 {odd_cnt}:{6-odd_cnt} ║ 고저 {high_cnt}:{6-high_cnt} ║")
    print(f"  └ 분포: [{vis_bar[:15]}|{vis_bar[15:30]}|{vis_bar[30:]}]")

def main():
    print("=" * 80)
    print("      수학적 확률 분석 및 필터링 기반 최적 로또 번호 생성기 v1.0")
    print("=" * 80)

    # 1. 실행 시 최신 DB 자동 파싱/동기화 연동
    sync_lotto_database()

    # 2. 핵심 엔진 초기화
    generator = LottoCoreGenerator()

    while True:
        print("\n[ 메뉴 선택 ]")
        print("1. 최적 로또 조합 생성 (5게임)")
        print("2. 과거 데이터 기반 알고리즘 백테스팅")
        print("3. DB 최신화 다시 실행")
        print("4. 프로그램 종료")
        choice = input("선택 (1-4): ").strip()

        if choice == "1":
            print("\n" + "=" * 80)
            games, attempts = generator.generate_combinations(count=5)
            print(f"▶ 필터 체인 검증 완료 (무작위 시도 {attempts:,}회 중 조건 충족 조합 5개 선별)")
            print("-" * 80)
            for idx, game in enumerate(games, 1):
                render_dashboard(game, idx)
            print("=" * 80)

        elif choice == "2":
            backtester = LottoBacktester(generator)
            backtester.run_backtest(test_draws=20, games_per_draw=5)

        elif choice == "3":
            sync_lotto_database()
            generator.reload_engine()

        elif choice == "4":
            print("프로그램을 종료합니다.")
            sys.exit()
        else:
            print("잘못된 입력입니다.")

if __name__ == "__main__":
    main()