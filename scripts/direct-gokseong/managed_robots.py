"""Exact observed managed robots composition. Never strips or rewrites policy.

This accepts only the approved source bytes, or one fixed Cloudflare prefix
followed by those exact bytes. A provider prefix change fails closed for review.
"""
import hashlib
import re
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser

PREFIX_SHA256 = '3073d1e371afb3271c7666148766fedc5145f7d8440f7114062db79b7bd58add'
PREFIX_BYTES = 2676
BEGIN = b'# BEGIN Cloudflare Managed content'
END = b'# END Cloudflare Managed Content'
SEARCH_AGENTS = ('*', 'Googlebot', 'Yeti', 'bingbot', 'IndexNow')
MANAGED_PREFIX = b"# As a condition of accessing this website, you agree to abide by the following\n# content signals:\n\n# (a)  If a Content-Signal = yes, you may collect content for the corresponding\n#      use.\n# (b)  If a Content-Signal = no, you may not collect content for the\n#      corresponding use.\n# (c)  If the website operator does not include a Content-Signal for a\n#      corresponding use, the website operator neither grants nor restricts\n#      permission via Content-Signal with respect to the corresponding use.\n\n# The content signals and their meanings are:\n\n# search:   building a search index and providing search results (e.g., returning\n#           hyperlinks and short excerpts from your website's contents). Search does not\n#           include providing AI-generated search summaries.\n# ai-input: inputting content into one or more AI models (e.g., retrieval\n#           augmented generation, grounding, or other real-time taking of content for\n#           generative AI search answers).\n# ai-train: training or fine-tuning AI models.\n# use:      how AI systems may consume the content (immediate, reference, or full).\n\n# ANY RESTRICTIONS EXPRESSED VIA CONTENT SIGNALS ARE EXPRESS RESERVATIONS OF\n# RIGHTS UNDER ARTICLE 4 OF THE EUROPEAN UNION DIRECTIVE 2019/790 ON COPYRIGHT\n# AND RELATED RIGHTS IN THE DIGITAL SINGLE MARKET.\n\n# BEGIN Cloudflare Managed content\n\n\nUser-agent: *\nContent-Signal: search=yes,ai-train=no,use=reference\nAllow: /\n\n# Training crawlers\nUser-agent: Amazonbot\nDisallow: /\n\nUser-agent: Applebot-Extended\nDisallow: /\n\nUser-agent: Bytespider\nDisallow: /\n\nUser-agent: CCBot\nDisallow: /\n\nUser-agent: ClaudeBot\nDisallow: /\n\nUser-agent: Diffbot\nDisallow: /\n\nUser-agent: Google-Extended\nDisallow: /\n\nUser-agent: GPTBot\nDisallow: /\n\nUser-agent: omgili\nDisallow: /\n\nUser-agent: anthropic-ai\nDisallow: /\n\nUser-agent: Claude-Web\nDisallow: /\n\nUser-agent: cohere-ai\nDisallow: /\n\nUser-agent: MistralAI-Training\nDisallow: /\n\nUser-agent: meta-externalagent\nDisallow: /\n\nUser-agent: GoogleOther\nDisallow: /\n\nUser-agent: Baiduspider\nDisallow: /\n\nUser-agent: PetalBot\nDisallow: /\n\nUser-agent: AwarioSmartBot\nUser-agent: AwarioRssBot\nDisallow: /\n\nUser-agent: Google-CloudVertexBot\nDisallow: /\n\nUser-agent: QualifiedBot\nDisallow: /\n\nUser-agent: Cotoyogi\nDisallow: /\n\nUser-agent: ICC-Crawler\nDisallow: /\n\nUser-agent: atlassian-bot\nDisallow: /\n\nUser-agent: FishBot\nDisallow: /\n\nUser-agent: BorderxBot\nDisallow: /\n\nUser-agent: NavuBot\nDisallow: /\n\nUser-agent: SemrushBot-SWA\nDisallow: /\n\nUser-agent: WARDBot\nDisallow: /\n\nUser-agent: magpie-crawler\nDisallow: /\n\nUser-agent: KimiBot\nDisallow: /\n\nUser-agent: CitibotSiteCrawler\nDisallow: /\n\n# END Cloudflare Managed Content\n\n"


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def require(ok, code):
    if not ok:
        raise ValueError(code)


def verify(body, expected_source_sha256, origin, sitemap_urls):
    require(type(body) is bytes, 'robots_bytes_required')
    require(type(origin) is str and re.fullmatch(r'https://[a-z0-9-]+[.]fwith[.]kr', origin), 'robots_origin_invalid')
    require(type(expected_source_sha256) is str and re.fullmatch('[0-9a-f]{64}', expected_source_sha256), 'robots_source_digest_invalid')
    source=('User-agent: *\nAllow: /\nSitemap: '+origin+'/sitemap-index.xml\n').encode('ascii')
    require(digest(source)==expected_source_sha256, 'robots_source_contract_mismatch')
    require(type(sitemap_urls) is list and sitemap_urls and len(sitemap_urls)==len(set(sitemap_urls)), 'robots_sitemap_scope_invalid')
    require(all(type(url) is str and url.startswith(origin+'/') and urlsplit(url).netloc==urlsplit(origin).netloc and not urlsplit(url).query and not urlsplit(url).fragment for url in sitemap_urls), 'robots_sitemap_scope_invalid')
    require(origin+'/' in sitemap_urls, 'robots_home_scope_required')
    managed=body!=source
    if managed:
        require(len(body)==PREFIX_BYTES+len(source), 'robots_composite_length_mismatch')
        require(body.count(BEGIN)==1 and body.count(END)==1 and body.index(BEGIN)<body.index(END), 'robots_managed_marker_mismatch')
        prefix=body[:PREFIX_BYTES]
        require(len(MANAGED_PREFIX)==PREFIX_BYTES and digest(MANAGED_PREFIX)==PREFIX_SHA256, 'robots_pinned_prefix_invalid')
        require(prefix==MANAGED_PREFIX and digest(prefix)==PREFIX_SHA256, 'robots_managed_prefix_mismatch')
        require(body[PREFIX_BYTES:]==source, 'robots_source_suffix_mismatch')
    else:
        require(BEGIN not in body and END not in body, 'robots_plain_marker_forbidden')
    text=body.decode('ascii')
    sitemaps=[line.split(':',1)[1].strip() for line in text.splitlines() if line.lower().startswith('sitemap:')]
    require(sitemaps==[origin+'/sitemap-index.xml'], 'robots_sitemap_mismatch')
    parser=RobotFileParser();parser.parse(text.splitlines())
    checked=sorted(set(sitemap_urls+[origin+'/robots.txt',origin+'/sitemap-index.xml',origin+'/sitemap-0.xml']))
    require(all(parser.can_fetch(agent,url) for agent in SEARCH_AGENTS for url in checked), 'robots_search_crawler_blocked')
    if managed:
        signals=[line for line in text.splitlines() if line.lower().startswith('content-signal:')]
        require(signals==['Content-Signal: search=yes,ai-train=no,use=reference'], 'robots_content_signal_mismatch')
        require(all(not parser.can_fetch(agent,origin+'/') for agent in ('GPTBot','Google-Extended','Baiduspider','PetalBot')), 'robots_managed_policy_mismatch')
    return dict(state='exact_managed_composite_verified' if managed else 'exact_source_robots_verified',
                rawBodySha256=digest(body),rawBodyBytes=len(body),sourceSuffixSha256=expected_source_sha256,
                sourceSuffixBytes=len(source),managedPrefixSha256=PREFIX_SHA256 if managed else None,
                managedPrefixBytes=PREFIX_BYTES if managed else 0,managedComposites=1 if managed else 0,
                searchAgentsChecked=list(SEARCH_AGENTS),checkedUrls=checked,rawBodyUnmodified=True)


def verify_headers(headers):
    content_types=[value for key,value in headers.items() if key.lower()=='content-type']
    require(len(content_types)==1 and re.fullmatch(r'text/plain(?:[ \t]*;[ \t]*charset=[ \t]*(?:utf-8|"utf-8"))?', content_types[0].strip(' \t'), re.I), 'robots_content_type_mismatch')
    require(not any(value.strip() for key,value in headers.items() if key.lower()=='cf-mitigated'), 'robots_challenge_forbidden')
    tags=','.join(value for key,value in headers.items() if key.lower()=='x-robots-tag')
    require(not re.search(r'\b(noindex|nofollow|none)\b',tags,re.I), 'robots_header_blocks_search')

