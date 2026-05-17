const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// Set to true when backend API is unavailable; falls back to mock data
const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true'

const SCENES = [
  { id: 'cafe_order', name: 'カフェで注文する' },
  { id: 'hotel_checkin', name: 'ホテルチェックイン' },
  { id: 'directions', name: '道の聞き方' },
  { id: 'shopping', name: 'ショッピング' },
]

const LEVELS = [
  { id: 'A1', name: 'A1 (初級)' },
  { id: 'A2', name: 'A2 (初中級)' },
  { id: 'B1', name: 'B1 (中級)' },
  { id: 'B2', name: 'B2 (中上級)' },
]

const MOCK_RESULTS = {
  cafe_order: {
    A1: {
      transcript: 'I want a coffee, please.',
      reply_en: "Sure! Would you like a latte, a cappuccino, or a regular coffee?",
      reply_ja: 'はい！ラテ、カプチーノ、それとも普通のコーヒーにされますか？',
      feedback_ja: '「I want」は少し直接的です。「I\'d like」や「Can I have」を使うともっと自然です。',
      next_practice: '「I\'d like a coffee, please.」と注文してみましょう。',
    },
    A2: {
      transcript: 'Could I have a latte with oat milk, please?',
      reply_en: 'Of course! Would you like it hot or iced?',
      reply_ja: 'はい！ホットにされますか？アイスにされますか？',
      feedback_ja: '「Could I have」を使うと丁寧な注文になります。 oat milk の指定も完璧です。',
      next_practice: '「I\'d like oat milk, please.」と注文してみましょう。',
    },
    B1: {
      transcript: 'I\'d like to order a cappuccino with extra shot if possible.',
      reply_en: 'Absolutely! An extra shot cappuccino coming right up. Anything else for you?',
      reply_ja: 'はい！エクスプレスショット入りカプチーノを用意します。他にもお気軽にお申し付けください。',
      feedback_ja: '「If possible」をつけて依頼を柔らげるのが良いです。',
      next_practice: '「Can I get a cappuccino with an extra shot, please?」に挑戦してみましょう。',
    },
    B2: {
      transcript: 'I\'m in the market for a good coffee. What would you recommend around here?',
      reply_en: 'Our house blend is quite popular. It has notes of chocolate and caramel.',
      reply_ja: '弊店のオリジナルブレンドがよく使われています。チョコレートとキャラメルの香りがあります。',
      feedback_ja: '「I\'m in the market for」は自然な表現です。',
      next_practice: '「What\'s your signature drink?」と聞いてみましょう。',
    },
  },
  hotel_checkin: {
    A1: {
      transcript: 'I have a reservation.',
      reply_en: "Great! May I have your name, please?",
      reply_ja: 'はい！お名前をお聞かせいただけますか？',
      feedback_ja: '短文ですが伝わる表現です。長い文に挑戦してみましょう。',
      next_practice: '「I\'d like to check in, please.」と言ってみましょう。',
    },
    A2: {
      transcript: 'I\'d like to check in. My name is Tanaka.',
      reply_en: 'Welcome, Mr. Tanaka. A king room for three nights, correct?',
      reply_ja: 'タナカ様、ようこそ。キングルームを3泊ですね？',
      feedback_ja: '「I\'d like to」は丁寧で良い表現です。',
      next_practice: '「Is breakfast included?」と聞いてみましょう。',
    },
    B1: {
      transcript: 'I\'m here for my reservation under the name Tanaka. Do you have a gym?',
      reply_en: "Right this way, Mr. Tanaka. And yes, we have a gym on the second floor.",
      reply_ja: 'こちらのお席です、タナカ様。はい、2階にジムがございます。',
      feedback_ja: '「under the name」は予約时使用できる表現ですが「in the name of」の方が一般的です。',
      next_practice: '「Could I get a room on a higher floor?」と依頼してみましょう。',
    },
    B2: {
      transcript: 'I was wondering if you could accommodate an early check-in, if possible.',
      reply_en: 'Let me check our availability... Yes, your room is ready. Enjoy your stay!',
      reply_ja: '確認いたします...はい、お部屋は準備できております。お気軽にご利用ください。',
      feedback_ja: '「I was wondering if」は柔らかい依頼の表現で素晴らしいです。',
      next_practice: '「Could you recommend some local restaurants?」と聞いてみましょう。',
    },
  },
  directions: {
    A1: {
      transcript: 'Where is the station?',
      reply_en: "Go straight and turn left. The station is on your right.",
      reply_ja: '真っ直ぐ行って左に曲がってください。駅は右手にあります。',
      feedback_ja: '短い質問ですが伝わります。',
      next_practice: '「Excuse me, how can I get to the station?」と聞いてみましょう。',
    },
    A2: {
      transcript: 'Excuse me, how can I get to the nearest station?',
      reply_en: 'Go straight for two blocks, then turn right. It\'s next to a bank.',
      reply_ja: '2ブロック真っ直ぐ行って右に曲がってください。銀行の隣です。',
      feedback_ja: '「Excuse me」は道案内の定番です。',
      next_practice: '「Is it within walking distance?」と聞いてみましょう。',
    },
    B1: {
      transcript: 'Could you tell me how far the train station is from here?',
      reply_en: "It's about a 10-minute walk. Would you like me to draw you a map?",
      reply_ja: '歩いて約10分です。道をお描きしましょうか？',
      feedback_ja: '「Could you tell me」は丁寧な質問の形です。',
      next_practice: '「Is there a bus that goes there?」と聞いてみましょう。',
    },
    B2: {
      transcript: 'I\'m trying to find the nearest train station. Any ideas?',
      reply_en: 'Sure! Head north for about five minutes and you\'ll see it on your left.',
      reply_ja: 'はい！北へ約5分進んでください。左手に見えますよ。',
      feedback_ja: '「Any ideas?」はカジュアルな聞き方です。友人同士の会話に合っています。',
      next_practice: '「Which exit should I take?」と聞いてみましょう。',
    },
  },
  shopping: {
    A1: {
      transcript: 'How much is this?',
      reply_en: 'It\'s 2,000 yen. Would you like to buy it?',
      reply_ja: '2,000円です。お買い求めになりますか？',
      feedback_ja: 'シンプルな質問です。すぐに伝わります。',
      next_practice: '「Do you have this in a different color?」と聞いてみましょう。',
    },
    A2: {
      transcript: 'Could you help me find some shoes?',
      reply_en: 'Of course! What size are you?',
      reply_ja: 'はい！どのサイズをお探しですか？',
      feedback_ja: '「Could you help me」は丁寧な依頼です。',
      next_practice: '「Can I try this on?」と聞いてみましょう。',
    },
    B1: {
      transcript: 'I\'m looking for a gift. Do you have any recommendations?',
      reply_en: 'These scarves are very popular. Would you like to see them?',
      reply_ja: 'このスカーフはとても人気があります。ご覧になりましょうか？',
      feedback_ja: '「Do you have any recommendations?」は自然な聞き方です。',
      next_practice: '「Do you offer gift wrapping?」と聞いてみましょう。',
    },
    B2: {
      transcript: 'I\'m wondering if you have this in a larger size. The one I\'m holding is a bit too tight.',
      reply_en: 'Let me check our stock. I\'ll be right back with a larger size.',
      reply_ja: '在庫を確認してきます。大きいサイズを持ってくるわ。',
      feedback_ja: '「I\'m wondering if」は柔らかい表現で、丁寧な尋ね方です。',
      next_practice: '「Is there a discount for multiples?」と聞いてみましょう。',
    },
  },
}

export function getScenes() {
  return SCENES
}

export function getLevels() {
  return LEVELS
}

export function getMockResult(sceneId, levelId) {
  return {
    transcript: MOCK_RESULTS[sceneId]?.[levelId]?.transcript || MOCK_RESULTS.cafe_order[levelId]?.transcript,
    reply_en: MOCK_RESULTS[sceneId]?.[levelId]?.reply_en || MOCK_RESULTS.cafe_order[levelId]?.reply_en,
    reply_ja: MOCK_RESULTS[sceneId]?.[levelId]?.reply_ja || MOCK_RESULTS.cafe_order[levelId]?.reply_ja,
    feedback_ja: MOCK_RESULTS[sceneId]?.[levelId]?.feedback_ja || MOCK_RESULTS.cafe_order[levelId]?.feedback_ja,
    next_practice: MOCK_RESULTS[sceneId]?.[levelId]?.next_practice || MOCK_RESULTS.cafe_order[levelId]?.next_practice,
  }
}

export async function submitAudio(file, sceneId, levelId) {
  if (USE_MOCK) {
    // mock: wait 2 seconds then return mock data
    // This simulates the backend processing time.
    // Note: transcript should match the scene/level combo.
    return new Promise((resolve) => {
      setTimeout(() => {
        const sceneKey = SCENES.find((s) => s.id === sceneId)?.id || 'cafe_order'
        const levelKey = LEVELS.find((l) => l.id === levelId)?.id || 'A2'
        resolve(getMockResult(sceneKey, levelKey))
      }, 2000)
    })
  }

  // When backend API becomes available, call:
  //   POST /api/conversation
  //   body: FormData { audio: Blob, scene: string, level: string }
  //   response: { transcript, reply_en, reply_ja, feedback_ja, next_practice }

  const formData = new FormData()
  formData.append('audio', file)
  formData.append('scene', sceneId)
  formData.append('level', levelId)

  const resp = await fetch(`${API_BASE}/api/conversation`, {
    method: 'POST',
    body: formData,
  })

  if (!resp.ok) {
    throw new Error(`API error: ${resp.status}`)
  }

  return resp.json()
}
