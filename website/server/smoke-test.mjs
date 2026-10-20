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

const submissionForm = new FormData()
submissionForm.set('displayName', `Smoke Pet ${Date.now()}`)
submissionForm.set('authorName', 'Smoke Test Creator')
submissionForm.set('authorEmail', email)
submissionForm.set('version', '1.0.0')
submissionForm.set('description', '这是用于 API smoke test 的角色投稿说明，包含足够的描述文字。')
submissionForm.set('licenseText', 'Smoke test owns the submitted test assets.')
submissionForm.set('licenseAccepted', 'true')
submissionForm.set('packageFile', new Blob([Buffer.from([0x50, 0x4b, 0x03, 0x04]), new TextEncoder().encode('asset.json')], { type: 'application/zip' }), 'smoke-pet.wpet')
submissionForm.set('demoVideo', new Blob([Buffer.from('0000ftypisom-smoke')], { type: 'video/mp4' }), 'smoke-demo.mp4')
const submitted = await request('/api/submissions', { method: 'POST', body: submissionForm })
const pendingSubmission = await request(`/api/submissions/${submitted.submission.id}?token=${encodeURIComponent(submitted.trackingToken)}`)
const adminSubmissions = await request('/api/admin/submissions', { headers: adminHeaders() })
const reviewedSubmission = await request(`/api/admin/submissions/${submitted.submission.id}/review`, {
  method: 'POST',
  headers: adminHeaders(),
  body: JSON.stringify({ status: 'approved', reviewNote: 'Smoke test approved.' }),
})
const publishedStore = await request('/api/store/pets')
if (pendingSubmission.submission.status !== 'pending_review' || reviewedSubmission.submission.status !== 'approved') {
  throw new Error('Submission review flow returned an unexpected status')
}
if (!publishedStore.packages.some((item) => item.id === `creator-${submitted.submission.id}`)) {
  throw new Error('Approved submission did not enter the public package catalog')
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
const profile = await request('/api/auth/profile', {
  method: 'PATCH',
  headers: authHeaders(login.token),
  body: JSON.stringify({ socialHandles: { douyin: 'smoke-douyin', bilibili: 'smoke-bili', qq: '10086' } }),
})
if (profile.user.socialHandles.qq !== '10086') throw new Error('Profile social handles were not saved')
const mySubmissions = await request('/api/me/submissions', { headers: { Authorization: `Bearer ${login.token}` } })
if (!Array.isArray(mySubmissions.submissions)) throw new Error('Authenticated submission list was not returned')
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
      submissionId: submitted.submission.id,
      submissionStatus: reviewedSubmission.submission.status,
      adminSubmissionCount: adminSubmissions.submissions.length,
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
      allUnlocked: entitlements.allUnlocked,
    },
    null,
    2,
  ),
)
