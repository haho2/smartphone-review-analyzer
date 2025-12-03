import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from datetime import datetime
from dotenv import load_dotenv

# 환경변수 로드 (backend 폴더와 루트 폴더 모두 확인)
load_dotenv()  # 루트 폴더의 .env
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))  # backend/.env

# MongoDB 설정
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
DATABASE_NAME = os.getenv('MONGODB_DATABASE', 'youtube_reviews_db')
COLLECTION_NAME = os.getenv('MONGODB_COLLECTION', 'reviews')

# 디버깅: 환경변수 확인
print(f"🔍 MongoDB URI 확인: {MONGODB_URI[:50]}..." if len(MONGODB_URI) > 50 else f"🔍 MongoDB URI 확인: {MONGODB_URI}")

# MongoDB 클라이언트 및 컬렉션 초기화
client = None
collection = None

try:
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    # 연결 테스트
    client.admin.command('ping')
    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]
    print(f"✅ MongoDB 연결 성공: 데이터베이스 [{DATABASE_NAME}], 컬렉션 [{COLLECTION_NAME}]")
except (ConnectionFailure, ServerSelectionTimeoutError) as e:
    print(f"⚠️ MongoDB 연결 경고: {str(e)}")
    print("   → MongoDB 서버가 실행 중이지 않거나 연결 정보가 잘못되었습니다.")
    print("   → 로컬 MongoDB: mongodb://localhost:27017/")
    print("   → MongoDB Atlas: mongodb+srv://username:password@cluster.mongodb.net/")
    print("   → 캐싱 기능이 비활성화됩니다.")
    client = None
    collection = None
except Exception as e:
    print(f"⚠️ MongoDB 연결 오류: {str(e)}")
    client = None
    collection = None


def get_review_from_db(video_id):
    """
    MongoDB에서 비디오 분석 결과 조회 (Cache Hit)
    
    Args:
        video_id (str): 유튜브 영상 ID
    
    Returns:
        dict: 분석 결과 데이터 또는 None (Cache Miss)
    """
    if collection is None:
        return None
    
    try:
        result = collection.find_one({'video_id': video_id})
        
        if result:
            print(f"   ✅ 캐시 히트: [{video_id}]")
            # MongoDB의 _id 필드 제거 (JSON 직렬화 문제 방지)
            result.pop('_id', None)
            return result
        else:
            print(f"   ❌ 캐시 미스: [{video_id}]")
            return None
            
    except Exception as e:
        print(f"   ⚠️ 데이터베이스 조회 오류: {str(e)}")
        return None


def save_review_to_db(video_id, analysis_result):
    """
    MongoDB에 비디오 분석 결과 저장 (Cache 저장)
    
    Args:
        video_id (str): 유튜브 영상 ID
        analysis_result (str): Gemini AI 분석 결과 텍스트
    
    Returns:
        bool: 저장 성공 여부
    """
    if collection is None:
        return False
    
    try:
        current_timestamp = int(datetime.now().timestamp())
        
        document = {
            'video_id': video_id,
            'analysis': analysis_result,
            'created_at': current_timestamp,
            'updated_at': current_timestamp
        }
        
        # upsert 사용: video_id가 있으면 업데이트, 없으면 삽입
        collection.update_one(
            {'video_id': video_id},
            {'$set': document},
            upsert=True
        )
        print(f"   ✅ 캐시 저장 완료: [{video_id}]")
        return True
        
    except Exception as e:
        print(f"   ⚠️ 데이터베이스 저장 오류: {str(e)}")
        return False


def create_index_if_not_exists():
    """
    MongoDB에 video_id 인덱스 생성 (성능 최적화)
    """
    if collection is None:
        return False
    
    try:
        # video_id에 고유 인덱스 생성
        collection.create_index('video_id', unique=True)
        print(f"   ✅ 인덱스 생성 완료: video_id")
        return True
    except Exception as e:
        # 인덱스가 이미 존재하는 경우 무시
        if 'already exists' in str(e).lower():
            return True
        print(f"   ⚠️ 인덱스 생성 오류: {str(e)}")
        return False


# 모듈 로드 시 인덱스 생성 시도
if collection is not None:
    create_index_if_not_exists()
