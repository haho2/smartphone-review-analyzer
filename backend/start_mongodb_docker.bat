@echo off
echo MongoDB Docker 컨테이너 시작 중...
docker run -d -p 27017:27017 --name mongodb mongo:latest
echo.
echo MongoDB가 시작되었습니다!
echo 연결 URI: mongodb://localhost:27017/
echo.
echo 컨테이너 중지: docker stop mongodb
echo 컨테이너 삭제: docker rm mongodb
pause

