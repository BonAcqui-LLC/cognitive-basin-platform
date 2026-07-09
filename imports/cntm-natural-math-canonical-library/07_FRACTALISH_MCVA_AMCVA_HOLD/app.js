const atlasTags = [
  "Lichtenberg figure",
  "River delta network",
  "Solidification dendrites",
  "Lightning scar / fulgurite",
  "Vascular tree",
  "Root / mycelium network",
  "Fracture surface",
  "Road crack network",
  "Erosion front",
];

const domainCards = [
  {
    title: "Roads and public works",
    body: "Surface cracking, branching, patch boundaries, and failure topology can become open morphology cues for maintenance prioritization.",
  },
  {
    title: "Fracture and materials failure",
    body: "Breakage often remembers load history, impurity, route-to-failure, and local stress concentration.",
  },
  {
    title: "River deltas and drainage",
    body: "Landscape branching may preserve memory about flow, sediment, constraint, and channel competition.",
  },
  {
    title: "Roots and mycelium",
    body: "Exploratory growth under local constraint is a natural target for morphology and Natural Math comparison.",
  },
  {
    title: "Batteries and dendrites",
    body: "Electrochemical branching can be treated as process memory written into failure structure.",
  },
  {
    title: "Manufacturing and lithography",
    body: "Morphology-first inspection may reveal subtle process drift before obvious defects dominate.",
  },
  {
    title: "Healing and repair",
    body: "Scars and closure patterns may preserve evidence about damage, repair cost, and constraint.",
  },
  {
    title: "Research-only biomedical morphology",
    body: "Potentially important, but public framing should remain cautious, non-diagnostic, and explicitly research-only.",
  },
  {
    title: "Geometry interaction cases",
    body: "The workbench should quantify where branching mixes with circles, grids, lattices, waves, lamination, or capture artifacts instead of forcing a single reading.",
  },
];

const books = [
  {
    title: "Volume I - The Writing in the Shape of Things",
    body: "The discovery journey and the birth of Morphological Memory Theory.",
  },
  {
    title: "Volume II - The First Language of Form",
    body: "The MCVA/AMCVA atlas, operators, negative regimes, and morphology hashes.",
  },
  {
    title: "Volume III - The Green Lightning",
    body: "Life, photosynthesis, medicine, evolution, healing, and the question: why fractals?",
  },
  {
    title: "Volume IV - The Machine That Learned to See",
    body: "Machine-native vision, InfinitySight, robotics, AI perception, and morphology-first sensing.",
  },
];

const archiveLinks = [
  {
    title: "Fractalish Commons",
    body: "The open upload-and-analysis portal for morphology traces, AMCVA counterexamples, HOLD cases, and cross-domain comparison exports.",
    href: "/commons",
  },
  {
    title: "Reference Library",
    body: "Synthetic anchors, proof-positive examples, proof-negative controls, and HOLD cases with trace files attached.",
    href: "/library",
  },
  {
    title: "The Recovery Wake Is the Evidence",
    body: "A Fractalish research note on post-bifurcation recovery signatures: pressure, split, turbulent wake, semi-recovery, and the downstream memory marks a constraint may leave behind.",
    href: "/research/recovery-wake",
  },
  {
    title: "MCVA / AMCVA Atlas",
    body: "The public atlas layer: morphology examples, boundary cases, descriptor tags, source notes, and the growing language for signal, non-signal, and justified uncertainty.",
    href: "/archive/mcva-amcva-atlas",
  },
  {
    title: "Morphological Memory Paper",
    body: "The core thesis paper on why form may preserve partial evidence of process, constraint, damage, healing, and boundary history without pretending that every shape has a single readable cause.",
    href: "/archive/morphological-memory-paper",
  },
  {
    title: "First Life Archive",
    body: "A visual and conceptual seed archive around early branching, green-lightning imagery, first visible contact, and the recurring intuition that life writes itself into structure before it writes itself into language.",
    href: "/archive/first-life-archive",
  },
  {
    title: "Machine-Native Vision",
    body: "A future-facing dossier on morphology-first sensing, machine-native perception, and the idea that systems may learn to emit morphology-bearing tokens before they reconstruct human-style pictures.",
    href: "/archive/machine-native-vision",
  },
  {
    title: "Evidence Library",
    body: "A working collection of examples, demos, notes, and comparison lanes showing where morphology seems to preserve process and where caution, AMCVA, or HOLD should block over-reading.",
    href: "/archive/evidence-library",
  },
  {
    title: "Book Notes",
    body: "Working notes for the Fractalish book sequence: discovery story, vocabulary formation, negative atlas, machine vision, and the long attempt to make this worldview legible without overclaiming.",
    href: "/archive/book-notes",
  },
];

function fillTokenList(id, items) {
  const node = document.getElementById(id);
  if (!node) return;
  node.innerHTML = items.map((item) => `<span>${item}</span>`).join("");
}

function fillCardGrid(id, items, className) {
  const node = document.getElementById(id);
  if (!node) return;
  node.innerHTML = items
    .map(
      (item) => `
        <article class="${className}">
          <h3>${item.title}</h3>
          <p>${item.body}</p>
        </article>
      `
    )
    .join("");
}

function fillArchive(id, items) {
  const node = document.getElementById(id);
  if (!node) return;
  node.innerHTML = items
    .map(
      (item) => `
        <a class="archive-card" href="${item.href}">
          <h3>${item.title}</h3>
          <p>${item.body}</p>
        </a>
      `
    )
    .join("");
}

function initNavigation() {
  const button = document.querySelector(".menu-toggle");
  const nav = document.getElementById("site-nav");
  if (!button || !nav) return;

  button.addEventListener("click", () => {
    const expanded = button.getAttribute("aria-expanded") === "true";
    button.setAttribute("aria-expanded", String(!expanded));
    nav.classList.toggle("is-open", !expanded);
  });

  nav.querySelectorAll("a").forEach((link) => {
    link.addEventListener("click", () => {
      button.setAttribute("aria-expanded", "false");
      nav.classList.remove("is-open");
    });
  });
}

function initReveal() {
  const nodes = document.querySelectorAll(".reveal");
  if (!("IntersectionObserver" in window)) {
    nodes.forEach((node) => node.classList.add("is-visible"));
    return;
  }

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.14 }
  );

  nodes.forEach((node) => observer.observe(node));
}

function initParallax() {
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

  const update = () => {
    const hero = document.getElementById("hero");
    if (!hero) return;
    const shift = Math.min(window.scrollY * 0.08, 36);
    hero.style.setProperty("--hero-shift", `${shift}px`);
  };

  update();
  window.addEventListener("scroll", update, { passive: true });
}

fillTokenList("atlas-tags", atlasTags);
fillCardGrid("domain-grid", domainCards, "domain-card");
fillCardGrid("book-series", books, "book-card");
fillArchive("archive-links", archiveLinks);
initNavigation();
initReveal();
initParallax();
