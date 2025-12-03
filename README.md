# 스마트폰 리뷰 분석 서비스

유튜브 리뷰와 커뮤니티 후기를 AI로 분석하여 구매 결정을 도와주는 웹 서비스입니다.

## 🚀 주요 기능

- **유튜브 리뷰 분석**: 전문 리뷰어의 영상 자막을 AI로 분석하여 장단점 추출
- **커뮤니티 후기 수집**: 클리앙, 뽐뿌, 네이버 블로그 등에서 실제 사용자 후기 수집
- **구매 결정 가이드**: 전문가 의견과 일반 사용자 의견을 종합한 구매 가이드 제공
- **제품명 정규화**: 다양한 입력 형식(s25, 갤25, 갤S25 등)을 자동으로 정규화

## 🛠️ 기술 스택

### Backend
- Python 3.11+
- Flask
- MongoDB
- Google Gemini API
- BeautifulSoup4 (크롤링)

### Frontend
- React 19
- Vite
- Axios

## 📦 설치 및 실행

### 1. 저장소 클론

```bash
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name
```

### 2. Backend 설정

```bash
cd backend
pip install -r requirements.txt
```

`.env` 파일 생성:
```env
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DATABASE=youtube_reviews_db
MONGODB_COLLECTION=reviews
GOOGLE_API_KEY=your_gemini_api_key
```

### 3. Frontend 설정

```bash
cd frontend
npm install
```

### 4. 실행

**Backend:**
```bash
cd backend
python app.py
```

**Frontend:**
```bash
cd frontend
npm run dev
```

## 🗄️ 데이터베이스 설정

MongoDB가 필요합니다. 로컬 또는 MongoDB Atlas를 사용할 수 있습니다.

### MongoDB Atlas 사용 시
1. [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)에서 계정 생성
2. 클러스터 생성
3. 네트워크 액세스 설정 (IP 화이트리스트)
4. 데이터베이스 사용자 생성
5. 연결 문자열을 `.env` 파일에 설정

## 📊 배치 크롤링

제품별 데이터를 미리 수집하려면:

```bash
cd backend
python batch_crawler.py
```

## 🌐 배포

### Vercel (Frontend) + Railway/Render (Backend)

#### Frontend 배포 (Vercel)
1. [Vercel](https://vercel.com)에 로그인
2. GitHub 저장소 연결
3. Root Directory: `frontend` 설정
4. Build Command: `npm run build`
5. Output Directory: `dist`
6. Environment Variables: 없음 (API는 백엔드에서 처리)

#### Backend 배포 (Railway)
1. [Railway](https://railway.app)에 로그인
2. GitHub 저장소 연결
3. New Project → Deploy from GitHub repo
4. Root Directory: `backend` 설정
5. Start Command: `python app.py`
6. Environment Variables 설정:
   - `MONGODB_URI`
   - `MONGODB_DATABASE`
   - `MONGODB_COLLECTION`
   - `GOOGLE_API_KEY`

#### Backend 배포 (Render)
1. [Render](https://render.com)에 로그인
2. New → Web Service
3. GitHub 저장소 연결
4. 설정:
   - Name: `your-backend-name`
   - Environment: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python app.py`
   - Root Directory: `backend`

### 환경 변수 설정 (배포 시)

배포 플랫폼의 환경 변수 설정에서 다음을 추가:

```
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/
MONGODB_DATABASE=youtube_reviews_db
MONGODB_COLLECTION=reviews
GOOGLE_API_KEY=your_gemini_api_key
```

### CORS 설정

프론트엔드 URL을 백엔드의 CORS 허용 목록에 추가해야 합니다.

`backend/app.py`:
```python
CORS(app, resources={r"/api/*": {"origins": ["https://your-frontend.vercel.app"]}})
```

## 📝 API 엔드포인트

### POST `/api/analyze-product`
제품명을 받아서 종합 분석 결과 반환

**Request:**
```json
{
  "product_name": "갤럭시 S25"
}
```

**Response:**
```json
{
  "product_name": "갤럭시 S25",
  "youtube_reviews": [...],
  "community_reviews": {...},
  "purchase_guide_status": "processing"
}
```

### GET `/api/purchase-guide/<product_name>`
구매 가이드 생성 상태 및 결과 조회

## 📄 라이선스

MIT License

## 👤 작성자

Your Name

