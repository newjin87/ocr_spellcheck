# src/spell_corrector.py (수정된 최종 코드)
import streamlit as st
import google.generativeai as genai
# ✅ 새로 만든 모듈 import
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
    
    # 🟢 "맞춤법 교정" 모드를 JSON 분석 기능으로 연결
    if mode == "맞춤법 교정":
        json_data = analyze_and_correct_to_json(text)
        # JSON 결과를 텍스트로 변환하여 main_app.py에 반환
        return format_json_result_to_text(json_data)
        
    # ----------------------------------------------------------------------
    # 💡 기존 일반 텍스트 교정 로직 (나머지 모드)
    # ----------------------------------------------------------------------

    try:
        api_key = st.secrets["gemini"]["api_key"]
    except KeyError:
        return "❌ Gemini API 오류: '.streamlit/secrets.toml'에서 [gemini] 섹션 또는 'api_key' 키를 찾을 수 없습니다."
    
    try:
        genai.configure(api_key=api_key)
        # ✅ 모델 이름을 일관성 있게 변경 (gemini-2.5-flash)
        model = genai.GenerativeModel("gemini-2.5-flash") 
    except Exception as e:
        return f"❌ Gemini 클라이언트 초기화 실패: {e}"


    prompts = {
        # "맞춤법 교정" 모드는 이제 위에서 처리됩니다.
        "문장 자연스럽게 다듬기": (
            f"다음 텍스트를 읽고, 내용의 핵심을 유지하면서 한국인이 보기에 가장 자연스럽고 세련된 문장으로 다듬어주세요. "
            f"수정된 결과만 출력해:\n\n{text}"
        ),
        "요약하기": f"다음 문장을 간결하게 요약해줘. 결과만 보여줘:\n\n{text}",
        "영어 번역": f"다음 텍스트를 전문적인 비즈니스 영어로 번역해주세요. 번역된 결과만 출력해:\n\n{text}"
    }

    selected_prompt = prompts.get(mode) # "맞춤법 교정"이 프롬프트에서 제거됨

    # 만약 맞춤법 교정 외의 모드를 선택했다면
    if selected_prompt:
        try:
            response = model.generate_content(selected_prompt)
            return response.text
        except Exception as e:
            return f"❌ Gemini API 호출 오류: {e}"
    else:
        # 이전에 처리되지 않은 모드가 넘어오면 오류 메시지 반환
        return f"❌ 정의되지 않은 교정 모드: {mode}"