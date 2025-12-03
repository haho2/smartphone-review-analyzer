from flask import Flask, request, jsonify
from flask_cors import CORS
import ai_service  # 방금 이름 바꾼 파일(ai_service.py)을 불러옵니다
import database  # MongoDB 캐싱 레이어
import crawler  # 유튜브 검색 및 커뮤니티 크롤링
import os
import threading
import json

app = Flask(__name__)
# 프론트엔드(React)에서 요청을 보낼 때 보안 문제를 해결해줍니다.
CORS(app)

# 구매 가이드 생성 상태 저장 (메모리 기반, 데모용)
# 구조: { "제품명": {"status": "processing"|"completed", "guide": {...}, "error": "..."} }
purchase_guide_cache = {}
purchase_guide_lock = threading.Lock() 

@app.route('/')
def home():
    return "AI 리뷰 분석 서버가 정상 작동 중입니다! 🚀"

@app.route('/api/analyze', methods=['POST'])
def analyze_video():
    """
    프론트엔드에서 { "video_id": "..." } 데이터를 보내면
    AI 분석 결과를 돌려주는 API입니다.
    
    동작 흐름:
    1. MongoDB에서 캐시 확인 (Cache Hit/Miss)
    2. Hit: 즉시 반환
    3. Miss: AI 분석 수행 → DB 저장 → 반환
    """
    data = request.get_json()
    video_id = data.get('video_id')

    if not video_id:
        return jsonify({"error": "video_id가 필요합니다."}), 400

    print(f"📡 요청 수신: 비디오 ID [{video_id}] 분석 시작...")

    # 1. MongoDB 캐시 확인 (Cache Hit 체크)
    cached_result = database.get_review_from_db(video_id)
    
    if cached_result:
        # 캐시 히트: 저장된 분석 결과 즉시 반환
        print(f"   ⚡ 캐시에서 결과 반환 (생성 시간: {cached_result.get('created_at', 'N/A')})")
        return jsonify({
            "video_id": video_id,
            "analysis": cached_result.get('analysis', ''),
            "cached": True
        })

    # 2. 캐시 미스: AI 분석 수행
    print(f"   🔄 캐시 미스: AI 분석 시작...")
    
    # 2-1. 자막 가져오기 (ai_service의 함수 사용)
    script = ai_service.get_youtube_script(video_id)
    
    if script.startswith("❌"):
        return jsonify({"error": script}), 500

    # 2-2. Gemini 분석 (ai_service의 함수 사용)
    result = ai_service.analyze_with_gemini(script)

    if result.startswith("❌"):
        return jsonify({"error": result}), 500

    # 3. 분석 결과를 MongoDB에 저장 (캐싱)
    database.save_review_to_db(video_id, result)

    # 4. 성공 결과 반환
    return jsonify({
        "video_id": video_id,
        "analysis": result,
        "cached": False
    })


@app.route('/api/analyze-product', methods=['POST'])
def analyze_product():
    """
    제품명을 받아서 유튜브 영상 3개와 커뮤니티 후기를 종합 분석하는 API
    
    Request Body:
    {
        "product_name": "갤럭시 S25"
    }
    
    Response:
    {
        "product_name": "갤럭시 S25",
        "youtube_reviews": [
            {"video_id": "...", "title": "...", "analysis": "..."},
            ...
        ],
        "community_reviews": {
            "summary": "...",
            "raw_count": 10
        },
        "purchase_guide": "..."
    }
    """
    data = request.get_json()
    product_name = data.get('product_name')
    
    if not product_name:
        return jsonify({"error": "product_name이 필요합니다."}), 400
    
    print(f"📡 요청 수신: 제품명 [{product_name}] 종합 분석 시작...")
    
    try:
        # 제품명 정규화 (Fuzzy 매칭으로 실제 존재하는 모델만 반환)
        import product_normalizer
        normalized_product_name = product_normalizer.normalize_product_name(product_name, use_fuzzy_matching=True)
        
        # 정규화 실패 시 에러 반환
        if not normalized_product_name:
            return jsonify({"error": f"'{product_name}'에 해당하는 제품을 찾을 수 없습니다."}), 404
        
        if normalized_product_name != product_name:
            print(f"   → 정규화: {product_name} -> {normalized_product_name}")
        
        # 1. 유튜브 영상 조회 (DB 우선, 없으면 실시간 검색)
        print(f"   🔍 유튜브 영상 조회 중...")
        
        # DB에서 먼저 조회 시도 (정규화된 이름으로)
        import batch_crawler
        youtube_videos_from_db = batch_crawler.get_youtube_videos_from_db(normalized_product_name)
        
        if youtube_videos_from_db:
            print(f"   ⚡ DB에서 유튜브 영상 조회 성공 ({len(youtube_videos_from_db)}개)")
            youtube_videos = youtube_videos_from_db
        else:
            # DB에 없으면 실시간 검색 (사용자 입력 그대로 사용)
            print(f"   🔄 DB에 없음: 실시간 검색 시작...")
            youtube_videos = crawler.search_youtube_top3(product_name)  # 원본 입력 사용
            
            # 검색 성공 시 DB에 저장 (정규화된 이름으로 저장)
            if youtube_videos:
                batch_crawler.save_youtube_videos_to_db(normalized_product_name, youtube_videos)
        
        if not youtube_videos:
            return jsonify({"error": "유튜브 영상을 찾을 수 없습니다."}), 404
        
        print(f"   ✅ {len(youtube_videos)}개 영상 발견")
        
        # 2. 각 영상 분석 (캐시 확인 포함)
        youtube_analyses = []
        youtube_summaries = []
        
        for video in youtube_videos:
            video_id = video['id']
            video_title = video['title']
            
            print(f"   📹 영상 분석 중: {video_title[:50]}...")
            
            # 캐시 확인
            cached_result = database.get_review_from_db(video_id)
            
            if cached_result:
                analysis_raw = cached_result.get('analysis', '')
                # 캐시된 데이터가 JSON 문자열인 경우 파싱
                import json
                try:
                    if isinstance(analysis_raw, str):
                        analysis = json.loads(analysis_raw)
                    else:
                        analysis = analysis_raw
                except:
                    analysis = analysis_raw
                print(f"      ⚡ 캐시 히트")
            else:
                # 자막 추출 및 분석
                script = ai_service.get_youtube_script(video_id)
                if script.startswith("❌"):
                    print(f"      ❌ 자막 추출 실패: {script}")
                    continue
                
                analysis = ai_service.analyze_with_gemini(script)
                if isinstance(analysis, str) and analysis.startswith("❌"):
                    print(f"      ❌ 분석 실패: {analysis}")
                    continue
                
                # 캐시 저장 (JSON 또는 텍스트 모두 저장 가능)
                import json
                if isinstance(analysis, dict):
                    database.save_review_to_db(video_id, json.dumps(analysis, ensure_ascii=False))
                else:
                    database.save_review_to_db(video_id, analysis)
            
            # 분석 결과를 구조화된 형태로 저장
            youtube_analyses.append({
                "video_id": video_id,
                "title": video_title,
                "analysis": analysis  # dict 또는 str
            })
            
            # 구매 가이드 생성을 위한 요약 (텍스트 형태)
            if isinstance(analysis, dict):
                summary_text = f"장점: {', '.join(analysis.get('pros', []))}\n단점: {', '.join(analysis.get('cons', []))}"
            else:
                summary_text = str(analysis)
            youtube_summaries.append(summary_text)
        
        # 3. 커뮤니티 후기 조회 (DB 우선, 없으면 실시간 크롤링)
        print(f"   🌐 커뮤니티 후기 조회 중...")
        
        # DB에서 먼저 조회 시도 (정규화된 이름으로)
        import batch_crawler
        # 정규화된 이름으로 DB 조회 (더 정확한 매칭)
        # 반환값: (reviews_text, sources, analysis_summary)
        result = batch_crawler.get_community_reviews_from_db(normalized_product_name)
        
        if len(result) == 3:
            community_reviews_text, community_sources, cached_analysis = result
        else:
            # 하위 호환성
            community_reviews_text, community_sources = result[:2]
            cached_analysis = None
        
        if community_reviews_text:
            print(f"   ⚡ DB에서 커뮤니티 후기 조회 성공 ({len(community_reviews_text.split(chr(10)))}개)")
        else:
            # DB에 없으면 실시간 크롤링 (Fallback)
            print(f"   🔄 DB에 없음: 실시간 크롤링 시작...")
            community_reviews_result = crawler.crawl_community_reviews(product_name)
            
            if isinstance(community_reviews_result, tuple):
                if len(community_reviews_result) == 3:
                    community_reviews_text, community_sources, _ = community_reviews_result
                else:
                    community_reviews_text, community_sources = community_reviews_result
            else:
                community_reviews_text = community_reviews_result
                community_sources = []
            
            # 크롤링 성공 시 DB에 저장 (다음 요청을 위해)
            if community_reviews_text and "가져오지 못했습니다" not in community_reviews_text:
                # 실제 개수 추출 (리스트에서)
                actual_count = len([line for line in community_reviews_text.split('\n') if line.strip().startswith('[')])
                batch_crawler.save_community_reviews_to_db(normalized_product_name, community_reviews_text, community_sources, actual_count)
            cached_analysis = None
        
        # 커뮤니티 후기 분석 (캐시 확인)
        community_summary = None
        if community_reviews_text and "가져오지 못했습니다" not in community_reviews_text:
            # 캐시된 분석 결과가 있으면 사용
            if cached_analysis:
                print(f"   ⚡ DB에서 커뮤니티 분석 결과 캐시 히트")
                import json
                try:
                    if isinstance(cached_analysis, str):
                        community_summary = json.loads(cached_analysis)
                    else:
                        community_summary = cached_analysis
                except:
                    community_summary = cached_analysis
            else:
                # 캐시 없으면 AI 분석 수행
                print(f"   ✅ 커뮤니티 후기 수집 완료, AI 분석 시작...")
                community_summary = ai_service.analyze_community_reviews_with_gemini(community_reviews_text)
                
                # dict가 아닌 경우 (오류 등) 처리
                if isinstance(community_summary, str) and community_summary.startswith("❌"):
                    community_summary = None
                else:
                    # 분석 성공 시 DB에 캐싱
                    if community_summary:
                        batch_crawler.save_community_analysis_to_db(normalized_product_name, community_summary)
                        print(f"   ✅ 커뮤니티 분석 완료 및 캐시 저장")
        else:
            community_summary = None
        
        # 4. 구매 가이드는 백그라운드에서 비동기 생성
        print(f"   📊 구매 가이드 생성 시작 (백그라운드)...")
        
        # 구매 가이드 생성 상태 초기화
        with purchase_guide_lock:
            purchase_guide_cache[normalized_product_name] = {"status": "processing"}
        
        # 백그라운드 스레드에서 구매 가이드 생성
        def generate_guide_async():
            try:
                youtube_combined = "\n\n---\n\n".join(youtube_summaries)
                community_text = ""
                if isinstance(community_summary, dict):
                    community_text = f"장점: {', '.join(community_summary.get('pros', []))}\n단점: {', '.join(community_summary.get('cons', []))}"
                elif community_summary:
                    community_text = str(community_summary)
                
                guide = ai_service.generate_purchase_guide(
                    youtube_combined,
                    community_text,
                    normalized_product_name
                )
                
                # 결과 저장
                with purchase_guide_lock:
                    purchase_guide_cache[normalized_product_name] = {
                        "status": "completed",
                        "guide": guide
                    }
                print(f"   ✅ 구매 가이드 생성 완료: {normalized_product_name}")
            except Exception as e:
                print(f"   ❌ 구매 가이드 생성 실패: {str(e)}")
                with purchase_guide_lock:
                    purchase_guide_cache[normalized_product_name] = {
                        "status": "error",
                        "error": str(e)
                    }
        
        # 백그라운드 스레드 시작
        guide_thread = threading.Thread(target=generate_guide_async, daemon=True)
        guide_thread.start()
        
        # 5. 결과 반환 (구매 가이드 제외)
        return jsonify({
            "product_name": product_name,
            "youtube_reviews": youtube_analyses,
            "community_reviews": {
                "summary": community_summary,  # dict 또는 None
                "raw_count": len(community_reviews_text.split('\n')) if community_reviews_text else 0,
                "source": ", ".join(community_sources) if community_sources else "수집 실패",
                "note": "클리앙과 뽐뿌 커뮤니티에서 직접 수집한 신뢰할 수 있는 사용자 후기입니다."
            },
            "purchase_guide_status": "processing"  # 구매 가이드는 별도 엔드포인트로 확인
        })
        
    except Exception as e:
        print(f"   ❌ 오류 발생: {str(e)}")
        return jsonify({"error": f"분석 중 오류가 발생했습니다: {str(e)}"}), 500


@app.route('/api/purchase-guide/<product_name>', methods=['GET'])
def get_purchase_guide(product_name):
    """
    구매 가이드 생성 상태 및 결과 조회 (폴링용)
    
    Response:
    {
        "status": "processing" | "completed" | "error",
        "guide": {...} (status가 completed일 때만),
        "error": "..." (status가 error일 때만)
    }
    """
    import product_normalizer
    normalized_product_name = product_normalizer.normalize_product_name(product_name, use_fuzzy_matching=True)
    
    if not normalized_product_name:
        return jsonify({
            "status": "error",
            "error": f"'{product_name}'에 해당하는 제품을 찾을 수 없습니다."
        }), 404
    
    with purchase_guide_lock:
        cached = purchase_guide_cache.get(normalized_product_name)
    
    if not cached:
        return jsonify({
            "status": "not_started",
            "message": "구매 가이드 생성이 시작되지 않았습니다."
        }), 404
    
    if cached["status"] == "processing":
        return jsonify({
            "status": "processing",
            "message": "구매 가이드를 생성 중입니다..."
        })
    elif cached["status"] == "completed":
        return jsonify({
            "status": "completed",
            "guide": cached["guide"]
        })
    else:  # error
        return jsonify({
            "status": "error",
            "error": cached.get("error", "알 수 없는 오류")
        }), 500


if __name__ == '__main__':
    # 서버 실행
    # 배포 환경에서는 PORT 환경 변수 사용 (Railway, Render 등)
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    app.run(debug=debug_mode, host='0.0.0.0', port=port, use_reloader=False)