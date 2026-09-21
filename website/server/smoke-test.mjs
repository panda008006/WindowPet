const base = process.env.API_BASE || 'http://127.0.0.1:8787'
const email = `smoke-${Date.now()}@windowpet.local`
const password = 'windowpet123'
const adminToken = process.env.WINDOWPET_ADMIN_TOKEN || 'windowpet-admin-local'
process.env.NODE_ENV ??= 'development'
process.env.WINDOWPET_ALLOW_MOCK_LOGIN ??= 'true'

async function request(path, options = {}) {
  const response = await fetch(`${base}${path}`, options)
  const body = await response.json()
  if (!response.ok) {
    throw new Error(`${response.status} ${JSON.stringify(body)}`)
  }
  return body
}

function authHeaders(token) {
  return {
    Authorization: `Bearer ${token}`,
    'Content-Type': 'application/json',
  }
}

function adminHeaders() {
  return {
    'Content-Type': 'application/json',
    'X-WindowPet-Admin-Token': adminToken,
  }
}

const health = await request('/api/health')
const providers = await request('/api/auth/providers')
if (providers.password !== true || providers.wechatQr !== false || providers.sms !== false) {
  throw new Error('Unexpected auth provider configuration')
}
const store = await request('/api/store/pets')
const numberedPackage = await request('/api/store/packages/0006')
if (numberedPackage.package.packageCode !== '0006' || numberedPackage.package.id !== 'jiyi') {
  throw new Error('Four-digit package lookup returned the wrong package')
}
let registered
let login
if (process.env.WINDOWPET_RETURN_DEV_CODE === 'true') {
  const code = await request('/api/auth/email-code', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, purpose: 'register', name: 'Smoke Test' }),
  })
  registered = await request('/api/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email,
      name: 'Smoke Test',
      password,
      emailCode: code.devCode || process.env.WP_DEV_EMAIL_CODE,
    }),
  })
  login = await request('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })
} else {
  registered = await request('/api/auth/mock-login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, name: 'Smoke Test' }),
  })
  login = registered
}
const batch = await request('/api/admin/egg-codes/batch', {
  method: 'POST',
  headers: adminHeaders(),
  body: JSON.stringify({
    batchName: 'Smoke Test Codes',
    count: 1,
    maxUses: 1,
    prefix: 'SMK',
    rewardId: 'kukukaka-library-pass',
  }),
})
const egg = await request('/api/campaign/egg-redeem', {
  method: 'POST',
  headers: authHeaders(login.token),
  body: JSON.stringify({ code: batch.codes[0].code }),
})
const adminCodes = await request('/api/admin/egg-codes', { headers: adminHeaders() })
const synced = await request(`/api/sync/${registered.user.id}/devices/wp-demo-device-001`, {
  method: 'PUT',
  headers: authHeaders(registered.token),
  body: JSON.stringify({
    installId: 'install-jiyi',
    packageId: 'jiyi',
    state: {
      petDisplayName: '吉伊',
      x: 96,
      y: 120,
      scale: 110,
      opacity: 96,
      speed: 105,
      locked: false,
      alwaysOnTop: true,
      clickThrough: false,
      dockMode: 'none',
      currentAnimation: 'waving',
      enabledAccessories: [],
      memoVisible: true,
      memoText: '云同步 smoke test',
      memoChecked: false,
    },
  }),
})
const pulled = await request(`/api/sync/${registered.user.id}?deviceId=wp-demo-device-001`)

// Payment flow smoke test
const plans = await request('/api/pay/plans')
const order = await request('/api/pay/order/create', {
  method: 'POST',
  headers: authHeaders(login.token),
  body: JSON.stringify({ planId: 'plan_lifetime' }),
})
const orderStatus = await request(`/api/pay/order/status/${order.order.id}`)
const mockPay = await request('/api/pay/order/mock-pay', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ orderId: order.order.id }),
})
const finalStatus = await request(`/api/pay/order/status/${order.order.id}`)
const entitlements = await request('/api/pay/my-entitlements', { headers: authHeaders(login.token) })

console.log(
  JSON.stringify(
    {
      health: health.ok,
      authProviders: providers,
      packageCount: store.packages.length,
      numberedPackage: `${numberedPackage.package.packageCode}:${numberedPackage.package.id}`,
      registeredUser: registered.user.email,
      loginUser: login.user.email,
      generatedEggCode: batch.codes[0].code,
      eggReward: egg.reward.title,
      redemptions: adminCodes.redemptions.length,
      revision: synced.state.revision,
      pulledStates: pulled.deviceStates.length,
      paymentPlansCount: plans.plans.length,
      createdOrderId: order.order.id,
      paymentVerified: finalStatus.isPaid,
      entitlementsCount: entitlements.entitlements.length,
      userIsVip: entitlements.isVip,
    },
    null,
    2,
  ),
)
