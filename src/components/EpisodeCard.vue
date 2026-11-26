<script setup>
import Named from './Named.vue'

defineProps({
  ep: { type: Object, required: true },
  href: { type: String, required: true },
  // 스티커처럼 살짝 기울이기 (도)
  tilt: { type: Number, default: 0 },
})

const dot = (d) => d.replaceAll('-', '.')
</script>

<template>
  <a class="ep" :href="href" target="_blank" rel="noopener" :style="{ '--tilt': `${tilt}deg` }">
    <div class="cover">
      <img :src="ep.cover" :alt="ep.title" loading="lazy" width="540" height="675" />
    </div>
    <p class="title"><Named :text="ep.title" /></p>
    <p class="date">{{ dot(ep.date) }}</p>
  </a>
</template>

<style scoped>
.ep {
  display: block;
}

.cover {
  position: relative;
  aspect-ratio: 4 / 5;
  border: 6px solid #fff;
  border-radius: 18px;
  overflow: hidden;
  background: #fff;
  box-shadow:
    0 2px 0 rgba(43, 33, 64, 0.06),
    0 14px 30px -12px rgba(122, 76, 140, 0.45);
  transform: rotate(var(--tilt));
  transition:
    transform 0.35s cubic-bezier(0.34, 1.56, 0.64, 1),
    box-shadow 0.3s ease;
}

.ep:hover .cover,
.ep:focus-visible .cover {
  transform: rotate(0deg) translateY(-6px) scale(1.04);
  box-shadow: 0 22px 40px -14px rgba(122, 76, 140, 0.6);
}

.cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 12px;
}

.title {
  margin-top: 12px;
  padding: 0 2px;
  font-size: 15px;
  font-weight: 700;
  line-height: 1.4;
}

.date {
  margin-top: 3px;
  padding: 0 2px;
  font-size: 12.5px;
  font-weight: 600;
  color: var(--ink-soft);
  font-variant-numeric: tabular-nums;
}
</style>
