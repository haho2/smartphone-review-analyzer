"""
배치 크롤링 스크립트: 제품별 유튜브 영상과 커뮤니티 후기를 미리 수집하여 MongoDB에 저장
"""
import crawler
import database
import ai_service
import sys
import json
from datetime import datetime

# Windows에서 UTF-8 출력을 위한 설정
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# 크롤링할 제품 목록 (product_normalizer의 VALID_MODELS 참조)
import product_normalizer

# 실제 존재하는 모델만 크롤링 (환각 방지)
PRODUCTS_TO_CRAWL = product_normalizer.VALID_MODELS.copy()

def save_community_reviews_to_db(product_name, reviews_text, sources, actual_count=None):
    """
    제품별 커뮤니티 후기를 MongoDB에 저장
    
    Args:
        product_name: 제품명
        reviews_text: 후기 텍스트
        sources: 소스 리스트
        actual_count: 실제 수집된 후기 개수 (선택사항)
    """
    try:
        from pymongo import MongoClient
        import os
        from dotenv import load_dotenv
        
        load_dotenv()
        load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))
        
        MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
        DATABASE_NAME = os.getenv('MONGODB_DATABASE', 'youtube_reviews_db')
        COLLECTION_NAME = 'community_reviews'  # 새로운 컬렉션
        
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]
        
        current_timestamp = int(datetime.now().timestamp())
        
        # 실제 후기 개수 계산 (리스트 길이 사용, 없으면 줄 수로 추정)
        if actual_count is not None:
            review_count = actual_count
        elif reviews_text:
            # "[소스]"로 시작하는 줄만 카운트 (실제 후기 항목)
            review_count = len([line for line in reviews_text.split('\n') if line.strip().startswith('[')])
        else:
            review_count = 0
        
        document = {
            'product_name': product_name,
            'reviews_text': reviews_text,
            'sources': sources,
            'review_count': review_count,
            'created_at': current_timestamp,
            'updated_at': current_timestamp
        }
        
        # 제품명으로 upsert
        collection.update_one(
            {'product_name': product_name},
            {'$set': document},
            upsert=True
        )
        
        print(f"   ✅ DB 저장 완료: {product_name} ({review_count}개 후기)")
        client.close()
        return True
        
    except Exception as e:
        print(f"   ❌ DB 저장 실패: {str(e)}")
        return False


def save_youtube_videos_to_db(product_name, videos_data):
    """
    제품별 유튜브 영상 정보를 MongoDB에 저장
    """
    try:
        from pymongo import MongoClient
        import os
        from dotenv import load_dotenv
        
        load_dotenv()
        load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))
        
        MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
        DATABASE_NAME = os.getenv('MONGODB_DATABASE', 'youtube_reviews_db')
        COLLECTION_NAME = 'youtube_videos'  # 유튜브 영상 정보 컬렉션
        
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]
        
        current_timestamp = int(datetime.now().timestamp())
        
        document = {
            'product_name': product_name,
            'videos': videos_data,  # 영상 리스트
            'video_count': len(videos_data),
            'created_at': current_timestamp,
            'updated_at': current_timestamp
        }
        
        # 제품명으로 upsert
        collection.update_one(
            {'product_name': product_name},
            {'$set': document},
            upsert=True
        )
        
        print(f"   ✅ 유튜브 영상 DB 저장 완료: {product_name} ({len(videos_data)}개 영상)")
        client.close()
        return True
        
    except Exception as e:
        print(f"   ❌ 유튜브 영상 DB 저장 실패: {str(e)}")
        return False


def crawl_product_batch(product_name):
    """
    특정 제품의 유튜브 영상과 커뮤니티 후기를 크롤링하여 DB에 저장 (제품명 정규화 적용)
    """
    import product_normalizer
    
    # 제품명 정규화
    normalized_name = product_normalizer.normalize_product_name(product_name)
    
    print(f"\n{'='*60}")
    print(f"📱 제품 크롤링 시작: {product_name}")
    if normalized_name != product_name:
        print(f"   → 정규화: {product_name} -> {normalized_name}")
    print(f"{'='*60}")
    
    success = True
    
    try:
        # 1. 유튜브 영상 검색 및 분석
        print(f"   🎥 유튜브 영상 검색 중...")
        youtube_videos = crawler.search_youtube_top3(normalized_name)
        
        if youtube_videos:
            print(f"      ✅ {len(youtube_videos)}개 영상 발견")
            
            # 각 영상에 대해 자막 추출 및 AI 분석 수행
            analyzed_videos = []
            for video in youtube_videos:
                video_id = video['id']
                video_title = video['title']
                
                print(f"      📹 [{video_id}] {video_title[:50]}...")
                
                # DB에서 이미 분석된 영상인지 확인
                cached_result = database.get_review_from_db(video_id)
                
                if cached_result:
                    print(f"         ⚡ 이미 분석됨 (캐시 히트)")
                    analyzed_videos.append(video)
                else:
                    # 자막 추출 및 AI 분석
                    print(f"         🔄 자막 추출 및 AI 분석 중...")
                    script = ai_service.get_youtube_script(video_id)
                    
                    if script.startswith("❌"):
                        print(f"         ❌ 자막 추출 실패: {script}")
                        analyzed_videos.append(video)  # 영상 정보는 저장
                        continue
                    
                    analysis = ai_service.analyze_with_gemini(script)
                    
                    if isinstance(analysis, str) and analysis.startswith("❌"):
                        print(f"         ❌ AI 분석 실패: {analysis}")
                        analyzed_videos.append(video)  # 영상 정보는 저장
                        continue
                    
                    # 분석 결과 DB에 저장
                    import json
                    if isinstance(analysis, dict):
                        database.save_review_to_db(video_id, json.dumps(analysis, ensure_ascii=False))
                    else:
                        database.save_review_to_db(video_id, analysis)
                    
                    print(f"         ✅ 분석 완료 및 저장")
                    analyzed_videos.append(video)
            
            # 영상 정보 저장
            save_youtube_videos_to_db(normalized_name, analyzed_videos)
        else:
            print(f"      ⚠️ 유튜브 영상을 찾지 못했습니다.")
            success = False
        
        # 2. 커뮤니티 후기 크롤링 및 저장
        print(f"   💬 커뮤니티 후기 크롤링 중...")
        result = crawler.crawl_community_reviews(normalized_name)
        
        if isinstance(result, tuple):
            if len(result) == 3:
                reviews_text, sources, actual_count = result
            else:
                reviews_text, sources = result
                actual_count = None
        else:
            reviews_text = result
            sources = []
            actual_count = None
        
        if reviews_text and "가져오지 못했습니다" not in reviews_text:
            # DB에 저장 (정규화된 제품명으로 저장)
            save_community_reviews_to_db(normalized_name, reviews_text, sources, actual_count)
            
            # 커뮤니티 후기 AI 분석 수행 및 저장
            print(f"   🤖 커뮤니티 후기 AI 분석 중...")
            community_analysis = ai_service.analyze_community_reviews_with_gemini(reviews_text)
            
            if isinstance(community_analysis, str) and community_analysis.startswith("❌"):
                print(f"      ❌ 커뮤니티 분석 실패: {community_analysis}")
            else:
                # 분석 결과 DB에 저장
                save_community_analysis_to_db(normalized_name, community_analysis)
                print(f"      ✅ 커뮤니티 분석 완료 및 저장")
        else:
            print(f"   ⚠️ {normalized_name}: 커뮤니티 후기를 수집하지 못했습니다.")
            success = False
        
        return success
            
    except Exception as e:
        print(f"   ❌ {normalized_name} 크롤링 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def get_youtube_videos_from_db(product_name):
    """
    MongoDB에서 제품별 유튜브 영상 정보 조회 (제품명 변형 자동 처리)
    """
    try:
        import product_normalizer
        from pymongo import MongoClient
        import os
        from dotenv import load_dotenv
        
        load_dotenv()
        load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))
        
        MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
        DATABASE_NAME = os.getenv('MONGODB_DATABASE', 'youtube_reviews_db')
        COLLECTION_NAME = 'youtube_videos'
        
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]
        
        # 정규화된 제품명으로 먼저 검색
        normalized_name = product_normalizer.normalize_product_name(product_name)
        result = collection.find_one({'product_name': normalized_name})
        
        if result:
            videos = result.get('videos', [])
            client.close()
            return videos
        
        # 정확히 일치하지 않으면 유사 제품명 검색
        all_products = collection.find({}, {'product_name': 1})
        db_product_names = [p['product_name'] for p in all_products]
        
        similar_product = product_normalizer.find_similar_product_in_db(product_name, db_product_names)
        
        if similar_product:
            print(f"   🔍 유사 제품명 발견: '{product_name}' -> '{similar_product}'")
            result = collection.find_one({'product_name': similar_product})
            if result:
                videos = result.get('videos', [])
                client.close()
                return videos
        
        client.close()
        return None
            
    except Exception as e:
        print(f"   ⚠️ 유튜브 영상 DB 조회 실패: {str(e)}")
        return None


def get_community_reviews_from_db(product_name):
    """
    MongoDB에서 제품별 커뮤니티 후기 조회 (제품명 변형 자동 처리)
    분석 결과도 함께 반환 (캐싱된 경우)
    """
    try:
        import product_normalizer
        from pymongo import MongoClient
        import os
        from dotenv import load_dotenv
        
        load_dotenv()
        load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))
        
        MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
        DATABASE_NAME = os.getenv('MONGODB_DATABASE', 'youtube_reviews_db')
        COLLECTION_NAME = 'community_reviews'
        
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]
        
        # 정규화된 제품명으로 먼저 검색
        normalized_name = product_normalizer.normalize_product_name(product_name)
        result = collection.find_one({'product_name': normalized_name})
        
        if result:
            reviews_text = result.get('reviews_text', '')
            sources = result.get('sources', [])
            analysis_summary = result.get('analysis_summary', None)  # 캐싱된 분석 결과
            client.close()
            return reviews_text, sources, analysis_summary
        
        # 정확히 일치하지 않으면 모든 제품명 가져와서 유사도 검색
        all_products = collection.find({}, {'product_name': 1})
        db_product_names = [p['product_name'] for p in all_products]
        
        similar_product = product_normalizer.find_similar_product_in_db(product_name, db_product_names)
        
        if similar_product:
            print(f"   🔍 유사 제품명 발견: '{product_name}' -> '{similar_product}'")
            result = collection.find_one({'product_name': similar_product})
            if result:
                reviews_text = result.get('reviews_text', '')
                sources = result.get('sources', [])
                analysis_summary = result.get('analysis_summary', None)  # 캐싱된 분석 결과
                client.close()
                return reviews_text, sources, analysis_summary
        
        client.close()
        return None, [], None
            
    except Exception as e:
        print(f"   ⚠️ DB 조회 실패: {str(e)}")
        return None, [], None


def save_community_analysis_to_db(product_name, analysis_summary):
    """
    제품별 커뮤니티 후기 AI 분석 결과를 MongoDB에 저장 (캐싱)
    """
    try:
        from pymongo import MongoClient
        import os
        from dotenv import load_dotenv
        import json
        
        load_dotenv()
        load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))
        
        MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
        DATABASE_NAME = os.getenv('MONGODB_DATABASE', 'youtube_reviews_db')
        COLLECTION_NAME = 'community_reviews'
        
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]
        
        # 분석 결과를 JSON 문자열로 변환
        if isinstance(analysis_summary, dict):
            analysis_json = json.dumps(analysis_summary, ensure_ascii=False)
        else:
            analysis_json = str(analysis_summary)
        
        # 제품명으로 분석 결과 업데이트
        collection.update_one(
            {'product_name': product_name},
            {'$set': {'analysis_summary': analysis_json, 'analysis_updated_at': int(datetime.now().timestamp())}},
            upsert=False  # 이미 존재하는 문서만 업데이트
        )
        
        print(f"   ✅ 커뮤니티 분석 결과 캐시 저장 완료: {product_name}")
        client.close()
        return True
        
    except Exception as e:
        print(f"   ⚠️ 분석 결과 캐시 저장 실패: {str(e)}")
        return False


if __name__ == "__main__":
    print("🚀 배치 크롤링 시작")
    print(f"총 {len(PRODUCTS_TO_CRAWL)}개 제품 크롤링 예정\n")
    
    success_count = 0
    fail_count = 0
    
    for product in PRODUCTS_TO_CRAWL:
        if crawl_product_batch(product):
            success_count += 1
        else:
            fail_count += 1
    
    print(f"\n{'='*60}")
    print(f"✅ 완료: {success_count}개 성공, ❌ 실패: {fail_count}개")
    print(f"{'='*60}")

