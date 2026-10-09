/*
 * Minimal, safe posts preview for Decap 3.16.3. No HTML injection,
 * extra dependencies or editable content transformation.
 * Only display same-origin /uploads images and same-origin pending blob assets.
 */
(function () {
  "use strict";

  const cms = window.CMS;
  const h = window.h || (window.React && window.React.createElement);
  if (!cms || typeof cms.registerPreviewTemplate !== "function" || typeof h !== "function") {
    return; // Leave the built-in preview available if the extension cannot register.
  }

  const origin = window.location.origin;

  function publicImageUrl(path) {
    if (typeof path !== "string") return null;
    try {
      const u = new URL(path, origin);
      if (u.origin !== origin || !u.pathname.startsWith("/uploads/")) return null;
      return u.href;
    } catch {
      return null;
    }
  }

  function localAssetUrl(path, getAsset) {
    if (typeof getAsset !== "function") return null;
    try {
      const asset = getAsset(path);
      const result = asset && typeof asset.toString === "function" ? asset.toString() : "";
      if (typeof result === "string" && result.startsWith("blob:" + origin + "/")) return result;
    } catch {
      // In-memory asset unavailable: the public upload path may still be usable.
    }
    return null;
  }

  const surface = {
    fontFamily: '"Noto Sans KR", "Apple SD Gothic Neo", "Malgun Gothic", sans-serif',
    lineHeight: 1.85,
    color: "#1c2634",
    maxWidth: "780px",
    margin: "20px auto",
    padding: "12px 24px",
    overflowWrap: "anywhere",
    wordBreak: "keep-all",
  };

  const imageStyle = {
    width: "auto",
    maxWidth: "100%",
    maxHeight: "600px",
    height: "auto",
    display: "block",
    objectFit: "contain",
    borderRadius: "8px",
  };

  // A safety fallback avoids the browser's broken-image icon; it does not
  // mistake an unsaved in-memory image for a live published asset.
  function imageNode(markdownPath, alt, caption, getAsset, key) {
    const publicUrl = publicImageUrl(markdownPath);
    if (!publicUrl) return h("p", { key, role: "status" }, "허용된 /uploads 이미지 주소가 아닙니다.");
    const preview = localAssetUrl(markdownPath, getAsset) || publicUrl;
    const fallback = "미리보기 이미지가 아직 준비되지 않았습니다. 글 저장 후 다시 열어 확인하세요.";
    return h("figure", { key, style: { margin: "18px 0 24px" } },
      h("img", {
        src: preview,
        alt: alt || "게시물 이미지",
        title: caption || undefined,
        style: imageStyle,
        onError: function (event) {
          const img = event.currentTarget;
          if (!img || !img.dataset) return;
          if (img.dataset.retried !== "1" && img.src !== publicUrl) {
            img.dataset.retried = "1";
            img.src = publicUrl;
            return;
          }
          img.hidden = true;
          if (img.nextSibling) img.nextSibling.hidden = false;
        },
      }),
      h("small", { hidden: true, style: { color: "#93510c", display: "block" } }, fallback),
      caption ? h("figcaption", { style: { color: "#6a7280", fontSize: "0.88rem" } }, caption) : null
    );
  }

  function plainLink(value) {
    if (typeof value !== "string") return null;
    try {
      const u = new URL(value, origin);
      return u.protocol === "https:" && u.origin === origin ? u.href : null;
    } catch {
      return null;
    }
  }

  function textNodes(text, prefix) {
    // Text remains React text nodes; no raw HTML insertion and no permissive sanitizer.
    const nodes = [];
    const rx = /\[([^\]]+)\]\(([^)\s]+)\)|(\*\*([^*]+)\*\*)/g;
    let match, last = 0, i = 0;
    while ((match = rx.exec(text)) !== null) {
      if (match.index > last) nodes.push(text.slice(last, match.index));
      if (match[1] !== undefined) {
        const href = plainLink(match[2]);
        nodes.push(href ? h("a", { key: prefix + "-a" + i, href, target: "_blank",
          rel: "noopener noreferrer" }, match[1]) : match[1]);
      } else {
        nodes.push(h("strong", { key: prefix + "-b" + i }, match[4]));
      }
      last = rx.lastIndex;
      i++;
    }
    if (last < text.length) nodes.push(text.slice(last));
    return nodes.length ? nodes : [text];
  }

  // Markdown-lite display only: the authoritative output is Astro's public page.
  // Images appear inline and paragraphs after images have their own insertion line.
  function renderBody(body, getAsset) {
    const result = [];
    const lines = String(body || "").replace(/\r\n/g, "\n").split("\n");
    let inCode = false, codeLines = [];
    function flushCode(index) {
      if (codeLines.length) {
        result.push(h("pre", { key: "code" + index, style: { padding: "12px",
          background: "#f0f2f5", overflowX: "auto", whiteSpace: "pre-wrap" } },
          h("code", {}, codeLines.join("\n"))));
      }
      codeLines = [];
    }
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();
      if (/^(`{3}|~{3})/.test(line)) {
        if (inCode) flushCode(i);
        inCode = !inCode;
        continue;
      }
      if (inCode) { codeLines.push(lines[i]); continue; }
      if (!line) continue;
      const image = /^!\[([^\]]*)\]\((\S+?)(?:\s+"([^"]*)")?\)$/.exec(line);
      if (image) {
        result.push(imageNode(image[2], image[1], image[3], getAsset, "image" + i));
        continue;
      }
      const heading = /^(#{2,6})\s+(.+)$/.exec(line);
      if (heading) {
        const size = Math.max(17, 26 - (heading[1].length - 2) * 2);
        result.push(h("div", { key: "heading" + i, role: "heading",
          "aria-level": heading[1].length, style: {
            fontSize: size + "px", fontWeight: 700, margin: "20px 0 10px",
          } }, ...textNodes(heading[2], "h" + i)));
        continue;
      }
      const list = /^[-*+]\s+(.+)$/.exec(line);
      if (list) {
        result.push(h("p", { key: "bullet" + i, style: { margin: "6px 0 6px 14px" } },
          "• ", ...textNodes(list[1], "l" + i)));
        continue;
      }
      result.push(h("p", { key: "paragraph" + i, style: { margin: "12px 0" } },
        ...textNodes(line, "p" + i)));
    }
    if (inCode) flushCode(lines.length);
    return result.length ? result : [h("p", { key: "empty" }, "본문을 입력하면 여기에 표시됩니다.")];
  }

  function PostsPreview(props) {
    const entry = props.entry;
    const data = entry && entry.get ? entry.get("data") : null;
    const get = function (name) {
      if (data && typeof data.get === "function") return data.get(name);
      return undefined;
    };
    const title = String(get("title") || "제목을 입력하세요");
    const description = String(get("description") || "");
    const date = get("pubDatetime");

    return h("article", { style: surface },
      h("h1", { style: { fontSize: "28px", lineHeight: 1.35, marginBottom: "8px" } }, title),
      description ? h("p", { style: { color: "#697386" } }, description) : null,
      date ? h("p", { style: { fontSize: "13px", color: "#697386" } }, String(date)) : null,
      ...renderBody(get("body"), props.getAsset)
    );
  }

  cms.registerPreviewTemplate("posts", PostsPreview);
})();
