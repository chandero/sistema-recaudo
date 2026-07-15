import { beforeEach, describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import AppMenu from '@/components/AppMenu.vue'
import { useAuthStore } from '@/stores/auth'

function renderFor(role) {
  const pinia = createPinia()
  setActivePinia(pinia)
  const store = useAuthStore()
  store.currentUser = { id: 1, role }

  return mount(AppMenu, {
    global: {
      plugins: [pinia],
      stubs: {
        RouterLink: {
          props: ['to'],
          template: '<a :href="to"><slot /></a>'
        }
      }
    }
  })
}

describe('AppMenu por rol', () => {
  beforeEach(() => localStorage.setItem('locale', 'es'))

  it('muestra tenants y usuarios a plataforma', () => {
    const wrapper = renderFor('PLATFORM_ADMIN')
    expect(wrapper.find('a[href="/admin"]').exists()).toBe(true)
    expect(wrapper.find('a[href="/admin/usuarios"]').exists()).toBe(true)
  })

  it('muestra usuarios pero no tenants al administrador de tenant', () => {
    const wrapper = renderFor('TENANT_ADMIN')
    expect(wrapper.find('a[href="/admin"]').exists()).toBe(false)
    expect(wrapper.find('a[href="/admin/usuarios"]').exists()).toBe(true)
  })

  it('oculta ambas opciones a roles operativos', () => {
    const wrapper = renderFor('OPERATOR')
    expect(wrapper.find('a[href="/admin"]').exists()).toBe(false)
    expect(wrapper.find('a[href="/admin/usuarios"]').exists()).toBe(false)
  })
})
