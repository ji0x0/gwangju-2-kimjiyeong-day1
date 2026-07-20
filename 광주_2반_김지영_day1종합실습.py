# ==========================================
# 프로그램 : 데이터 수집 미니 파이프라인
# 작성자 : 김지영
# 작성일 : 2026-07-20
# 기능 :
# 1. asyncio와 httpx를 활용한 3개 API 비동기 데이터 수집
# 2. Open-Meteo 데이터에서 3일간 3시간 간격 날씨 데이터 추출
# 3. Pydantic v2를 활용한 API별 수집 데이터 스키마 검증
# 4. API별 검증 데이터를 CSV·Parquet 파일로 저장
# 5. API별 CSV·Parquet 읽기·쓰기 성능 측정 및 비교
# 변경이력 :
# 2026-07-20 | 최초 작성 및 데이터 수집·검증·저장 파이프라인 구현
# 2026-07-20 | 날씨 데이터 3시간 간격 추출 및 API별 파일 저장·성능 비교 기능 추가
# ==========================================
import asyncio
import logging
import time

import httpx
import pandas as pd
from pydantic import BaseModel, Field, ValidationError


# 로그 출력 형식 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)

logger = logging.getLogger(__name__)


# 3개 API 주소 정의
WEATHER_URL = (
    "https://api.open-meteo.com/v1/forecast"
    "?latitude=37.5665"
    "&longitude=126.9780"
    "&hourly=temperature_2m,precipitation_probability"
    "&forecast_days=3"
    "&timezone=Asia/Seoul"
)

COUNTRY_URL = "https://countries.dev/alpha/KOR"
IP_URL = "http://ip-api.com/json/8.8.8.8"


# ============================================================
# 1. asyncio와 httpx를 활용한 3개 API 비동기 데이터 수집
# ============================================================

# 하나의 API에 비동기 요청을 보내고 JSON 응답을 반환
async def fetch_json(client, url):
    response = await client.get(url)
    response.raise_for_status()
    return response.json()


# asyncio.gather()를 사용하여 3개 API를 동시에 수집
async def collect_all():
    async with httpx.AsyncClient() as client:
        weather_data, country_data, ip_data = await asyncio.gather(
            fetch_json(client, WEATHER_URL),
            fetch_json(client, COUNTRY_URL),
            fetch_json(client, IP_URL),
        )

    return weather_data, country_data, ip_data


# ============================================================
# 2. Open-Meteo 데이터에서 3일간 3시간 간격 날씨 데이터 추출
# ============================================================

# Open-Meteo의 1시간 간격 데이터에서 3시간마다 하나의 데이터를 추출
def extract_weather_3h(weather_data):
    times = weather_data["hourly"]["time"]
    temperatures = weather_data["hourly"]["temperature_2m"]
    precipitation_probabilities = weather_data["hourly"][
        "precipitation_probability"
    ]

    weather_data_3h = [
        {
            "time": times[i],
            "temperature_2m": temperatures[i],
            "precipitation_probability": precipitation_probabilities[i],
        }
        for i in range(0, len(times), 3)
    ]

    return weather_data_3h


# ============================================================
# 3. Pydantic v2를 활용한 API별 수집 데이터 스키마 검증
# ============================================================

# Open-Meteo 날씨 데이터 검증 모델
class WeatherRecord(BaseModel):
    time: str
    temperature_2m: float
    precipitation_probability: int = Field(ge=0, le=100)


# Countries.dev 국가 데이터 검증 모델
class CountryRecord(BaseModel):
    name: str
    region: str


# ip-api 위치 데이터 검증 모델
class IPRecord(BaseModel):
    query: str
    country: str
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)


# ============================================================
# 4. API별 검증 데이터를 CSV·Parquet 파일로 저장
# 5. API별 CSV·Parquet 읽기·쓰기 성능 측정 및 비교
# ============================================================

# DataFrame을 CSV·Parquet으로 저장하면서 읽기·쓰기 시간을 측정
def measure_io(df, name):
    # 4번 기능 + 5번 기능
    # CSV 파일 저장 및 저장 시간 측정
    start = time.perf_counter()
    df.to_csv(f"{name}.csv", index=False, encoding="utf-8-sig")
    csv_write_time = time.perf_counter() - start

    # 5번 기능
    # CSV 파일 읽기 시간 측정
    start = time.perf_counter()
    pd.read_csv(f"{name}.csv")
    csv_read_time = time.perf_counter() - start

    # 4번 기능 + 5번 기능
    # Parquet 파일 저장 및 저장 시간 측정
    start = time.perf_counter()
    df.to_parquet(f"{name}.parquet", index=False)
    parquet_write_time = time.perf_counter() - start

    # 5번 기능
    # Parquet 파일 읽기 시간 측정
    start = time.perf_counter()
    pd.read_parquet(f"{name}.parquet")
    parquet_read_time = time.perf_counter() - start

    # 성능 측정 결과 출력
    print(f"\n[{name}] CSV / Parquet 성능 비교 ({len(df)}행)")
    print(f"CSV 저장 시간     : {csv_write_time:.6f}초")
    print(f"CSV 읽기 시간     : {csv_read_time:.6f}초")
    print(f"Parquet 저장 시간 : {parquet_write_time:.6f}초")
    print(f"Parquet 읽기 시간 : {parquet_read_time:.6f}초")


# ============================================================
# 전체 프로그램 실행
# ============================================================

def main():

    # 1. asyncio와 httpx를 활용한 3개 API 비동기 데이터 수집
    try:
        weather_data, country_data, ip_data = asyncio.run(collect_all())

        logger.info("Open-Meteo 수집 완료")
        logger.info("Countries.dev 수집 완료")
        logger.info("ip-api 수집 완료")

    except httpx.HTTPError as e:
        logger.error("API 수집 오류: %s", e)
        return


    # 2. Open-Meteo 데이터에서 3일간 3시간 간격 날씨 데이터 추출
    try:
        weather_data_3h = extract_weather_3h(weather_data)


        # 3. Pydantic v2를 활용한 API별 수집 데이터 스키마 검증

        # Open-Meteo 날씨 데이터 검증
        weather_records = [
            WeatherRecord.model_validate(record)
            for record in weather_data_3h
        ]

        # Countries.dev 국가 데이터 검증
        country_record = CountryRecord.model_validate({
            "name": country_data["name"],
            "region": country_data["region"],
        })

        # ip-api 위치 데이터 검증
        ip_record = IPRecord.model_validate({
            "query": ip_data["query"],
            "country": ip_data["country"],
            "lat": ip_data["lat"],
            "lon": ip_data["lon"],
        })

        # 모든 API 데이터를 리스트 형태로 통일
        country_records = [country_record]
        ip_records = [ip_record]

        logger.info("Pydantic 스키마 검증 완료")

    except (KeyError, ValidationError) as e:
        logger.error("스키마 검증 오류: %s", e)
        return


    # 검증 결과 건수 출력
    print("\n[검증 결과 요약]")
    print(f"weather : 유효 {len(weather_records)}건")
    print(f"country : 유효 {len(country_records)}건")
    print(f"ip      : 유효 {len(ip_records)}건")


    # 추출 및 검증된 3시간 간격 날씨 데이터 출력
    print("\n[Open-Meteo] 서울 3일간 3시간 간격 날씨")

    for record in weather_records:
        print(
            f"- {record.time}: "
            f"{record.temperature_2m}°C, "
            f"강수확률 {record.precipitation_probability}%"
        )


    # Pydantic 모델을 딕셔너리 형태로 변환
    weather_rows = [record.model_dump() for record in weather_records]
    country_rows = [record.model_dump() for record in country_records]
    ip_rows = [record.model_dump() for record in ip_records]

    # 딕셔너리 데이터를 pandas DataFrame으로 변환
    weather_df = pd.DataFrame(weather_rows)
    country_df = pd.DataFrame(country_rows)
    ip_df = pd.DataFrame(ip_rows)


    # 4. API별 검증 데이터를 CSV·Parquet 파일로 저장
    # 5. API별 CSV·Parquet 읽기·쓰기 성능 측정 및 비교
    measure_io(weather_df, "weather")
    measure_io(country_df, "country")
    measure_io(ip_df, "ip")


# 이 Python 파일을 직접 실행했을 때만 main() 함수 실행
if __name__ == "__main__":
    main()