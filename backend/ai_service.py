import os
import sys
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi
from dotenv import load_dotenv

# Windows에서 UTF-8 출력을 위한 설정
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# 1. 환경변수(.env) 로드
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("❌ 오류: .env 파일에 GOOGLE_API_KEY가 없습니다.")
    exit()

# 2. Gemini 설정
genai.configure(api_key=api_key)

def get_youtube_script(video_id):
    """유튜브 자막(스크립트) 가져오기"""
    try:
        # YouTubeTranscriptApi 인스턴스 생성
        ytt_api = YouTubeTranscriptApi()
        
        # 사용 가능한 자막 목록 가져오기
        transcript_list = ytt_api.list(video_id)
        
        # 한국어 또는 영어 자막 찾기
        try:
            transcript = transcript_list.find_transcript(['ko', 'en'])
            print(f"   → {transcript.language_code} 자막 사용")
        except:
            # ko, en이 없으면 첫 번째 자막 사용
            transcript = list(transcript_list)[0]
            print(f"   → {transcript.language_code} 자막 사용")
        
        # 자막 데이터 가져오기
        transcript_data = transcript.fetch()
        
        full_text = ""
        for line in transcript_data:
            seconds = int(line.start)
            minutes = seconds // 60
            sec = seconds % 60
            timestamp = f"[{minutes:02d}:{sec:02d}]"
            full_text += f"{timestamp} {line.text}\n"
            
        return full_text
    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e)
        print(f"   오류 상세: {error_type} - {error_msg}")
        return f"❌ 자막 추출 실패 ({error_type}): {error_msg}"

def analyze_with_gemini(script_text):
    """Gemini에게 분석 요청하기 - 구조화된 JSON 반환"""
    prompt = f"""
    너는 스마트폰 전문 리뷰어 AI야. 아래 유튜브 리뷰 스크립트를 읽고 분석해줘.
    
    [요청사항]
    반드시 다음 JSON 형식으로만 응답해줘:
    {{
        "pros": ["장점1", "장점2", "장점3"],
        "cons": ["단점1", "단점2", "단점3"],
        "highlight": {{
            "timestamp": "[00:00]",
            "quote": "인상적인 멘트"
        }}
    }}
    
    주의사항:
    - pros와 cons는 각각 정확히 3개만 작성
    - 각 항목은 간결하게 한 문장으로 작성
    - highlight의 timestamp는 스크립트에 있는 실제 타임스탬프 형식 사용 (예: [05:23])
    - quote는 해당 타임스탬프의 실제 멘트를 그대로 인용
    
    --- 리뷰 스크립트 (시작) ---
    {script_text[:15000]} 
    --- 리뷰 스크립트 (끝) ---
    """
    
    # 사용 가능한 모델 확인 및 시도
    try:
        available_models = []
        for model in genai.list_models():
            if 'generateContent' in model.supported_generation_methods:
                model_name = model.name.replace('models/', '')
                available_models.append(model_name)
        
        if available_models:
            print(f"   사용 가능한 모델: {', '.join(available_models[:3])}")
            # Flash 모델을 우선적으로 사용 (쿼터가 더 여유로울 수 있음)
            flash_models = [m for m in available_models if 'flash' in m.lower()]
            models_to_try = flash_models + [m for m in available_models if m not in flash_models]
            
            for model_name in models_to_try:
                try:
                    print(f"   → {model_name} 모델 시도 중...")
                    model = genai.GenerativeModel(model_name)
                    response = model.generate_content(prompt)
                    result_text = response.text
                    
                    # JSON 파싱 시도
                    import json
                    import re
                    # JSON 부분만 추출 (마크다운 코드 블록 제거)
                    json_match = re.search(r'\{[\s\S]*\}', result_text)
                    if json_match:
                        json_str = json_match.group(0)
                        try:
                            parsed = json.loads(json_str)
                            return parsed
                        except:
                            pass
                    
                    # JSON 파싱 실패 시 텍스트 반환 (하위 호환성)
                    return result_text
                except Exception as e:
                    error_msg = str(e)
                    # 쿼터 초과가 아닌 다른 오류면 즉시 반환
                    if 'quota' not in error_msg.lower() and '429' not in error_msg:
                        return f"❌ AI 분석 실패: {error_msg}"
                    # 쿼터 초과면 다음 모델 시도
                    if model_name == models_to_try[-1]:
                        return f"❌ AI 분석 실패: 모든 모델의 쿼터가 초과되었습니다. 잠시 후 다시 시도해주세요."
                    continue
        else:
            return "❌ AI 분석 실패: 사용 가능한 모델을 찾을 수 없습니다."
    except Exception as e:
        return f"❌ AI 분석 실패: {str(e)}"

def analyze_community_reviews_with_gemini(reviews_text):
    """
    커뮤니티 후기를 Gemini로 분석하여 장단점 추출
    
    Args:
        reviews_text (str): 크롤링한 커뮤니티 후기 텍스트
    
    Returns:
        str: 분석 결과 텍스트
    """
    prompt = f"""
    너는 제품 리뷰 분석 전문가 AI야. 아래 커뮤니티 사용자들의 실제 사용 후기를 읽고 분석해줘.
    
    [요청사항]
    반드시 다음 JSON 형식으로만 응답해줘:
    {{
        "pros": ["장점1", "장점2", "장점3"],
        "cons": ["단점1", "단점2", "단점3"],
        "quotes": ["실제 사용자 멘트1", "실제 사용자 멘트2"]
    }}
    
    주의사항:
    - pros와 cons는 각각 정확히 3개만 작성
    - 각 항목은 간결하게 한 문장으로 작성
    - quotes는 실제 사용자들의 생생한 후기 멘트 2-3개를 그대로 인용
    
    --- 커뮤니티 후기 (시작) ---
    {reviews_text[:15000]}
    --- 커뮤니티 후기 (끝) ---
    """
    
    # 사용 가능한 모델 확인 및 시도
    try:
        available_models = []
        for model in genai.list_models():
            if 'generateContent' in model.supported_generation_methods:
                model_name = model.name.replace('models/', '')
                available_models.append(model_name)
        
        if available_models:
            flash_models = [m for m in available_models if 'flash' in m.lower()]
            models_to_try = flash_models + [m for m in available_models if m not in flash_models]
            
            for model_name in models_to_try:
                try:
                    model = genai.GenerativeModel(model_name)
                    response = model.generate_content(prompt)
                    result_text = response.text
                    
                    # JSON 파싱 시도
                    import json
                    import re
                    json_match = re.search(r'\{[\s\S]*\}', result_text)
                    if json_match:
                        json_str = json_match.group(0)
                        try:
                            parsed = json.loads(json_str)
                            return parsed
                        except:
                            pass
                    
                    # JSON 파싱 실패 시 텍스트 반환
                    return result_text
                except Exception as e:
                    error_msg = str(e)
                    if 'quota' not in error_msg.lower() and '429' not in error_msg:
                        return f"❌ AI 분석 실패: {error_msg}"
                    if model_name == models_to_try[-1]:
                        return f"❌ AI 분석 실패: 모든 모델의 쿼터가 초과되었습니다."
                    continue
        else:
            return "❌ AI 분석 실패: 사용 가능한 모델을 찾을 수 없습니다."
    except Exception as e:
        return f"❌ AI 분석 실패: {str(e)}"


def generate_purchase_guide(youtube_summary, community_summary, product_name):
    """
    유튜브 리뷰와 커뮤니티 후기를 종합하여 구매 결정 가이드 생성 - 구조화된 JSON 반환
    
    Args:
        youtube_summary (str): 유튜브 리뷰 분석 결과
        community_summary (str): 커뮤니티 후기 분석 결과
        product_name (str): 제품명
    
    Returns:
        dict 또는 str: 구매 결정 가이드 (구조화된 JSON 또는 텍스트)
    """
    prompt = f"""
    너는 제품 구매 컨설턴트 AI야. 아래 {product_name}에 대한 전문 리뷰어(유튜브)와 일반 사용자들(커뮤니티)의 의견을 종합하여 구매 결정 가이드를 작성해줘.
    
    [요청사항]
    반드시 다음 JSON 형식으로만 응답해줘:
    {{
        "recommend_for": [
            "상황1 (예: 게임을 자주 하는 사용자)",
            "상황2 (예: 카메라 성능이 중요한 사용자)",
            "상황3"
        ],
        "not_recommend_for": [
            "상황1 (예: 배터리 수명이 중요한 사용자)",
            "상황2 (예: 예산이 제한적인 사용자)",
            "상황3"
        ],
        "summary": "종합 가이드를 2-3줄로 간결하게 요약"
    }}
    
    주의사항:
    - recommend_for와 not_recommend_for는 각각 정확히 3개만 작성
    - 각 항목은 한 문장으로 간결하게 작성 (예: "게임을 자주 하는 사용자", "배터리 수명이 중요한 사용자")
    - summary는 2-3줄로 매우 간결하게 작성 (전체 요약)
    
    --- 전문 리뷰어 의견 (유튜브) ---
    {youtube_summary[:8000]}
    
    --- 일반 사용자 의견 (커뮤니티) ---
    {community_summary[:8000]}
    """
    
    # 사용 가능한 모델 확인 및 시도
    try:
        available_models = []
        for model in genai.list_models():
            if 'generateContent' in model.supported_generation_methods:
                model_name = model.name.replace('models/', '')
                available_models.append(model_name)
        
        if available_models:
            flash_models = [m for m in available_models if 'flash' in m.lower()]
            models_to_try = flash_models + [m for m in available_models if m not in flash_models]
            
            for model_name in models_to_try:
                try:
                    model = genai.GenerativeModel(model_name)
                    response = model.generate_content(prompt)
                    result_text = response.text
                    
                    # JSON 파싱 시도
                    import json
                    import re
                    json_match = re.search(r'\{[\s\S]*\}', result_text)
                    if json_match:
                        json_str = json_match.group(0)
                        try:
                            parsed = json.loads(json_str)
                            return parsed
                        except:
                            pass
                    
                    # JSON 파싱 실패 시 텍스트 반환
                    return result_text
                except Exception as e:
                    error_msg = str(e)
                    if 'quota' not in error_msg.lower() and '429' not in error_msg:
                        return f"❌ 구매 가이드 생성 실패: {error_msg}"
                    if model_name == models_to_try[-1]:
                        return f"❌ 구매 가이드 생성 실패: 모든 모델의 쿼터가 초과되었습니다."
                    continue
        else:
            return "❌ 구매 가이드 생성 실패: 사용 가능한 모델을 찾을 수 없습니다."
    except Exception as e:
        return f"❌ 구매 가이드 생성 실패: {str(e)}"


# --- 테스트 실행 영역 ---
if __name__ == "__main__":
    # 테스트하고 싶은 유튜브 영상 ID (예: 갤럭시 S25 관련 영상)
    # URL이 https://www.youtube.com/watch?v=ABCDEFG 라면 'ABCDEFG'가 ID입니다.

    test_video_id = "sCffhYaBP4s"
    
    print(f"▶ 영상 ID [{test_video_id}] 자막 다운로드 중...")
    script = get_youtube_script(test_video_id)
    
    if script.startswith("❌"):
        print(script)
    else:
        print(f"✅ 자막 확보 완료! (길이: {len(script)}자)")
        print("▶ Gemini AI 분석 시작 (약 5~10초 소요)...")
        
        result = analyze_with_gemini(script)
        
        print("\n" + "="*50)
        print("🤖 AI 분석 결과")
        print("="*50)
        print(result)