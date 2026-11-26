<script setup>
// 기울어진 띠 위로 회차 표지가 끝없이 흘러간다. 두 벌 이어 붙여 -50%만큼 움직이면 이음매가 안 보인다.
defineProps({
  episodes: { type: Array, required: true },
  reverse: { type: Boolean, default: false },
  color: { type: String, default: 'pink' },
})
</script>

<template>
  <div class="ribbon" :class="[color, { reverse }]" aria-hidden="true">
    <div class="track">
      <template v-for="n in 2" :key="n">
        <img v-for="ep in episodes" :key="`${n}-${ep.num}`" :src="ep.cover" alt="" loading="lazy" width="540" height="675" />
      </template>
    </div>
  </div>
</template>

<style scoped>
.ribbon {
  overflow: hidden;
  padding: 14px 0;
  transform: rotate(-3deg);
  margin: 0 -6vw;
  box-shadow: 0 16px 30px -18px rgba(43, 33, 64, 0.5);
}

.ribbon.reverse {
  transform: rotate(2deg);
}

.ribbon.pink {
  background: linear-gradient(90deg, var(--daeng-hi), var(--daeng));
}

.ribbon.blue {
  background: linear-gradient(90deg, var(--meong), var(--meong-hi));
}

.track {
  display: flex;
  gap: 14px;
  width: max-content;
  animation: slide 60s linear infinite;
}

.reverse .track {
  animation-direction: reverse;
}

.track img {
  width: clamp(92px, 22vw, 150px);
  aspect-ratio: 4 / 5;
  object-fit: cover;
  border: 4px solid #fff;
  border-radius: 12px;
}

@keyframes slide {
  to {
    transform: translateX(-50%);
  }
}
</style>
