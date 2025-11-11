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
uploaded_file = st.file_uploader("📤 PDF 파일 업로드", type=["pdf"])

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
        st.markdown("*원본을 저장한 후 아래 버튼을 클릭하면 '맞춤법 교정' → '글쓰기 교정'이 순차적으로 실행됩니다.*")
        
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
                                        st.write(f"- `{c.get('incorrect_word')}` → `{c.get('correct_word')}`")
                    
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
                                recheck = analyze_and_correct_to_json(edited_spell)
                                if isinstance(recheck, dict) and 'error' in recheck:
                                    st.error(f"오류: {recheck['error']}")
                                else:
                                    remaining = [it for it in recheck if not it.get('is_correct')]
                                    if not remaining:
                                        st.success("🟢 재검사 완료: 오류 없음")
                                    else:
                                        st.warning(f"⚠️ 여전히 {len(remaining)}개 문장에 오류가 있습니다.")
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
            
            if st.session_state.get('proceed_to_writing', False) or st.session_state.get('workflow_started', False):
                # 글쓰기 교정 실행
                if 'draft_after_writing' not in st.session_state:
                    with st.spinner("글쓰기 교정 중입니다... ⏳"):
                        current_draft = st.session_state.get('draft_after_spell', st.session_state['original_text'])
                        writing_feedback = correct_text(current_draft, "글쓰기 교정")
                        
                        if isinstance(writing_feedback, dict) and 'error' in writing_feedback:
                            st.error(f"❌ 오류: {writing_feedback['error']}")
                        else:
                            st.session_state['draft_after_writing'] = current_draft
                            st.session_state['writing_feedback'] = writing_feedback
                
                # 글쓰기 교정 피드백 표시
                if 'writing_feedback' in st.session_state:
                    st.subheader("📝 교사 평가 및 고쳐쓰기 제안")
                    feedback = st.session_state['writing_feedback']
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
                            refeedback = correct_text(edited_writing, "글쓰기 교정")
                            if isinstance(refeedback, dict) and 'error' in refeedback:
                                st.error(f"오류: {refeedback['error']}")
                            else:
                                st.text_area(
                                    "재평가 결과:",
                                    value=refeedback if isinstance(refeedback, str) else str(refeedback),
                                    height=200,
                                    disabled=True
                                )
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

# -------------------------------------------------------
# 📂 파일 업로드
# -------------------------------------------------------
uploaded_file = st.file_uploader("📤 PDF 파일 업로드", type=["pdf"])

# -------------------------------------------------------
# 🧾 OCR 실행 및 결과 표시
# -------------------------------------------------------
if uploaded_file:
    st.info("📘 PDF 업로드 완료 — OCR을 시작합니다...")
    extracted_text = run_ocr_pipeline(uploaded_file)

    if extracted_text:
        st.success("✅ OCR 완료! 추출된 텍스트가 아래에 표시됩니다. (수정 가능)")
        # 사용자가 OCR 결과를 바로 수정할 수 있도록 편집 가능한 텍스트 영역 제공
        edited_text = st.text_area("📜 OCR 결과 (수정 가능)", value=extracted_text, height=250, key="ocr_editable")

        # -------------------------------------------------------
        # ✍️ Gemini 교정 단계
        # -------------------------------------------------------
        st.subheader("✏️ Gemini 맞춤법 및 문장 교정")

        # 단순화된 모드: 맞춤법 교정, 글쓰기 교정, 글 다시 쓰기
        mode = st.selectbox(
            "원하는 기능을 선택하세요:",
            ["맞춤법 교정", "글쓰기 교정", "글 다시 쓰기"]
        )

        # 글쓰기 교정은 자동으로 평가(교사용)와 제안(학생용)을 함께 제공합니다

        if mode == "글 다시 쓰기":
            # 왼쪽: 글쓰기 교정(평가 + 제안) 결과
            # 오른쪽: 편집 가능한 원문 텍스트
            col1, col2 = st.columns([1, 1])

            with col1:
                st.subheader("📝 글쓰기 교정 (평가 & 제안)")
                # 평가와 제안을 각각 호출하여 표시
                combined = correct_text(edited_text, "글쓰기 교정")

                if isinstance(combined, dict) and 'error' in combined:
                    st.error(f"글쓰기 교정 오류: {combined['error']}")
                else:
                    st.text_area("평가 및 제안", combined if isinstance(combined, str) else str(combined), height=520)

            with col2:
                st.subheader("✍️ 오른쪽: 원문 편집")
                # 편집 가능한 원문(초기값은 OCR로 추출한 텍스트)
                edited = st.text_area("원문을 편집하세요:", value=edited_text, height=400, key="rewrite_editable")

                # 다시 쓰기 실행: 사용자가 편집한 내용을 기반으로 교사가 다듬어 줌
                if st.button("🔁 다시 쓰기 실행"):
                    with st.spinner("다시 쓰기 중입니다... ⏳"):
                        rewritten = correct_text(edited, "글 다시 쓰기")
                        if isinstance(rewritten, dict) and 'error' in rewritten:
                            st.error(f"다시 쓰기 오류: {rewritten['error']}")
                        else:
                            st.success("✅ 다시 쓰기 완료!")
                            # 결과를 하단에 표시하고 복사/다운로드 가능하게 함
                            st.markdown("#### 수정된 글 (아래에서 복사하거나 다운로드하세요)")
                            st.code(rewritten, language='text')
                            st.download_button("📥 다운로드 (.txt)", data=rewritten, file_name="rewritten.txt")
                            # 편의용: 수정된 글을 텍스트 영역에 다시 채우기 (선택적)
                            st.session_state['rewrite_result'] = rewritten

                # 만약 이전에 다시 쓰기 결과가 있다면 보여주기
                if 'rewrite_result' in st.session_state:
                    st.markdown("#### 마지막으로 생성된 수정본")
                    st.code(st.session_state['rewrite_result'], language='text')

        else:
            # 맞춤법 검사 또는 글쓰기 교정(평가/제안)
            if st.button("🚀 실행"):
                with st.spinner("처리 중입니다... ⏳"):
                    if mode == "맞춤법 교정":
                        # 분석 결과를 JSON으로 받아서 틀린 문장/단어만 표시
                        json_data = analyze_and_correct_to_json(edited_text)
                        if isinstance(json_data, dict) and 'error' in json_data:
                            st.error(json_data['error'])
                        else:
                            # 두 열: 왼쪽은 문제 목록, 오른쪽은 글 다시 쓰기 및 재검사
                            col1, col2 = st.columns([1,1])
                            with col1:
                                st.subheader("🔍 맞춤법 오류 목록")
                                incorrect_items = [it for it in json_data if not it.get('is_correct')]
                                if not incorrect_items:
                                    st.success("🟢 오류 없음: 모든 문장이 올바릅니다.")
                                else:
                                    for i, item in enumerate(incorrect_items):
                                        st.markdown(f"**문장 {item.get('sentence_id', i)+1}**: {item.get('original_sentence')}")
                                        corrections = item.get('corrections', [])
                                        if corrections:
                                            for c in corrections:
                                                st.write(f"- 틀린 부분: `{c.get('incorrect_word')}` → 제안: `{c.get('correct_word')}`")
                                        else:
                                            st.write("- 상세 정보 없음")

                            with col2:
                                st.subheader("✍️ 글 다시 쓰기")
                                edited_for_rewrite = st.text_area("원문을 편집하여 다시 쓰기:", value=edited_text, height=300, key='rewrite_for_spelling')
                                if st.button("🔁 다시 쓰기 적용", key='rewrite_apply_spelling'):
                                    with st.spinner("다시 쓰기 중..."):
                                        rewritten = correct_text(edited_for_rewrite, "글 다시 쓰기")
                                        if isinstance(rewritten, dict) and 'error' in rewritten:
                                            st.error(rewritten['error'])
                                        else:
                                            st.success("✅ 다시 쓰기 완료")
                                            st.code(rewritten, language='text')
                                            st.download_button("📥 다운로드 (.txt)", data=rewritten, file_name="rewritten_spelling.txt")
                                            # 재검사 버튼
                                            if st.button("� 이 결과로 다시 검사하기", key='recheck_spelling'):
                                                recheck_json = analyze_and_correct_to_json(rewritten)
                                                if isinstance(recheck_json, dict) and 'error' in recheck_json:
                                                    st.error(recheck_json['error'])
                                                else:
                                                    st.write("재검사 결과:")
                                                    rem = [it for it in recheck_json if not it.get('is_correct')]
                                                    if not rem:
                                                        st.success("🟢 재검사: 오류 없음")
                                                    else:
                                                        for item in rem:
                                                            st.write(f"- 문장 {item.get('sentence_id', '?')+1}: {item.get('original_sentence')}")
                                                            for c in item.get('corrections', []):
                                                                st.write(f"  - {c.get('incorrect_word')} -> {c.get('correct_word')}")
                                            # 저장 옵션
                                            if st.button("✅ 이 결과를 최종본으로 저장", key='save_final_spelling'):
                                                st.session_state['final_text'] = rewritten

                    elif mode == "글쓰기 교정":
                        # 왼쪽: 평가+제안 (종합), 오른쪽: 글 다시 쓰기 및 재검사
                        col1, col2 = st.columns([1,1])
                        with col1:
                            st.subheader("📝 평가 및 고쳐쓰기 제안")
                            combined = correct_text(edited_text, "글쓰기 교정")
                            if isinstance(combined, dict) and 'error' in combined:
                                st.error(combined['error'])
                            else:
                                st.text_area("평가 및 제안", combined if isinstance(combined, str) else str(combined), height=400)
                        with col2:
                            st.subheader("✍️ 글 다시 쓰기")
                            edited_for_rewrite = st.text_area("원문을 편집하여 다시 쓰기:", value=edited_text, height=300, key='rewrite_for_writing')
                            if st.button("🔁 다시 쓰기 적용", key='rewrite_apply_writing'):
                                with st.spinner("다시 쓰기 중..."):
                                    rewritten = correct_text(edited_for_rewrite, "글 다시 쓰기")
                                    if isinstance(rewritten, dict) and 'error' in rewritten:
                                        st.error(rewritten['error'])
                                    else:
                                        st.success("✅ 다시 쓰기 완료")
                                        st.code(rewritten, language='text')
                                        st.download_button("📥 다운로드 (.txt)", data=rewritten, file_name="rewritten_writing.txt")
                                        if st.button("🔎 이 결과로 다시 검사하기", key='recheck_writing'):
                                            recombined = correct_text(rewritten, "글쓰기 교정")
                                            if isinstance(recombined, dict) and 'error' in recombined:
                                                st.error(recombined['error'])
                                            else:
                                                st.markdown("**재검사(평가 및 제안)**")
                                                st.text_area("재검사 결과", recombined if isinstance(recombined, str) else str(recombined), height=300)
                                        if st.button("✅ 이 결과를 최종본으로 저장", key='save_final_writing'):
                                            st.session_state['final_text'] = rewritten

        # ---------- 완성된 글 보기 ----------
        st.markdown("---")
        st.subheader("📌 완성된 글 보기")
        final = st.session_state.get('final_text', None)
        if final:
            st.code(final, language='text')
            st.download_button("📥 완성글 다운로드 (.txt)", data=final, file_name="final_text.txt")
            st.button("📋 클립보드에 복사", on_click=lambda: st.write("복사: 클립보드 기능은 브라우저에서 직접 복사하세요."))
        else:
            st.info("아직 최종 저장된 글이 없습니다. '이 결과를 최종본으로 저장' 버튼을 사용하세요.")
    else:
        st.error("❌ OCR에서 텍스트를 추출하지 못했습니다. 로그를 확인하세요.")

# -------------------------------------------------------
# 🧩 Footer
# -------------------------------------------------------
st.markdown("---")
st.caption("Made with ❤️ by 유성진 | Vision API + Gemini 통합 버전")
