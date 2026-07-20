# ==========================================
# 프로그램 : 데이터 분석을 위한 Python의 이해 및 실습
# 작성자 : 김지영
# 작성일 : 2026-07-20
# 기능 :
# 1. JSON 파일 안전 로딩 및 예외·로그 처리
# 2. Pydantic v2를 활용한 SalesRecord 스키마 정의
# 3. 데이터 검증 후 valid / errors 분리
# 4. 검증 결과 CSV·JSON 저장 및 재로딩 검증
# 변경이력 : 
# 2026-07-20 | 최초 작성 및 JSON 파일 오류·예외 처리 추가
# ==========================================
import json
import logging
import csv
from pydantic import BaseModel, Field, ValidationError, field_validator
from typing import Optional


#1. 예외 처리 + 파일 읽기
# 로그 출력 형식 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)

logger = logging.getLogger(__name__)


# JSON 파일을 안전하게 불러오는 함수
# 성공 시 데이터 반환, 실패 시 None 반환
def safe_load_csv(filename):
    try:
        # JSON 파일 읽기
        with open(filename, "r", encoding="utf-8") as file:
            data = json.load(file)

        logger.info("파일을 정상적으로 불러왔습니다.")
        return data

    # 파일이 존재하지 않는 경우
    except FileNotFoundError:
        logger.error("파일을 찾을 수 없습니다.")
        return None

    # JSON 형식이 올바르지 않은 경우
    except json.JSONDecodeError:
        logger.error("JSON 파일 형식이 올바르지 않습니다.")
        return None

    # 성공/실패 여부와 관계없이 실행
    finally:
        print("로딩 종료")


# 2. Pydantic v2 스키마 정의
# SalesRecord 모델을 통해 각 판매 데이터의 형식과 조건을 정의
class SalesRecord(BaseModel):
    # 필수 항목
    month: str
    region: str

    # 매출액은 0보다 큰 값만 허용
    amount: int = Field(gt=0)

    # 카테고리는 값이 없어도 허용
    category: Optional[str] = None

    # month와 region이 빈 문자열 또는 공백만 있는 경우 오류 발생
    @field_validator("month", "region")
    @classmethod
    def check_not_blank(cls, value):
        if not value.strip():
            raise ValueError("빈 값 또는 공백만 입력할 수 없습니다.")
        return value

if __name__ == "__main__":
    # 존재하지 않는 파일은 예외 대신 None을 반환하는지 확인
    assert safe_load_csv("not_exists.json") is None

    # 데이터 불러오기
    raw_data = safe_load_csv("Python_Practice2_Data.json")

    # 3. 검증 파이프라인
    valid = []
    errors = []

    if raw_data is not None:
        for row in raw_data:
            try:
                record = SalesRecord.model_validate(row)
                valid.append(record.model_dump())
            except ValidationError as e:
                errors.append({
                    "row": row,
                    "error": e.errors(include_context=False)
                })

    if errors:
        logger.warning(
            "검증 오류가 %d건 있습니다. 자세한 내용은 error_log.json을 확인하세요.",
            len(errors)
        )

    print("검증 성공 건수 :", len(valid))
    print("검증 실패 건수 :", len(errors))

    # 4. 검증 결과 저장 및 재로딩 확인
    with open("valid_sales.csv", "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["month", "region", "amount", "category"]
        )
        writer.writeheader()
        writer.writerows(valid)

    with open("error_log.json", "w", encoding="utf-8") as file:
        json.dump(errors, file, ensure_ascii=False, indent=2)

    with open("valid_sales.csv", "r", encoding="utf-8-sig") as file:
        reloaded_valid = list(csv.DictReader(file))

    with open("error_log.json", "r", encoding="utf-8") as file:
        reloaded_errors = json.load(file)

    print("원본 valid 건수 :", len(valid))
    print("재로딩 valid 건수 :", len(reloaded_valid))
    print("원본 errors 건수 :", len(errors))
    print("재로딩 errors 건수 :", len(reloaded_errors))

    assert len(reloaded_valid) == len(valid)
    assert all(len(reloaded) == 4 for reloaded in reloaded_valid)
    assert len(reloaded_errors) == len(errors)
