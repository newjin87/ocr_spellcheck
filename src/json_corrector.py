# src/json_corrector.py
import streamlit as st
import google.generativeai as genai
import json
import time
import re
import traceback

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

    # 안전한 JSON 파싱 유틸리티: 문자열에서 JSON 배열/객체 부분을 추출해 파싱 시도
    def try_parse_json(text: str):
        text = text.strip()
        # 빠른 시도
        try:
            return json.loads(text)
        except Exception:
            pass

        # 배열 또는 객체의 첫/마지막 괄호 위치를 찾아 부분 문자열로 파싱 시도
        # 우선 배열 '[ ... ]' 탐색
        arr_match = re.search(r"(\[.*\])", text, re.S)
        if arr_match:
            try:
                return json.loads(arr_match.group(1))
            except Exception:
                pass

        # 객체 '{ ... }' 탐색
        obj_match = re.search(r"(\{.*\})", text, re.S)
        if obj_match:
            try:
                return json.loads(obj_match.group(1))
            except Exception:
                pass

        # 실패
        raise ValueError("응답에서 JSON을 파싱할 수 없습니다.")

    # 재시도/백오프 설정
    max_retries = 3
    base_delay = 1.0

    last_exc = None
    for attempt in range(1, max_retries + 1):
        try:
            # 2. Gemini API 호출
            response = model.generate_content(contents=prompt)

            # 3. 모델이 반환한 JSON 문자열을 파이썬 객체로 변환
            if hasattr(response, 'text') and response.text:
                try:
                    json_data = try_parse_json(response.text)
                    return json_data
                except Exception as parse_err:
                    # 파싱 실패는 재시도하지 않고 오류로 반환 (모델 출력 교정 필요)
                    tb = traceback.format_exc()
                    return {"error": f"JSON 파싱 실패: {parse_err}. 응답 일부: {response.text[:200]}", "trace": tb}
            else:
                # 응답이 비어있는 경우 재시도
                raise RuntimeError("응답 텍스트가 비어있습니다.")

        except Exception as e:
            last_exc = e
            # 내부 서버 오류(500)등 일시적 오류일 경우 재시도
            if attempt < max_retries:
                delay = base_delay * (2 ** (attempt - 1))
                time.sleep(delay)
                continue
            else:
                # 최대 재시도 후 실패: 더 자세한 정보 반환
                resp_snippet = None
                try:
                    if response is not None and hasattr(response, 'text'):
                        resp_snippet = response.text[:300]
                except Exception:
                    resp_snippet = None

                tb = traceback.format_exc()
                return {"error": f"Gemini JSON API 호출 오류 (attempts={max_retries}): {e}", "response_snippet": resp_snippet, "trace": tb}