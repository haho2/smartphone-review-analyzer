import { useState } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [productName, setProductName] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [purchaseGuide, setPurchaseGuide] = useState(null);
  const [guideLoading, setGuideLoading] = useState(false);

  // API URL 설정 (환경 변수 또는 기본값)
  const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:5000';

  const handleAnalyze = async () => {
    if (!productName.trim()) {
      alert("제품명을 입력해주세요!");
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);
    setPurchaseGuide(null);
    setGuideLoading(false);

    try {
      const response = await axios.post(`${API_URL}/api/analyze-product`, {
        product_name: productName.trim()
      });

      setResult(response.data);
      
      // 구매 가이드는 별도로 폴링 시작
      if (response.data.purchase_guide_status === 'processing') {
        pollPurchaseGuide(productName.trim());
      }
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.error || "분석에 실패했습니다. 백엔드 서버가 켜져 있는지 확인해주세요.");
    } finally {
      setLoading(false);
    }
  };

  const pollPurchaseGuide = async (productName) => {
    setGuideLoading(true);
    const maxAttempts = 30; // 최대 30번 시도 (약 30초)
    let attempts = 0;

    const poll = async () => {
      try {
        const response = await axios.get(`${API_URL}/api/purchase-guide/${encodeURIComponent(productName)}`);
        
        if (response.data.status === 'completed') {
          setPurchaseGuide(response.data.guide);
          setGuideLoading(false);
          return;
        } else if (response.data.status === 'error') {
          setError(response.data.error || '구매 가이드 생성 중 오류가 발생했습니다.');
          setGuideLoading(false);
          return;
        }
        
        // 아직 처리 중이면 계속 폴링
        attempts++;
        if (attempts < maxAttempts) {
          setTimeout(poll, 1000); // 1초마다 확인
        } else {
          setError('구매 가이드 생성 시간이 초과되었습니다.');
          setGuideLoading(false);
        }
      } catch (err) {
        console.error('구매 가이드 폴링 오류:', err);
        attempts++;
        if (attempts < maxAttempts) {
          setTimeout(poll, 1000);
        } else {
          setError('구매 가이드를 가져오는 중 오류가 발생했습니다.');
          setGuideLoading(false);
        }
      }
    };

    // 첫 폴링 시작 (약 1초 후)
    setTimeout(poll, 1000);
  };

  // 타임스탬프를 초로 변환 (예: [05:23] -> 323)
  const parseTimestamp = (timestamp) => {
    const match = timestamp.match(/\[(\d+):(\d+)\]/);
    if (match) {
      const minutes = parseInt(match[1]);
      const seconds = parseInt(match[2]);
      return minutes * 60 + seconds;
    }
    return 0;
  };

  // 유튜브 링크 생성 (타임스탬프 포함)
  const getYouTubeLink = (videoId, timestamp) => {
    const seconds = parseTimestamp(timestamp);
    return `https://www.youtube.com/watch?v=${videoId}&t=${seconds}s`;
  };

  return (
    <div className="container">
      <h1>🤖 스마트폰 리뷰 AI 종합 분석기</h1>
      <p className="subtitle">전문 리뷰어(유튜브) + 일반 사용자(커뮤니티) 의견을 종합하여 구매 결정을 도와드립니다</p>
      
      <div className="input-group">
        <input 
          type="text" 
          placeholder="제품명 입력 (예: 갤럭시 S25, 아이폰 17)" 
          value={productName}
          onChange={(e) => setProductName(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleAnalyze()}
        />
        <button onClick={handleAnalyze} disabled={loading}>
          {loading ? '분석 중...' : '분석하기'}
        </button>
      </div>

      {error && <div className="error-box">{error}</div>}

      {loading && (
        <div className="loading-box">
          <div className="spinner"></div>
          <p>유튜브 영상 검색 및 분석 중... (1-2분 소요)</p>
        </div>
      )}

      {result && (
        <div className="results">
          <h2 className="product-title">📱 {result.product_name} 분석 결과</h2>
          
          {/* 상단: 유튜브 리뷰 + 커뮤니티 리뷰 */}
          <div className="reviews-grid">
            {/* 왼쪽: 유튜브 리뷰 */}
            <div className="youtube-section">
              <h3>🎥 전문 리뷰어 의견</h3>
              {result.youtube_reviews && result.youtube_reviews.length > 0 ? (
                <div className="youtube-reviews">
                  {result.youtube_reviews.map((review, index) => {
                    const analysis = review.analysis;
                    const isStructured = typeof analysis === 'object' && analysis !== null;
                    
                    return (
                      <div key={review.video_id} className="review-card">
                        <h4 className="video-title">
                          <a 
                            href={`https://www.youtube.com/watch?v=${review.video_id}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="video-link"
                          >
                            {index + 1}. {review.title}
                          </a>
                        </h4>
                        
                        {isStructured ? (
                          <div className="structured-analysis">
                            <div className="pros-section">
                              <h5>✅ 장점</h5>
                              <ul>
                                {analysis.pros && analysis.pros.map((pro, i) => (
                                  <li key={i}>{pro}</li>
                                ))}
                              </ul>
                            </div>
                            <div className="cons-section">
                              <h5>❌ 단점</h5>
                              <ul>
                                {analysis.cons && analysis.cons.map((con, i) => (
                                  <li key={i}>{con}</li>
                                ))}
                              </ul>
                            </div>
                            {analysis.highlight && (
                              <div className="highlight-section">
                                <h5>💡 인상적인 멘트</h5>
                                <a
                                  href={getYouTubeLink(review.video_id, analysis.highlight.timestamp)}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="timestamp-link"
                                >
                                  {analysis.highlight.timestamp} {analysis.highlight.quote}
                                </a>
                              </div>
                            )}
                          </div>
                        ) : (
                          <div className="text-analysis">
                            <pre>{String(analysis)}</pre>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              ) : (
                <p className="no-data">유튜브 리뷰를 찾을 수 없습니다.</p>
              )}
            </div>

            {/* 오른쪽: 커뮤니티 리뷰 */}
            <div className="community-section">
              <h3>💬 일반 사용자 의견</h3>
              {result.community_reviews && result.community_reviews.summary ? (
                <div className="community-review">
                  {typeof result.community_reviews.summary === 'object' ? (
                    <div className="structured-analysis">
                      <div className="pros-section">
                        <h5>✅ 장점</h5>
                        <ul>
                          {result.community_reviews.summary.pros && result.community_reviews.summary.pros.map((pro, i) => (
                            <li key={i}>{pro}</li>
                          ))}
                        </ul>
                      </div>
                      <div className="cons-section">
                        <h5>❌ 단점</h5>
                        <ul>
                          {result.community_reviews.summary.cons && result.community_reviews.summary.cons.map((con, i) => (
                            <li key={i}>{con}</li>
                          ))}
                        </ul>
                      </div>
                      {result.community_reviews.summary.quotes && result.community_reviews.summary.quotes.length > 0 && (
                        <div className="quotes-section">
                          <h5>💬 실제 사용자 멘트</h5>
                          <ul className="quotes-list">
                            {result.community_reviews.summary.quotes.map((quote, i) => (
                              <li key={i} className="quote-item">"{quote}"</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="text-analysis">
                      <pre>{result.community_reviews.summary}</pre>
                    </div>
                  )}
                  
                  {result.community_reviews.source && (
                    <div className="source-info">
                      <span className="source-label">📌 데이터 소스:</span> {result.community_reviews.source}
                    </div>
                  )}
                </div>
              ) : (
                <p className="no-data">커뮤니티 후기를 수집하지 못했습니다.</p>
              )}
            </div>
          </div>

          {/* 하단: 구매 결정 가이드 */}
          <div className="guide-box">
            <h3>💡 구매 결정 가이드</h3>
            {guideLoading ? (
              <div className="loading-box">
                <div className="spinner"></div>
                <p>구매 가이드를 생성 중입니다... (10-30초 소요)</p>
              </div>
            ) : purchaseGuide ? (
              typeof purchaseGuide === 'object' && purchaseGuide !== null ? (
                <div className="structured-guide">
                  <div className="recommend-section">
                    <h4>✅ 추천하는 경우</h4>
                    <ul>
                      {purchaseGuide.recommend_for && purchaseGuide.recommend_for.map((item, i) => (
                        <li key={i}>{item}</li>
                      ))}
                    </ul>
                  </div>
                  <div className="not-recommend-section">
                    <h4>❌ 비추천하는 경우</h4>
                    <ul>
                      {purchaseGuide.not_recommend_for && purchaseGuide.not_recommend_for.map((item, i) => (
                        <li key={i}>{item}</li>
                      ))}
                    </ul>
                  </div>
                  {purchaseGuide.summary && (
                    <div className="guide-summary">
                      <h4>📋 종합 가이드</h4>
                      <p>{purchaseGuide.summary}</p>
                    </div>
                  )}
                </div>
              ) : (
                <div className="guide-content">{purchaseGuide}</div>
              )
            ) : (
              <p className="no-data">구매 가이드를 생성 중입니다...</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
