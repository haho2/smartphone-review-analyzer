"""
MongoDB 캐시 데이터 삭제 스크립트
프롬프트 변경으로 인한 데이터 형식 변경으로 기존 캐시를 삭제합니다.
"""
import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

# MongoDB 설정
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
DATABASE_NAME = os.getenv('MONGODB_DATABASE', 'youtube_reviews_db')
COLLECTION_NAME = os.getenv('MONGODB_COLLECTION', 'reviews')

print("=" * 50)
print("🗑️  MongoDB 캐시 데이터 삭제")
print("=" * 50)
print(f"데이터베이스: {DATABASE_NAME}")
print(f"컬렉션: {COLLECTION_NAME}")
print(f"URI: {MONGODB_URI[:50]}...")
print()

try:
    # MongoDB 연결
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]
    
    # 현재 문서 개수 확인
    count_before = collection.count_documents({})
    print(f"📊 삭제 전 문서 개수: {count_before}개")
    
    if count_before == 0:
        print("✅ 삭제할 데이터가 없습니다.")
    else:
        # 사용자 확인
        response = input(f"\n⚠️  정말로 모든 캐시 데이터를 삭제하시겠습니까? (yes/no): ")
        
        if response.lower() == 'yes':
            # 모든 문서 삭제
            result = collection.delete_many({})
            print(f"\n✅ 삭제 완료: {result.deleted_count}개 문서 삭제됨")
            
            # 삭제 후 확인
            count_after = collection.count_documents({})
            print(f"📊 삭제 후 문서 개수: {count_after}개")
        else:
            print("\n❌ 삭제가 취소되었습니다.")
    
    client.close()
    
except (ConnectionFailure, ServerSelectionTimeoutError) as e:
    print(f"❌ MongoDB 연결 실패: {str(e)}")
    print("   → MongoDB 서버가 실행 중인지 확인해주세요.")
except Exception as e:
    print(f"❌ 오류 발생: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 50)

