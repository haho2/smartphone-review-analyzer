# 배포 가이드

## 🚀 빠른 배포 가이드

### 1. GitHub에 업로드

```bash
# Git 초기화 (아직 안 했다면)
git init

# .gitignore 확인 (이미 생성됨)
# .env 파일은 업로드되지 않도록 주의!

# 파일 추가
git add .

# 커밋
git commit -m "Initial commit: 스마트폰 리뷰 분석 서비스"

# GitHub 저장소 생성 후
git remote add origin https://github.com/your-username/your-repo-name.git
git branch -M main
git push -u origin main
```

### 2. Frontend 배포 (Vercel)

1. **Vercel 가입**: https://vercel.com
2. **New Project** 클릭
3. **Import Git Repository** → GitHub 저장소 선택
4. **프로젝트 설정**:
   - Framework Preset: `Vite`
   - Root Directory: `frontend`
   - Build Command: `npm run build` (자동 감지됨)
   - Output Directory: `dist` (자동 감지됨)
5. **Environment Variables**: 없음 (프론트엔드는 백엔드 API 호출)
6. **Deploy** 클릭

**중요**: `frontend/src/App.jsx`에서 백엔드 URL을 배포된 URL로 변경:

```javascript
// 개발 환경
const API_URL = 'http://127.0.0.1:5000';

// 배포 환경 (환경 변수 사용 권장)
const API_URL = import.meta.env.VITE_API_URL || 'https://your-backend.railway.app';
```

환경 변수 사용 시 Vercel에서:
- Key: `VITE_API_URL`
- Value: `https://your-backend.railway.app`

### 3. Backend 배포 (Railway) - 추천

1. **Railway 가입**: https://railway.app
2. **New Project** → **Deploy from GitHub repo**
3. 저장소 선택
4. **Settings** → **Root Directory**: `backend` 설정
5. **Variables** 탭에서 환경 변수 추가:
   ```
   MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/
   MONGODB_DATABASE=youtube_reviews_db
   MONGODB_COLLECTION=reviews
   GOOGLE_API_KEY=your_gemini_api_key
   ```
6. **Deploy** 자동 시작

**Railway는 자동으로 포트를 할당하므로 `app.py` 수정 필요:**

```python
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port, use_reloader=False)
```

### 4. Backend 배포 (Render) - 대안

1. **Render 가입**: https://render.com
2. **New** → **Web Service**
3. GitHub 저장소 연결
4. 설정:
   - **Name**: `your-backend-name`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python app.py`
   - **Root Directory**: `backend`
5. **Environment Variables** 추가 (Railway와 동일)
6. **Create Web Service**

### 5. CORS 설정 업데이트

배포된 프론트엔드 URL을 백엔드 CORS에 추가:

`backend/app.py`:
```python
from flask_cors import CORS

# 개발 환경
CORS(app)

# 또는 배포 환경 (특정 도메인만 허용)
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "https://your-frontend.vercel.app",
            "http://localhost:5173"  # 개발용
        ]
    }
})
```

## 🔧 배포 전 체크리스트

- [ ] `.env` 파일이 `.gitignore`에 포함되어 있는지 확인
- [ ] 민감한 정보(API 키 등)가 코드에 하드코딩되지 않았는지 확인
- [ ] MongoDB 연결 정보 확인
- [ ] 프론트엔드 API URL이 환경 변수로 관리되는지 확인
- [ ] CORS 설정 확인
- [ ] `requirements.txt`에 모든 의존성이 포함되어 있는지 확인

## 📝 환경 변수 목록

### Backend
- `MONGODB_URI`: MongoDB 연결 문자열
- `MONGODB_DATABASE`: 데이터베이스 이름
- `MONGODB_COLLECTION`: 컬렉션 이름 (선택사항)
- `GOOGLE_API_KEY`: Gemini API 키
- `PORT`: 서버 포트 (Railway/Render에서 자동 할당)

### Frontend
- `VITE_API_URL`: 백엔드 API URL (선택사항)

## 🐛 문제 해결

### 백엔드가 시작되지 않을 때
- 포트가 올바르게 설정되었는지 확인
- 환경 변수가 모두 설정되었는지 확인
- 로그 확인 (Railway/Render 대시보드)

### CORS 오류
- 프론트엔드 URL이 백엔드 CORS 설정에 포함되어 있는지 확인
- `Access-Control-Allow-Origin` 헤더 확인

### MongoDB 연결 실패
- MongoDB Atlas 네트워크 액세스 설정 확인 (IP 화이트리스트)
- 연결 문자열 형식 확인
- 사용자 이름/비밀번호 확인

