# 종합실습 코드에서 WeatherRecord 모델 불러오기
from 광주_2반_김지영_day1종합실습 import WeatherRecord


# 정상적인 날씨 데이터가 Pydantic 검증을 통과하는지 테스트
def test_weather_record():
    record = WeatherRecord(
        time="2026-07-20T09:00",
        temperature_2m=28.5,
        precipitation_probability=30
    )

    assert record.time == "2026-07-20T09:00"
    assert record.temperature_2m == 28.5
    assert record.precipitation_probability == 30