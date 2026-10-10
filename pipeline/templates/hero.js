/* MoveInRate hero: full-screen video background, navbar, tagline pill, headline, CTAs.
   Shared by the report and the dashboard. Needs React, ReactDOM and htm loaded first.
   Usage: mountHero(element, config) — see the config objects in each page. */
(function () {
  const { useState, useEffect, useRef } = React;
  const html = htm.bind(React.createElement);

  const VIDEO = "https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260210_031346_d87182fb-b0af-4273-84d1-c6fd17d6bf0f.mp4";

  // MoveInRate mark: a five-point rating star on a rounded tile
  const Logo = () => html`
    <svg width="30" height="30" viewBox="0 0 28 28" fill="none" aria-hidden="true" className="block">
      <rect x="0.5" y="0.5" width="27" height="27" rx="8" fill="white" fill-opacity="0.12" stroke="white" stroke-opacity="0.35"/>
      <path d="M14 4.5L16.4 10.9L23.2 11.2L17.9 15.4L19.7 22L14 18.2L8.3 22L10.1 15.4L4.8 11.2L11.6 10.9Z" fill="white"/>
    </svg>`;

  const Chevron = ({ open }) => html`
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"
      aria-hidden="true" className=${"block transition-transform " + (open ? "rotate-180" : "")}><path d="m6 9 6 6 6-6"/></svg>`;

  const MenuIcon = () => html`
    <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" aria-hidden="true" className="block">
      <path d="M4 7h16M4 12h16M4 17h16"/></svg>`;

  const CloseIcon = () => html`
    <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" aria-hidden="true" className="block">
      <path d="M6 6l12 12M18 6L6 18"/></svg>`;

  function Navbar({ brand, links, secondary, primary }) {
    const [menu, setMenu] = useState(false);
    const [dropdown, setDropdown] = useState(false);
    const ddRef = useRef(null);

    useEffect(() => {
      const close = (e) => { if (ddRef.current && !ddRef.current.contains(e.target)) setDropdown(false); };
      const esc = (e) => { if (e.key === "Escape") { setDropdown(false); setMenu(false); } };
      document.addEventListener("click", close);
      document.addEventListener("keydown", esc);
      return () => { document.removeEventListener("click", close); document.removeEventListener("keydown", esc); };
    }, []);

    useEffect(() => { document.body.style.overflow = menu ? "hidden" : ""; }, [menu]);

    return html`
      <nav className="relative z-20 w-full bg-transparent px-6 lg:px-[120px] py-[16px] flex items-center justify-between">
        <div className="flex items-center gap-12">
          <a href="#top" className="flex items-center gap-2.5 text-white hover:opacity-80 transition-opacity" aria-label=${brand + " home"}>
            <${Logo} />
            <span className="font-manrope font-bold text-[16px] tracking-[-0.01em] text-white">${brand}</span>
          </a>
          <ul className="hidden lg:flex items-center gap-8 list-none m-0 p-0">
            ${links.map((l) => l.children
              ? html`<li key=${l.label} className="relative" ref=${ddRef}>
                  <button type="button" onClick=${(e) => { e.stopPropagation(); setDropdown(!dropdown); }}
                    aria-expanded=${dropdown} aria-haspopup="true"
                    className="flex items-center gap-1 bg-transparent border-0 p-0 cursor-pointer font-manrope font-medium text-[14px] text-white hover:opacity-80 transition-opacity">
                    ${l.label}<${Chevron} open=${dropdown} />
                  </button>
                  ${dropdown && html`<div role="menu"
                      className="absolute left-0 top-[calc(100%+12px)] min-w-[220px] rounded-[10px] border border-[rgba(164,132,215,0.5)] bg-[rgba(43,35,68,0.92)] backdrop-blur-md p-1.5 shadow-xl">
                    ${l.children.map((c) => html`<a key=${c.label} role="menuitem" href=${c.href} onClick=${() => setDropdown(false)}
                        className="block rounded-[6px] px-3 py-2 font-manrope font-medium text-[14px] text-white hover:bg-white/10">
                        ${c.label}${c.note && html`<span className="block text-[12px] font-normal text-white/60">${c.note}</span>`}</a>`)}
                  </div>`}
                </li>`
              : html`<li key=${l.label}><a href=${l.href} className="font-manrope font-medium text-[14px] text-white hover:opacity-80 transition-opacity">${l.label}</a></li>`)}
          </ul>
        </div>

        <div className="hidden lg:flex items-center gap-3">
          <a href=${secondary.href} target=${secondary.external ? "_blank" : undefined} rel="noopener"
            className="inline-flex items-center bg-white border border-solid border-[#d4d4d4] rounded-[8px] px-4 py-2 font-manrope font-semibold text-[14px] text-[#171717] hover:bg-neutral-100 transition-colors">${secondary.label}</a>
          <a href=${primary.href} target=${primary.external ? "_blank" : undefined} rel="noopener"
            className="inline-flex items-center bg-[#7b39fc] rounded-[8px] px-4 py-2 font-manrope font-semibold text-[14px] text-[#fafafa] shadow-[0_1px_2px_rgba(16,24,40,0.25)] hover:bg-[#8a4ffd] transition-colors">${primary.label}</a>
        </div>

        <button type="button" onClick=${() => setMenu(true)} aria-label="Open menu"
          className="mobile-only lg:hidden bg-transparent border-0 p-1 cursor-pointer"><${MenuIcon} /></button>

        ${menu && html`
          <div className="fixed inset-0 z-50 bg-black flex flex-col px-6 py-[16px]" role="dialog" aria-modal="true" aria-label="Menu">
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-2.5"><${Logo} /><span className="font-manrope font-bold text-[16px] text-white">${brand}</span></span>
              <button type="button" onClick=${() => setMenu(false)} aria-label="Close menu" className="bg-transparent border-0 p-1 cursor-pointer"><${CloseIcon} /></button>
            </div>
            <ul className="list-none m-0 p-0 mt-12 flex flex-col gap-6">
              ${links.flatMap((l) => l.children ? l.children : [l]).map((l) => html`
                <li key=${l.label}><a href=${l.href} onClick=${() => setMenu(false)} className="font-manrope font-medium text-[22px] text-white hover:opacity-80">${l.label}</a></li>`)}
            </ul>
            <div className="mt-auto flex flex-col gap-3 pb-6">
              <a href=${secondary.href} target=${secondary.external ? "_blank" : undefined} rel="noopener" className="text-center bg-white border border-solid border-[#d4d4d4] rounded-[8px] px-4 py-3 font-manrope font-semibold text-[14px] text-[#171717]">${secondary.label}</a>
              <a href=${primary.href} target=${primary.external ? "_blank" : undefined} rel="noopener" onClick=${() => setMenu(false)} className="text-center bg-[#7b39fc] rounded-[8px] px-4 py-3 font-manrope font-semibold text-[14px] text-[#fafafa]">${primary.label}</a>
            </div>
          </div>`}
      </nav>`;
  }

  function Hero(c) {
    const [videoOk, setVideoOk] = useState(true);
    const [before, italic, after] = c.headline;
    return html`
      <section id="top" className="hero-fallback relative min-h-screen w-full overflow-hidden flex flex-col pb-24">
        ${videoOk && html`<video className="absolute inset-0 w-full h-full min-h-screen object-cover" src=${VIDEO}
            autoPlay loop muted playsInline preload="auto" aria-hidden="true" onError=${() => setVideoOk(false)} />`}
        <${Navbar} brand=${c.brand} links=${c.links} secondary=${c.navSecondary} primary=${c.navPrimary} />
        <div className="relative z-10 mt-32 flex flex-col items-center text-center px-6">
          <div className="inline-flex items-center gap-2.5 h-[38px] rounded-[10px] bg-[rgba(85,80,110,0.4)] backdrop-blur-md border border-solid border-[rgba(164,132,215,0.5)] pl-1 pr-3.5">
            <span className="bg-[#7b39fc] rounded-[6px] px-2 py-[5px] font-cabin font-medium text-[14px] leading-none text-white">${c.badge}</span>
            <span className="font-cabin font-medium text-[14px] text-white whitespace-nowrap">${c.taglineShort ? html`<span className="sm:hidden">${c.taglineShort}</span><span className="hidden sm:inline">${c.tagline}</span>` : c.tagline}</span>
          </div>
          <h1 className="font-instrument font-normal text-white text-5xl md:text-7xl lg:text-[96px] leading-[1.1] tracking-[-0.01em] max-w-[1100px] mt-8 mb-0">
            ${before}<em className="italic font-instrument mx-[0.06em] tracking-[0.01em]">${italic}</em>${after}
          </h1>
          <p className="font-inter font-normal text-[18px] leading-[1.6] text-white/70 max-w-[662px] mt-6 mb-0">${c.subtext}</p>
          <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
            <a href=${c.cta1.href} className="inline-flex items-center bg-[#7b39fc] hover:bg-[#8f57fd] transition-colors rounded-[10px] px-6 py-3.5 font-cabin font-medium text-[16px] text-white">${c.cta1.label}</a>
            <a href=${c.cta2.href} target=${c.cta2.external ? "_blank" : undefined} rel="noopener" className="inline-flex items-center bg-[#2b2344] hover:bg-[#3a3058] transition-colors rounded-[10px] px-6 py-3.5 font-cabin font-medium text-[16px] text-[#f6f7f9]">${c.cta2.label}</a>
          </div>
        </div>
      </section>`;
  }

  // Re-mounting reuses the same root, so live pages can re-render the hero with fresh data
  window.mountHero = (el, config) => { (el._heroRoot ||= ReactDOM.createRoot(el)).render(html`<${Hero} ...${config} />`); };
})();
