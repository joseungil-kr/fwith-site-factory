# blog.fwith.kr

꽃이랑의 전국 꽃배달 블로그입니다. 지역, 근조, 축하 주제의 검토 완료 안내를 게시합니다.

## Local verification

```sh
corepack pnpm install --frozen-lockfile
SITE_URL=https://blog-fwith-guide-qa.joseungil.workers.dev SITE_INDEXABLE=false SITE_FACTORY_REVISION=<40-char-sha> pnpm run build
python scripts/qa_static.py
```

이 설치는 `satnaing/astro-paper@35cfa7fbe0b897306d27670d3819e55d5205f3dd`를 기반으로 하며, 원본 MIT 라이선스는 [LICENSE](./LICENSE)에 보존되어 있습니다. 자세한 원본·수정 파일 구분은 `upstream-provenance.json`을 확인하세요.

공개 검증 전에는 noindex 상태를 유지합니다. 이 저장소 변경만으로 production 배포, 도메인 연결, IndexNow 제출을 수행하지 않습니다.
