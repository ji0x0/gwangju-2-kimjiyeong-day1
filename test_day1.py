# 종합실습 코드에서 WeatherRecord 모델 불러오기
from 광주_2반_김지영_day1종합실습 import WeatherRecord


# 정상적인 위도와 경도 값이 Pydantic 검증을 통과하는지 테스트
def test_weather_record():
    record = WeatherRecord(
        latitude=37.55,
        longitude=127.0,
        timezone="Asia/Seoul"
    )

    assert record.latitude == 37.55
    assert record.longitude == 127.0