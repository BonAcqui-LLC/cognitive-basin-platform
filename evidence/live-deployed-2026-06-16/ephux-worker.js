// worker.js
var worker_default = {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.hostname === "www.ephux.com") {
      return Response.redirect(`https://ephux.com${url.pathname}${url.search}${url.hash}`, 301);
    }
    const pageMap = /* @__PURE__ */ new Map([
      ["/", "/index.html"],
      ["/privacy", "/privacy.html"],
      ["/support", "/support.html"],
      ["/terms", "/terms.html"],
      ["/refunds", "/refunds.html"]
    ]);
    const normalizedPath = url.pathname === "/" ? "/" : url.pathname.replace(/\/$/, "");
    const mappedPath = pageMap.get(normalizedPath);
    if (mappedPath) {
      const mapped = new URL(request.url);
      mapped.pathname = mappedPath;
      return env.ASSETS.fetch(new Request(mapped, request));
    }
    return env.ASSETS.fetch(request);
  }
};
export {
  worker_default as default
};
//# sourceMappingURL=worker.js.map
