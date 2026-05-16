const { getScenes, getLevels, getMockResult } = require('../frontend/src/services/conversationApi.js')

// mock import.meta.env
const originalMeta = import.meta
Object.defineProperty(globalThis, 'import', {
  value: { meta: { env: { VITE_USE_MOCK: 'false', VITE_API_BASE_URL: 'http://localhost:8000' } } },
  writable: true,
})

describe('getScenes()', function () {
  it('should return 4 scenes', function () {
    const scenes = getScenes()
    assert.equal(scenes.length, 4)
    assert(scenes[0].id === 'cafe_order')
    assert(scenes[3].id === 'shopping')
  })
})

describe('getLevels()', function () {
  it('should return 4 levels', function () {
    const levels = getLevels()
    assert.equal(levels.length, 4)
    assert(levels[0].id === 'A1')
    assert(levels[0].name.includes('初級'))
    assert(levels[3].id === 'B2')
  })
})

describe('getMockResult()', function () {
  const EXPECTED_FIELDS = ['transcript', 'reply_en', 'reply_ja', 'feedback_ja', 'next_practice']
  const SCENE_KEYS = ['cafe_order', 'hotel_checkin', 'directions', 'shopping']
  const LEVEL_KEYS = ['A1', 'A2', 'B1', 'B2']

  it('should return valid result for every scene/level combo (16 cases)', function () {
    for (const scene of SCENE_KEYS) {
      for (const level of LEVEL_KEYS) {
        const result = getMockResult(scene, level)
        for (const field of EXPECTED_FIELDS) {
          assert(result[field] !== undefined, `Missing field: ${field} for ${scene}/${level}`)
          assert(typeof result[field] === 'string', `Field ${field} is not a string for ${scene}/${level}`)
          assert(result[field].length > 0, `Field ${field} is empty for ${scene}/${level}`)
        }
      }
    }
  })

  it('should return fallback data when scene is invalid', function () {
    const result = getMockResult('nonexistent', 'A1')
    EXPECTED_FIELDS.forEach(function (field) {
      assert(result[field] !== undefined, `Missing fallback field: ${field}`)
    })
  })

  it('should return fallback data when level is invalid', function () {
    const result = getMockResult('cafe_order', 'X')
    EXPECTED_FIELDS.forEach(function (field) {
      assert(result[field] !== undefined, `Missing fallback field: ${field}`)
    })
  })

  it('should return fallback data when both scene and level are invalid', function () {
    const result = getMockResult('nonexistent', 'X')
    EXPECTED_FIELDS.forEach(function (field) {
      assert(result[field] !== undefined, `Missing fallback field: ${field}`)
    })
  })
})
