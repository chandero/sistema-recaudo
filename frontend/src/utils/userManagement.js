export const PLATFORM_ADMIN = 'PLATFORM_ADMIN'
export const TENANT_ADMIN = 'TENANT_ADMIN'
export const USER_ADMIN_ROLES = [PLATFORM_ADMIN, TENANT_ADMIN]

export const ROLE_OPTIONS = [
  { label: 'Administrador de plataforma', value: PLATFORM_ADMIN },
  { label: 'Administrador de tenant', value: TENANT_ADMIN },
  { label: 'Gerente', value: 'MANAGER' },
  { label: 'Operador', value: 'OPERATOR' },
  { label: 'Visualizador', value: 'VIEWER' }
]

export function isPlatformAdmin(role) {
  return role === PLATFORM_ADMIN
}

export function canManageUsers(role) {
  return USER_ADMIN_ROLES.includes(role)
}

export function assignableRolesFor(role) {
  return isPlatformAdmin(role)
    ? ROLE_OPTIONS
    : ROLE_OPTIONS.filter(option => option.value !== PLATFORM_ADMIN)
}

export function validateUserForm(form, { editing = false, platformAdmin = false } = {}) {
  if (!form.full_name || !form.username || !form.email || !form.role) {
    return 'Completa todos los campos obligatorios.'
  }
  if (platformAdmin && form.role !== PLATFORM_ADMIN && !form.tenant_id) {
    return 'Selecciona un tenant.'
  }
  if (!editing && !/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/.test(form.password || '')) {
    return 'La contraseña no cumple los requisitos de seguridad.'
  }
  return ''
}
