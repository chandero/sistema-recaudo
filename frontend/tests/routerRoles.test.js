import { describe, expect, it } from 'vitest'
import router from '@/router'

function routeByName(name) {
  return router.getRoutes().find(route => route.name === name)
}

describe('metadatos de rutas administrativas', () => {
  it('restringe administración general a plataforma', () => {
    expect(routeByName('Admin').meta.roles).toEqual(['PLATFORM_ADMIN'])
  })

  it('permite gestión de usuarios a ambos administradores', () => {
    expect(routeByName('Usuarios').meta.roles).toEqual([
      'PLATFORM_ADMIN',
      'TENANT_ADMIN'
    ])
  })

  it('mantiene pública la aceptación de invitaciones', () => {
    const invitationRoute = routeByName('AceptarInvitacion')
    expect(invitationRoute.path).toBe('/aceptar-invitacion')
    expect(invitationRoute.meta.roles).toBeUndefined()
  })
})
