import sqlite3
import pandas as pd
import os

def update_lotto_database(excel_path="lotto.xlsx", db_path="lotto.db"):
    if not os.path.exists(excel_path):
        return
    
    df = pd.read_excel(excel_path)
    # 필요한 컬럼 정렬 및 DB 업데이트 로직
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lotto_history (
            draw_number INTEGER PRIMARY KEY,
            num1 INTEGER, num2 INTEGER, num3 INTEGER,
            num4 INTEGER, num5 INTEGER, num6 INTEGER, bonus INTEGER
        )
    """)
    
    for _, row in df.iterrows():
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO lotto_history 
                (draw_number, num1, num2, num3, num4, num5, num6, bonus)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (int(row.iloc[0]), int(row.iloc[1]), int(row.iloc[2]), 
                  int(row.iloc[3]), int(row.iloc[4]), int(row.iloc[5]), 
                  int(row.iloc[6]), int(row.iloc[7])))
        except Exception:
            pass
            
    conn.commit()
    conn.close()
