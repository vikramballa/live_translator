# Smoke eval v0, 2026-10-15

72 real calls through LiveKit and the agent (12 sentences × 6 directions), M4 MacBook Air, `m4-local` profile.
The speaker audio is **our own TTS** (Piper te, Kokoro hi/en/zh), so speech recognition scores are optimistic; real people on phones will be worse. Treat this as a smoke test, not the Phase 1 benchmark.

Meaning was reviewed by Claude (the assistant) for every sentence: ✅ correct, ⚠️ understandable with a small error, ❌ wrong meaning. A native speaker should re-check before these numbers are quoted.

Raw data: `smoke-v0-call-run2.json` (all directions) and `smoke-v0-call-hi-te-fresh.json` (hi→te re-run on a fresh agent; in the full run the Mac was swapping, see below). First run before the number fixes: `smoke-v0-call-run1.json`.

## te → en

| id | heard (ASR) | translation | verdict | SE2FA |
|---|---|---|---|---|
| te01 | నమస్కారం. మీరు ఎలా ఉన్నారు? | Hello. How are u? | ✅ "u" instead of "you" | 1.47 s |
| te02 | ఈ బియ్యం ధర కిలోకి 50 రూపాయలు. | The price of this rice is Rs 50 per kg. | ✅  | 1.90 s |
| te03 | నాకు 3 కిలోల టమోటాలు కావాలి. | I want 3 kg of tomatoes. | ✅  | 1.65 s |
| te04 | మొత్తం 2500 రూపాయలు అయి్యింది. | The total has become 2500 rupees. | ✅  | 1.92 s |
| te05 | నేను రేపు రాను. | I'm not coming tomorrow. | ✅  | 1.52 s |
| te06 | ఈ ధరకు నేను అమ్మను. | I won't sell at this price. | ✅  | 1.58 s |
| te07 | నా ఫోన్ నంబర్ 9848022338. | My phone number is 9848022338. | ✅  | 2.01 s |
| te08 | సరుకు సోమవారం సాయంత్రం 5 గంటలకు వస్తుంది. | The consignment arrives at 5 pm on Monday. | ✅  | 1.83 s |
| te09 | మీరు ముందుగా సగం డబ్బు పంపండి, మిగతాది డెలివరీ తరువాత ఇవ్వండి. | You send half the money first, and give the rest after delivery. | ✅  | 1.55 s |
| te10 | ఈ నెల 15వ తేదీ లోపుడబ్బు చెల్లించాలి. | Payments must be made by the 15th of this month. | ✅  | 1.82 s |
| te11 | మీకు ఎన్ని బస్తాలు కావాలి? | How many bags do you need? | ✅  | 1.53 s |
| te12 | నాకు ఆ రంగు నచ్చలేదు, వేరే రంగు చూపించండి. | I don't like that color, show me a different color. | ✅  | 1.57 s |

## te → hi

| id | heard (ASR) | translation | verdict | SE2FA |
|---|---|---|---|---|
| te01 | నమస్కారం. మీరు ఎలా ఉన్నారు? | नमस्ते। आप कैसे हैं? | ✅  | 1.64 s |
| te02 | ఈ బియ్యం ధర కిలోకి 50 రూపాయలు. | इस चावल की कीमत 50 रुपये प्रति किलोग्राम है। | ✅  | 2.03 s |
| te03 | నాకు 3 కిలోల టమోటాలు కావాలి. | मुझे 3 किलो टमाटर चाहिए। | ✅  | 1.85 s |
| te04 | మొత్తం 2500 రూపాయలు అయ్యింది. | कुल मिलाकर 2,500 रुपये। | ✅  | 1.79 s |
| te05 | నేను రేపు రాను. | मैं कल नहीं जाऊंगा। | ⚠️ "won't go" instead of "won't come" | 1.61 s |
| te06 | ఈ ధరకు నేను అమ్మను. | मैं इस कीमत पर नहीं बेचूंगा। | ✅  | 1.69 s |
| te07 | నా ఫోన్ నంబర్ 9848022338. | मेरा फोन नंबर 9848022338 है। | ✅  | 2.27 s |
| te08 | సరుకు సోమవారం సాయంత్రం 5 గంటలకు వస్తుంది. | माल सोमवार को शाम 5 बजे आएगा। | ✅  | 1.93 s |
| te09 | మీరు ముందుగా సగం డబ్బు పంపండి, మిగతా అది డెలివరీ తరువాత ఇవ్వండి. | आप पहले आधे पैसे भेजते हैं और बाकी डिलीवरी के बाद देते हैं। | ⚠️ a statement ("you send…") instead of a request | 2.37 s |
| te10 | ఈ నెల 15వ తేదీ లోపుడబ్బు చెల్లించాలి. | इस महीने की 15 तारीख से पहले भुगतान किया जाना है। | ✅  | 2.24 s |
| te11 | మీకు ఎన్ని బస్తాలు కావాలి? | आपको कितने थैले चाहिए? | ✅  | 1.60 s |
| te12 | నాకు ఆ రంగు నచ్చలేదు, వేరే రంగు చూపించండి. | मुझे वह रंग पसंद नहीं आया, एक अलग रंग दिखाएँ। | ✅  | 2.16 s |

## te → zh

| id | heard (ASR) | translation | verdict | SE2FA |
|---|---|---|---|---|
| te01 | నమస్కారం. మీరు ఎలా ఉన్నారు? | 哈啰。你怎么样? | ✅  | 1.91 s |
| te02 | ఈ బియ్యం ధర కిలోకి 50 రూపాయలు. | 这米的价格是每公斤50卢比。 | ✅  | 2.25 s |
| te03 | నాకు 3 కిలోల టమోటాలు కావాలి. | 我要三公斤西红柿。 | ✅  | 2.04 s |
| te04 | మొత్తం 2500 రూపాయలు అయి్యింది. | 总数已达2500卢比。 | ✅  | 2.11 s |
| te05 | నేను రేపు రాను. | 我明天不来了。 | ✅  | 1.74 s |
| te06 | ఈ ధరకు నేను అమ్మను. | 我不会这么卖的。 | ⚠️ "I won't sell it like this": "at this price" is lost | 1.90 s |
| te07 | నా ఫోన్ నంబర్ 9848022338. | 我的电话号码是9848022338。 | ✅  | 2.42 s |
| te08 | సరుకు సోమవారం సాయంత్రం 5 గంటలకు వస్తుంది. | 货物于星期一下午5时抵达。 | ✅  | 2.27 s |
| te09 | మీరు ముందుగా సగం డబ్బు పంపండి, మిగతాది డెలివరీ తర్వాత ఇవ్వండి. | 你先把一半的钱寄出去 其余的在交货后还给你。 | ❌ "the rest will be returned to you": the payment direction is reversed | 2.77 s |
| te10 | ఈ నెల 15వ తేదీలోకు డబ్బు చెల్లించాలి. | 必须在本月15日之前支付。 | ✅  | 2.13 s |
| te11 | మీకు ఎన్ని బస్తాలు కావాలి? | 你需要几个包? | ✅  | 1.84 s |
| te12 | నాకు ఆ రంగు నచ్చలేదు, వేరే రంగు చూపించండి. | 我不喜欢那种颜色,给我看不同的颜色。 | ✅  | 2.43 s |

## en → te

| id | heard (ASR) | translation | verdict | SE2FA |
|---|---|---|---|---|
| en01 | Good morning, how is your family? | గుడ్ మార్నింగ్, మీ కుటుంబం ఎలా ఉంది? | ✅  | 1.07 s |
| en02 | The price is 500 rupees per kilo. | దీని ధర కిలోకు 500 రూపాయలు. | ✅  | 1.05 s |
| en03 | I need 20 bags rice by Friday. | నాకు శుక్రవారం నాటికి 20 సంచుల బియ్యం కావాలి. | ✅  | 1.21 s |
| en04 | Ple don't the goods before the payment. | దయచేసి చెల్లింపుకు ముందు వస్తువులను తీసుకోకండి. | ❌ ASR dropped "send", so it became "don't take the goods before payment" | 1.22 s |
| en05 | My number is 9876543210. | నా నంబర్ 9876543210. | ✅  | 1.17 s |
| en06 | The total comes to 12500 rupees. | మొత్తం 12500 రూపాయలు వస్తుంది. | ✅  | 1.08 s |
| en07 | I will not pay more than 300 rupees. | నేను 300 రూపాయలకు మించి చెల్లించను. | ✅  | 1.23 s |
| en08 | Can you deliver it tomorrow morning? | మీరు రేపు ఉదయం దానిని పంపిణీ చేయగలరా? | ⚠️ పంపిణీ ("distribute") for "deliver" | 1.01 s |
| en09 | The meeting is at four o'clock in the afternoon. | సమావేశం మధ్యాహ్నం నాలుగు గంటలకు జరుగుతుంది. | ✅  | 1.02 s |
| en10 | We have never had this problem before. | మాకు ఇంతకు ముందెన్నడూ ఈ సమస్య ఎదురుకాలేదు. | ✅  | 1.16 s |
| en11 | Send me 2 kilos of onions and 1 liter of oil. | నాకు 2 కిలోల ఉల్లిపాయలు మరియు 1 లీటరు నూనె పంపండి. | ✅  | 1.42 s |
| en12 | Thank you very much, see you next week. | చాలా ధన్యవాదాలు, వచ్చే వారం కలుద్దాం. | ✅  | 1.20 s |

## hi → te

| id | heard (ASR) | translation | verdict | SE2FA |
|---|---|---|---|---|
| hi01 | नमस्ते, आप कैसे हैं? | హలో, మీరు ఎలా ఉన్నారు? | ✅  | 1.09 s |
| hi02 | इस चावल का दाम 50 रुपये किलो है। | ఈ బియ్యం ధర కిలోకు 50 రూపాయలు. | ✅  | 1.66 s |
| hi03 | मुझे 3 किलो टमाटर चाहिए। | నాకు 3 కిలోల టమోటాలు కావాలి. | ✅  | 1.19 s |
| hi04 | कुल 2500 रुपये हुए। | మొత్తం రూ. 2500. | ✅  | 1.52 s |
| hi05 | मैं कल नहीं आऊँगा। | నేను రేపు వచ్చేవాడిని కాదు. | ⚠️ awkward: "I am not the one who will come" | 1.14 s |
| hi06 | इस दाम पर मैं नहीं बेचूँगा। | ఈ ధరకు నేను విక్రయించను. | ✅  | 1.25 s |
| hi07 | मेरा नंबर 9848022338 है। | నా నంబర్ 9848022338. | ✅  | 1.35 s |
| hi08 | माल सोमवार शाम 5 बजे पहुँचेगा। | సోమవారం సాయంత్రం 5 గంటలకు సరుకు చేరుకుంటుంది. | ✅  | 1.21 s |
| hi09 | आप पहले आधे पैसे भेज दीजिए, बाक़ डिलीवरी के बाद दीजिए। | మీరు మొదటి సగం డబ్బును పంపండి, డెలివరీ తర్వాత మిగిలిన మొత్తాన్ని చెల్లించండి. | ✅  | 1.46 s |
| hi10 | इस महीने की पन्ंद्रह तारीख तक भुगतान करना है। | ఈ నెల పదిహేను తేదీ నాటికి చెల్లించాల్సి ఉంటుంది. | ✅  | 1.22 s |
| hi11 | आपको कितने बोरे चाहिए? | మీకు ఎన్ని సంచులు కావాలి? | ✅  | 1.27 s |
| hi12 | मुझे वह रंग पसंद नहीं आया, दूसरा रंग दिखाए। | ఆ రంగును నేను ఇష్టపడలేదు, మరొక రంగును చూపించాను. | ❌ "…I showed another colour" instead of "show me another colour" (ASR: दिखाए vs दिखाइए) | 1.41 s |

## zh → te

| id | heard (ASR) | translation | verdict | SE2FA |
|---|---|---|---|---|
| zh01 | 你好,最近怎么样Ｂ | హలో. మీరు ఎలా ఉన్నారు, బి? | ⚠️ Whisper added a stray "B", which the translation repeats | 1.98 s |
| zh02 | 这个大米每公斤50块。 | కిలో బియ్యానికి 50 యువాన్. | ✅  | 2.00 s |
| zh03 | 我要3公斤西红柿。 | నాకు 3 కిలోల టమోటాలు కావాలి. | ✅  | 2.07 s |
| zh04 | 一共2500块。 | అంటే 2,500 యువాన్. | ⚠️ "that is 2,500 yuan" instead of "2,500 yuan in total" | 1.85 s |
| zh05 | 我明天不来。 | నేను రేపు రావడం లేదు. | ✅  | 1.93 s |
| zh06 | 这个价格我不卖。 | నేను ఈ ధరను విక్రయించడం లేదు. | ⚠️ awkward: "I am not selling this price" | 1.96 s |
| zh07 | 我的电话是13812345678。 | నా నంబర్ 13812345678. | ✅  | 2.17 s |
| zh08 | 货物星期一下午5点到。 | సోమవారం సాయంత్రం 5 గంటలకు సరుకు చేరుకుంటుంది. | ✅  | 2.04 s |
| zh09 | 请先付一半的钱,剩下的获到了再付。 | దయచేసి మొదట సగం డబ్బు చెల్లించండి, మిగిలినది మాకు వచ్చినప్పుడు చెల్లించబడుతుంది. | ✅  | 2.36 s |
| zh10 | 这个月15号之前要付款。 | ఈ నెల 15వ తేదీలోగా చెల్లింపు చేయాల్సి ఉంటుంది. | ✅  | 2.20 s |
| zh11 | 你需要多少袋7? | మీకు ఎన్ని సంచులు అవసరం? | ✅  | 1.93 s |
| zh12 | 我不喜欢这个颜色,给我看看别的颜色。 | నాకు ఈ రంగు ఇష్టం లేదు. నాకు మరో రంగు చూపించు. | ✅  | 2.19 s |
