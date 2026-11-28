<script setup>
// 화면에 나오는 회차·소개는 모두 site.json에서 온다 (tools/build_data.py가 작업 공간 원천 파일로 만든다).
// 꾸밈 그림은 public/art/ (tools/make_art.py가 Codex 원본으로 만든다).
import { ref, computed, watchEffect } from 'vue'
import site from './data/site.json'
import Named from './components/Named.vue'
import EpisodeCard from './components/EpisodeCard.vue'
import CoverRibbon from './components/CoverRibbon.vue'

const { profile } = site
const en = profile.en

// ---------- 언어 ----------
// ?lang=ko|en > 방문자가 직접 고른 값(localStorage) > 브라우저 언어 설정 (한국어면 ko, 그 밖은 en)
function initialLang() {
  const q = new URLSearchParams(location.search).get('lang')
  if (q === 'ko' || q === 'en') return q
  try {
    const saved = localStorage.getItem('lang')
    if (saved === 'ko' || saved === 'en') return saved
  } catch {}
  const langs = navigator.languages?.length ? navigator.languages : [navigator.language || '']
  return langs.some((l) => l.toLowerCase().startsWith('ko')) ? 'ko' : 'en'
}
const lang = ref(initialLang())
const ko = computed(() => lang.value === 'ko')
function setLang(l) {
  lang.value = l
  try {
    localStorage.setItem('lang', l)
  } catch {}
  window.scrollTo({ top: 0 })
}

// 화면 글씨. 한국어는 원래 문구, 영어는 프로필.md "영문 인스타"와 그 번역
const T = {
  ko: {
    name: profile.name,
    bio: profile.bio,
    insta: profile.instagram,
    other: en.instagram,
    heroArt: '멍이와 댕이 하이파이브',
    instaBtn: '인스타그램에서 보기',
    otherBtn: '영어판 인스타그램',
    duo: ['멍이', '댕이'],
    duoSub: '동갑인데 키는 18cm 차이',
    startHead: ['처음 오셨다면', '여기부터'],
    startBtn: '첫 편 보기',
    see: (s) => `${s} 보기`,
    all: '전체 회차',
    allSub: (n) => `올린 순서대로 ${n}편`,
    bye: '손 흔드는 멍이와 댕이',
    footInsta: '인스타그램',
    footOther: '영어판',
    copy: '© 멍댕툰',
    switchTo: 'EN',
    switchLabel: 'Switch to English',
  },
  en: {
    name: en.name,
    bio: en.bio,
    insta: en.instagram,
    other: profile.instagram,
    heroArt: 'Meong and Daeng high-five',
    instaBtn: 'Read on Instagram',
    otherBtn: 'Korean originals',
    duo: ['Meong', 'Daeng'],
    duoSub: 'Same age, 18cm apart',
    startHead: ['New here?', 'Start here'],
    startBtn: 'Read the first one',
    see: (s) => `Read ${s}`,
    all: 'All comics',
    allSub: (n) => `${n} so far, in upload order`,
    soonHead: 'English comics are on the way',
    soonText: "We're translating our comics into English. Follow us to catch the first one.",
    soonBtn: 'Follow on Instagram',
    bye: 'Meong and Daeng waving',
    footInsta: 'Instagram',
    footOther: 'Korean originals',
    copy: '© MeongDaeng Comics',
    switchTo: '한국어',
    switchLabel: '한국어로 보기',
  },
}
const t = computed(() => T[lang.value])

watchEffect(() => {
  document.documentElement.lang = lang.value
  document.title = t.value.name
})

// 회차: 한국어 페이지는 한국 계정 회차, 영어 페이지는 영문 계정에 올린 영문판
const episodes = computed(() => (ko.value ? site.episodes : site.episodes_en || []))
// 띠는 꾸밈이라 영문판이 적을 때는 한국어 표지를 그대로 흘린다
const ribbon = computed(() => (episodes.value.length >= 6 ? episodes.value : site.episodes))

// "멍댕툰 | 게이커플툰" → 로고(멍·댕을 이름 색으로)와 꼬리 글씨.
// 영어 "MeongDaeng Comics | Korean Gay Couple" → 로고 두 줄 MeongDaeng / Comics
const logoParts = computed(() => t.value.name.split('|').map((s) => s.trim()))
const tagline = computed(() => logoParts.value[1] || '')
const logoLines = computed(() => {
  const mark = logoParts.value[0]
  if (ko.value) return [[...mark].map((c) => ({ c, cls: { 멍: 'meong', 댕: 'daeng' }[c] || 'ink' }))]
  const [word, ...rest] = mark.split(' ')
  const colored = [...word].map((c, i) => ({ c, cls: i < 5 ? 'meong' : i < 10 ? 'daeng' : 'ink' }))
  return rest.length ? [colored, [...rest.join(' ')].map((c) => ({ c, cls: 'ink' }))] : [colored]
})

// 게시글 링크가 아직 없으면 그 언어 계정의 인스타 프로필로 보낸다
const hrefOf = (ep) => ep.link || t.value.insta.url

const start = computed(() => episodes.value.find((e) => e.num === site.start))

// 인물 소개. 툰에 실제로 나온 말만 쓴다 (업로드한 회차, characters/ 인물 파일 "공개된 정보" 표).
// 자막: 005 12장 자연 다큐 자막 "대형견 (188cm)". 말풍선: 017 4장 멍이, 11장 댕이 대사.
// 소개: 사용자 문구 (2026-11-27). 영어는 그 번역 (이름 Meong·Daeng, direction.md "영문판")
const CHARS = [
  {
    key: 'meong',
    art: '/art/meong.webp',
    ko: { name: '멍이', tag: '대형견 (188cm)', quote: '아닌데 멋있는 건데', narr: '늘 남자다운 늑대가 되고 싶어 하지만 실상은...' },
    en: { name: 'Meong', tag: 'Big puppy (188cm)', quote: "Nuh-uh, it's cool!", narr: 'Always wants to be a manly wolf, but in reality...' },
  },
  {
    key: 'daeng',
    art: '/art/daeng.webp',
    ko: { name: '댕이', tag: '소형견 (170cm)', quote: '이게 늑대 맞아?', narr: '늘 본인은 귀엽지\u00a0않다고 주장하는데...' },
    en: { name: 'Daeng', tag: 'Small puppy (170cm)', quote: 'Is that a wolf?', narr: "Always insists he's not cute, but..." },
  },
]
const chars = computed(() => CHARS.map((c) => ({ key: c.key, art: c.art, ...c[lang.value] })))

const TILTS = [-2, 1.5, -1, 2, -1.5, 1]
const tilt = (i) => TILTS[i % TILTS.length]
const dot = (d) => d.replaceAll('-', '.')

// 첫 화면 그림을 누르면 둘이 통 튀고 하트가 터진다
const HEARTS = ['heart-pink', 'heart-blue', 'paw-pink', 'paw-blue', 'star']
const bursts = ref([])
const boing = ref(false)
let burstId = 0
function cheer() {
  boing.value = false
  requestAnimationFrame(() => (boing.value = true))
  const id = ++burstId
  const parts = Array.from({ length: 10 }, (_, i) => {
    const angle = (Math.PI * 2 * i) / 10 + Math.random() * 0.4
    const dist = 120 + Math.random() * 90
    return {
      src: `art/sticker-${HEARTS[i % HEARTS.length]}.webp`,
      x: Math.cos(angle) * dist,
      y: Math.sin(angle) * dist - 40,
      r: Math.random() * 80 - 40,
    }
  })
  bursts.value.push({ id, parts })
  setTimeout(() => (bursts.value = bursts.value.filter((b) => b.id !== id)), 1100)
}
</script>

<template>
  <!-- ---------- 첫 화면 ---------- -->
  <header class="hero">
    <button class="lang-switch" type="button" :aria-label="t.switchLabel" @click="setLang(ko ? 'en' : 'ko')">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
        <circle cx="12" cy="12" r="9" />
        <path d="M3 12h18M12 3c2.8 3 2.8 15 0 18M12 3c-2.8 3-2.8 15 0 18" />
      </svg>
      {{ t.switchTo }}
    </button>
    <div class="floaters" aria-hidden="true">
      <img class="f f1" src="/art/sticker-heart-pink.webp" alt="" />
      <img class="f f2" src="/art/sticker-paw-blue.webp" alt="" />
      <img class="f f3" src="/art/sticker-star.webp" alt="" />
      <img class="f f4" src="/art/sticker-bone.webp" alt="" />
      <img class="f f5" src="/art/sticker-heart-blue.webp" alt="" />
      <img class="f f6" src="/art/sticker-cloud.webp" alt="" />
      <img class="f f7" src="/art/sticker-paw-pink.webp" alt="" />
      <img class="f f8" src="/art/sticker-rainbow.webp" alt="" />
    </div>

    <div class="hero-inner">
      <button class="hero-art" type="button" :aria-label="t.heroArt" @click="cheer">
        <span class="halo" aria-hidden="true"></span>
        <img :class="{ boing }" src="/art/hero.webp" alt="" width="1100" height="1100" @animationend="boing = false" />
        <span v-for="b in bursts" :key="b.id" class="burst" aria-hidden="true">
          <img
            v-for="(p, i) in b.parts"
            :key="i"
            :src="p.src"
            alt=""
            :style="{ '--x': `${p.x}px`, '--y': `${p.y}px`, '--r': `${p.r}deg` }"
          />
        </span>
      </button>

      <div class="hero-text">
        <h1 :key="lang" class="logo" :class="{ en: !ko }" :aria-label="t.name">
          <span v-for="(line, l) in logoLines" :key="l" class="logo-line">
            <span
              v-for="(p, i) in line"
              :key="i"
              :class="p.cls"
              :style="{ animationDelay: `${150 + (l * 10 + i) * (ko ? 120 : 45)}ms` }"
              aria-hidden="true"
              >{{ p.c === ' ' ? ' ' : p.c }}</span
            >
          </span>
        </h1>
        <p v-if="tagline" class="tagline">{{ tagline }}</p>
        <div class="bio">
          <p v-for="line in t.bio" :key="line"><Named :text="line" /></p>
        </div>
        <nav class="cta">
          <a class="btn pink" :href="t.insta.url" target="_blank" rel="noopener">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" aria-hidden="true">
              <rect x="3" y="3" width="18" height="18" rx="5.5" />
              <circle cx="12" cy="12" r="4.2" />
              <circle cx="17.4" cy="6.6" r="1.1" fill="currentColor" stroke="none" />
            </svg>
            {{ t.instaBtn }}
          </a>
          <a v-if="ko" class="btn blue" :href="profile.youtube.url" target="_blank" rel="noopener">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <rect x="2" y="5" width="20" height="14" rx="4.5" fill="currentColor" />
              <path d="M10 9.2v5.6l4.8-2.8z" fill="#4f6e93" />
            </svg>
            유튜브 쇼츠 보기
          </a>
          <a v-else class="btn blue" :href="t.other.url" target="_blank" rel="noopener">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" aria-hidden="true">
              <rect x="3" y="3" width="18" height="18" rx="5.5" />
              <circle cx="12" cy="12" r="4.2" />
              <circle cx="17.4" cy="6.6" r="1.1" fill="currentColor" stroke="none" />
            </svg>
            {{ t.otherBtn }}
          </a>
        </nav>
        <p v-if="ko" class="other-insta">
          <a :href="t.other.url" target="_blank" rel="noopener">{{ t.otherBtn }} {{ t.other.handle }}</a>
        </p>
      </div>
    </div>
  </header>

  <div class="ribbons">
    <CoverRibbon :episodes="ribbon" color="pink" />
    <CoverRibbon :episodes="[...ribbon].reverse()" color="blue" reverse />
  </div>

  <main>
    <!-- ---------- 멍이 × 댕이 ---------- -->
    <section class="wrap duo">
      <div v-reveal class="duo-head">
        <h2><span class="meong">{{ t.duo[0] }}</span> × <span class="daeng">{{ t.duo[1] }}</span></h2>
        <p class="sub duo-sub">{{ t.duoSub }}</p>
      </div>
      <div class="duo-grid" :class="{ en: !ko }">
        <article v-for="(c, i) in chars" :key="c.key" v-reveal="i * 120" class="char" :class="c.key">
          <p class="bubble">{{ c.quote }}</p>
          <img class="char-art" :src="c.art" :alt="c.name" width="1100" height="1100" loading="lazy" />
          <h3 class="char-name">{{ c.name }}</h3>
          <p class="tag">{{ c.tag }}</p>
          <p class="narr"><Named :text="c.narr" /></p>
        </article>
      </div>
    </section>

    <!-- ---------- 처음 오셨다면 ---------- -->
    <section v-if="start" class="wrap start">
      <div v-reveal class="start-card">
        <img class="start-mascot" src="/art/start.webp" alt="" width="1100" height="1100" loading="lazy" />
        <div class="start-text">
          <h2>{{ t.startHead[0] }}<br />{{ t.startHead[1] }}</h2>
          <p class="start-title"><Named :text="start.title" /></p>
          <p class="start-date">{{ dot(start.date) }}</p>
          <a class="btn pink" :href="hrefOf(start)" target="_blank" rel="noopener">{{ t.startBtn }}</a>
        </div>
        <a class="start-cover" :href="hrefOf(start)" target="_blank" rel="noopener" :aria-label="t.see(start.title)">
          <img :src="start.cover" alt="" width="540" height="675" />
        </a>
      </div>
    </section>

    <!-- ---------- 전체 회차 ---------- -->
    <!-- 영어 페이지인데 영문판을 아직 안 올렸으면: 곧 나온다는 카드 -->
    <section v-if="!episodes.length" class="wrap start">
      <div v-reveal class="start-card soon">
        <img class="start-mascot" src="/art/episodes.webp" alt="" width="1100" height="733" loading="lazy" />
        <div class="start-text">
          <h2>{{ t.soonHead }}</h2>
          <p class="soon-text">{{ t.soonText }}</p>
          <a class="btn pink" :href="t.insta.url" target="_blank" rel="noopener">{{ t.soonBtn }}</a>
        </div>
      </div>
    </section>

    <section v-else class="wrap block">
      <div class="head">
        <div v-reveal>
          <h2>{{ t.all }}</h2>
          <p class="sub">{{ t.allSub(episodes.length) }}</p>
        </div>
        <img v-reveal="120" class="mascot wide" src="/art/episodes.webp" alt="" width="1100" height="733" loading="lazy" />
      </div>
      <div class="grid">
        <EpisodeCard
          v-for="(ep, i) in episodes"
          :key="ep.num"
          v-reveal="(i % 4) * 70"
          :ep="ep"
          :href="hrefOf(ep)"
          :tilt="tilt(i)"
        />
      </div>
    </section>
  </main>

  <!-- ---------- 꼬리 ---------- -->
  <footer class="foot">
    <div class="foot-inner">
      <img v-reveal class="bye" src="/art/bye.webp" :alt="t.bye" width="1100" height="1100" loading="lazy" />
      <p class="logo small" :class="{ en: !ko }" :aria-label="logoParts[0]">
        <span v-for="(line, l) in logoLines" :key="l" class="logo-line">
          <span v-for="(p, i) in line" :key="i" :class="p.cls" aria-hidden="true">{{ p.c === ' ' ? ' ' : p.c }}</span>
        </span>
      </p>
      <nav class="cta foot-cta">
        <a class="btn pink" :href="t.insta.url" target="_blank" rel="noopener">{{ t.footInsta }} {{ t.insta.handle }}</a>
        <a v-if="ko" class="btn blue" :href="profile.youtube.url" target="_blank" rel="noopener">유튜브 {{ profile.youtube.handle }}</a>
        <a class="btn blue" :href="t.other.url" target="_blank" rel="noopener">{{ t.footOther }} {{ t.other.handle }}</a>
      </nav>
      <p class="copy">{{ t.copy }}</p>
    </div>
  </footer>
</template>

<style scoped>
.wrap {
  max-width: var(--wrap);
  margin: 0 auto;
  padding: 0 var(--gutter);
}

/* ================= 첫 화면 ================= */
.hero {
  position: relative;
  padding: 28px var(--gutter) 64px;
  overflow: hidden;
}

.hero-inner {
  position: relative;
  max-width: var(--wrap);
  margin: 0 auto;
  display: grid;
  justify-items: center;
  text-align: center;
}

/* 떠다니는 스티커 */
.floaters .f {
  position: absolute;
  width: clamp(46px, 10vw, 84px);
  filter: drop-shadow(0 8px 10px rgba(43, 33, 64, 0.18));
  animation: float 6s ease-in-out infinite;
}

.f1 { top: 6%; left: 4%; --rot: -14deg; animation-delay: -1s; }
.f2 { top: 14%; right: 6%; --rot: 12deg; animation-duration: 7s; }
.f3 { top: 42%; left: 2%; --rot: 8deg; width: 44px; animation-duration: 5s; }
.f4 { top: 48%; right: 3%; --rot: -20deg; animation-delay: -3s; }
.f5 { bottom: 16%; left: 8%; --rot: 10deg; animation-duration: 8s; }
.f6 { top: 2%; left: 42%; --rot: 0deg; width: 64px; opacity: 0.9; animation-duration: 9s; }
.f7 { bottom: 8%; right: 10%; --rot: -8deg; animation-delay: -2s; }
.f8 { bottom: 30%; right: 26%; --rot: 6deg; width: 56px; }

/* 폰: 아래쪽 스티커는 버튼 뒤로 숨으니 뺀다 */
.f5,
.f7,
.f8 {
  display: none;
}

@keyframes float {
  0%,
  100% {
    transform: translateY(0) rotate(var(--rot, 0deg));
  }
  50% {
    transform: translateY(-16px) rotate(calc(var(--rot, 0deg) * -1));
  }
}

/* 그림 */
.hero-art {
  position: relative;
  width: min(92vw, 460px);
  padding: 0;
  border: 0;
  background: none;
  cursor: pointer;
  -webkit-tap-highlight-color: transparent;
}

.halo {
  position: absolute;
  inset: 8%;
  border-radius: 50%;
  background:
    radial-gradient(circle at 35% 35%, #fff 0%, transparent 55%),
    conic-gradient(from 0deg, var(--pink), var(--sky), var(--lilac), var(--butter), var(--pink));
  filter: blur(6px);
  animation: spin 18s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.hero-art > img {
  position: relative;
  width: 100%;
  filter: drop-shadow(0 18px 22px rgba(43, 33, 64, 0.22));
  animation: bob 3.2s ease-in-out infinite;
}

.hero-art > img.boing {
  animation: boing 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
}

@keyframes bob {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-14px);
  }
}

@keyframes boing {
  0% {
    transform: scale(1, 1);
  }
  30% {
    transform: scale(1.12, 0.88) translateY(10px);
  }
  60% {
    transform: scale(0.94, 1.08) translateY(-26px);
  }
  100% {
    transform: scale(1, 1);
  }
}

.burst {
  position: absolute;
  left: 50%;
  top: 45%;
  pointer-events: none;
}

.burst img {
  position: absolute;
  width: 44px;
  margin: -22px 0 0 -22px;
  animation: pop 1s cubic-bezier(0.2, 0.8, 0.2, 1) forwards;
}

@keyframes pop {
  0% {
    transform: translate(0, 0) scale(0.2) rotate(0deg);
    opacity: 1;
  }
  70% {
    opacity: 1;
  }
  100% {
    transform: translate(var(--x), var(--y)) scale(1) rotate(var(--r));
    opacity: 0;
  }
}

/* 로고: 스티커처럼 흰 테두리 + 아래 그림자, 글자마다 통통 튀며 등장 */
.logo {
  margin-top: -6px;
  font-family: var(--mark);
  font-weight: 400;
  font-size: clamp(88px, 25vw, 156px);
  line-height: 1;
  letter-spacing: 0.01em;
}

.logo span {
  display: inline-block;
  text-shadow:
    5px 0 0 #fff, -5px 0 0 #fff, 0 5px 0 #fff, 0 -5px 0 #fff,
    4px 4px 0 #fff, -4px 4px 0 #fff, 4px -4px 0 #fff, -4px -4px 0 #fff,
    0 12px 0 rgba(43, 33, 64, 0.16);
  animation: letter 0.8s cubic-bezier(0.34, 1.56, 0.64, 1) both;
}

.logo .ink {
  color: var(--ink);
}

@keyframes letter {
  0% {
    transform: translateY(60px) scale(0.4) rotate(-12deg);
    opacity: 0;
  }
  100% {
    transform: none;
    opacity: 1;
  }
}

.logo span:nth-child(2) {
  transform-origin: bottom;
}

.tagline {
  margin-top: 6px;
  display: inline-block;
  padding: 6px 18px;
  border-radius: 999px;
  background: var(--ink);
  color: #fff;
  font-size: 15px;
  font-weight: 800;
  letter-spacing: 0.02em;
}

.bio {
  margin-top: 20px;
  font-size: 16.5px;
  font-weight: 600;
  line-height: 1.8;
}

.cta {
  display: grid;
  gap: 16px;
  width: 100%;
  max-width: 380px;
  margin: 30px auto 0;
}

@media (min-width: 900px) {
  .hero {
    padding-top: 56px;
    padding-bottom: 96px;
  }

  .hero-inner {
    grid-template-columns: 1fr 1.05fr;
    align-items: center;
    justify-items: start;
    text-align: left;
    gap: 24px;
  }

  .hero-text {
    order: -1;
  }

  .hero-art {
    width: 100%;
    max-width: 560px;
    justify-self: end;
  }

  .cta {
    grid-template-columns: 1fr 1fr;
    max-width: 540px;
    margin-left: 0;
  }

  .f5,
  .f7,
  .f8 {
    display: block;
  }

  /* 넓은 화면: 글씨·버튼 위에 걸리지 않게 그림 쪽으로 */
  .f3 {
    top: 74%;
    left: 44%;
  }

  .f5 {
    bottom: 4%;
    left: 34%;
  }

  .tagline {
    font-size: 17px;
  }

  .bio {
    font-size: 19px;
  }

  .cta .btn {
    min-height: 60px;
    padding: 0 20px;
    font-size: 18px;
    white-space: nowrap;
  }
}

/* ================= 흘러가는 표지 띠 ================= */
.ribbons {
  position: relative;
  display: grid;
  gap: 0;
  margin: 8px 0 20px;
  /* 기울인 띠가 화면 양옆으로 26px쯤 삐져나온다. body의 overflow-x: hidden만으로는 폰(사파리·인앱 브라우저)에서
     페이지가 옆으로 밀리므로 여기서 가로만 자른다 (clip은 세로를 그대로 두고 스크롤 상자도 만들지 않는다) */
  overflow-x: clip;
}

@supports not (overflow: clip) {
  .ribbons {
    overflow: hidden;
    padding: 24px 0;
    margin: -16px 0 4px;
  }
}

.ribbons > :last-child {
  margin-top: -18px;
}

/* ================= 섹션 공통 ================= */
main {
  padding-bottom: 24px;
}

h2 {
  font-size: clamp(30px, 8vw, 44px);
  font-weight: 900;
  letter-spacing: -0.03em;
  line-height: 1.15;
}

.block {
  margin-top: 80px;
}

.head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 12px;
}

.sub {
  margin-top: 6px;
  font-size: 14px;
  font-weight: 700;
  color: var(--ink-soft);
}

.mascot {
  width: clamp(120px, 34vw, 190px);
  margin-bottom: -10px;
  filter: drop-shadow(0 10px 14px rgba(43, 33, 64, 0.2));
}

.mascot.wide {
  width: clamp(170px, 48vw, 280px);
}

/* ================= 멍이 × 댕이 ================= */
.duo {
  margin-top: 56px;
}

.duo-head {
  text-align: center;
}

.duo-head .meong {
  color: var(--meong);
}

.duo-head .daeng {
  color: var(--daeng);
}

.duo-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
  margin-top: 22px;
  align-items: stretch; /* 문구 줄 수가 달라도 두 카드 높이를 같게 */
}

/* 인물 카드: 그림이 카드 위로 튀어나오고, 둘이 살짝 반대로 기운다 */
.char {
  position: relative;
  margin-top: 118px;
  padding: 0 10px 22px;
  border-radius: 28px;
  color: var(--ink);
  border: 3px solid #fff;
  text-align: center;
  box-shadow: 0 24px 44px -26px rgba(122, 76, 140, 0.6);
  transform: rotate(-1.5deg);
}

.char.meong {
  background: linear-gradient(180deg, #e3eeff, var(--sky));
}

.char.daeng {
  background: linear-gradient(180deg, #ffe8f0, var(--pink));
  transform: rotate(1.5deg);
}

.char-art {
  width: 92%;
  aspect-ratio: 1 / 2; /* 두 그림 비율이 조금 달라도 이름 줄이 같은 높이에 오게 */
  object-fit: contain;
  margin: -70px auto 0;
  filter: drop-shadow(0 10px 12px rgba(43, 33, 64, 0.22));
  transition: transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.char:hover .char-art {
  transform: translateY(-8px) rotate(-3deg);
}

.char-name {
  margin-top: 4px;
  font-family: var(--mark);
  font-size: clamp(34px, 10vw, 52px);
  font-weight: 400;
  line-height: 1;
  -webkit-text-stroke: 0;
  text-shadow:
    3px 3px 0 #fff, -3px 3px 0 #fff, 3px -3px 0 #fff, -3px -3px 0 #fff,
    0 3px 0 #fff, 3px 0 0 #fff, 0 -3px 0 #fff, -3px 0 0 #fff;
}

.meong .char-name {
  color: var(--meong);
}

.daeng .char-name {
  color: var(--daeng);
}

/* 툰 말풍선: 손글씨(나눔펜), 흰 바탕에 검은 외곽선, 머리 위에서 꼬리가 아래로 */
.bubble {
  position: absolute;
  z-index: 2;
  top: -118px;
  left: 50%;
  transform: translateX(-50%) rotate(-2deg);
  padding: 5px 13px 7px;
  border: 2.5px solid var(--ink);
  border-radius: 999px;
  background: #fff;
  font-family: 'Nanum Pen Script', var(--sans);
  font-size: 20px;
  line-height: 1.1;
  white-space: nowrap;
  color: var(--ink);
}

.daeng .bubble {
  transform: translateX(-50%) rotate(2deg);
}

.bubble::before,
.bubble::after {
  content: '';
  position: absolute;
  left: 50%;
  border-style: solid;
  transform: translateX(-50%);
}

.bubble::before {
  top: 100%;
  border-width: 12px 8px 0;
  border-color: var(--ink) transparent transparent;
}

.bubble::after {
  top: calc(100% - 3.5px);
  border-width: 9px 5.5px 0;
  border-color: #fff transparent transparent;
}

/* 툰 자연 다큐 자막처럼 */
.tag {
  display: inline-block;
  margin-top: 8px;
  padding: 2px 10px 3px;
  border-radius: 6px;
  background: rgba(43, 33, 64, 0.82);
  color: #fff;
  font-size: 12.5px;
  font-weight: 700;
}

/* 툰 내레이션 글씨(푸어스토리) */
.narr {
  margin-top: 12px;
  padding: 0 4px;
  font-family: 'Poor Story', var(--sans);
  font-size: 17px;
  line-height: 1.45;
  word-break: keep-all;
}

.duo-sub {
  font-family: 'Poor Story', var(--sans);
  font-size: 18px;
  font-weight: 400;
}

@media (min-width: 900px) {
  .duo-grid {
    gap: 40px;
    max-width: 820px;
    margin: 30px auto 0;
  }

  .char {
    margin-top: 190px;
    padding: 0 28px 30px;
  }

  .char-art {
    width: auto;
    height: 400px;
    margin-top: -130px;
  }

  .bubble {
    top: -190px;
    font-size: 30px;
    padding: 6px 20px 9px;
  }

  .tag {
    font-size: 14px;
  }

  .narr {
    font-size: 20px;
    max-width: 300px;
    margin-inline: auto;
  }
}

/* ================= 처음 오셨다면 ================= */
.start {
  margin-top: 64px;
}

.start-card {
  position: relative;
  display: grid;
  grid-template-columns: 1fr;
  gap: 18px;
  padding: 28px 24px 30px;
  border-radius: 32px;
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  border: 2px solid #fff;
  box-shadow: 0 30px 60px -30px rgba(122, 76, 140, 0.55);
  overflow: hidden;
}

.start-card::before {
  content: '';
  position: absolute;
  width: 320px;
  height: 320px;
  right: -90px;
  top: -110px;
  border-radius: 50%;
  background: radial-gradient(circle, var(--pink), transparent 70%);
  z-index: -1;
}

.start-text {
  position: relative;
  z-index: 1;
}

.start-title {
  margin-top: 14px;
  font-size: 18px;
  font-weight: 800;
}

.start-date {
  font-size: 13px;
  font-weight: 600;
  color: var(--ink-soft);
}

.start-text .btn {
  margin-top: 20px;
}

.start-cover {
  justify-self: center;
  width: min(62%, 260px);
  transform: rotate(3deg);
  transition: transform 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.start-cover:hover {
  transform: rotate(0deg) scale(1.04);
}

.start-cover img {
  border: 7px solid #fff;
  border-radius: 20px;
  box-shadow: 0 24px 40px -16px rgba(43, 33, 64, 0.5);
}

/* 모바일: 댕이가 표지 왼쪽 아래에서 가리킨다 */
.start-mascot {
  position: absolute;
  left: -14px;
  bottom: -8px;
  width: 44%;
  max-width: 220px;
  z-index: 2;
  filter: drop-shadow(0 10px 14px rgba(43, 33, 64, 0.2));
  pointer-events: none;
}

.start-card > .start-cover {
  margin-left: 30%;
}

@media (min-width: 900px) {
  .start-card {
    grid-template-columns: 260px 1fr 280px;
    align-items: center;
    gap: 32px;
    padding: 36px 48px;
  }

  .start-mascot {
    position: static;
    width: 100%;
    max-width: none;
    order: -1;
  }

  .start-card > .start-cover {
    margin-left: 0;
    width: 100%;
  }
}

/* ================= 전체 회차 ================= */
.grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 32px 18px;
  margin-top: 28px;
}

@media (min-width: 640px) {
  .grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (min-width: 960px) {
  .grid {
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 40px 28px;
  }
}

/* ================= 꼬리 ================= */
.foot {
  position: relative;
  margin-top: 110px;
  isolation: isolate;
  color: #fff;
}

/* 물결과 몸통을 한 판의 그라데이션으로 칠하고 윗부분만 물결 모양으로 오려 낸다.
   물결을 따로 단색으로 칠하면 오른쪽에서 그라데이션과 색이 어긋나 경계선이 보인다. */
.foot::before {
  content: '';
  position: absolute;
  inset: -79px 0 0;
  z-index: -1;
  background: linear-gradient(160deg, var(--daeng-hi) 0%, #a77bc4 50%, var(--meong-hi) 100%);
  --wave: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1440 80' preserveAspectRatio='none'%3E%3Cpath d='M0,40 C240,90 480,0 720,36 C960,72 1200,10 1440,44 L1440,80 L0,80 Z'/%3E%3C/svg%3E");
  -webkit-mask:
    var(--wave) top / 100% 80px no-repeat,
    linear-gradient(#000 0 0) bottom / 100% calc(100% - 79px) no-repeat;
  mask:
    var(--wave) top / 100% 80px no-repeat,
    linear-gradient(#000 0 0) bottom / 100% calc(100% - 79px) no-repeat;
}

.foot-inner {
  display: grid;
  justify-items: center;
  gap: 16px;
  padding: 0 var(--gutter) 40px;
  text-align: center;
}

.bye {
  width: min(70vw, 300px);
  margin-top: -110px;
  filter: drop-shadow(0 14px 18px rgba(43, 33, 64, 0.3));
}

.logo.small {
  margin: 0;
  font-size: 64px;
}

.logo.small span {
  animation: none;
}

.foot-cta {
  margin-top: 8px;
}

.foot-cta .btn {
  min-height: 50px;
  font-size: 15px;
}

.foot-cta .btn.pink {
  background: #fff;
  color: var(--daeng);
  box-shadow: 0 6px 0 rgba(43, 33, 64, 0.25);
}

.foot-cta .btn.blue {
  background: rgba(255, 255, 255, 0.18);
  color: #fff;
  box-shadow: inset 0 0 0 2px #fff, 0 6px 0 rgba(43, 33, 64, 0.2);
}

.copy {
  margin-top: 6px;
  font-size: 12.5px;
  font-weight: 600;
  opacity: 0.85;
}

/* ================= 언어 (한국어 / 영어) ================= */
.lang-switch {
  position: absolute;
  z-index: 5;
  top: 14px;
  right: var(--gutter);
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 40px;
  padding: 0 14px;
  border: 2.5px solid var(--ink);
  border-radius: 999px;
  background: #fff;
  color: var(--ink);
  font-family: var(--mark);
  font-size: 17px;
  box-shadow: 0 4px 0 var(--ink);
  cursor: pointer;
  transition: transform 0.12s ease, box-shadow 0.12s ease;
}

.lang-switch:active {
  transform: translateY(3px);
  box-shadow: 0 1px 0 var(--ink);
}

.lang-switch svg {
  width: 18px;
  height: 18px;
}

/* 영어 로고는 MeongDaeng / Comics 두 줄이라 글자를 줄인다 */
.logo .logo-line {
  display: block;
  animation: none;
  text-shadow: none;
}

.logo.en {
  font-size: min(80px, 14vw);
  line-height: 0.95;
}

.logo.en .logo-line {
  white-space: nowrap;
}

.logo.small.en {
  font-size: 40px;
}

.other-insta {
  margin-top: 18px;
  font-size: 14px;
  font-weight: 700;
}

.other-insta a {
  color: var(--ink-soft);
  text-decoration: underline;
  text-underline-offset: 3px;
}

/* 영어 말풍선은 글자가 길어 조금 작게 */
.duo-grid.en .bubble {
  font-size: 18px;
  white-space: nowrap;
}

.duo-grid.en .tag {
  font-size: 11.5px;
  white-space: nowrap;
  padding-left: 8px;
  padding-right: 8px;
}

/* 영문판이 아직 없을 때 카드: 그림 위, 글 아래 */
.soon .start-mascot {
  position: static;
  justify-self: center;
  width: 78%;
  max-width: 300px;
}

.soon h2 {
  line-height: 1.15;
}

.soon-text {
  margin-top: 12px;
  font-size: 16px;
  font-weight: 600;
  line-height: 1.6;
  color: var(--ink-soft);
}

@media (min-width: 900px) {
  .lang-switch {
    top: 22px;
  }

  /* 글 칸이 화면의 절반쯤이라 MeongDaeng 한 줄이 들어가게 */
  .logo.en {
    font-size: min(84px, calc(7.6vw - 10px));
  }

  .duo-grid.en .bubble {
    font-size: 26px;
  }

  .soon.start-card {
    grid-template-columns: 320px 1fr;
  }

  .soon .start-mascot {
    width: 100%;
    max-width: none;
  }
}
</style>
