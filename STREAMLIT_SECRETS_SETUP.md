# 🔑 Streamlit Cloud Secrets 설정 가이드

## 에러 원인

```
KeyError: This app has encountered an error...
KeyError: gcp_service_account
```

**이유**: Streamlit Cloud에 API 키와 Google Cloud 인증 정보가 설정되지 않았습니다.

---

## ✅ 해결 방법 (5분)

### **Step 1: Streamlit Cloud 앱 관리 페이지 접속**

```
https://share.streamlit.io
→ 배포된 앱 클릭
→ 우측 상단 "⋮" 메뉴
→ "Manage app" 클릭
```

또는 앱 우측 하단에서 **"Manage app"** 버튼 클릭

### **Step 2: Settings → Secrets 탭 클릭**

### **Step 3: 다음 내용을 복사해서 붙여넣기**

**⚠️ 중요**: 아래 내용을 **그대로** 복사하여 Secrets 텍스트 영역에 붙여넣으세요.

```toml
[gcp_service_account]
type = "service_account"
project_id = "korean-spelling-app"
private_key_id = "19e357dc02fa418cf8272bcf68075f2e6bd1bb5f"
private_key = "-----BEGIN PRIVATE KEY-----\nMIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQDjIr7XQo8T8Mg+\nAHBBXnolxnweM tMtoGJmii78P4MEgcUeyDb1aj83cAI1BKsbj3AGr+T0KGfn+7H1\ne3F2otlaXLOJPUAVJg3wiwrJQcBnkxVqf+Mp+T/HVywf4UtZbq+l0NZ2l09gDTm6\nJ9/b4jPyeRJonYRziU+m9e7w67iLlezLNNK4R5HISoSYfNVMG3cq+bGxyb3bh6tt\ntNVh2Gj8XS0ty3ivP3ZYkF7B8PFFsl3evyleAqylGrDpLTU50nc6xv+tOdUukhb6\nlGZEgI/ljHGEp3dH12Fu9cxAxbkvakxkRQzVeQcTswv4DJ9nOCLB5DSeCAJ6CvjQ\nBSdnhZghAgMBAAECgf8VopNaGaR0dd67HT9Dw4f22zgPN2J9/4NL4v+S9yHp+wuI\njmA6VD92S4IwlfGQ1gQn6jOWW/UgXNYJew6eZJMUjgd6WsLAgjVnCifKChgLiV1Y\nE4xkgY638o2TnHCUE5W6X7JAJNz5He8IAax7HxAqPxQHddFp3Rg+2vq7ANwkLjFg\nKShnCxfuG9i1V40lZqm70WezvDGAxpUcift/tL9pp9RTg4x/GD7pFIcreElN2vZ7\nwfOcdSNudEUFndWxJyCQ2dy1rf374+rW+clHeXvfnCSzkw6/mOZA9w5cRIAZXAVV\nD3ZavtPdDdnavhqR3ynSFTJqAkArjci2eLG962kCgYEA9LDJ9jKiueyYMaIYGq+I\n//AK4tq/RokZgglcj+ftD7Li0SX74FllZKVQEZ/9IMhS8HiJ72UCO3CouJ7RWa0s\njuAzT2aD+2Pt5wC8eNft4SXW3aDkMn1MCAiTdkTSUX/Zl9w87VFSKmLlC/wa5SLt\nDHXPSYb14M5A9B1E3bdZXrkCgYEA7aI+xGQJfpEJdBgahV65rVGEs9E4YyuKXbrd\nWGcwk4FNADt6WNnWs/Va74xY/J/OaIfXECxWQqoEWpPBe4X8R/3C476dzx6aAUBq\nJcZ3rpGkrPNb/cESBKK0nQiIJuEg2o5vZz97Ojz4NjUqcKnhQEcufal7s3bT/o3Y\npysukKkCgYEA4+d55I7bE9LzGl+AlfJi5wc8DHlz6I2vrXdsuDhri9CxA96eECMT\nlj+HKTNbv9n1rjaHOutYveY7r+F02lK6isT15YF1coNrxVnhMajkzmzBCSJfCUu8\nskrSljiZsAEluRUPxnaU0hfUgGoq3rq+EXn1POWwQ9e3ledhCiVI3zkCgYBrBgNW\n1+cexZuIWcK4Bm2BjZFCmxvWLinnBN3jjrXl+PoA/Mihc5qq+fm2oXMCc8a2dVd6\nxT0kUQYc9SbSxwlUMwmvII5aVeHuZmBoGvaT/Kw56HCp3GaNB+poPwty1znAtR2f\nVovdMtBnOZKfoyL7nBNoLQi1TvMzVhcZUu1p4QKBgQCjaJ/4j2hkk+Hc7/4sIDZ+\ngBg0PqxPvxEGUT0gmeLvroJNGe2NUqsRMssxItE9Ts/YNLPUoaAVmAKVHiL18/nS\nwm60oGEsiHYUEEGX9VrfjPgjfnJjROdDd0QBzLWdjCtPBHaZIh41VhbkeuONLlT9\nni6mKVUSEbZ3lKbI3DPFRg==\n-----END PRIVATE KEY-----"
client_email = "ocr-service-471@korean-spelling-app.iam.gserviceaccount.com"
client_id = "109686659875679889659"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/ocr-service-471%40korean-spelling-app.iam.gserviceaccount.com"
universe_domain = "googleapis.com"

[gemini]
api_key = "AIzaSyDKXOfhVSC1RnXpm2uaua082hpkjINOfqU"
```

### **Step 4: Save 버튼 클릭**

```
Secrets 텍스트 영역 아래 "Save" 버튼 클릭
```

### **Step 5: 앱 자동 재시작 대기**

```
Streamlit Cloud가 자동으로 앱을 재시작합니다 (30초~1분)
```

---

## ✅ 설정 완료 확인

앱이 다시 로드되면:

```
✅ "🧾 AI OCR + 맞춤법 교정기" 페이지가 정상 표시됨
✅ PDF 파일 업로드 버튼이 보임
✅ 에러 메시지 없음
```

---

## 📊 설정된 정보

| 항목 | 상태 | 설명 |
|------|------|------|
| **Google Cloud Service Account** | ✅ 설정됨 | OCR 기능 활성화 |
| **Gemini API Key** | ✅ 설정됨 | AI 교정 기능 활성화 |
| **프로젝트 ID** | korean-spelling-app | 한글 맞춤법 앱 |

---

## 🔒 보안 주의

```
⚠️ 이 Secrets는 Streamlit Cloud에만 저장되며:
✅ GitHub에는 푸시되지 않음
✅ 공개되지 않음 (로그 에디터만 접근)
✅ Streamlit Cloud의 암호화된 서버에 저장
```

---

## 🆘 문제 해결

### **"Still getting KeyError" 에러?**

1️⃣ **캐시 삭제**
```
브라우저 개발자 도구 (F12)
→ Application/Storage
→ All → Clear site data
→ 앱 새로고침
```

2️⃣ **앱 재시작**
```
Streamlit Cloud 대시보드
→ 앱 우측 상단 "⋮"
→ "Reboot app" 클릭
```

3️⃣ **Secrets 재확인**
```
Settings → Secrets
→ 복사한 내용이 정확히 붙여졌는지 확인
→ 특수 문자나 빈 줄 확인
```

### **"Invalid TOML" 에러?**

```
원인: 복사 과정에서 특수 문자 손상

해결: 
1. 기존 내용 삭제
2. 위의 전체 내용을 다시 복사
3. 천천히 붙여넣기
4. 저장 전 검토
```

---

## 🎯 완료!

Secrets 설정 완료 후:

```
✅ 앱 자동 재시작
✅ PDF 업로드 가능
✅ OCR 작동
✅ Gemini AI 교정 기능 활성화

이제 앱을 사용할 수 있습니다! 🎉
```

---

**예상 시간**: 5분  
**난이도**: ⭐ (매우 쉬움)  
**중요도**: ⭐⭐⭐⭐⭐ (필수)
