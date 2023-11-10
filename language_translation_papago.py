import requests
import const

# API 요청 URL
translate_url = 'https://openapi.naver.com/v1/papago/n2mt'
detect_url = 'https://openapi.naver.com/v1/papago/detectLangs'

# API 요청 헤더
headers = {
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'X-Naver-Client-Id': const.papago_id,
    'X-Naver-Client-Secret': const.papago_secret,
}

def detect_language(text):
    data = {
        'query': text,
    }

    response = requests.post(detect_url, headers=headers, data=data)

    if response.status_code == 200:
        result = response.json()
        detected_language = result['langCode']
        return detected_language
    else:
        return None

def translate_text(text, target_language):
    source_language = detect_language(text)  # 입력 텍스트의 언어 감지

    data = {
        'source': source_language,  # 원본 언어 코드
        'target': target_language,  # 번역하려는 언어 코드
        'text': text,
    }

    response = requests.post(translate_url, headers=headers, data=data)

    if response.status_code == 200:
        result = response.json()
        translated_text = result['message']['result']['translatedText']
        return translated_text
    else:
        return f'Failed to translate. Status code: {response.status_code}'

# 사용자 입력 받기
#text_to_translate = input('번역할 텍스트를 입력하세요: ')
# = input('번역하려는 언어 코드를 입력하세요 (예: ko): ')

#translated_text = translate_text(text_to_translate, target_language)
#print(f'Translated text ({target_language}): {translated_text}')
