# 🚀 모달 팝업 기반 워크플로우 (2025-11-12 11:18)

## 📋 개요

사용자 요청에 따라 기존의 탭 기반 UI에서 **모달 팝업 기반 UI**로 완전히 전환되었습니다.

### 주요 변경 사항

| 항목 | 이전 | 현재 |
|------|------|------|
| **UI 구조** | 3개 탭 (원본, 맞춤법, 글쓰기) | 원본 편집 + 모달 팝업 |
| **"글 고쳐쓰기" 버튼** | 탭 사이 전환용 | 모달 팝업 실행 |
| **위치** | 여러 위치에 배치 | 초기 화면에만 표시 |
| **워크플로우** | 탭 클릭으로 수행 | 팝업 내 순차 진행 |
| **초기화** | "다시 시작" 버튼 | "처음으로" 버튼 |
| **최종 화면** | 탭 내 표시 | 팝업 종료 후 메인에서 표시 |

---

## 🎯 사용 흐름

### Step 1️⃣: PDF 업로드 및 원본 편집

```
📤 PDF 업로드
    ↓
✅ OCR 완료
    ↓
📜 원본 글 (편집 가능)
   [원본 글 편집 영역] ← OCR 결과를 사용자가 수정
   [✅ 원본 저장] 버튼 클릭
```

**세션 상태**: `st.session_state['original_text']` = 저장된 원본

---

### Step 2️⃣: 모달 팝업 실행

```
[🚀 글 고쳐쓰기 시작] 버튼 클릭
    ↓
✔️ 원본이 저장되어 있는지 확인
    ↓
💥 모달 팝업 열기
   st.dialog("🚀 글 고쳐쓰기 워크플로우")
```

**세션 상태**: `st.session_state['show_workflow_modal'] = True`

---

### Step 3️⃣: 모달 내 맞춤법 교정 탭

```
┌─────────────────────────────────────────┐
│  🚀 글 고쳐쓰기 워크플로우 (모달)         │
├─────────────────────────────────────────┤
│  [🔍 맞춤법 교정] | [✍️ 글쓰기 교정]     │
│                                         │
│  🔍 맞춤법 교정                          │
│  ────────────────────────────────────   │
│                                         │
│  ⚡ 초기 분석 (자동)                     │
│  original_text → analyze_to_json()      │
│       ↓                                 │
│  modal_draft_after_spell ← original     │
│  modal_spell_check_result ← 분석 결과   │
│                                         │
│  🔴 발견된 오류 (Expander로 표시)        │
│  ┌─ 문장 1: "원문" ...                  │
│  │  수정 제안: 단어1 → 수정1             │
│  ├─ 문장 2: "원문" ...                  │
│  │  수정 제안: 단어2 → 수정2             │
│  └─ ...                                 │
│                                         │
│  ✍️ 맞춤법 교정 후 글 편집               │
│  [편집 가능 텍스트 영역]                 │
│                                         │
│  [💾 저장] [🔎 다시 검사] [➡️ 다음]     │
│                                         │
└─────────────────────────────────────────┘
```

#### 버튼 동작

| 버튼 | 동작 | 결과 |
|------|------|------|
| **💾 저장** | 현재 텍스트를 `modal_draft_after_spell`에 저장 | 성공 메시지 표시 |
| **🔎 다시 검사** | 편집된 텍스트 재분석 | `modal_spell_check_result` 업데이트 + `st.rerun()` |
| **➡️ 다음** | 다음 탭으로 이동 | `modal_proceed_to_writing = True` |

---

### Step 4️⃣: 모달 내 글쓰기 교정 탭

```
┌─────────────────────────────────────────┐
│  🚀 글 고쳐쓰기 워크플로우 (모달)         │
├─────────────────────────────────────────┤
│  [🔍 맞춤법 교정] | [✍️ 글쓰기 교정]     │
│                                         │
│  ✍️ 글쓰기 교정                          │
│  ────────────────────────────────────   │
│                                         │
│  ⚡ 초기 분석 (자동, modal_draft_after_spell 사용)
│  modal_draft_after_spell → correct_text() 
│       ↓                                 │
│  modal_draft_after_writing ← 입력글     │
│  modal_writing_feedback ← 피드백        │
│                                         │
│  📝 교사 평가 및 고쳐쓰기 제안           │
│  [읽기 전용 피드백 영역]                 │
│  - 주장의 명확성: ...                   │
│  - 근거의 타당성: ...                   │
│  - 논리적 흐름: ...                     │
│  - 독자 표현: ...                       │
│  - 맞춤법 정확성: ...                   │
│                                         │
│  ✍️ 글쓰기 교정 후 글 편집               │
│  [편집 가능 텍스트 영역]                 │
│                                         │
│  [💾 저장] [🔎 다시 평가] [✅ 완성!]   │
│                                         │
└─────────────────────────────────────────┘
```

#### 버튼 동작

| 버튼 | 동작 | 결과 |
|------|------|------|
| **💾 저장** | 현재 텍스트를 `modal_draft_after_writing`에 저장 | 성공 메시지 표시 |
| **🔎 다시 평가** | 편집된 텍스트 재분석 | `modal_writing_feedback` 업데이트 + `st.rerun()` |
| **✅ 완성!** | 최종 결과로 저장하고 모달 종료 | `final_text` 설정 + `workflow_completed = True` |

---

### Step 5️⃣: 최종 결과 비교 (모달 종료 후)

```
모달 팝업 자동 종료
    ↓
📊 최종 결과 비교 (메인 화면에 표시)
┌────────────────────────────────────┐
│  📄 원본 글          │ ✨ 완성된 글  │
│  ─────────────────  │ ─────────────│
│  [읽기 전용]         │  [읽기 전용]  │
│                      │              │
│  (원본 글 내용)      │ (최종 글)     │
│                      │              │
└────────────────────────────────────┘

[📥 원본 다운로드] [📥 완성본 다운로드] [🔄 처음으로]
```

#### 버튼 동작

| 버튼 | 동작 |
|------|------|
| **📥 원본 다운로드** | `original.txt` 파일 다운로드 |
| **📥 완성본 다운로드** | `completed.txt` 파일 다운로드 |
| **🔄 처음으로** | 모든 상태 초기화 + 페이지 리로드 |

---

## 🔄 세션 상태 관리

### 메인 상태 변수

```python
# 기본 데이터
st.session_state['original_text']          # 원본 글 (사용자가 저장)
st.session_state['final_text']             # 최종 완성된 글

# 워크플로우 제어
st.session_state['show_workflow_modal']    # 모달 팝업 표시 여부
st.session_state['workflow_completed']     # 워크플로우 완료 여부

# 모달 내부 상태 (modal_ 접두사)
st.session_state['modal_draft_after_spell']          # 맞춤법 교정 후 글
st.session_state['modal_spell_check_result']         # 맞춤법 분석 결과 (JSON)
st.session_state['modal_proceed_to_writing']         # 글쓰기 교정 진행 여부
st.session_state['modal_draft_after_writing']        # 글쓰기 교정 후 글
st.session_state['modal_writing_feedback']           # 글쓰기 교정 피드백
```

### 초기화 로직

**"🔄 처음으로" 버튼 클릭 시**:

```python
for key in list(st.session_state.keys()):
    if key.startswith('modal_') or key in ['original_text', 'workflow_completed', 'final_text', 'show_workflow_modal']:
        del st.session_state[key]
st.rerun()
```

---

## 📊 데이터 흐름

```
original_text (사용자 입력)
       ↓
[🚀 글 고쳐쓰기 시작]
       ↓
┌─────────────────────────────────────────┐
│       모달 팝업 워크플로우                 │
├─────────────────────────────────────────┤
│ TAB 1: 맞춤법 교정                       │
│ ─────────────────────────────────────   │
│ original_text                           │
│     ↓                                   │
│ analyze_and_correct_to_json()           │
│     ↓                                   │
│ modal_spell_check_result (JSON 배열)     │
│     ↓                                   │
│ [편집] → modal_draft_after_spell        │
│ [다시 검사] → 재분석                    │
│ [다음] → TAB 2로 이동                   │
├─────────────────────────────────────────┤
│ TAB 2: 글쓰기 교정                       │
│ ─────────────────────────────────────   │
│ modal_draft_after_spell (TAB1 결과)      │
│     ↓                                   │
│ correct_text(mode="글쓰기 교정")        │
│     ↓                                   │
│ modal_writing_feedback (평가 피드백)     │
│     ↓                                   │
│ [편집] → modal_draft_after_writing      │
│ [다시 평가] → 재분석                    │
│ [완성!] → 워크플로우 종료                │
└─────────────────────────────────────────┘
       ↓
final_text = modal_draft_after_writing
       ↓
📊 최종 비교 화면
original vs final
       ↓
[🔄 처음으로] → 초기화
```

---

## 🎛️ UI 구조

### 계층도

```
main_app.py
│
├─ [📤 PDF 업로드]
│  └─ [✅ OCR 완료]
│
├─ 📜 원본 글 섹션
│  ├─ [편집 가능 텍스트 영역]
│  └─ [✅ 원본 저장]
│
├─ [🚀 글 고쳐쓰기 시작] ← 초기 화면에만 표시
│
└─ IF show_workflow_modal:
│  └─ st.dialog() ← 모달 팝업
│     ├─ TAB 1: 맞춤법 교정
│     │  ├─ 오류 목록 (Expander)
│     │  ├─ 편집 영역
│     │  └─ [💾 저장] [🔎 다시 검사] [➡️ 다음]
│     │
│     └─ TAB 2: 글쓰기 교정 (proceed_to_writing=True일 때만)
│        ├─ 피드백 표시
│        ├─ 편집 영역
│        └─ [💾 저장] [🔎 다시 평가] [✅ 완성!]
│
└─ IF workflow_completed:
   └─ 📊 최종 결과 비교
      ├─ 원본 vs 완성본 (병렬 표시)
      └─ [📥 원본] [📥 완성본] [🔄 처음으로]
```

---

## 🔧 주요 코드 스니펫

### 모달 열기

```python
if st.button("🚀 글 고쳐쓰기 시작"):
    if not st.session_state['original_text'].strip():
        st.error("❌ 먼저 원본 글을 저장해주세요.")
    else:
        st.session_state['show_workflow_modal'] = True
        st.rerun()
```

### 모달 구조

```python
if st.session_state.get('show_workflow_modal', False):
    with st.dialog("🚀 글 고쳐쓰기 워크플로우", width="large"):
        modal_tab1, modal_tab2 = st.tabs(["🔍 맞춤법 교정", "✍️ 글쓰기 교정"])
        
        with modal_tab1:
            # 맞춤법 교정 로직
            ...
        
        with modal_tab2:
            # 글쓰기 교정 로직
            ...
```

### 재검사 로직 (모달 내)

```python
if st.button("🔎 다시 검사", key="modal_recheck_spell"):
    with st.spinner("재검사 중..."):
        recheck = analyze_and_correct_to_json(edited_spell)
        st.session_state['modal_spell_check_result'] = recheck
        st.session_state['modal_draft_after_spell'] = edited_spell
        st.rerun()  # ← 필수: 화면 새로고침
```

### 완성 및 모달 종료

```python
if st.button("✅ 완성!", key="modal_finish"):
    st.session_state['final_text'] = edited_writing
    st.session_state['workflow_completed'] = True
    st.session_state['show_workflow_modal'] = False  # ← 팝업 닫기
    st.rerun()
```

---

## ✅ 구현 체크리스트

- ✅ 모달 팝업 기반 UI로 전환
- ✅ "글 고쳐쓰기 시작" 버튼을 초기 화면에만 표시
- ✅ 팝업 내 맞춤법 교정 → 글쓰기 교정 순차 진행
- ✅ 각 탭에서 편집/저장/재검사 가능
- ✅ 다음 탭으로 이전 탭 결과 전파
- ✅ 최종 비교 화면에서 원본 vs 완성본 표시
- ✅ "🔄 처음으로" 버튼으로 완전 초기화
- ✅ 파일 다운로드 기능

---

## 🚀 실행 방법

```bash
cd /Users/sungjinyoo/.../check_spell
source .venv/bin/activate
streamlit run main_app.py
```

---

## 📝 파일 목록

- **main_app.py** (271 라인)
  - 모달 팝업 기반 전체 워크플로우
  - 초기 화면 + 팝업 + 최종 화면 3단계

- **src/spell_corrector.py**
  - 맞춤법 교정 및 글쓰기 교정 요청 라우팅

- **src/json_corrector.py**
  - Gemini API 호출 (맞춤법 분석 JSON 응답)

- **src/vision_ocr.py**
  - Google Vision OCR 통합

---

## 🎯 특징

1. **직관적인 모달 워크플로우**
   - 팝업으로 집중된 작업 환경 제공
   - 사용자가 한눈에 현재 진행 상황 파악 가능

2. **완전한 상태 관리**
   - `modal_` 접두사로 팝업 상태 분리
   - 메인 화면과의 혼동 없음

3. **유연한 편집 및 재검사**
   - 각 단계에서 텍스트 편집 가능
   - 재검사/재평가로 즉시 피드백 업데이트

4. **세련된 초기화**
   - "🔄 처음으로" 버튼으로 한 번에 초기화
   - 모든 modal_ 상태 변수 자동 제거

5. **최종 비교 기능**
   - 원본과 완성본을 병렬로 비교
   - 파일 다운로드 지원

---

## 📌 주의사항

1. **modal_ 변수 초기화**
   - 워크플로우 종료 후 "🔄 처음으로"를 반드시 클릭해야 상태 초기화
   - 그렇지 않으면 다음 워크플로우 시작 시 이전 데이터 남아있을 수 있음

2. **팝업 내 탭 순서**
   - 맞춤법 교정이 먼저 완료되어야 글쓰기 교정 탭 활성화
   - 반드시 "➡️ 다음" 버튼을 클릭해야 함

3. **오류 발생 시**
   - Gemini API 오류 메시지 확인
   - `.streamlit/secrets.toml`에서 API 키 설정 확인

---

**Last Updated**: 2025-11-12 11:18  
**Version**: 2.0 (Modal-based Workflow)
