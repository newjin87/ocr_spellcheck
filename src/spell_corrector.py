import streamlit as st
import google.genai as genai
# json_corrector 모듈이 src 폴더에 있으므로 src.json_corrector로 수정
from src.json_corrector import analyze_and_correct_to_json 
import json 

def format_json_result_to_text(json_data):
    """
    JSON 분석 결과를 main_app.py가 표시할 수 있는 깔끔한 텍스트 형식으로 변환합니다.
    (오류 통계 및 상세 교정 내용을 포함)
    """
    if isinstance(json_data, dict) and 'error' in json_data:
        return f"❌ 오류 발생: {json_data['error']}"

    output_text = []
    total_sentences = len(json_data)
    incorrect_sentences = sum(1 for item in json_data if not item['is_correct'])

    # 1. 통계 요약
    output_text.append("="*50)
    output_text.append(f"          맞춤법 오류 분석 결과 (총 {total_sentences} 문장)")
    output_text.append("="*50)
    output_text.append(f"🟢 오류 없음: {total_sentences - incorrect_sentences} 문장")
    output_text.append(f"🔴 오류 발견: {incorrect_sentences} 문장")
    output_text.append("="*50 + "\n")

    # 2. 문장별 상세 분석 (오류 문장만)
    for i, item in enumerate(json_data):
        if not item['is_correct']:
            output_text.append(f"--- [문장 {i+1}] 오류 발견 ---")
            output_text.append(f"원본: {item['original_sentence']}")
            
            # 오류 내용 목록
            if item['corrections']:
                output_text.append("세부 교정 내용:")
                for correction in item['corrections']:
                    output_text.append(
                        f"  - [틀린 부분: {correction['incorrect_word']}] -> "
                        f"[교정: {correction['correct_word']}] ({correction['reason']})"
                    )
            else:
                output_text.append("  - 상세 교정 내용 없음")
            output_text.append("\n")

    return "\n".join(output_text)


def correct_text(text: str, mode: str = "맞춤법 교정") -> str:
    """Gemini API를 사용해 텍스트 맞춤법/문법 교정"""
    
    # 🟢 "맞춤법 교정" 모드는 JSON 분석 기능으로 연결됨
    if mode == "맞춤법 교정":
        json_data = analyze_and_correct_to_json(text)
        return format_json_result_to_text(json_data)
        
    # ----------------------------------------------------------------------
    # 💡 기존 일반 텍스트 교정 로직 (나머지 모드)
    # ----------------------------------------------------------------------

    try:
        api_key = st.secrets["gemini"]["api_key"]
    except KeyError:
        return "❌ Gemini API 오류: '.streamlit/secrets.toml'에서 [gemini] 섹션 또는 'api_key' 키를 찾을 수 없습니다."
    
    try:
        # ✅ SDK 오류 해결: Client 방식으로 변경
        client = genai.Client(api_key=api_key) 
    except Exception as e:
        return f"❌ Gemini 클라이언트 초기화 실패: {e}"


    prompts = {
        "문장 자연스럽게 다듬기": (
            f"다음 텍스트를 읽고, 내용의 핵심을 유지하면서 한국인이 보기에 가장 자연스럽고 세련된 문장으로 다듬어주세요. "
            f"수정된 결과만 출력해:\n\n{text}"
        ),
        "요약하기": f"다음 문장을 간결하게 요약해줘. 결과만 보여줘:\n\n{text}",
        "영어 번역": f"다음 텍스트를 전문적인 비즈니스 영어로 번역해주세요. 번역된 결과만 출력해:\n\n{text}"
    }

    selected_prompt = prompts.get(mode) 

    if selected_prompt:
        try:
            # ✅ Client.models.generate_content 사용
            response = client.models.generate_content(
                model="gemini-2.5-flash", # gemini-2.5-flash 모델 사용
                contents=selected_prompt
            )
            return response.text
        except Exception as e:
            return f"❌ Gemini API 호출 오류: {e}"
    else:
        return f"❌ 정의되지 않은 교정 모드: {mode}"