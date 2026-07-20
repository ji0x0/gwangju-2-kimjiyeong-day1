# ==========================================
# 프로그램 : 데이터 수집 미니 파이프라인
# 작성자 : 김지영
# 작성일 : 2026-07-20
# 기능 :
# 1. asyncio와 httpx를 활용한 3개 API 비동기 데이터 수집
# 2. Pydantic v2를 활용한 수집 데이터 스키마 검증
# 3. 검증 데이터의 CSV·Parquet 파일 저장
# 4. CSV·Parquet 읽기·쓰기 성능 측정
# 변경이력 :
# 2026-07-20 | 최초 작성 및 데이터 수집·검증·저장 파이프라인 구현
# ==========================================
import asyncio
import httpx
import time
import pandas as pd
import logging
from pydantic import BaseModel, Field, ValidationError

# 로그 출력 형식 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)

logger = logging.getLogger(__name__)

# 1. asyncio와 httpx를 활용한 3개 API 비동기 API 수집
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

# 하나의 API에 비동기 요청을 보내고 JSON 응답을 반환
async def fetch_json(client, url):
    response = await client.get(url)
    response.raise_for_status()
    return response.json()

# 3개 API를 동시에 수집
async def collect_all():
    async with httpx.AsyncClient() as client:
        weather_data, country_data, ip_data = await asyncio.gather(
            fetch_json(client, WEATHER_URL),
            fetch_json(client, COUNTRY_URL),
            fetch_json(client, IP_URL),
        )

    return weather_data, country_data, ip_data

#2. Pydantic v2를 활용한 데이터 스키마 검증
# Open-Meteo 응답에서 사용할 데이터 모델
class WeatherRecord(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    timezone: str


# Countries.dev 응답에서 사용할 데이터 모델
class CountryRecord(BaseModel):
    name: str
    region: str


# ip-api 응답에서 사용할 데이터 모델
class IPRecord(BaseModel):
    query: str
    country: str
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)

# 프로그램 실행 흐름: API 수집, 검증, 파일 저장 및 성능 비교
def main():
    # API 요청 과정에서 발생할 수 있는 네트워크 오류 처리
    try:
        weather_data, country_data, ip_data = asyncio.run(collect_all())

        logger.info("Open-Meteo 수집 완료")
        logger.info("Countries.dev 수집 완료")
        logger.info("ip-api 수집 완료")

    except httpx.HTTPError as e:
        logger.error("API 수집 오류: %s", e)
        return

    try:
        # Open-Meteo 필요한 필드 추출 및 검증
        weather_record = WeatherRecord.model_validate({
            "latitude": weather_data["latitude"],
            "longitude": weather_data["longitude"],
            "timezone": weather_data["timezone"],
        })

        # Countries.dev 필요한 필드 추출 및 검증
        country_record = CountryRecord.model_validate({
            "name": country_data["name"],
            "region": country_data["region"],
        })

        # ip-api 필요한 필드 추출 및 검증
        ip_record = IPRecord.model_validate({
            "query": ip_data["query"],
            "country": ip_data["country"],
            "lat": ip_data["lat"],
            "lon": ip_data["lon"],
        })

        logger.info("Pydantic 스키마 검증 완료")
        print(weather_record)
        print(country_record)
        print(ip_record)

    except (KeyError, ValidationError) as e:
        logger.error("스키마 검증 오류: %s", e)
        return

    # 3.검증 데이터의 CSV·Parquet 파일 저장
    # 검증된 3개 API 데이터를 하나의 리스트로 구성
    validated_data = [
        {
            "source": "Open-Meteo",
            **weather_record.model_dump(),
        },
        {
            "source": "Countries.dev",
            **country_record.model_dump(),
        },
        {
            "source": "ip-api",
            **ip_record.model_dump(),
        },
    ]

    # 리스트 형태의 데이터를 pandas DataFrame으로 변환
    df = pd.DataFrame(validated_data)

    # 4. CSV·Parquet 읽기·쓰기 성능 측정
    # CSV 파일 저장 시간 측정
    start = time.perf_counter()
    df.to_csv("api_data.csv", index=False, encoding="utf-8-sig")
    csv_write_time = time.perf_counter() - start

    # CSV 파일 읽기 시간 측정
    start = time.perf_counter()
    pd.read_csv("api_data.csv")
    csv_read_time = time.perf_counter() - start

    # Parquet 파일 저장 시간 측정
    start = time.perf_counter()
    df.to_parquet("api_data.parquet", index=False)
    parquet_write_time = time.perf_counter() - start

    # Parquet 파일 읽기 시간 측정
    start = time.perf_counter()
    pd.read_parquet("api_data.parquet")
    parquet_read_time = time.perf_counter() - start

    # 검증 결과 출력
    print("\n[CSV / Parquet 성능 비교]")
    print(f"CSV 저장 시간     : {csv_write_time:.6f}초")
    print(f"CSV 읽기 시간     : {csv_read_time:.6f}초")
    print(f"Parquet 저장 시간 : {parquet_write_time:.6f}초")
    print(f"Parquet 읽기 시간 : {parquet_read_time:.6f}초")


if __name__ == "__main__":
    main()
