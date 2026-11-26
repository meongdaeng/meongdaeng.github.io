import { createApp } from 'vue'
import App from './App.vue'
import './style.css'

// v-reveal: 화면에 들어오면 .in을 붙여 튀어나오게 한다. 값은 지연(ms)
const io =
  typeof IntersectionObserver !== 'undefined'
    ? new IntersectionObserver(
        (entries) => {
          for (const e of entries) {
            if (e.isIntersecting) {
              e.target.classList.add('in')
              io.unobserve(e.target)
            }
          }
        },
        { threshold: 0.15, rootMargin: '0px 0px -40px 0px' },
      )
    : null

createApp(App)
  .directive('reveal', {
    mounted(el, { value }) {
      el.classList.add('reveal')
      if (value) el.style.setProperty('--delay', `${value}ms`)
      if (io) io.observe(el)
      else el.classList.add('in')
    },
  })
  .mount('#app')
