# src/json_corrector.py
import streamlit as st
import google.generativeai as genai
import json

# ----------------------------------------------------------------------
# 📝 JSON 출력 스키마 정의
# ----------------------------------------------------------------------
# Gemini 모델에게 요청할 JSON의 구조를 문자열로 명시합니다.
JSON_SCHEMA = """
[
  {
    "sentence_id": int, // 0부터 시작하는 문장 인덱스
    "original_sentence": "string", // 원본 문장 내용
    "is_correct": bool, // 문장에 오류가 없으면 true, 있으면 false
    "corrections": [
      {
        "incorrect_word": "string", // 틀린 단어 또는 구
        "correct_word": "string", // 올바른 교정 내용
        "reason": "string" // 오류가 발생한 이유 또는 유형 (띄어쓰기, 맞춤법 등)
      }
    ]
  }
]
"""

# ----------------------------------------------------------------------
# ⚙️ JSON 교정 핵심 함수
# ----------------------------------------------------------------------
def analyze_and_correct_to_json(text: str):
    """
    텍스트를 분석하여 맞춤법 오류를 찾아 JSON 구조로 반환합니다.
    """
    try:
        # ✅ 키 로드 (secrets.toml의 [gemini] api_key와 일치)
        api_key = st.secrets["gemini"]["api_key"]
    except KeyError:
        return {"error": "Gemini API 오류: '.streamlit/secrets.toml'에서 [gemini] 섹션 또는 'api_key' 키를 찾을 수 없습니다."}
    
    try:
        genai.configure(api_key=api_key)
        # ✅ JSON 출력에 안정적인 최신 모델 사용
        model = genai.GenerativeModel("gemini-2.5-flash") 
    except Exception as e:
        return {"error": f"Gemini 클라이언트 초기화 실패: {e}"}

    # 1. 프롬프트 구성 (역할 부여 및 JSON 스키마 명시)
    prompt = (
        f"당신은 한국어 맞춤법 및 문법 분석 전문가입니다. "
        f"다음 텍스트를 문장 단위로 나누어 분석하고, 모든 오류(맞춤법, 띄어쓰기, 문법)를 찾아 {JSON_SCHEMA} 형식의 JSON 배열로만 반환하세요. "
        f"오류가 없으면 'is_correct'를 true로, 'corrections'는 빈 배열로 설정해야 합니다. "
        f"반드시 JSON만 출력해야 합니다. 원본 텍스트:\n\n{text}"
    )

    # 🟢 UnboundLocalError 해결: response 변수를 미리 None으로 초기화
    response = None 
    
    try:
        # 2. Gemini API 호출 (JSON 출력 강제 옵션 사용)
        response = model.generate_content(
            contents=prompt,
            config=genai.types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        
        # 3. 모델이 반환한 JSON 문자열을 파이썬 객체로 변환
        json_data = json.loads(response.text)
        return json_data
        
    except Exception as e:
        # 🟢 response가 None이 아닐 때만 .text에 접근하여 오류 메시지 구성
        error_msg = f"Gemini JSON API 호출 오류: {e}"
        if response is not None:
             error_msg += f" (응답 텍스트: {response.text[:50]}...)"
             
        # JSON 파싱 실패 시, 모델이 JSON이 아닌 텍스트를 반환했을 가능성이 높으므로, 
        # API 오류 대신 JSON 파싱 오류 메시지를 포함하여 반환합니다.
        return {"error": error_msg}