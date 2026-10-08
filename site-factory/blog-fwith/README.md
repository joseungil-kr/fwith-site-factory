# blog.fwith.kr

꽃이랑의 전국 꽃배달 블로그입니다. 지역, 근조, 축하 주제의 검토 완료 안내를 게시합니다.

## Local verification

```sh
corepack pnpm install --frozen-lockfile
export SITE_URL=https://blog-fwith-guide-qa.joseungil.workers.dev
export SITE_INDEXABLE=false
export SITE_FACTORY_REVISION=<40-char-sha>
pnpm run build
python scripts/qa_static.py
```

이 설치는 `satnaing/astro-paper@35cfa7fbe0b897306d27670d3819e55d5205f3dd`를 기반으로 하며, 원본 MIT 라이선스는 [LICENSE](./LICENSE)에 보존되어 있습니다. 자세한 원본·수정 파일 구분은 `upstream-provenance.json`을 확인하세요.

공개 검증 전에는 noindex 상태를 유지합니다. 정적 QA는 현재 모든 HTML route의 canonical origin·noindex revision meta, robots, header, sitemap origin과 선택된 정적 자산을 확인합니다. 일반 내부 링크 집합, canonical exact path 전체, Pagefind/OG 자산의 hosted HTTP 응답은 staging hosted QA에서 별도로 확인해야 합니다.

이 저장소 변경만으로 production 배포, 도메인 연결, IndexNow 제출을 수행하지 않습니다.
