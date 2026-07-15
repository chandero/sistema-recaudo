import { describe, expect, it } from 'vitest'
import {
  assignableRolesFor,
  canManageUsers,
  isPlatformAdmin,
  validateUserForm
} from '@/utils/userManagement'

const validForm = {
  full_name: 'Usuario Prueba',
  username: 'usuario',
  email: 'usuario@example.com',
  password: 'Secure123',
  role: 'OPERATOR',
  tenant_id: 1
}

describe('reglas de gestión de usuarios', () => {
  it('solo permite administrar a los dos roles administrativos', () => {
    expect(canManageUsers('PLATFORM_ADMIN')).toBe(true)
    expect(canManageUsers('TENANT_ADMIN')).toBe(true)
    expect(canManageUsers('MANAGER')).toBe(false)
    expect(canManageUsers(undefined)).toBe(false)
  })

  it('identifica exclusivamente al administrador de plataforma', () => {
    expect(isPlatformAdmin('PLATFORM_ADMIN')).toBe(true)
    expect(isPlatformAdmin('TENANT_ADMIN')).toBe(false)
  })

  it('impide que un administrador de tenant asigne PLATFORM_ADMIN', () => {
    const tenantRoles = assignableRolesFor('TENANT_ADMIN').map(role => role.value)
    const platformRoles = assignableRolesFor('PLATFORM_ADMIN').map(role => role.value)

    expect(tenantRoles).not.toContain('PLATFORM_ADMIN')
    expect(platformRoles).toContain('PLATFORM_ADMIN')
  })

  it('valida campos obligatorios y contraseña al crear', () => {
    expect(validateUserForm({ ...validForm, full_name: '' })).toContain('obligatorios')
    expect(validateUserForm({ ...validForm, password: 'debil' })).toContain('contraseña')
    expect(validateUserForm(validForm)).toBe('')
  })

  it('exige tenant a plataforma excepto al crear PLATFORM_ADMIN', () => {
    expect(validateUserForm(
      { ...validForm, tenant_id: null },
      { platformAdmin: true }
    )).toContain('tenant')
    expect(validateUserForm(
      { ...validForm, tenant_id: null, role: 'PLATFORM_ADMIN' },
      { platformAdmin: true }
    )).toBe('')
  })

  it('no exige contraseña durante la edición', () => {
    expect(validateUserForm(
      { ...validForm, password: '' },
      { editing: true }
    )).toBe('')
  })
})
