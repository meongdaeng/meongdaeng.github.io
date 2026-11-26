<script setup>
// 글씨 속 멍이·댕이(별칭 대형견남·소형견남 포함)를 이름 색으로 칠한다 (characters/design-brief.md "이름 색 구분")
import { computed } from 'vue'

const props = defineProps({ text: { type: String, required: true } })

const NAMES = { 멍이: 'meong', 대형견남: 'meong', 댕이: 'daeng', 소형견남: 'daeng' }
const PATTERN = /(멍이|댕이|대형견남|소형견남)/

const parts = computed(() =>
  props.text
    .split(PATTERN)
    .filter(Boolean)
    .map((s) => ({ s, cls: NAMES[s] || null })),
)
</script>

<template>
  <template v-for="(p, i) in parts" :key="i"><span v-if="p.cls" :class="p.cls">{{ p.s }}</span><template v-else>{{ p.s }}</template></template>
</template>
