# ==========================================
# 프로그램 : 데이터 분석을 위한 Python의 이해 및 실습
# 작성자 : 김지영
# 작성일 : 2026-07-20
# 기능 :
# 1. 컴프리헨션을 활용한 amount >= 1000 거래 필터링 및 지역별 총매출 집계
# 2. Counter로 지역별 거래 건수 계산 및 defaultdict로 카테고리별 총매출 집계
# 3. amount > 1000 거래 제너레이터 작성 및 리스트와 메모리 사용량 비교
# 4. month·category 기준 월별 카테고리 총매출 집계 및 TOP 3 내림차순 정렬
# 변경이력 : 
# 2026-07-20 | 최초 작성 및 JSON 파일 오류·예외 처리 추가
# ==========================================
import json
from collections import Counter, defaultdict
import sys

# JSON 파일 불러오기
with open("Python_Practice2_Data.json", "r", encoding="utf-8") as file:
    sales = json.load(file)

# JSON 파일 불러오기 및 예외 처리
try:
    with open("Python_Practice2_Data.json", "r", encoding="utf-8") as file:
        sales = json.load(file)

except FileNotFoundError:
    print("오류: JSON 파일을 찾을 수 없습니다.")
    sys.exit()

except json.JSONDecodeError:
    print("오류: JSON 파일 형식이 올바르지 않습니다.")
    sys.exit()

# 1-1. amount가 1000 이상인 거래만 필터링
high_sales = [sale for sale in sales if sale["amount"] >= 1000]

# 지역 목록 추출
regions = {sale["region"] for sale in high_sales}

# 1-2. 지역별 총 매출 집계
region_total = {
    region: sum (
        (sale["amount"] 
        for sale in high_sales 
        if sale["region"] == region)
    )
    for region in regions
}

print("amount >= 1000인 거래만 필터링한 후 지역별 총매출 :", region_total)

#체크포인트 확인용
assert region_total["서울"] == 17670

# 2-1. Counter를 사용하여 지역별 거래 건수 계산
region_count = Counter(sale["region"] for sale in sales)
region_count_ranking = region_count.most_common()

print("지역별 거래 건수 :", region_count_ranking)

# 2-2. defaultdict를 사용하여 카테고리별 총 매출 계산
category_sales = defaultdict(int)

for sale in sales:
    category_sales[sale["category"]] += sale["amount"]

print("카테고리별 총 매출 :", dict(category_sales))

# 3. amount가 1000보다 큰 행만 반환하는 제너레이터
def high_amount_generator(sales):
    for sale in sales:
        if sale["amount"] > 1000:
            yield sale

# 리스트 버전
high_amount_list = [sale for sale in sales if sale["amount"] > 1000]

# 제너레이터 버전
high_amount_gen = high_amount_generator(sales)

# 메모리 크기 비교
print("리스트 메모리 크기 :", sys.getsizeof(high_amount_list), "bytes")
print("제너레이터 메모리 크기 :", sys.getsizeof(high_amount_gen), "bytes")

# 4. 월별·카테고리별 총 매출 집계
# defaultdict 생성
monthly_category_sales = defaultdict(int)

# 컴프리헨션을 사용하여 (month, category)와 amount 추출
sales_data = [
    ((sale["month"], sale["category"]), sale["amount"])
    for sale in sales
]

# 월별·카테고리별 amount 합산
for key, amount in sales_data:
    monthly_category_sales[key] += amount

print("월별·카테고리별 총 매출 :", dict(monthly_category_sales))

# 금액 기준 TOP 3 내림차순 정렬
top3 = sorted(
    monthly_category_sales.items(),
    key=lambda item: item[1],
    reverse=True
)[:3]

print("월별·카테고리별 매출 TOP 3 :", top3)