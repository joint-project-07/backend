# 1. Slim 기반의 Python 이미지를 사용
FROM python:3.13-slim

# 2. 작업 디렉토리 설정
WORKDIR /app

# 3. Poetry 공식 설치 스크립트로 Poetry 설치 (버전 1.8.5)
RUN apt-get update && \
    apt-get install -y curl && \
    curl -sSL https://install.python-poetry.org | python3 - --version 1.8.5

# 4. Poetry가 설치된 경로를 PATH에 추가
ENV PATH="/root/.local/bin:$PATH"

# 5. 필수 시스템 패키지 설치 (PostgreSQL 사용)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 6. 의존성 파일을 복사
COPY pyproject.toml poetry.lock /app/

# 7. Poetry로 의존성 설치
RUN poetry install --no-dev

# 8. 프로젝트 파일 복사
COPY . .

# 9. 가상환경 경로 확인 (옵션)
RUN poetry env info --path  # 가상환경 경로 확인

# 9. Django와 관련된 의존성 설치 확인
RUN poetry show  # 의존성 확인

# 10. 정적 파일 모으기
RUN poetry run python manage.py collectstatic --noinput

# 11. 실행 명령어 설정
CMD ["poetry", "run", "gunicorn", "-b", "0.0.0.0:8000", "--timeout", "300", "Dangnyang_Heroes.wsgi:application"]

