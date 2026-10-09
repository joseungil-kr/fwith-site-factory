import type { UIStrings } from "../types";
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
