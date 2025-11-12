"""
main_app.py
----------------------------------
Streamlit 통합 실행 파일 (순차적 워크플로우)

프로세스:
1. PDF 업로드 -> Vision OCR -> 텍스트 추출
2. [원본 글 탭] 추출 텍스트를 수정 후 저장
3. [글 고쳐쓰기 시작] 버튼 -> 맞춤법 교정 -> 글쓰기 교정 순차 실행
4. 각 단계: 편집/저장/재검사 가능, 다음 단계로 결과 전파
5. 최종 비교 뷰: 원본 vs 완성본 (복사/다운로드)
----------------------------------
"""

import streamlit as st
from src.vision_ocr import run_ocr_pipeline
from src.spell_corrector import correct_text
from src.json_corrector import analyze_and_correct_to_json

# -------------------------------------------------------
# 🎨 UI 기본 설정
# -------------------------------------------------------
st.set_page_config(page_title="AI OCR + 맞춤법 교정기", page_icon="🧠", layout="wide")
st.title("🧾 AI OCR + 맞춤법 교정기 (Google Vision + Gemini)")

st.markdown("""
이 앱은 PDF에서 문서를 자동으로 읽고  
Google Gemini를 사용해 **맞춤법 교정 -> 글쓰기 교정**을 순차적으로 수행합니다. ✨
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
        
        # 탭 구성: 원본 글 탭만 유지
        tab1, tab2, tab3 = st.tabs(["📝 원본 글", "🔍 맞춤법 교정", "✍️ 글쓰기 교정"])
        
        # ============================================================
        # TAB 1: 원본 글 저장
        # ============================================================
        with tab1:
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
                    st.success("원본 글이 저장되었습니다. 이제 '글 고쳐쓰기 시작' 버튼을 누르세요.")
        
        # ============================================================
        # 단일 워크플로우: "글 고쳐쓰기 시작" 버튼
        # ============================================================
        st.markdown("---")
        st.subheader("🚀 글 고쳐쓰기 시작")
        st.markdown("*원본을 저장한 후 아래 버튼을 클릭하면 '맞춤법 교정' -> '글쓰기 교정'이 순차적으로 실행됩니다.*")
        
        if st.button("🚀 글 고쳐쓰기 시작", use_container_width=True, key="start_workflow"):
            if 'original_text' not in st.session_state or not st.session_state['original_text'].strip():
                st.error("❌ 먼저 '원본 글' 탭에서 원본을 저장해주세요.")
            else:
                st.session_state['workflow_started'] = True
        
        # ============================================================
        # TAB 2: 맞춤법 교정 (워크플로우 실행 시)
        # ============================================================
        with tab2:
            st.subheader("🔍 맞춤법 교정")
            
            if st.session_state.get('workflow_started', False):
                # 맞춤법 교정 실행
                if 'draft_after_spell' not in st.session_state:
                    with st.spinner("맞춤법 교정 중입니다... ⏳"):
                        original = st.session_state['original_text']
                        json_data = analyze_and_correct_to_json(original)
                        
                        if isinstance(json_data, dict) and 'error' in json_data:
                            st.error(f"❌ 오류: {json_data['error']}")
                            st.session_state['workflow_started'] = False
                        else:
                            # 초안을 원본으로 설정 (수정 사항 미적용)
                            st.session_state['draft_after_spell'] = original
                            st.session_state['spell_check_result'] = json_data
                
                # 맞춤법 오류 목록 표시
                if 'spell_check_result' in st.session_state:
                    json_data = st.session_state['spell_check_result']
                    incorrect_items = [it for it in json_data if not it.get('is_correct')]
                    
                    if not incorrect_items:
                        st.success("🟢 오류 없음: 모든 문장이 올바릅니다.")
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
                        value=st.session_state.get('draft_after_spell', st.session_state['original_text']),
                        height=300,
                        key="edit_after_spell"
                    )
                    
                    col1, col2, col3 = st.columns([1, 1, 1])
                    with col1:
                        if st.button("💾 이 상태 저장", key="save_spell", use_container_width=True):
                            st.session_state['draft_after_spell'] = edited_spell
                            st.success("✅ 맞춤법 교정 단계 저장 완료")
                    with col2:
                        if st.button("🔎 다시 검사", key="recheck_spell", use_container_width=True):
                            with st.spinner("재검사 중..."):
                                # 편집된 글을 기반으로 새로운 맞춤법 검사 수행
                                recheck = analyze_and_correct_to_json(edited_spell)
                                if isinstance(recheck, dict) and 'error' in recheck:
                                    st.error(f"오류: {recheck['error']}")
                                else:
                                    # 새로운 결과로 업데이트
                                    st.session_state['spell_check_result'] = recheck
                                    st.session_state['draft_after_spell'] = edited_spell
                                    remaining = [it for it in recheck if not it.get('is_correct')]
                                    if not remaining:
                                        st.success("🟢 재검사 완료: 오류 없음")
                                    else:
                                        st.warning(f"⚠️ 여전히 {len(remaining)}개 문장에 오류가 있습니다.")
                                    st.rerun()
                    with col3:
                        if st.button("➡️ 다음 단계로", key="next_from_spell", use_container_width=True):
                            st.session_state['draft_after_spell'] = edited_spell
                            st.session_state['proceed_to_writing'] = True
                            st.rerun()
            else:
                st.info("ℹ️ 위의 '글 고쳐쓰기 시작' 버튼을 클릭하여 워크플로우를 시작하세요.")
        
        # ============================================================
        # TAB 3: 글쓰기 교정 (맞춤법 교정 후)
        # ============================================================
        with tab3:
            st.subheader("✍️ 글쓰기 교정")
            
            if st.session_state.get('proceed_to_writing', False):
                # 글쓰기 교정 실행 (맞춤법 교정 후 저장된 글을 기반으로)
                if 'draft_after_writing' not in st.session_state or 'writing_feedback_for_current' not in st.session_state:
                    with st.spinner("글쓰기 교정 중입니다... ⏳"):
                        # 맞춤법 교정에서 저장된 글을 기반으로 교정 진행
                        current_draft = st.session_state.get('draft_after_spell', st.session_state['original_text'])
                        writing_feedback = correct_text(current_draft, "글쓰기 교정")
                        
                        if isinstance(writing_feedback, dict) and 'error' in writing_feedback:
                            st.error(f"❌ 오류: {writing_feedback['error']}")
                        else:
                            st.session_state['draft_after_writing'] = current_draft
                            st.session_state['writing_feedback_for_current'] = writing_feedback
                
                # 글쓰기 교정 피드백 표시
                if 'writing_feedback_for_current' in st.session_state:
                    st.subheader("📝 교사 평가 및 고쳐쓰기 제안")
                    feedback = st.session_state['writing_feedback_for_current']
                    st.text_area(
                        "평가 및 제안 (읽기 전용):",
                        value=feedback if isinstance(feedback, str) else str(feedback),
                        height=250,
                        disabled=True
                    )
                
                # 글쓰기 교정 후 글 편집 영역
                st.markdown("---")
                st.subheader("✍️ 글쓰기 교정 후 글 편집")
                edited_writing = st.text_area(
                    "글쓰기 교정 후 글 (편집 가능):",
                    value=st.session_state.get('draft_after_writing', st.session_state['original_text']),
                    height=300,
                    key="edit_after_writing"
                )
                
                col1, col2, col3 = st.columns([1, 1, 1])
                with col1:
                    if st.button("💾 이 상태 저장", key="save_writing", use_container_width=True):
                        st.session_state['draft_after_writing'] = edited_writing
                        st.success("✅ 글쓰기 교정 단계 저장 완료")
                with col2:
                    if st.button("🔎 다시 평가", key="recheck_writing", use_container_width=True):
                        with st.spinner("재평가 중..."):
                            # 편집된 글을 기반으로 새로운 피드백 생성
                            refeedback = correct_text(edited_writing, "글쓰기 교정")
                            if isinstance(refeedback, dict) and 'error' in refeedback:
                                st.error(f"오류: {refeedback['error']}")
                            else:
                                # 새로운 피드백으로 업데이트
                                st.session_state['writing_feedback_for_current'] = refeedback
                                st.session_state['draft_after_writing'] = edited_writing
                                st.success("✅ 재평가 완료! 위의 평가 섹션을 확인하세요.")
                                st.rerun()
                with col3:
                    if st.button("✅ 완성!", key="finish_workflow", use_container_width=True):
                        st.session_state['draft_after_writing'] = edited_writing
                        st.session_state['final_text'] = edited_writing
                        st.session_state['workflow_completed'] = True
                        st.rerun()
            else:
                st.info("ℹ️ '맞춤법 교정' 탭에서 '다음 단계로' 버튼을 클릭하세요.")
        
        # ============================================================
        # 최종 결과 비교 뷰
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
                if st.button("🔄 다시 시작", use_container_width=True):
                    # 워크플로우 상태 초기화
                    st.session_state['workflow_started'] = False
                    st.session_state['proceed_to_writing'] = False
                    st.session_state['workflow_completed'] = False
                    if 'spell_check_result' in st.session_state:
                        del st.session_state['spell_check_result']
                    if 'draft_after_spell' in st.session_state:
                        del st.session_state['draft_after_spell']
                    if 'writing_feedback' in st.session_state:
                        del st.session_state['writing_feedback']
                    if 'draft_after_writing' in st.session_state:
                        del st.session_state['draft_after_writing']
                    if 'final_text' in st.session_state:
                        del st.session_state['final_text']
                    st.rerun()
    else:
        st.error("❌ OCR에서 텍스트를 추출하지 못했습니다. 로그를 확인하세요.")

# -------------------------------------------------------
# 🧩 Footer
# -------------------------------------------------------
st.markdown("---")
st.caption("Made with ❤️ by 유성진 | Vision API + Gemini 통합 버전")
