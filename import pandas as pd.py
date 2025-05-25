import pandas as pd
import os
import pandas as pd
from tkinter import Tk, filedialog

# Tkinter 창 숨기기
root = Tk()
root.withdraw()

# 파일 선택 대화상자
file_path = filedialog.askopenfilename(
    title="CSV 파일 선택",
    filetypes=(("CSV files", "*.csv"), ("All files", "*.*"))
)

# 파일 경로가 선택되었는지 확인
if file_path:
    print(f"선택한 파일 경로: {file_path}")

    try:
        df = pd.read_csv(file_path, encoding='utf-8-sig')  # 또는 encoding='cp949'
        print("📄 데이터프레임 미리보기:")
        print(df.head())
    except Exception as e:
        print(f"❌ 파일을 여는 중 오류 발생: {e}")
else:
    print("❌ 파일을 선택하지 않았습니다.")


# 저장 폴더 생성
os.makedirs("split_snack_categories", exist_ok=True)

# 분류 기준 정의 (키워드 기반)
category_keywords = {
    "수제간식": ["수제", "핸드메이드"],
    "덴탈껌": ["덴탈", "껌"],
    "사시미/육포": ["육포", "사시미", "져키", "저키", "트릿"],
    "저키": ["저키", "져키", "트릿"],  # 중복 포함 가능
    "뼈간식": ["뼈", "우족", "갈비", "목뼈"],
    "동결/건조": ["동결", "건조", "후reeze", "freeze", "말린"],
    "비스켓/쿠키": ["비스켓", "쿠키", "비스킷"],
    "소시지": ["소시지", "소세지"],
    "우유": ["우유", "밀크", "요거트"]
}

# 키워드에 따라 상품 분류 및 저장
for category, keywords in category_keywords.items():
    filtered_df = df[df["상품명"].str.contains('|'.join(keywords), case=False, na=False)]
    
    if not filtered_df.empty:
        filename = f"split_snack_categories/{category}.csv"
        filtered_df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"📁 '{category}' 카테고리 - {len(filtered_df)}개 저장 완료 → {filename}")
    else:
        print(f"⚠️ '{category}' 카테고리에 해당하는 상품이 없습니다.")
