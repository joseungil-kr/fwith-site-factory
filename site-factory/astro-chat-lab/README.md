# Astro 웹채팅 블로그 실험실

이 폴더는 AstroPaper 35cfa7fbe0b897306d27670d3819e55d5205f3dd의 전체 실행 의존 소스에서 시작한 독립 실험입니다.

- Node 24 / pnpm 11.3.0 / pnpm install --frozen-lockfile
- Astro 정적 출력 / Markdown 게시물 하나
- GitHub Actions에서 Workers Static Assets로 배포
- 고정 계정 workers.dev에 노출 / noindex
- 배포 시각과 실제 Workers 계정 하위 도메인은 Actions 실행의 GET-only 사전검증으로 확인
- 원본 저작권 및 MIT 라이선스는 LICENSE 참조

새 글을 추가할 때는 src/content/posts에 Markdown 파일을 작성한 후 시험 브랜치에 커밋합니다. 원본 템플릿의 릴리스 예시 글은 포함하지 않습니다.
