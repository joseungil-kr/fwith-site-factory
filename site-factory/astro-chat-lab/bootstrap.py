#!/usr/bin/env python3
"""Materialize and localize the pinned, complete AstroPaper project once.

Runs only in the dedicated astro-chat-lab GitHub Actions workspace. No changes
to main, client sites, shared registries, or original upstream sources.
"""
from pathlib import Path
import json
import os
import re
import shutil
import subprocess

PIN = "35cfa7fbe0b897306d27670d3819e55d5205f3dd"
root = Path("site-factory/astro-chat-lab")
source = Path(os.environ["UPSTREAM_DIR"])
actual = subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip()
assert actual == PIN, f"Unexpected AstroPaper revision: {actual}"
assert root.is_dir() and (root / "bootstrap.py").is_file()
assert not (root / "package.json").exists(), "Test source already exists: abort rather than overwrite"

for name in (
    ".gitignore", ".prettierrc", ".prettierignore",
    "LICENSE", "package.json", "pnpm-lock.yaml", "pnpm-workspace.yaml",
    "tsconfig.json", "eslint.config.js",
    "astro.config.ts", "astro-paper.config.ts", "src", "public",
):
    item = source / name
    assert item.exists(), f"Pinned AstroPaper missing {name}"
    target = root / name
    if item.is_dir():
        shutil.copytree(item, target)
    else:
        shutil.copy2(item, target)

# Remove posts from the *copied* template only, not from upstream or client sites.
posts = root / "src/content/posts"
shutil.rmtree(posts)
posts.mkdir(parents=True)

post = """---
title: "웹채팅으로 만든 Astro 블로그 첫 게시물"
description: "GPT 웹채팅에서 Astro 블로그를 구성하고 GitHub Actions와 Cloudflare로 공개하는 실제 실험 기록입니다."
pubDatetime: 2026-10-09T00:00:00+09:00
draft: false
featured: false
tags:
  - Astro
  - 웹채팅
  - 배포실험
---

이 글은 **웹채팅만으로 정적 블로그를 만들고 실제 주소에 게시할 수 있는지** 확인하기 위한 첫 게시물입니다. 사용자의 PC에 개발 프로그램을 설치하는 대신, 연결된 GitHub에 소스를 보관하고 GitHub Actions에서 빌드하며 Cloudflare가 완성된 파일을 제공합니다.

## 이번 실험에서 확인하는 것

첫째, 글의 목록과 본문이 실제 인터넷 주소에서 열리는지 확인합니다. 둘째, 제목과 한국어 문장, 소제목, 목록, 링크, 스타일이 깨지지 않는지 살펴봅니다. 셋째, 존재하지 않는 주소를 요청했을 때 올바른 404 오류를 돌려주는지도 검사합니다.

- **빌드:** Astro가 Markdown 글을 HTML로 변환합니다.
- **공개:** GitHub Actions가 정적 파일을 Cloudflare Workers Static Assets에 배포합니다.
- **검증:** 홈페이지·글 상세·CSS 파일·없는 주소의 HTTP 응답을 검사합니다.

## 목록에서 이 글로 이동하는 방법

[블로그 첫 화면](/)에는 글 목록이 표시됩니다. 목록의 **웹채팅으로 만든 Astro 블로그 첫 게시물** 제목을 선택하면 이 상세 페이지로 이동합니다. 메뉴에서 게시물 목록으로 이동해도 같은 글을 찾을 수 있습니다.

## 정적 블로그란?

정적 블로그는 방문자가 글을 열 때마다 서버에서 데이터베이스를 조회하지 않습니다. 글을 작성한 뒤 미리 만들어 둔 HTML·CSS·JavaScript 파일을 방문자에게 전달합니다. 그래서 운영 구조가 비교적 단순하고, 콘텐츠가 바뀌지 않는 동안 서버에서 매번 글을 조립할 필요가 없습니다.

## 앞으로 글을 추가하는 방식

새 글을 작성할 때는 GitHub 저장소의 \`src/content/posts/\` 아래에 Markdown 파일을 추가합니다. 제목과 날짜, 요약, 태그, 공개 여부를 문서 맨 위에 입력하고 코드를 커밋하면, GitHub Actions를 통해 사이트를 다시 빌드하고 배포할 수 있습니다.

이번 시험에는 **공개 테스트 글을 정확히 한 개만** 남겼으며 검색엔진 색인은 허용하지 않았습니다. 실제 광고나 고객 사이트 운영 기능은 시험 범위에 포함하지 않습니다.
"""
(posts / "webchat-astro-first-post.md").write_text(post, encoding="utf-8")

cfg_path = root / "astro-paper.config.ts"
cfg = cfg_path.read_text(encoding="utf-8")
cfg = cfg.replace('url: "https://astro-paper.pages.dev/"', 'url: process.env.ASTRO_CHAT_SITE_URL ?? "https://astro-chat-lab-qa.invalid/"')
cfg = cfg.replace('title: "AstroPaper"', 'title: "웹채팅 Astro 블로그 실험실"')
cfg = cfg.replace('description: "A minimal, responsive and SEO-friendly Astro blog theme."', 'description: "웹채팅에서 구축하고 Cloudflare에 공개하는 정적 블로그 실험"')
cfg = cfg.replace('author: "Sat Naing"', 'author: "Astro 웹채팅 실험"')
cfg = cfg.replace('profile: "https://satna.ing"', 'profile: ""')
cfg = cfg.replace('lang: "en"', 'lang: "ko"')
cfg = cfg.replace('timezone: "Asia/Bangkok"', 'timezone: "Asia/Seoul"')
cfg = cfg.replace('dynamicOgImage: true', 'dynamicOgImage: false')
cfg = cfg.replace('showArchives: true', 'showArchives: false')
cfg = cfg.replace('enabled: true', 'enabled: false')
cfg = cfg.replace('search: "pagefind"', 'search: false')
cfg = re.sub(r'  socials: \[[\s\S]*?\],\n  shareLinks: \[[\s\S]*?\],', '  socials: [],\n  shareLinks: [],', cfg, count=1)
assert 'lang: "ko"' in cfg and 'search: false' in cfg and 'socials: []' in cfg
cfg_path.write_text(cfg, encoding="utf-8")

astro_path = root / "astro.config.ts"
astro = astro_path.read_text(encoding="utf-8")
astro = astro.replace('locales: ["en"]', 'locales: ["ko"]')
astro = astro.replace('defaultLocale: "en"', 'defaultLocale: "ko"')
assert 'locales: ["ko"]' in astro
astro_path.write_text(astro, encoding="utf-8")

layout_path = root / "src/layouts/Layout.astro"
layout = layout_path.read_text(encoding="utf-8")
needle = '<meta name="description" content={description} />'
assert needle in layout
layout = layout.replace(needle, needle + '\n    <meta name="robots" content="noindex, nofollow" />\n    <link rel="preconnect" href="https://fonts.googleapis.com" />\n    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />\n    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700&display=swap" rel="stylesheet" />')
layout_path.write_text(layout, encoding="utf-8")

theme_path = root / "src/styles/theme.css"
theme = theme_path.read_text(encoding="utf-8")
assert '--font-app: var(--font-google-sans-code);' in theme
theme = theme.replace('--font-app: var(--font-google-sans-code);',
                      '--font-app: "Noto Sans KR", "Apple SD Gothic Neo", "Malgun Gothic", sans-serif;')
theme_path.write_text(theme, encoding="utf-8")

global_path = root / "src/styles/global.css"
global_css = global_path.read_text(encoding="utf-8")
global_css += '\n/* Korean readability and narrow-screen line wrapping. */\nbody { word-break: keep-all; overflow-wrap: anywhere; line-height: 1.75; }\n'
global_path.write_text(global_css, encoding="utf-8")

robots_path = root / "src/pages/robots.txt.ts"
robots_path.write_text("""import type { APIRoute } from "astro";
export const GET: APIRoute = () =>
  new Response("User-agent: *\\nDisallow: /\\n", {
    headers: { "Content-Type": "text/plain; charset=utf-8" },
  });
""", encoding="utf-8")

index_path = root / "src/pages/index.astro"
index = index_path.read_text(encoding="utf-8")
hero = """<section id="hero" class="border-border border-b pt-8 pb-8">
      <h1 class="my-4 text-3xl font-bold leading-snug sm:text-5xl">웹채팅 Astro 블로그 실험실</h1>
      <p class="text-muted-foreground mt-3 leading-8">GPT 웹채팅에서 GitHub에 소스를 저장하고 Cloudflare의 기본 주소에 공개한 실험용 정적 블로그입니다.</p>
      <p class="mt-2">아래 첫 게시물을 선택해 실제 본문과 한글 표시를 확인해 보세요.</p>
    </section>"""
index, n = re.subn(r'<section id="hero"[\s\S]*?</section>', hero, index, count=1)
assert n == 1
index_path.write_text(index, encoding="utf-8")

about = """---
title: "실험 소개"
description: "Astro 웹채팅 블로그 구축 실험 안내"
---

이 사이트는 GPT 웹채팅에서 실제로 블로그를 구축하고 공개할 수 있는지 검증하기 위한 **독립 시험 사이트**입니다. 광고·고객정보·운영 도메인과 연결되지 않습니다.

- 기반 템플릿: [AstroPaper](https://github.com/satnaing/astro-paper)
- 정적 사이트 프레임워크: [Astro](https://astro.build/)
- 호스팅: Cloudflare Workers Static Assets
- 검색엔진 색인: 허용하지 않음

원본 AstroPaper의 MIT 라이선스 고지는 저장소의 LICENSE 파일에 보존되어 있습니다.
"""
(root / "src/content/pages/about.md").write_text(about, encoding="utf-8")

lang = """import type { UIStrings } from "../types";
export default {
  nav: { home:"홈", posts:"게시물", tags:"태그", about:"소개", archives:"보관함", search:"검색" },
  post: { publishedAt:"게시일", updatedAt:"수정일", sharePostIntro:"이 글 공유", sharePostOn:"{{platform}}에 공유", sharePostViaEmail:"이메일로 공유", tagLabel:"태그", backToTop:"맨 위로", goBack:"뒤로", editPage:"글 수정", previousPost:"이전 글", nextPost:"다음 글" },
  pagination: { prev:"이전", next:"다음", page:"페이지" },
  home: { socialLinks:"소셜 링크", featured:"추천 글", recentPosts:"최근 게시물", allPosts:"모든 게시물" },
  footer: { copyright:"저작권", allRightsReserved:"웹채팅 배포 시험용 · 검색 색인 제외" },
  pages: { tagTitle:"태그", tagDesc:"이 태그를 사용한 글", tagsTitle:"태그", tagsDesc:"게시물의 태그", postsTitle:"게시물", postsDesc:"공개된 게시물을 살펴보세요.", archivesTitle:"보관함", archivesDesc:"날짜별 게시물", searchTitle:"검색", searchDesc:"게시물 검색" },
  a11y: { skipToContent:"본문 바로가기", openMenu:"메뉴 열기", closeMenu:"메뉴 닫기", toggleTheme:"테마 전환", searchPlaceholder:"게시물 검색", noResults:"검색 결과 없음", goToPreviousPage:"이전 페이지", goToNextPage:"다음 페이지" },
  notFound: { title:"페이지를 찾을 수 없습니다", message:"요청한 페이지가 없습니다.", goHome:"첫 화면으로" }
} satisfies UIStrings;
"""
(root / "src/i18n/lang/ko.ts").write_text(lang, encoding="utf-8")

(root / "_headers").write_text("/*\\n  X-Robots-Tag: noindex, nofollow\\n", encoding="utf-8")  # provider-specific, not relied on for index control
(root / "public/_headers").write_text("/*\\n  X-Robots-Tag: noindex, nofollow\\n", encoding="utf-8")
(root / "wrangler.jsonc").write_text(json.dumps({
    "name":"astro-chat-lab-qa",
    "compatibility_date":"2026-10-09",
    "workers_dev":True,
    "assets":{"directory":"./dist","html_handling":"auto-trailing-slash","not_found_handling":"404-page"}
}, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
(root / "UPSTREAM_PIN.json").write_text(json.dumps({
    "upstream":"https://github.com/satnaing/astro-paper",
    "revision": PIN,
    "packageManager":"pnpm@11.3.0",
    "node":"24",
    "license":"MIT",
    "posts": ["src/content/posts/webchat-astro-first-post.md"]
}, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
(root / "README.md").write_text("""# Astro 웹채팅 블로그 실험실

이 폴더는 AstroPaper 35cfa7fbe0b897306d27670d3819e55d5205f3dd의 전체 실행 의존 소스에서 시작한 독립 실험입니다.

- Node 24 / pnpm 11.3.0 / pnpm install --frozen-lockfile
- Astro 정적 출력 / Markdown 게시물 하나
- GitHub Actions에서 Workers Static Assets로 배포
- 고정 계정 workers.dev에 노출 / noindex
- 배포 시각과 실제 Workers 계정 하위 도메인은 Actions 실행의 GET-only 사전검증으로 확인
- 원본 저작권 및 MIT 라이선스는 LICENSE 참조

새 글을 추가할 때는 src/content/posts에 Markdown 파일을 작성한 후 시험 브랜치에 커밋합니다. 원본 템플릿의 릴리스 예시 글은 포함하지 않습니다.
""",encoding="utf-8")

assert len(list(posts.rglob("*.md"))) + len(list(posts.rglob("*.mdx"))) == 1
assert (root/"pnpm-lock.yaml").stat().st_size > 10000
assert (root/"LICENSE").read_text(encoding="utf-8").startswith("MIT License")
assert (root/"src/pages/posts/[...slug]/index.astro").is_file()
assert (root/"src/components/Card.astro").is_file()
assert (root/"src/styles/global.css").is_file()
print("AstroPaper pinned full source materialized: one published post, Korean UI, noindex")
