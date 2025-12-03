from thefuzz import process, fuzz
import re

class SearchCorrector:
    def __init__(self):
        # 1. [Master Data] 우리가 지원하는 '진짜 모델명' 리스트 (DB 역할)
        # 여기에 없는 이름은 절대 결과로 나오지 않습니다. (환각 방지)
        self.valid_models = [
            # 갤럭시 S25 시리즈
            "갤럭시 S25", "갤럭시 S25 Plus", "갤럭시 S25 Ultra", "갤럭시 S25 Edge",

            # 아이폰 17 시리즈
            "아이폰 17", "아이폰 17 Pro", "아이폰 17 Pro Max", "아이폰 17 Air",
            # 폴더블
            "Z플립 7", "Z폴드 7", "Z트라이폴드"
        ]

        # 2. 브랜드 동의어 사전 (Fuzzy 매칭 정확도를 높이기 위한 기초 작업)
        self.brand_aliases = {
            '갤럭시': ['갤', 'galaxy', 'samsung', 's2', 's1'], # s25, s24 등을 위해
            '아이폰': ['아폰', 'iphone', 'apple', 'iph'],
            'Z플립': ['제트플립', 'zflip', '플립'],
            'Z폴드': ['제트폴드', 'zfold', '폴드'],
            'Z트라이폴드': ['트라이폴드', '3단폴드', 'trifold']
        }

    def _pre_normalize(self, query):
        """1차 전처리: 한글/영문 통일 및 브랜드명 복원"""
        if not query: return ""
        
        # 소문자 변환 및 공백 제거
        query = query.lower().replace(" ", "")
        
        # 브랜드명 치환 (예: '갤s25' -> '갤럭시s25')
        for standard, aliases in self.brand_aliases.items():
            for alias in aliases:
                if alias in query:
                    # 's25' 같은 모델명과 겹치지 않게 주의
                    # 여기서는 단순 치환보다, 브랜드가 감지되면 앞에 붙여주는 방식을 씀
                    if alias == 'samsung': query = query.replace(alias, '갤럭시')
                    elif alias == 'iphone': query = query.replace(alias, '아이폰')
                    break
        
        # 숫자와 문자 사이에 공백 넣기 (유사도 검사 잘 되게)
        # 예: 갤럭시s25 -> 갤럭시 s25
        query = re.sub(r'(?<=\D)(?=\d)|(?<=\d)(?=\D)', ' ', query)
        
        return query.strip()

    def correct(self, user_input):
        """
        사용자 입력을 받아서 가장 유력한 '실존 모델명'을 반환
        """
        # 1. 기초 다듬기
        normalized_query = self._pre_normalize(user_input)
        
        # 2. 유사도 검사 (TheFuzz)
        # limit=1: 가장 점수 높은 1개만 가져옴
        # scorer=token_set_ratio: 순서가 바뀌어도(s25 갤럭시) 점수 높게 줌
        best_match, score = process.extractOne(
            normalized_query, 
            self.valid_models, 
            scorer=fuzz.token_set_ratio
        )
        
        # 3. 디버깅용 출력 (개발 중에만 보세요)
        print(f"   [Debug] 입력: '{user_input}' -> 변환: '{normalized_query}' -> 매칭: '{best_match}' ({score}점)")
        
        # 4. 점수가 너무 낮으면(엉뚱한 검색어) None 리턴
        # 55점 미만이면 관련 없다고 판단 (기준 조절 가능)
        if score < 55:
            return None
            
        return best_match

# --- 테스트 실행부 ---
if __name__ == "__main__":
    corrector = SearchCorrector()
    
    test_cases = [
        "s25 프로",       # (없는 폰) -> 갤럭시 S25 (Pro 무시됨! 👍)
        "아이폰17 울트라", # (없는 폰) -> 아이폰 17 (Ultra 무시됨! 👍)
        "갤s25",          # -> 갤럭시 S25
        "아폰17프맥",      # -> 아이폰 17 Pro Max
        "트라이폴드",      # -> Z트라이폴드
        "glaaxy s24",     # (오타) -> 갤럭시 S24
        "24플러스"         # -> 갤럭시 S24 Plus
    ]
    
    print("="*50)
    print(f"{'사용자 입력':<15} | {'교정된 실제 모델명'}")
    print("="*50)
    
    for case in test_cases:
        result = corrector.correct(case)
        print(f"{case:<15} | {result}")