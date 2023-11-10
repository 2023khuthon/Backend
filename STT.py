import speech_recognition as sr

# Recognizer 객체 생성
recognizer = sr.Recognizer()

# 마이크로폰으로 음성을 캡처
with sr.Microphone() as source:
    print("말해보세요...")
    recognizer.adjust_for_ambient_noise(source)  # 환경 소음을 조절합니다.
    audio = recognizer.listen(source, timeout=5, phrase_time_limit = 5)  # 5초 동안 음성을 캡처합니다.

# Google Web API를 사용하여 음성을 텍스트로 변환
try:
    text = recognizer.recognize_google(audio, language="ja")
    print("음성을 텍스트로 변환한 결과:", text)
except sr.UnknownValueError:
    print("음성을 인식할 수 없습니다.")
except sr.RequestError as e:
    print(f"음성 인식 서비스에 오류가 발생했습니다: {e}")
