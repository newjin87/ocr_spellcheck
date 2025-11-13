"""
main_app.py
----------------------------------
Streamlit 통합 실행 파일 (모달 팝업 워크플로우)

프로세스:
1. PDF 업로드 -> Vision OCR -> 텍스트 추출
2. [원본 글] OCR 결과 편집 & 저장 (초기 화면)
3. "글 고쳐쓰기 시작" 버튼 -> 모달 팝업 열기
4. [팝업] 맞춤법 교정 -> 글쓰기 교정 순차 진행
5. 최종 결과 비교 & 다운로드 + 처음으로 버튼
----------------------------------
"""

import streamlit as st
import uuid
from datetime import datetime

# 사용자별 고유 세션 ID 생성 (중요!)
if 'user_session_id' not in st.session_state:
    st.session_state.user_session_id = str(uuid.uuid4())[:8]
    st.session_state.session_start_time = datetime.now()

# 사용자별 독립적인 임시 디렉토리
import tempfile
import os
USER_TEMP_DIR = os.path.join(tempfile.gettempdir(), f"streamlit_{st.session_state.user_session_id}")
os.makedirs(USER_TEMP_DIR, exist_ok=True)

from src.vision_ocr import run_ocr_pipeline
from src.spell_corrector import correct_text
from src.json_corrector import analyze_and_correct_to_json

# -------------------------------------------------------
# 🎨 UI 기본 설정
# -------------------------------------------------------
st.set_page_config(page_title="당신의 논설문을 고쳐드립니다! (ver.1.1.0)", page_icon="✍️", layout="wide")
st.title("✍️ 당신의 논설문을 고쳐드립니다! (ver.1.1.0)")

st.markdown("""
PDF에서 문서를 자동으로 읽고 맞춤법을 검사한 후  
Google Gemini를 사용해 **글쓰기를 개선**합니다. 🚀
""")

# -------------------------------------------------------
# 📂 파일 업로드
# -------------------------------------------------------
uploaded_file = st.file_uploader("📤 PDF 파일 업로드", type=["pdf"], key="main_uploader")

if uploaded_file:
    st.info("📘 PDF 업로드 완료 — OCR을 시작합니다...")
    extracted_text = run_ocr_pipeline(uploaded_file)

    if extracted_text:
        st.success("✅ OCR 완료!")
        
        # ============================================================
        # 원본 글 편집 & 저장
        # ============================================================
        st.subheader("📜 원본 글 (OCR 결과를 수정 후 저장)")
        st.markdown("*OCR 결과를 검토하고 필요한 부분을 수정한 후 '원본 저장' 버튼을 클릭하세요.*")
        
        # 기존 원본이 있으면 그걸 표시, 없으면 추출된 텍스트 표시
        if 'original_text' not in st.session_state:
            st.session_state['original_text'] = extracted_text
        
        edited_original = st.text_area(
            "원본 글 (편집 가능)",
            value=st.session_state['original_text'],
            height=350,
            key="original_edit"
        )
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info("원본을 수정한 후 아래 '원본 저장' 버튼을 클릭하세요.")
        with col2:
            if st.button("✅ 원본 저장", key="save_original", use_container_width=True):
                st.session_state['original_text'] = edited_original
                st.success("원본 글이 저장되었습니다.")
        
        # ============================================================
        # "글 고쳐쓰기 시작" 버튼 (초기 화면에만 표시)
        # ============================================================
        st.markdown("---")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button(
                "🚀 글 고쳐쓰기 시작",
                key="start_workflow_button",
                use_container_width=True
            ):
                if 'original_text' not in st.session_state or not st.session_state['original_text'].strip():
                    st.error("❌ 먼저 '원본 글'을 저장해주세요.")
                else:
                    st.session_state['show_workflow_modal'] = True
                    st.rerun()
        
        # ============================================================
        # 모달 팝업: 맞춤법 교정 + 글쓰기 교정 워크플로우
        # ============================================================
        if st.session_state.get('show_workflow_modal', False):
            @st.dialog("🚀 글 고쳐쓰기 워크플로우", width="large")
            def show_workflow_modal():
                # 초기화
                if 'modal_current_tab' not in st.session_state:
                    st.session_state['modal_current_tab'] = 0
                
                # 탭 2개: 맞춤법 교정, 글쓰기 교정
                modal_tab1, modal_tab2 = st.tabs(["🔍 맞춤법 교정", "✍️ 글쓰기 교정"])
                
                # ============================================================
                # 모달 TAB 1: 맞춤법 교정
                # ============================================================
                with modal_tab1:
                    st.subheader("🔍 맞춤법 교정")
                    
                    # 초기 맞춤법 교정 실행
                    if 'modal_spell_check_result' not in st.session_state:
                        with st.spinner("맞춤법 교정 중입니다... ⏳"):
                            original = st.session_state['original_text']
                            json_data = analyze_and_correct_to_json(original)
                            
                            if isinstance(json_data, dict) and 'error' in json_data:
                                st.error(f"❌ 오류: {json_data['error']}")
                                st.session_state['modal_spell_check_result'] = []
                            else:
                                st.session_state['modal_draft_after_spell'] = original
                                st.session_state['modal_spell_check_result'] = json_data
                    
                    # 맞춤법 오류 목록 표시
                    if 'modal_spell_check_result' in st.session_state:
                        json_data = st.session_state['modal_spell_check_result']
                        incorrect_items = [it for it in json_data if not it.get('is_correct')]
                        
                        if not incorrect_items:
                            st.success("🟢 완벽해요! 맞춤법 오류가 없습니다.")
                            st.info("ℹ️ 완벽한 글이므로 바로 다음 단계로 진행할 수 있습니다.")
                        else:
                            st.subheader("🔴 발견된 맞춤법 오류:")
                            for i, item in enumerate(incorrect_items):
                                with st.expander(f"문장 {item.get('sentence_id', i)+1}: {item.get('original_sentence')[:50]}..."):
                                    st.write(f"**원문**: {item.get('original_sentence')}")
                                    corrections = item.get('corrections', [])
                                    if corrections:
                                        st.write("**수정 제안**:")
                                        for c in corrections:
                                            st.write(f"- `{c.get('incorrect_word')}` -> `{c.get('correct_word')}`")
                        
                        # 맞춤법 교정 후 글 편집 영역
                        st.markdown("---")
                        st.subheader("✍️ 맞춤법 교정 후 글 편집")
                        edited_spell = st.text_area(
                            "맞춤법 교정 후 글 (편집 가능):",
                            value=st.session_state.get('modal_draft_after_spell', st.session_state['original_text']),
                            height=250,
                            key="modal_edit_after_spell"
                        )
                        
                        col1, col2, col3 = st.columns([1, 1, 1])
                        with col1:
                            if st.button("💾 저장", key="modal_save_spell", use_container_width=True):
                                st.session_state['modal_draft_after_spell'] = edited_spell
                                st.success("✅ 저장 완료")
                        with col2:
                            # 오류가 없으면 "다시 검사" 버튼 비활성화
                            if incorrect_items:
                                if st.button("🔎 다시 검사", key="modal_recheck_spell", use_container_width=True):
                                    with st.spinner("재검사 중..."):
                                        recheck = analyze_and_correct_to_json(edited_spell)
                                        if isinstance(recheck, dict) and 'error' in recheck:
                                            st.error(f"오류: {recheck['error']}")
                                        else:
                                            st.session_state['modal_spell_check_result'] = recheck
                                            st.session_state['modal_draft_after_spell'] = edited_spell
                                            remaining = [it for it in recheck if not it.get('is_correct')]
                                            if not remaining:
                                                st.success("🟢 재검사 완료: 오류 없음")
                                            else:
                                                st.warning(f"⚠️ 여전히 {len(remaining)}개 문장에 오류가 있습니다.")
                                            st.rerun()
                            else:
                                st.button("🔎 다시 검사", key="modal_recheck_spell", use_container_width=True, disabled=True)
                        with col3:
                            if st.button("➡️ 다음", key="modal_next_spell", use_container_width=True):
                                st.session_state['modal_draft_after_spell'] = edited_spell
                                st.session_state['modal_proceed_to_writing'] = True
                                st.rerun()
                
                # ============================================================
                # 모달 TAB 2: 글쓰기 교정
                # ============================================================
                with modal_tab2:
                    st.subheader("✍️ 글쓰기 교정")
                    
                    # 맞춤법 교정 완료 체크
                    if not st.session_state.get('modal_proceed_to_writing', False):
                        st.info("ℹ️ 맞춤법 교정 탭에서 '다음' 버튼을 클릭하세요.")
                    else:
                        # 초기 글쓰기 교정 실행
                        if 'modal_writing_feedback' not in st.session_state:
                            with st.spinner("글쓰기 교정 중입니다... ⏳"):
                                current_draft = st.session_state.get('modal_draft_after_spell', st.session_state['original_text'])
                                writing_feedback = correct_text(current_draft, "글쓰기 교정")
                                
                                if isinstance(writing_feedback, dict) and 'error' in writing_feedback:
                                    st.error(f"❌ 오류: {writing_feedback['error']}")
                                else:
                                    st.session_state['modal_draft_after_writing'] = current_draft
                                    st.session_state['modal_writing_feedback'] = writing_feedback
                        
                        # 글쓰기 교정 피드백 표시
                        if 'modal_writing_feedback' in st.session_state:
                            st.subheader("📝 교사 평가 및 고쳐쓰기 제안")
                            feedback = st.session_state['modal_writing_feedback']
                            st.text_area(
                                "평가 및 제안 (읽기 전용):",
                                value=feedback if isinstance(feedback, str) else str(feedback),
                                height=200,
                                disabled=True,
                                key="modal_feedback_display"
                            )
                        
                        # 글쓰기 교정 후 글 편집 영역
                        st.markdown("---")
                        st.subheader("✍️ 글쓰기 교정 후 글 편집")
                        edited_writing = st.text_area(
                            "글쓰기 교정 후 글 (편집 가능):",
                            value=st.session_state.get('modal_draft_after_writing', st.session_state['original_text']),
                            height=200,
                            key="modal_edit_after_writing"
                        )
                        
                        col1, col2, col3 = st.columns([1, 1, 1])
                        with col1:
                            if st.button("💾 저장", key="modal_save_writing", use_container_width=True):
                                st.session_state['modal_draft_after_writing'] = edited_writing
                                st.success("✅ 저장 완료")
                        with col2:
                            if st.button("🔎 다시 평가", key="modal_recheck_writing", use_container_width=True):
                                with st.spinner("재평가 중..."):
                                    refeedback = correct_text(edited_writing, "글쓰기 교정")
                                    if isinstance(refeedback, dict) and 'error' in refeedback:
                                        st.error(f"오류: {refeedback['error']}")
                                    else:
                                        st.session_state['modal_writing_feedback'] = refeedback
                                        st.session_state['modal_draft_after_writing'] = edited_writing
                                        st.success("✅ 재평가 완료!")
                                        st.rerun()
                        with col3:
                            if st.button("✅ 완성!", key="modal_finish", use_container_width=True):
                                st.session_state['modal_draft_after_writing'] = edited_writing
                                st.session_state['final_text'] = edited_writing
                                st.session_state['workflow_completed'] = True
                                st.session_state['show_workflow_modal'] = False
                                st.rerun()
            
            # 모달 함수 호출
            show_workflow_modal()
        
        # ============================================================
        # 최종 결과 비교 뷰 (팝업 종료 후)
        # ============================================================
        if st.session_state.get('workflow_completed', False):
            st.markdown("---")
            st.subheader("📊 최종 결과 비교")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 📄 원본 글")
                st.text_area(
                    "원본",
                    value=st.session_state['original_text'],
                    height=300,
                    disabled=True,
                    key="final_original"
                )
            
            with col2:
                st.markdown("#### ✨ 완성된 글")
                st.text_area(
                    "완성본",
                    value=st.session_state['final_text'],
                    height=300,
                    disabled=True,
                    key="final_completed"
                )
            
            # 다운로드 버튼
            st.markdown("---")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.download_button(
                    "📥 원본 글 다운로드 (.txt)",
                    data=st.session_state['original_text'],
                    file_name="original.txt",
                    use_container_width=True
                )
            with col2:
                st.download_button(
                    "📥 완성된 글 다운로드 (.txt)",
                    data=st.session_state['final_text'],
                    file_name="completed.txt",
                    use_container_width=True
                )
            with col3:
                if st.button("🔄 처음으로", use_container_width=True, key="reset_button"):
                    # 모든 상태 초기화
                    for key in list(st.session_state.keys()):
                        if key.startswith('modal_') or key in ['original_text', 'workflow_completed', 'final_text', 'show_workflow_modal']:
                            del st.session_state[key]
                    st.rerun()
    else:
        st.error("❌ OCR에서 텍스트를 추출하지 못했습니다. 로그를 확인하세요.")

# -------------------------------------------------------
# 🧩 Footer
# -------------------------------------------------------
st.markdown("---")
st.caption("Made with ❤️ by 유성진 | Vision API + Gemini 통합 버전")
