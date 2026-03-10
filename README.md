# Planship

**Self-hosted 프로젝트 관리 시스템**

팀 기반의 셀프 호스팅 프로젝트 관리 플랫폼입니다. 칸반 보드, 타임라인, 팀 관리 등 프로젝트 운영에 필요한 핵심 기능을 제공합니다.

## 주요 기능

- **팀 관리**: 팀 생성, 멤버 초대, 역할 기반 접근 제어 (Owner / Admin / Member / Viewer)
- **프로젝트 관리**: 팀별 프로젝트 생성 및 상태 관리 (Active / Completed / Archived)
- **칸반 보드**: 드래그 앤 드롭 기반 칸반 보드로 카드 관리
- **카드 시스템**: Epic / Story / Task 타입, 우선순위, 담당자, 라벨, 댓글 지원
- **타임라인**: 프로젝트 일정 및 카드 기한 관리
- **대시보드**: 프로젝트 및 팀 현황 한눈에 파악
- **통합 검색**: 프로젝트와 카드를 통합 검색
- **관리자 패널**: 시스템 전체 사용자 및 팀 관리 (Superadmin 전용)
- **감사 로그**: 주요 활동 기록 추적

## 기술 스택

| 구분 | 기술 |
|------|------|
| **Backend** | Python 3.11+, FastAPI, SQLAlchemy 2.0 (async), Alembic |
| **Frontend** | React 18, TypeScript, Ant Design, TanStack Query |
| **Database** | PostgreSQL 15+ |
| **Authentication** | JWT (Access Token + Refresh Token) |
| **Infrastructure** | Docker, Docker Compose |
| **API Documentation** | Swagger UI (자동 생성) |

## 빠른 시작

### 사전 요구사항

- Docker 및 Docker Compose 설치
- Git

### 설치 및 실행

1. **저장소 클론**

```bash
git clone https://github.com/your-org/planship.git
cd planship
```

2. **환경 변수 설정**

```bash
cp .env.example .env
```

`.env` 파일을 열어 아래 항목을 환경에 맞게 수정합니다:

```env
# Database
POSTGRES_USER=planship
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=planship

# Host Port Mapping (host_port:container_port)
# 호스트에서 접근할 포트를 설정합니다. Docker 컨테이너 내부 포트는 고정입니다.
HOST_BACKEND_PORT=8000    # -> backend container 8000
HOST_FRONTEND_PORT=3000   # -> frontend container 80
HOST_POSTGRES_PORT=5432   # -> postgres container 5432

# JWT
SECRET_KEY=your_secret_key_here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS (HOST_FRONTEND_PORT를 변경한 경우 여기도 함께 수정하세요)
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

3. **Docker Compose로 실행**

```bash
docker-compose up --build
```

4. **접속** (기본 포트 기준, `.env`의 `HOST_*_PORT` 값에 따라 달라짐)

- Frontend: http://localhost:{HOST_FRONTEND_PORT} (기본 3000)
- Backend API: http://localhost:{HOST_BACKEND_PORT} (기본 8000)

### 기본 관리자 계정

최초 실행 시 기본 관리자 계정이 자동 생성됩니다. 로그인 후 반드시 비밀번호를 변경해 주세요.

> 기본 계정 정보는 `.env` 파일 또는 초기화 스크립트를 확인하세요.

## Docker 배포

### 프로덕션 배포

```bash
docker-compose -f docker-compose.yml up -d --build
```

### 서비스 중지

```bash
docker-compose down
```

### 로그 확인

```bash
docker-compose logs -f backend
docker-compose logs -f frontend
```
