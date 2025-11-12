# 순차 워크플로우 버그 수정 (2025-11-12)

## ✅ 수정 사항

### 1️⃣ **다음단계로 넘어가는 기능 작동 불가 문제**

**원인:**
- Tab3의 조건: `if st.session_state.get('proceed_to_writing', False) or st.session_state.get('workflow_started', False)`
- `workflow_started` 플래그가 계속 True이므로, Tab3가 "다음 단계로" 버튼 없이도 렌더링됨
- 결과: 사용자가 Tab2의 "다음 단계로" 버튼을 클릭해도 새로운 상태가 반영되지 않음

**수정:**
```python
# Before
if st.session_state.get('proceed_to_writing', False) or st.session_state.get('workflow_started', False):

# After
if st.session_state.get('proceed_to_writing', False):
```

**효과:**
- Tab2의 "다음 단계로" 버튼 클릭 시에만 Tab3가 활성화됨
- 사용자가 명확한 순서대로 진행 가능

---

### 2️⃣ **각 단계에서 이전 저장된 원본 기반 교정**

**원인:**
- Tab2에서 `draft_after_spell` 저장 후 Tab3로 이동했을 때, Tab3가 올바른 입력값 사용 불확실
- Tab3의 피드백 생성 후 `draft_after_writing`에 저장되지 않음

**수정:**
```python
# Tab3 피드백 생성 시:
current_draft = st.session_state.get('draft_after_spell', st.session_state['original_text'])
writing_feedback = correct_text(current_draft, "글쓰기 교정")

# 저장:
st.session_state['draft_after_writing'] = current_draft
st.session_state['writing_feedback_for_current'] = writing_feedback
```

**데이터 흐름:**
```
원본 글 (original_text)
    ↓ [Tab2 맞춤법 교정]
draft_after_spell (저장됨)
    ↓ [Tab3 글쓰기 교정 - draft_after_spell 사용]
draft_after_writing (저장됨)
    ↓ [최종 완성본]
final_text = draft_after_writing
```

---

### 3️⃣ **다시 검사 시 재작성한 글 기반 교정**

**원인:**
- Tab2의 "다시 검사": 결과를 화면에만 표시, `spell_check_result` 업데이트 안 함
- Tab3의 "다시 평가": 피드백을 별도 텍스트 영역에 표시, 메인 피드백과 동기화 안 됨

**수정:**

#### Tab2 ("🔎 다시 검사"):
```python
if st.button("🔎 다시 검사", key="recheck_spell", use_container_width=True):
    with st.spinner("재검사 중..."):
        recheck = analyze_and_correct_to_json(edited_spell)
        if isinstance(recheck, dict) and 'error' in recheck:
            st.error(f"오류: {recheck['error']}")
        else:
            # ✅ 새로운 결과로 업데이트
            st.session_state['spell_check_result'] = recheck
            st.session_state['draft_after_spell'] = edited_spell
            remaining = [it for it in recheck if not it.get('is_correct')]
            if not remaining:
                st.success("🟢 재검사 완료: 오류 없음")
            else:
                st.warning(f"⚠️ 여전히 {len(remaining)}개 문장에 오류가 있습니다.")
            st.rerun()  # ✅ 페이지 새로고침으로 업데이트된 오류 목록 표시
```

#### Tab3 ("🔎 다시 평가"):
```python
if st.button("🔎 다시 평가", key="recheck_writing", use_container_width=True):
    with st.spinner("재평가 중..."):
        refeedback = correct_text(edited_writing, "글쓰기 교정")
        if isinstance(refeedback, dict) and 'error' in refeedback:
            st.error(f"오류: {refeedback['error']}")
        else:
            # ✅ 피드백 업데이트 및 저장
            st.session_state['writing_feedback_for_current'] = refeedback
            st.session_state['draft_after_writing'] = edited_writing
            st.success("✅ 재평가 완료! 위의 평가 섹션을 확인하세요.")
            st.rerun()  # ✅ 새 피드백이 메인 피드백 영역에 표시됨
```

**효과:**
- "다시 검사/평가" 시 새로운 결과가 세션 상태에 반영됨
- `st.rerun()` 호출로 페이지가 새로고침되면서 업데이트된 내용 표시
- 각 단계의 최종 저장 상태가 다음 단계로 자동 전파

---

## 🔄 **전체 워크플로우 흐름**

```
1️⃣ 원본 글 저장
   └─> "글 고쳐쓰기 시작" 클릭 → workflow_started = True

2️⃣ Tab2: 맞춤법 교정 (workflow_started=True일 때만 표시)
   ├─ 원본_text 기반 맞춤법 검사
   ├─ 오류 목록 표시 + 편집 가능
   ├─ "💾 저장" → draft_after_spell 저장
   ├─ "🔎 다시 검사" → spell_check_result 업데이트 + 오류 목록 새로고침
   └─ "➡️ 다음 단계로" → proceed_to_writing = True + st.rerun()

3️⃣ Tab3: 글쓰기 교정 (proceed_to_writing=True일 때만 표시)
   ├─ draft_after_spell 기반 글쓰기 교정
   ├─ 교사 평가 + 제안 표시
   ├─ "💾 저장" → draft_after_writing 저장
   ├─ "🔎 다시 평가" → writing_feedback_for_current 업데이트 + 피드백 새로고침
   └─ "✅ 완성!" → final_text = draft_after_writing + workflow_completed = True

4️⃣ 최종 비교 뷰 (workflow_completed=True일 때 표시)
   ├─ 원본 글 vs 완성본 비교
   ├─ 다운로드 버튼
   └─ "🔄 다시 시작" → 모든 상태 초기화
```

---

## 🧪 **테스트 포인트**

- [ ] "다음 단계로" 버튼 클릭 후 Tab3 활성화 확인
- [ ] Tab2 "다시 검사" 후 오류 목록 업데이트 확인
- [ ] Tab3 "다시 평가" 후 피드백 업데이트 확인
- [ ] 각 단계 편집 내용이 다음 단계로 전파되는지 확인
- [ ] "완성!" 버튼으로 최종 비교 뷰 표시 확인

---

## 📝 **커밋**
- Hash: `ddc7566`
- Message: `fix: 순차 워크플로우 버그 수정 (다음단계, 재검사, 글 전파)`
