import { chromium } from 'playwright'
import { preview } from 'vite'

async function run() {
  console.log('Starting Vite preview server on port 4173...')
  const server = await preview({
    preview: { port: 4173, strictPort: true },
  })

  const browser = await chromium.launch({ channel: 'msedge', headless: true })
  const context = await browser.newContext({ viewport: { width: 1280, height: 800 } })
  const page = await context.newPage()

  const consoleErrors = []
  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      consoleErrors.push(msg.text())
    }
  })
  page.on('pageerror', (err) => {
    consoleErrors.push(err.message)
  })

  try {
    console.log('1. Loading home page at http://localhost:4173/ ...')
    await page.goto('http://localhost:4173/', { waitUntil: 'networkidle' })

    // Check navbar
    const navButtons = await page.$$eval('.site-nav nav .nav-link-btn', (els) =>
      els.map((el) => el.textContent.trim().replace(/\s+/g, ' ')),
    )
    console.log('Navbar buttons detected:', navButtons)
    if (navButtons.length !== 4) {
      throw new Error(`Expected 4 navbar buttons, but found ${navButtons.length}: ${JSON.stringify(navButtons)}`)
    }
    const expectedPrefixes = ['角色', '小鼻嘎展馆', '许愿角色', '宠物设计']
    for (let i = 0; i < expectedPrefixes.length; i++) {
      if (!navButtons[i].includes(expectedPrefixes[i])) {
        throw new Error(`Navbar button ${i} expected to include "${expectedPrefixes[i]}", got "${navButtons[i]}"`)
      }
    }

    // Check footer link
    const footerLink = await page.$('.footer-sub-link')
    if (!footerLink) {
      throw new Error('Footer sub-link for submission not found')
    }

    // 2. Test PetGallery
    console.log('2. Navigating to Gallery (#/gallery)...')
    await page.click('.nav-gallery-link')
    await page.waitForSelector('.unified-pet-grid', { timeout: 5000 })

    const petCards = await page.$$('.unified-pet-card')
    console.log(`Found ${petCards.length} pet cards in .unified-pet-grid`)
    if (petCards.length === 0) {
      throw new Error('No pet cards rendered in unified-pet-grid')
    }

    // Verify 3-tier structure on the first card
    const firstCard = petCards[0]
    const hasStage = await firstCard.$('.unified-card-stage')
    const hasMeta = await firstCard.$('.unified-card-meta')
    const hasAction = await firstCard.$('.unified-card-actions .unified-card-import-btn')
    if (!hasStage || !hasMeta || !hasAction) {
      throw new Error('Card does not satisfy 3-tier structure [stage, meta, actions]')
    }

    // Test clicking card opens modal
    console.log('Clicking first card to open modal...')
    await firstCard.click()
    await page.waitForSelector('.gallery-modal', { timeout: 3000 })
    console.log('Gallery modal opened successfully.')

    // Close modal
    await page.click('.gallery-modal-close')
    await page.waitForSelector('.gallery-modal', { state: 'detached', timeout: 3000 })
    console.log('Gallery modal closed successfully.')

    // 3. Test TutorialPage and Creator Submission CTA
    console.log('3. Navigating to Tutorial (#/tutorial)...')
    await page.goto('http://localhost:4173/#/tutorial', { waitUntil: 'networkidle' })
    await page.waitForSelector('.tutorial-chapter-grid', { timeout: 5000 })

    // Check Creator Ecosystem section
    const ecosystemHeading = await page.$eval('h2', () => {
      const headings = Array.from(document.querySelectorAll('h2'))
      const found = headings.find((h) => h.textContent.includes('向社区投稿你的角色'))
      return found ? found.textContent : null
    })
    console.log('Creator ecosystem heading:', ecosystemHeading)
    if (!ecosystemHeading) {
      throw new Error('Creator ecosystem heading not found in TutorialPage')
    }

    // Check action button "进入创作者投稿中心"
    const submitBtn = await page.$('button:has-text("进入创作者投稿中心")')
    if (!submitBtn) {
      throw new Error('"进入创作者投稿中心" button not found in TutorialPage')
    }

    console.log('Clicking "进入创作者投稿中心" button...')
    await submitBtn.click()
    await page.waitForTimeout(500)

    const currentUrl = page.url()
    console.log('Current URL after click:', currentUrl)
    if (!currentUrl.includes('#/submit')) {
      throw new Error(`Expected URL to include #/submit, but got ${currentUrl}`)
    }

    // 4. Verify SubmissionPage
    console.log('4. Verifying SubmissionPage...')
    await page.waitForSelector('.submission-page', { timeout: 5000 })
    const submissionHeading = await page.$eval('.submission-hero h1', (el) => el.textContent)
    console.log('Submission page heading:', submissionHeading)
    const creatorPanel = await page.$('.creator-account-card')
    if (!creatorPanel) {
      throw new Error('CreatorAccountPanel not rendered on SubmissionPage')
    }

    // 5. Test SubmissionReviewPage (#/review)
    console.log('5. Navigating to SubmissionReviewPage (#/review)...')
    await page.goto('http://localhost:4173/#/review', { waitUntil: 'networkidle' })
    await page.waitForSelector('.submission-review-page', { timeout: 5000 })
    const reviewHeading = await page.$eval('.submission-hero h1', (el) => el.textContent)
    console.log('Review page heading:', reviewHeading)

    // 6. Test Mobile Viewport
    console.log('6. Testing mobile viewport (375x667)...')
    await page.setViewportSize({ width: 375, height: 667 })
    await page.goto('http://localhost:4173/#/tutorial', { waitUntil: 'networkidle' })
    const mobileSubmitBtn = await page.$('button:has-text("进入创作者投稿中心")')
    if (!mobileSubmitBtn) {
      throw new Error('Mobile submit button not found')
    }
    await mobileSubmitBtn.click()
    await page.waitForTimeout(500)
    if (!page.url().includes('#/submit')) {
      throw new Error('Mobile navigation to #/submit failed')
    }

    console.log('Checking console errors...')
    // Filter out expected or benign warnings (e.g. 404 for missing deep link handler)
    const fatalErrors = consoleErrors.filter(
      (err) => !err.includes('windowpet://') && !err.includes('Failed to load resource'),
    )
    if (fatalErrors.length > 0) {
      throw new Error(`Console errors encountered: ${JSON.stringify(fatalErrors)}`)
    }

    console.log('ALL E2E CHECKS PASSED!')
  } finally {
    await browser.close()
    await server.close()
  }
}

run().catch((err) => {
  console.error('E2E TEST FAILED:', err)
  process.exit(1)
})
