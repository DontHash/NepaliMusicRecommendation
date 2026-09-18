# Line mood gold — review sheet (agent_v1)

Review rules live in `eval/line_mood_policy.md`. Fill `user_emotion` /
`user_note` in `eval/line_mood_review.csv` where you disagree; empty
`user_emotion` means the agent label is accepted. `model_pick` is the
current probe's per-line guess for context.

## 182 · Na Aau Feri — Akash khadka

Song gold: **sadness** (negative) — heartbreak and lost trust

| idx | x | text | label | model | probs (j/s/a) | cue | diff | note |
|----:|--:|------|-------|-------|---------------|-----|------|------|
| 0 | 1 | धेरै कुरा भन्नु थियो, सुन्न छैनौ तिमी | sadness | sadness | joy 0.06 sadness 0.84 anger 0.06 | context_only | medium | words unsaid; unheard |
| 1 | 1 | भारी हुन्छ मन मेरो, छाडी गयौ मलाई | sadness | sadness | joy 0.06 sadness 0.84 anger 0.06 | lexical | easy | heavy heart, left behind |
| 2 | 1 | वाचाहरू झूटो रहेछ तिमीले गरको मलाई | sadness | sadness | joy 0.05 sadness 0.84 anger 0.05 | context_only | medium | false promises; grief-toned |
| 3 | 1 | साथ हाम्रो अधूरो रहेछ, टाढा हुनुपर्यो है | sadness | sadness | joy 0.05 sadness 0.84 anger 0.04 | lexical | medium | incomplete bond; parting |
| 4 | 1 | नअल्झ है फेरि तिमी कतै | sadness | sadness | joy 0.05 sadness 0.85 anger 0.05 | context_only | medium | bittersweet warning |
| 5 | 1 | दुख्छ यो मन मायामा परे | sadness | sadness | joy 0.05 sadness 0.85 anger 0.05 | lexical | easy | heart hurts in love |
| 6 | 1 | नफ फर्क है फेरि मसँग नै | sadness | sadness | joy 0.05 sadness 0.85 anger 0.05 | context_only | medium | don't-return warning |
| 7 | 1 | मायामा विश्वास हराइसक्यो है | sadness | sadness | joy 0.06 sadness 0.78 anger 0.06 | lexical | easy | trust lost |
| 8 | 1 | नआऊ फेरि तिमी सपनी बनी | sadness | sadness | joy 0.06 sadness 0.77 anger 0.06 | address | easy | don't come even in dreams |
| 9 | 1 | सम्झेर रुनु छैन फेरि मलाई | sadness | sadness | joy 0.07 sadness 0.75 anger 0.06 | negation | medium | mustn't cry (रुनु छैन) |
| 10 | 1 | नगरिदेऊ अब याद मलाई | sadness | sadness | joy 0.10 sadness 0.57 anger 0.04 | address | medium | don't give memories |
| 11 | 1 | सुरुवात गर नयाँ कहानी आफ्नै, आफ्नै | neutral | sadness | joy 0.11 sadness 0.55 anger 0.03 | context_only | medium | farewell well-wishing |
| 12 | 1 | आफ्नै कहानी लेख अब | neutral | sadness | joy 0.11 sadness 0.55 anger 0.03 | context_only | medium | write your own story |
| 13 | 1 | बिर्सिदेऊ मलाई, एउटा याद सोच | sadness | sadness | joy 0.14 sadness 0.45 anger 0.01 | address | medium | forget-me plea |
| 14 | 1 | सपना तिम्रो सबै पूरा गर | neutral | neutral | joy 0.15 sadness 0.41 anger 0.01 | context_only | medium | well-wish |
| 15 | 1 | मात्र कामना मेरो तिम्रो साथ | sadness | neutral | joy 0.15 sadness 0.41 anger 0.01 | context_only | medium | only wish: togetherness |
| 16 | 1 | साथ, मात्र कामना साथ | sadness | neutral | joy 0.15 sadness 0.41 anger 0.01 | repetition | medium | togetherness refrain |
| 17 | 1 | साथ मात्र याद छ | sadness | neutral | joy 0.16 sadness 0.41 anger 0.00 | context_only | medium | only memory remains |
| 18 | 1 | एचएमएम-एमएमएम, एचएमएम | neutral | neutral | joy 0.16 sadness 0.41 anger 0.00 | filler | easy | humming |

## 263 · Aakashma Lekhe — Anil Singh

Song gold: **none** (positive) — romantic devotion (name written in sky)

| idx | x | text | label | model | probs (j/s/a) | cue | diff | note |
|----:|--:|------|-------|-------|---------------|-----|------|------|
| 0 | 1 | हावाले आए उडाए दियो | neutral | sadness | joy 0.29 sadness 0.57 anger 0.10 | context_only | medium | name blown away; conceit |
| 1 | 1 | जुन्नमा लेखे तिम्रो नौ | neutral | sadness | joy 0.29 sadness 0.57 anger 0.10 | context_only | easy | name on moon; devotion |
| 2 | 1 | ग्रहणले आए ढाकी दियो | neutral | sadness | joy 0.29 sadness 0.57 anger 0.10 | context_only | medium | eclipse covers it |
| 3 | 2 | हृद्यमा लेखे तिम्रो नौ | neutral | sadness | joy 0.36 sadness 0.52 anger 0.06 | context_only | easy | name in heart |
| 4 | 1 | प्रीत बानी फक्रिदियो? | neutral | sadness | joy 0.36 sadness 0.52 anger 0.06 | context_only | medium | love flourished? |
| 5 | 1 | पगल सम्झे पागल साही | neutral | sadness | joy 0.36 sadness 0.51 anger 0.06 | context_only | medium | if called mad, so be it |
| 6 | 1 | जोगी सम्झे जोगी साही | neutral | neutral | joy 0.41 sadness 0.45 anger 0.02 | context_only | medium | if called ascetic, so be it |
| 7 | 1 | जे भने ने मा हु प्रेमी | neutral | neutral | joy 0.41 sadness 0.44 anger 0.02 | context_only | easy | I am a lover |
| 8 | 1 | प्रेमको मा पूजारी? | neutral | neutral | joy 0.41 sadness 0.44 anger 0.02 | context_only | medium | love's priest? |
| 9 | 1 | फुलमा लेखे तिम्रो नौ | neutral | neutral | joy 0.36 sadness 0.42 anger 0.03 | context_only | easy | name on flower |
| 10 | 1 | भावराले टप्पा टिपे दियो | neutral | neutral | joy 0.36 sadness 0.41 anger 0.03 | context_only | medium | bee takes the mark |
| 11 | 1 | पातमा लेखे तिम्रो नौ | neutral | neutral | joy 0.36 sadness 0.41 anger 0.03 | context_only | easy | name on leaf |
| 12 | 1 | सीतले आए बगाई दियो | neutral | sadness | joy 0.30 sadness 0.49 anger 0.04 | context_only | medium | water washed it |
| 14 | 1 | सर्गम बानी गुन्जी दियो | neutral | sadness | joy 0.28 sadness 0.52 anger 0.04 | context_only | medium | echoes in melody |
| 15 | 1 | कुरा गरे कुराई को दुःख | sadness | sadness | joy 0.23 sadness 0.61 anger 0.03 | context_only | hard | grief/suffering in separation |
| 16 | 1 | तिमी बिना कहा चा सुखा | sadness | sadness | joy 0.21 sadness 0.65 anger 0.03 | context_only | medium | no happiness without you |
| 17 | 1 | तिम्रो यादमा हरपाल | neutral | sadness | joy 0.21 sadness 0.65 anger 0.03 | context_only | medium | always in your memory |
| 18 | 1 | भये मा प्रेम बियोगे | sadness | sadness | joy 0.23 sadness 0.62 anger 0.03 | context_only | medium | if separated in love |
| 19 | 1 | हिमालमा लेखे तिम्रो नौ | neutral | sadness | joy 0.29 sadness 0.52 anger 0.04 | context_only | easy | name on Himalaya |
| 20 | 1 | हेउ सँगै पग्ली दियो | neutral | sadness | joy 0.29 sadness 0.52 anger 0.04 | context_only | medium | snow melted together |
| 21 | 1 | किनारमा लेखे तिम्रो नौ | neutral | sadness | joy 0.29 sadness 0.52 anger 0.04 | context_only | easy | name on shore |
| 22 | 1 | चालले आए बगाये दियो | neutral | neutral | joy 0.40 sadness 0.36 anger 0.07 | context_only | medium | waves washed away |
| 23 | 1 | हृदिये मा लेखे तिम्रो नौ | neutral | joy | joy 0.45 sadness 0.28 anger 0.08 | context_only | easy | name in heart |
| 24 | 1 | धड्कन बानी धड्की दियो | neutral | joy | joy 0.46 sadness 0.27 anger 0.08 | context_only | medium | heartbeat image |

## 757 · Asaar — Bipul Chettri

Song gold: **joy** (mixed) — rain joy + fleeting life; mixed

| idx | x | text | label | model | probs (j/s/a) | cue | diff | note |
|----:|--:|------|-------|-------|---------------|-----|------|------|
| 0 | 1 | पानी पऱ्यो सरर, छाना बज्यो गरर | joy | sadness | joy 0.38 sadness 0.71 anger 0.00 | lexical | medium | rain joy imagery (सरर) |
| 1 | 1 | मनमा उठ्यो आज मेरो आनन्दको लहर | joy | sadness | joy 0.38 sadness 0.71 anger 0.00 | lexical | easy | आनन्द explicit |
| 2 | 2 | हिजोको बिपना आज भएछ सपना | sadness | sadness | joy 0.32 sadness 0.73 anger 0.01 | context_only | medium | sorrow turned to dream; nostalgic lament |
| 3 | 1 | ए कान्छी, कति चाँडै बितेको यो जीवन | sadness | sadness | joy 0.32 sadness 0.73 anger 0.01 | context_only | medium | life passed quickly; lament |
| 4 | 1 | पानी पऱ्यो सरर, भिज्यो कालेबुङ सहर | joy | sadness | joy 0.28 sadness 0.75 anger 0.01 | context_only | medium | city-soaked rain joy |
| 5 | 1 | कालो-कालो बादल चढी फर्की आयो असार, लहै | joy | sadness | joy 0.34 sadness 0.65 anger 0.02 | context_only | medium | monsoon return; delight |
| 6 | 1 | जिन्दगी कहिले घाम कहिले पानी, लैबरी लै | neutral | sadness | joy 0.40 sadness 0.56 anger 0.02 | context_only | medium | sun-and-rain philosophy |
| 7 | 1 | माया नै सबैभन्दा ठूलो कुरो रैछ नि है | neutral | joy | joy 0.48 sadness 0.35 anger 0.02 | context_only | medium | love is greatest |
| 8 | 1 | चारैतिर निला-निला आकाश नै छायो है | joy | joy | joy 0.50 sadness 0.32 anger 0.02 | context_only | medium | blue sky delight |
| 9 | 1 | वरिपरि लागेको यो कुइरो हरायो है | joy | joy | joy 0.48 sadness 0.35 anger 0.03 | context_only | medium | fog cleared; relief |
| 10 | 1 | मनलाई साँचो राखी हिँडिँरहेछु | neutral | joy | joy 0.48 sadness 0.36 anger 0.03 | context_only | medium | keeping heart true |
| 11 | 1 | म तिम्रो साहारामै बाँचिरहेछु, मायालु | neutral | sadness | joy 0.41 sadness 0.52 anger 0.02 | context_only | medium | living on your support |
| 12 | 1 | पानी पऱ्यो सरर, झोडा बग्याे गरर | joy | sadness | joy 0.33 sadness 0.62 anger 0.02 | context_only | medium | streams flowing; rain joy |
| 13 | 1 | फर्की आएँ तिम्रैतिर छाडी सारा संसार | neutral | sadness | joy 0.22 sadness 0.76 anger 0.01 | context_only | medium | returned to you; devotion |
| 15 | 1 | ए कान्छी, कति चाँडै बितेकाे याे जीवन | sadness | sadness | joy 0.23 sadness 0.80 anger 0.01 | context_only | medium | life passed quickly variant |
| 16 | 1 | पानी पऱ्यो सरर, भिज्याे कालेबुङ सहर | joy | sadness | joy 0.43 sadness 0.53 anger 0.03 | context_only | medium | city-soaked rain variant |
| 17 | 1 | कालाे-कालाे बादल चढी फर्की आयाे असार | joy | joy | joy 0.58 sadness 0.35 anger 0.03 | context_only | medium | monsoon return variant |
| 18 | 6 | लैबरी, लैबरी, लैबरी लै, ओ नानी, लैबरी, लैबरी लै | neutral | joy | joy 0.72 sadness 0.18 anger 0.03 | filler | easy | लैबरी filler refrain |

## 1365 · Sabin Rai - Timi Nai Hau [Romanized] — Genius Romanizations

Song gold: **joy** (positive) — nan

| idx | x | text | label | model | probs (j/s/a) | cue | diff | note |
|----:|--:|------|-------|-------|---------------|-----|------|------|
| 0 | 1 | उपहार स्वरूप यो तस्बीर माया गर्ने हरू लाई | neutral | sadness | joy 0.13 sadness 0.61 anger 0.05 | context_only | medium | gift picture to lovers |
| 1 | 1 | भलाई चोटो होला यहा सबै दृश्य अटाउन लाई | neutral | sadness | joy 0.14 sadness 0.60 anger 0.05 | context_only | hard | corrupt line |
| 2 | 1 | जिन्दगी नरहोस्, रही रहनेछ येसमा कैद पाल हरू | neutral | sadness | joy 0.17 sadness 0.56 anger 0.05 | context_only | hard | moments captured; philosophical |
| 3 | 1 | तिमी चाउ, तिम्रो प्यारो मान्छे चा | neutral | sadness | joy 0.23 sadness 0.49 anger 0.05 | context_only | medium | your dear person; devotion |
| 4 | 1 | त्यो भन्दा अरु के नै चाहिँचा एउटा माया गर्ने ब्यक्ति लाई | neutral | neutral | joy 0.39 sadness 0.32 anger 0.04 | context_only | medium | what else a lover needs |
| 5 | 4 | तिमी नै हाउ | neutral | neutral | joy 0.41 sadness 0.31 anger 0.04 | context_only | easy | it's you; devotion |
| 6 | 1 | मलाई माया गर्ने | neutral | joy | joy 0.64 sadness 0.15 anger 0.03 | context_only | easy | one who loves me |
| 7 | 4 | तिमी नै हाउ, तिमी नै हाउ | neutral | joy | joy 0.70 sadness 0.10 anger 0.02 | context_only | easy | it's you refrain |
| 10 | 1 | मलाई खुशी डाइनी | joy | joy | joy 0.83 sadness 0.06 anger 0.01 | lexical | easy | gives me happiness (खुशी) |
| 15 | 1 | हेरा मलाई समाउ यो हात | neutral | joy | joy 0.60 sadness 0.17 anger 0.02 | address | medium | hold this hand |
| 16 | 1 | नछुटोश हाम्रो दरिलो साथ | neutral | neutral | joy 0.34 sadness 0.45 anger 0.03 | context_only | medium | wish bond unbroken |
| 17 | 1 | देख्ने ले देखोश, सुनोश | neutral | sadness | joy 0.27 sadness 0.52 anger 0.03 | context_only | medium | let them see/hear |
| 18 | 1 | हाम्रो यो सम्बन्ध | neutral | sadness | joy 0.27 sadness 0.52 anger 0.03 | context_only | medium | this relationship |
| 19 | 1 | पश्चाताप चैन कुनै यहा | joy | sadness | joy 0.30 sadness 0.49 anger 0.05 | context_only | medium | no regret; contentment |
| 20 | 1 | खुसी चाउ हामी चाउ जहा | joy | sadness | joy 0.32 sadness 0.53 anger 0.08 | lexical | medium | we want happiness |
| 21 | 1 | वन्ने ले वनोश, गरोश | neutral | sadness | joy 0.32 sadness 0.53 anger 0.08 | context_only | medium | let them talk; resolve |
| 22 | 1 | हाम्रो ब्यारे कुरा | neutral | sadness | joy 0.37 sadness 0.47 anger 0.10 | context_only | medium | talk about us |
| 23 | 1 | जाति जे चा मेरो | neutral | joy | joy 0.50 sadness 0.31 anger 0.13 | context_only | medium | whatever my caste |
| 24 | 1 | तिमी हाउ | neutral | joy | joy 0.50 sadness 0.31 anger 0.13 | context_only | easy | it's you fragment |

## 1469 · Lekali Hey Choyako Doko — Harish Mathema

Song gold: **joy** (positive) — playful folk flirtation

| idx | x | text | label | model | probs (j/s/a) | cue | diff | note |
|----:|--:|------|-------|-------|---------------|-----|------|------|
| 0 | 2 | लेकाली Hey Hey चोया को डोको | neutral | joy | joy 0.85 sadness 0.05 anger 0.07 | address | medium | playful folk prop and address |
| 1 | 2 | सानो माया Hey Hey लगाउने धोको | neutral | joy | joy 0.85 sadness 0.05 anger 0.07 | context_only | medium | teasing risk of attachment |
| 2 | 2 | नपुग्दै मा मर्चु पो क्यारे | neutral | joy | joy 0.80 sadness 0.11 anger 0.04 | metaphor | hard | playful dying hyperbole; ambiguous |
| 3 | 2 | Hey भना सोल्टी बराबर नधती | neutral | joy | joy 0.80 sadness 0.11 anger 0.04 | context_only | hard | folk banter; unclear |
| 4 | 1 | (बहायो खोला बेसी घर्यो सम्मै | neutral | joy | joy 0.73 sadness 0.15 anger 0.03 | context_only | medium | river-valley scenery |
| 5 | 1 | तिम्रो माया कलेजी मा ताम्मै) - 2 | neutral | joy | joy 0.68 sadness 0.19 anger 0.02 | context_only | medium | love-in-heart; no happiness |
| 6 | 1 | आखै मा गजलु लपक्कै | neutral | joy | joy 0.68 sadness 0.18 anger 0.02 | context_only | medium | eyes-liner flirt image |
| 7 | 1 | भना माया लाएदिउँ की चापककै | neutral | joy | joy 0.66 sadness 0.18 anger 0.02 | context_only | medium | teasing invitation |
| 8 | 1 | बैसैमा बैसैमा मर्चु पो क्यारे | neutral | joy | joy 0.70 sadness 0.16 anger 0.02 | metaphor | hard | repeated dying hyperbole |
| 9 | 2 | Hey भना सोल्टी बराबर नधती - 2 | neutral | joy | joy 0.73 sadness 0.15 anger 0.03 | repetition | medium | folk refrain |
| 10 | 1 | (रातो चोलो पाखुरीमा तिमिक्कै | neutral | joy | joy 0.61 sadness 0.26 anger 0.03 | context_only | medium | red-blouse teasing image |
| 11 | 1 | माया बस्यो मखाइमा घिमिक्कै) - 2 | neutral | joy | joy 0.56 sadness 0.30 anger 0.03 | context_only | medium | love glowing on face |
| 12 | 1 | के गोड्नु कर्कला बारी | neutral | joy | joy 0.46 sadness 0.39 anger 0.04 | metaphor | medium | folk garden image |
| 13 | 1 | पर्खा तिमीलाई रोएरहने नपारी | neutral | joy | joy 0.46 sadness 0.39 anger 0.04 | address | medium | teasing reassurance; negated weeping |
| 14 | 1 | बैसैमा.. बैसैमा मर्चु पी क्यारे | neutral | joy | joy 0.62 sadness 0.24 anger 0.04 | context_only | hard | folk refrain fragment |

## 1511 · Mero Man Ma Aago — Himal Sagar

Song gold: **anger** (negative) — betrayal burns the heart

| idx | x | text | label | model | probs (j/s/a) | cue | diff | note |
|----:|--:|------|-------|-------|---------------|-----|------|------|
| 0 | 2 | मेरो मान मा आगो लाउने को | anger | joy | joy 0.69 sadness 0.15 anger 0.06 | metaphor | medium | who set my heart on fire |
| 1 | 2 | मेरो मान धार धार रुआँए को | anger | joy | joy 0.69 sadness 0.15 anger 0.06 | metaphor | medium | accusatory; tears as injury |
| 4 | 2 | तिम्रो पानी चाटी भित्र आगो डाँकियोस् | anger | joy | joy 0.62 sadness 0.20 anger 0.05 | metaphor | hard | curse: fire inside you |
| 5 | 9 | सँधै भरि माया पाउन मुटु चल्कियोस् | anger | joy | joy 0.53 sadness 0.28 anger 0.06 | metaphor | hard | curse: heart burns longing |
| 7 | 2 | चुलेसी ले रेटी रेटी तिखो चुरा चलायोउ | anger | joy | joy 0.63 sadness 0.29 anger 0.09 | metaphor | hard | knife-edge betrayal image |
| 8 | 1 | टिमले माया अन्तै सर्योउ जोगी पारी सबै हसायौ | anger | joy | joy 0.81 sadness 0.17 anger 0.07 | context_only | medium | love shifted; mocked |
| 10 | 1 | टिमले माया अन्तै सर्योउ जोरी पारी सबै हसायौ | anger | joy | joy 0.66 sadness 0.28 anger 0.17 | context_only | medium | love shifted; mocked variant |
| 11 | 1 | हासी हासी अचानो मा रेट्ने को | anger | sadness | joy 0.46 sadness 0.50 anger 0.19 | metaphor | medium | grinding on stone laughing |
| 12 | 1 | जिन्दगी नै डढेलो झैं आगो सल्कियोस् | anger | joy | joy 0.48 sadness 0.44 anger 0.14 | metaphor | hard | life as wildfire |
| 15 | 2 | तिमीले ता दुबै चड्योउ माना मिल्ने मुटु लाई | anger | joy | joy 0.55 sadness 0.17 anger 0.01 | context_only | hard | burdened the meeting heart |
| 16 | 2 | जिन्दगी भर आँसु दियोउ चोखो माया लाउने लाई | anger | neutral | joy 0.41 sadness 0.27 anger 0.01 | context_only | medium | lifetime of tears; blame |
| 19 | 1 | अर्का मन धार धारी रुआँए को | anger | sadness | joy 0.18 sadness 0.67 anger 0.06 | metaphor | hard | accusatory betrayal; parallel indictment |
| 20 | 1 | सुखा सँधै ताधै बाटा अन्तै तर्कियोस् | anger | sadness | joy 0.28 sadness 0.53 anger 0.06 | metaphor | hard | curse: may you drift |
| 23 | 1 | मेरो मन धार धार रुआने को | anger | joy | joy 0.63 sadness 0.16 anger 0.01 | metaphor | medium | who made my heart weep |

## 1938 · Aama — Mantra Band

Song gold: **joy** (positive) — gratitude and warmth toward mother

| idx | x | text | label | model | probs (j/s/a) | cue | diff | note |
|----:|--:|------|-------|-------|---------------|-----|------|------|
| 0 | 2 | अमूल्य मेरो मेरो जीवन | joy | joy | joy 0.63 sadness 0.18 anger 0.00 | context_only | medium | precious-life gratitude |
| 1 | 2 | उपहार तिम्रै नै हो | joy | joy | joy 0.63 sadness 0.18 anger 0.00 | lexical | medium | gift of life gratitude |
| 2 | 1 | कोसेली धेरै धेरै चोखो | joy | joy | joy 0.63 sadness 0.18 anger 0.00 | context_only | medium | pure gift gratitude |
| 3 | 1 | तिम्रै मायाको प्रतिक हो | joy | joy | joy 0.63 sadness 0.17 anger 0.00 | context_only | medium | symbol of love gratitude |
| 4 | 1 | तिम्रो न्यानो काख भरि | joy | joy | joy 0.64 sadness 0.17 anger 0.00 | context_only | medium | warm-lap warmth |
| 5 | 1 | कति सपना मैले देखें | joy | joy | joy 0.64 sadness 0.17 anger 0.00 | context_only | medium | dreams under her care |
| 6 | 1 | समाई तिम्रा हातहरु | joy | joy | joy 0.65 sadness 0.16 anger 0.01 | context_only | medium | holding hands warmth |
| 7 | 1 | कति बाटो म हिडें | neutral | joy | joy 0.69 sadness 0.12 anger 0.01 | none | medium | paths walked; factual |
| 8 | 5 | संसार तिमी नै हौ आमा | neutral | joy | joy 0.69 sadness 0.12 anger 0.01 | context_only | medium | adoration; no happiness |
| 9 | 5 | अपार तिमी नै छौ आमा | neutral | joy | joy 0.69 sadness 0.12 anger 0.01 | context_only | medium | adoration; no happiness |
| 10 | 1 | हे आमा हे आमा हे आमा | neutral | joy | joy 0.64 sadness 0.13 anger 0.02 | repetition | easy | vocative refrain |
| 13 | 1 | सबै रुप तिम्रो माया सरी | neutral | joy | joy 0.62 sadness 0.13 anger 0.03 | context_only | medium | praised likeness |
| 14 | 1 | तिमी नै मेरो धर्तीको परी | neutral | neutral | joy 0.38 sadness 0.36 anger 0.04 | context_only | medium | angel praise |
| 15 | 1 | बलिदान तिम्रो नि:स्वार्थ छ | joy | neutral | joy 0.33 sadness 0.40 anger 0.04 | context_only | medium | grateful for sacrifice |
| 16 | 1 | यो माया तिम्रो चोखो छ | joy | neutral | joy 0.32 sadness 0.41 anger 0.04 | context_only | medium | pure-love gratitude |
| 17 | 1 | कालो कालो रातमा | sadness | sadness | joy 0.21 sadness 0.50 anger 0.04 | metaphor | medium | dark-night suffering imagery |
| 18 | 1 | धेरै दुख्ने घातमा | sadness | sadness | joy 0.17 sadness 0.55 anger 0.04 | lexical | medium | hurtful-blow suffering |
| 19 | 2 | तिमीले मलाई सम्हाल्यौ | joy | sadness | joy 0.17 sadness 0.55 anger 0.04 | context_only | medium | comforted; being held |
| 20 | 1 | धेरै घाउमा धेरै बिझ्ने पिडामा | sadness | neutral | joy 0.28 sadness 0.39 anger 0.05 | lexical | medium | wounds and stinging pain |
| 22 | 2 | तिम्रै निम्ति म हाँसी दिन्छु | joy | neutral | joy 0.32 sadness 0.33 anger 0.05 | lexical | medium | smile for her |
| 23 | 2 | तिम्रै निम्ति म बाँची दिन्छु | neutral | neutral | joy 0.34 sadness 0.38 anger 0.04 | context_only | medium | live-for-you devotion |
| 26 | 1 | आँशु मेरो पुछि दियौ | joy | sadness | joy 0.19 sadness 0.64 anger 0.02 | context_only | medium | tears wiped; comfort |
| 27 | 1 | दुख मेरो बुझि दियौ | joy | sadness | joy 0.17 sadness 0.66 anger 0.01 | context_only | medium | sorrow understood; comfort |
| 28 | 1 | हरेक पल सुख दिन चाह्यौ | joy | sadness | joy 0.17 sadness 0.66 anger 0.01 | lexical | medium | wished happiness (सुख) |
| 29 | 1 | बाटो मलाई देखाई दियौ | joy | sadness | joy 0.27 sadness 0.54 anger 0.01 | context_only | medium | shown the way; gratitude |
| 30 | 1 | दियो मेरो जलाई दियौ | joy | sadness | joy 0.32 sadness 0.47 anger 0.01 | metaphor | medium | lit my lamp |
| 31 | 1 | उज्यालो जीवन बनाइदियौ | joy | sadness | joy 0.32 sadness 0.47 anger 0.01 | metaphor | medium | made life bright |
| 36 | 1 | हे आमा हे आमा | neutral | joy | joy 0.66 sadness 0.10 anger 0.02 | repetition | easy | vocative refrain |

## 2061 · Dherai Dherai — Mingma Sherpa

Song gold: **none** (neutral) — questioning whose love has bloomed

| idx | x | text | label | model | probs (j/s/a) | cue | diff | note |
|----:|--:|------|-------|-------|---------------|-----|------|------|
| 0 | 1 | मा संग माना मिलाउछु वन्दै | neutral | joy | joy 0.49 sadness 0.43 anger 0.01 | context_only | hard | corrupt OCR line |
| 1 | 1 | माया गसु वन्छ अन्त्यमा | neutral | joy | joy 0.49 sadness 0.43 anger 0.01 | context_only | hard | corrupt OCR line |
| 2 | 2 | मायालु मेरी माया | neutral | joy | joy 0.49 sadness 0.43 anger 0.01 | address | easy | my love, my love |
| 3 | 4 | कसको माया लाग्यो वना | neutral | joy | joy 0.49 sadness 0.44 anger 0.02 | context_only | medium | whose love? questioning |
| 4 | 2 | कस्तो यादा आयो वना | neutral | joy | joy 0.49 sadness 0.44 anger 0.02 | context_only | medium | what memory came |
| 6 | 1 | के वनी बोलाउ तिमीलाई | neutral | joy | joy 0.49 sadness 0.44 anger 0.02 | context_only | medium | what to call you |
| 7 | 1 | वनिदेउ वनिदेउ | neutral | joy | joy 0.56 sadness 0.40 anger 0.02 | repetition | easy | वनिदेउ filler |

## 2164 · Aja bholi hareko saajh — Narayan Gopal

Song gold: **sadness** (negative) — drinking to forget sorrow

| idx | x | text | label | model | probs (j/s/a) | cue | diff | note |
|----:|--:|------|-------|-------|---------------|-----|------|------|
| 0 | 1 | [आज भोली हरेक साँझ, मातिन थालेछ। | sadness | neutral | joy 0.43 sadness 0.32 anger 0.02 | context_only | medium | evening drunkenness |
| 1 | 1 | जिन्दगी देखि जिन्दगी, आतिन थालेछ।]...२ | sadness | neutral | joy 0.42 sadness 0.34 anger 0.02 | context_only | medium | life distressed |
| 2 | 3 | आज भोली, हरेक साँझ। | sadness | neutral | joy 0.39 sadness 0.39 anger 0.03 | repetition | medium | every-evening refrain |
| 3 | 1 | रहरै रहरमा पिए, विवश भएर पिए।...२ | sadness | neutral | joy 0.38 sadness 0.40 anger 0.03 | context_only | medium | helpless drinking |
| 4 | 1 | दुखमा पिए, सुखमा पिए।...२ | sadness | sadness | joy 0.35 sadness 0.48 anger 0.06 | lexical | medium | drank in sorrow and joy; escapism |
| 5 | 1 | पिउदिन पिउदिन, भन्दै पिए। | sadness | neutral | joy 0.41 sadness 0.42 anger 0.06 | context_only | medium | self-destructive pledge |
| 6 | 1 | आजभोली जिन्दगानी, छोटिन थालेछ। | sadness | joy | joy 0.51 sadness 0.36 anger 0.07 | lexical | medium | life shortening |
| 7 | 2 | जिन्दगी देखि जिन्दगी, आतिन थालेछ। | sadness | joy | joy 0.52 sadness 0.35 anger 0.05 | lexical | medium | life distressed refrain |
| 9 | 1 | मन्दिरमा बसेर पिए, मसानमा लडेर पिए।...२ | sadness | joy | joy 0.51 sadness 0.34 anger 0.04 | metaphor | medium | temple vs cremation drinking |
| 10 | 1 | नाचेर पिए, हाँसेर पिए।...२ | sadness | neutral | joy 0.43 sadness 0.39 anger 0.04 | context_only | hard | forced gaiety; escapism |
| 11 | 1 | एकान्तमा कहिलेकाहीं, रुदै पिए। | sadness | sadness | joy 0.29 sadness 0.53 anger 0.03 | lexical | easy | crying alone (रुदै) |
| 12 | 1 | आजभोली हरेक रात, रक्सिन थालेछ। | sadness | sadness | joy 0.27 sadness 0.55 anger 0.03 | context_only | medium | nightly intoxication |

## 2252 · Timile Pani Ma Jastai — Narayan Gopal

Song gold: **sadness** (mixed) — melancholic devotion; mixed

| idx | x | text | label | model | probs (j/s/a) | cue | diff | note |
|----:|--:|------|-------|-------|---------------|-----|------|------|
| 0 | 3 | मायालुको सम्झनामा आफूलाई बिर्सी हेरा - एक्स2 | sadness | sadness | joy 0.12 sadness 0.83 anger 0.01 | context_only | medium | remembrance self-loss |
| 1 | 1 | सुन साँ रात सँगै एकान्त भयेर हेरा - एक्स2 | sadness | sadness | joy 0.15 sadness 0.78 anger 0.01 | context_only | medium | alone together; longing |
| 2 | 1 | सागरा को लहरा जस्तै अशान्त भयेर हेरा | sadness | sadness | joy 0.17 sadness 0.75 anger 0.01 | metaphor | medium | restless like waves |
| 3 | 1 | आशुका थोपा जस्तै भुईमा खसेर हेरा | sadness | sadness | joy 0.33 sadness 0.49 anger 0.02 | metaphor | easy | teardrops falling |
| 5 | 1 | पूजा को फुल जस्तै दिन दिन मरेर हेरा - एक्स2 | sadness | neutral | joy 0.39 sadness 0.43 anger 0.01 | metaphor | medium | flower dying daily |
| 6 | 1 | ढुंगाको मूर्ति जस्तै दोबाटोमा बची हेरा | sadness | sadness | joy 0.31 sadness 0.56 anger 0.02 | metaphor | medium | stone statue at crossroads |
| 7 | 1 | छातीमा एउटा घाइते मुटु बोकेर हेरा | sadness | sadness | joy 0.19 sadness 0.76 anger 0.02 | metaphor | easy | wounded heart carried |

## 3174 · Ma Chahi Nepali — Samriddhi Rai

Song gold: **anger** (negative) — protest against caste division and violence

| idx | x | text | label | model | probs (j/s/a) | cue | diff | note |
|----:|--:|------|-------|-------|---------------|-----|------|------|
| 0 | 1 | आज कति भागमा फुट्यौं हामी? | anger | neutral | joy 0.34 sadness 0.18 anger 0.13 | context_only | medium | why divided? indictment |
| 1 | 1 | जातकै कुरामा अल्झी जानी-नजानी | anger | neutral | joy 0.34 sadness 0.18 anger 0.13 | context_only | medium | caste entanglement critique |
| 2 | 1 | जब संसार मिलिजुली एकै हुँदैछ | neutral | neutral | joy 0.31 sadness 0.21 anger 0.30 | context_only | medium | world uniting; setup |
| 3 | 1 | केटा कुन जातको मनपराईस्? | anger | neutral | joy 0.31 sadness 0.21 anger 0.34 | address | medium | caste-question indictment |
| 4 | 1 | केटी कुन थरको तैले भगाईस्? | anger | neutral | joy 0.30 sadness 0.21 anger 0.42 | address | medium | caste-question indictment |
| 5 | 1 | किन यहाँ सबैलाई राज्य चाहिएको छ? | anger | anger | joy 0.28 sadness 0.22 anger 0.54 | context_only | medium | everyone wants a kingdom? |
| 6 | 1 | को मतवाली, को बाहुन क्षेत्री? | anger | neutral | joy 0.34 sadness 0.20 anger 0.43 | context_only | medium | caste labels questioned |
| 7 | 1 | के हामी एकै होइनौं र? | anger | neutral | joy 0.40 sadness 0.17 anger 0.31 | context_only | medium | are we not the same? |
| 8 | 1 | त्यसैले जातभात छुट्याउनेलाई | anger | neutral | joy 0.40 sadness 0.17 anger 0.31 | context_only | medium | to those who divide |
| 9 | 1 | तिमी यही भन्ने गर | neutral | joy | joy 0.45 sadness 0.16 anger 0.29 | address | medium | say this; injunction |
| 10 | 2 | तिमी को हो थाहा भएन | neutral | joy | joy 0.59 sadness 0.14 anger 0.15 | context_only | medium | don't know who you are |
| 11 | 2 | म चाहिँ नेपाली | neutral | joy | joy 0.59 sadness 0.14 anger 0.15 | context_only | medium | Nepali identity assertion |
| 14 | 1 | मानिस ठूलो जातले हुन्न यहाँ | neutral | joy | joy 0.50 sadness 0.21 anger 0.19 | context_only | medium | philosophical/didactic maxim |
| 15 | 1 | दिल नै ठूलो सबै थोक भन्दा | neutral | neutral | joy 0.44 sadness 0.26 anger 0.24 | context_only | easy | heart is greatest |
| 16 | 1 | मुना-मदन आए गए, कसैले केही बुझेन | sadness | neutral | joy 0.39 sadness 0.28 anger 0.24 | context_only | medium | cynical regret of society |
| 17 | 1 | सगरमाथा कसको भागमा पर्ला फेरि? | anger | neutral | joy 0.19 sadness 0.38 anger 0.28 | context_only | medium | satire: whose Everest? |
| 18 | 1 | बुद्ध बाड्ने कसको जिम्मेवारी | anger | neutral | joy 0.19 sadness 0.38 anger 0.28 | context_only | medium | satire: dividing Buddha |
| 19 | 1 | नेपाल, हाम्रो प्यारो देशमा | neutral | neutral | joy 0.18 sadness 0.38 anger 0.28 | context_only | easy | dear Nepal address |
| 20 | 1 | हिंसा अब चाहिएन | neutral | neutral | joy 0.15 sadness 0.38 anger 0.29 | context_only | medium | violence no longer wanted |

## 3235 · Ooth Dekhi Ooth Samma — Saroj Dutta

Song gold: **joy** (positive) — joyous romance blessing

| idx | x | text | label | model | probs (j/s/a) | cue | diff | note |
|----:|--:|------|-------|-------|---------------|-----|------|------|
| 0 | 5 | ओठदेखि ओठसम्म, छाओस यस्तो खुशी | joy | joy | joy 0.58 sadness 0.36 anger 0.03 | lexical | easy | explicit happiness blessing (खुशी) |
| 2 | 2 | जीवनभर मदेखि, नहुनु है दु:खी | joy | joy | joy 0.60 sadness 0.31 anger 0.02 | negation | medium | blessing against sorrow (नहुनु दु:खी) |
| 4 | 2 | तनदेखि मनसम्म, तिम्रो मात्र छायाँ | neutral | joy | joy 0.68 sadness 0.18 anger 0.00 | context_only | medium | devotion imagery; no happiness |
| 6 | 1 | जहाँ जान्छु,जता जान्छु, तिम्रो हुन्छु दाँया-बाँया | neutral | joy | joy 0.59 sadness 0.12 anger 0.00 | context_only | medium | devotion; no happiness |
| 7 | 1 | जुनी-जुनीसम्म,तिम्रो साथ रहोस् | neutral | joy | joy 0.54 sadness 0.16 anger 0.00 | context_only | medium | togetherness wish; no happiness |
| 8 | 1 | तिम्रो मेरो मायाको,यस्तो संसार् बनोस् | neutral | joy | joy 0.56 sadness 0.18 anger 0.01 | context_only | medium | love-world wish; no happiness |

## 3248 · Maisab — Satyaraj Aacharya, Swaroopraj Aacharya

Song gold: **anger** (negative) — betrayed by own people

| idx | x | text | label | model | probs (j/s/a) | cue | diff | note |
|----:|--:|------|-------|-------|---------------|-----|------|------|
| 0 | 12 | मै'सबले घाइते दिलमा आरा चलाइस्यो | anger | sadness | joy 0.04 sadness 0.92 anger 0.24 | metaphor | medium | saw-on-wounded-heart accusation |
| 2 | 10 | लाउन नी के एचम्मको पारा चलाइस्यो | anger | sadness | joy 0.07 sadness 0.81 anger 0.31 | context_only | medium | what a game played on me |
| 6 | 4 | आइया पानी वन्न नपाई मारिने वो सरकार | anger | sadness | joy 0.04 sadness 0.78 anger 0.57 | context_only | hard | state kills; corrupt line |
| 10 | 2 | जालिम नजर कस्तो ज्यानमारा चलाइस्यो | anger | anger | joy 0.06 sadness 0.52 anger 0.55 | metaphor | medium | cruel murderous gaze |
| 16 | 1 | घाइते दिलमा आरा चलाइस्यो | anger | sadness | joy 0.13 sadness 0.79 anger 0.32 | metaphor | medium | saw on wounded heart |
| 17 | 1 | हो मै'सबले | neutral | sadness | joy 0.13 sadness 0.79 anger 0.32 | context_only | hard | fragment; my own kin |
| 18 | 4 | सुकला रा ज्युनार पानी गरिसिन्न अचेल | sadness | sadness | joy 0.28 sadness 0.65 anger 0.27 | metaphor | hard | dried springs lament; corrupt |
| 22 | 2 | यो कस्तो मुलुकी आइनको धारा चलाइस्यो | anger | neutral | joy 0.33 sadness 0.39 anger 0.07 | context_only | medium | what law applied? grievance |
| 28 | 4 | जहाँ जाउँ मेरै कुरा काट्ने वये सबै | anger | sadness | joy 0.04 sadness 0.82 anger 0.49 | context_only | medium | gossiped everywhere |
| 32 | 2 | किना येसरी टोल बजारमा नारा चलाइस्यो | anger | anger | joy 0.43 sadness 0.08 anger 0.52 | context_only | medium | slogans against me; why |
| 38 | 4 | त्यो दिलमा मलाई नै राज होस वाँसियो | anger | sadness | joy 0.34 sadness 0.47 anger 0.20 | context_only | hard | sarcastic king-in-heart |
| 42 | 2 | जुन वयेर हजुरले छेउको तारा चलाइस्यो | anger | neutral | joy 0.37 sadness 0.43 anger 0.05 | metaphor | medium | you struck the star |

## 3396 · Dashain Aayo — Sugam Pokharel

Song gold: **joy** (positive) — festival celebration

| idx | x | text | label | model | probs (j/s/a) | cue | diff | note |
|----:|--:|------|-------|-------|---------------|-----|------|------|
| 0 | 2 | दशै आयो खाउँला-पिउँला | joy | joy | joy 0.82 sadness 0.13 anger 0.11 | lexical | easy | festive eat-drink cheer |
| 1 | 2 | नयाँ नाना लगाइ हामी पिङ खेलैं न | joy | joy | joy 0.82 sadness 0.13 anger 0.11 | lexical | easy | new clothes, swing fun |
| 2 | 2 | दशै आयो उमङ्ग ल्यायो | joy | joy | joy 0.74 sadness 0.22 anger 0.08 | lexical | easy | उमङ्ग excitement |
| 3 | 2 | सारा संसारमा खुशीयाली छायो | joy | joy | joy 0.74 sadness 0.22 anger 0.08 | lexical | easy | खुशीयाली explicit |
| 4 | 2 | माथि-माथि-माथि चङ्गा उडाइ मज्जा गरौं न | joy | joy | joy 0.65 sadness 0.24 anger 0.07 | lexical | easy | मज्जा kite fun |
| 5 | 2 | रातो टिका अनि जमरा लगाइ आशिस थापैं न | joy | joy | joy 0.56 sadness 0.28 anger 0.06 | context_only | medium | ritual celebration |
| 6 | 2 | बर्ष दिनमा आउने यो चाड | neutral | neutral | joy 0.41 sadness 0.29 anger 0.09 | none | easy | factual festival line |
| 7 | 2 | सबै परिवार हुन्छ एकाग्रह, सबै मिलेर | joy | neutral | joy 0.41 sadness 0.29 anger 0.09 | context_only | medium | family gathering warmth |
| 8 | 3 | नाँचैं न, गाउं न, रमाइलो गरौं न, हामी पिङ खेलैं न | joy | neutral | joy 0.28 sadness 0.37 anger 0.12 | lexical | easy | dance-sing रमाइलो |
| 9 | 2 | रमाइलो गरौं न, नाँचैं न, गाउं न | joy | sadness | joy 0.16 sadness 0.51 anger 0.20 | lexical | easy | रमाइलो refrain |
| 10 | 1 | पर्देशीएका आफ्नत नि घर फर्की आउछन् | joy | sadness | joy 0.07 sadness 0.65 anger 0.25 | context_only | medium | reunion happiness |
| 11 | 2 | फर्की आउन नपाउनेहरू उतै दशै मनाउ छन् | sadness | sadness | joy 0.01 sadness 0.85 anger 0.24 | context_only | hard | left-behind ache; bittersweet |
| 12 | 1 | हो, पर्देशीएका आफ्नत नि घर फर्की आउछन् | joy | sadness | joy 0.04 sadness 0.85 anger 0.15 | context_only | medium | reunion happiness |
| 14 | 1 | घर परिवार सबैलाई सम्झेर | sadness | sadness | joy 0.17 sadness 0.74 anger 0.04 | context_only | medium | homesick remembrance |
| 15 | 1 | जहाँ भए नि मनाउ यो दशै | joy | sadness | joy 0.20 sadness 0.70 anger 0.02 | context_only | medium | consoling celebration |
| 16 | 1 | जहाँ भए नि मनाउ यो चाड, सबै मिलेर | joy | sadness | joy 0.20 sadness 0.68 anger 0.03 | context_only | medium | celebrate together |
| 28 | 1 | रमाइलो गरौं न, नाँचैं न, गाउं न, रमाइलो गरौं न, हामी पिङ खेलैं न | joy | neutral | joy 0.31 sadness 0.27 anger 0.18 | lexical | easy | रमाइलो run-on refrain |
| 29 | 1 | रमाइलो गरौं न, हामी पिङ खेलैं न, रमाइलो गरौं न | joy | neutral | joy 0.31 sadness 0.26 anger 0.20 | lexical | easy | run-on refrain variant |

## 3980 · Galli Sadak — VTEN

Song gold: **anger** (negative) — street life, jail

| idx | x | text | label | model | probs (j/s/a) | cue | diff | note |
|----:|--:|------|-------|-------|---------------|-----|------|------|
| 0 | 1 | जो गर्न खोज्छ यहाँ राम्रो काम, त्यही नर्क जान्छ | anger | neutral | joy 0.14 sadness 0.45 anger 0.25 | context_only | medium | injustice of good works |
| 1 | 1 | मेरो बानी बेहोराले यहाँ सब कुरा फरक पार्छ | neutral | sadness | joy 0.12 sadness 0.54 anger 0.22 | context_only | medium | self-assertion; defiant |
| 2 | 1 | जब हान्न थाल्छु राप, एक्कासि रगत तात्छ | anger | sadness | joy 0.09 sadness 0.63 anger 0.20 | metaphor | medium | violence imagery; blood boils |
| 3 | 1 | किनकी मेरो कहानीको सुरुआत भयो गल्ली र सडकबाट | neutral | sadness | joy 0.06 sadness 0.73 anger 0.23 | context_only | medium | street origin story |
| 4 | 1 | कसैलाई मद्दत मागेन, लागेँ म फरक बाटोमा | neutral | sadness | joy 0.06 sadness 0.72 anger 0.26 | context_only | medium | took own path; defiant |
| 5 | 1 | वान्टेड मा छ रे मेरो नाम पत्रिकाले खबर छापेछ | neutral | sadness | joy 0.10 sadness 0.57 anger 0.38 | context_only | medium | wanted; press coverage |
| 6 | 1 | त्यसको केही मतलब लागेन (के?) | neutral | sadness | joy 0.14 sadness 0.53 anger 0.36 | none | easy | didn't care |
| 7 | 1 | हेर्दिन समाचार म | neutral | neutral | joy 0.31 sadness 0.33 anger 0.32 | none | easy | don't watch news |
| 8 | 1 | एनकाउन्टर हान्ने सोचि राछस्, मुजी, खबरदार तँ | anger | neutral | joy 0.39 sadness 0.28 anger 0.26 | address | medium | encounter threat; beware |
| 9 | 1 | इज्जत गर् भेट्लास् (भेट्लास्) फेरि | anger | joy | joy 0.58 sadness 0.15 anger 0.13 | address | medium | respect-or-else threat |
| 10 | 2 | मेरो गाङ छ नेपाल भरि | neutral | joy | joy 0.72 sadness 0.08 anger 0.09 | context_only | medium | gang boast |
| 11 | 1 | तँ जस्तो हैन म हिँड्छु सबैलाई राम्रो व्यवहार गरी (सही हो) | neutral | joy | joy 0.76 sadness 0.06 anger 0.07 | context_only | medium | defiant contrast |
| 12 | 1 | केटाहरू सब भेज्जा छ नि | anger | joy | joy 0.82 sadness 0.06 anger 0.07 | context_only | medium | accusation of fakeness |
| 14 | 1 | राई, लिम्बू, तामाङ, मगर, गुरुङ, शेर्नेपा, नेवार धरि | neutral | joy | joy 0.60 sadness 0.11 anger 0.34 | none | easy | ethnic roll call |
| 15 | 1 | मुजी, हेर्, म जाँदिन जेल | anger | anger | joy 0.39 sadness 0.20 anger 0.57 | address | medium | refuse jail; defiant |
| 16 | 1 | मलाई खेल्नुछैन त्यो कवाडी सरकारी राजनीतिक खेल | anger | anger | joy 0.14 sadness 0.30 anger 0.84 | context_only | medium | resentment of politics |
| 17 | 1 | हँ, खाते, आफूलाई त्यहाँ राखेर हेर् | anger | anger | joy 0.12 sadness 0.33 anger 0.79 | address | medium | put-yourself-there taunt |
| 18 | 1 | मलाई के ल्याङ हान्छस्? | anger | anger | joy 0.08 sadness 0.41 anger 0.74 | address | medium | challenge question |
| 19 | 1 | चाहेँ भनेँ उल्टै तँलाई हाल्दीन्छु जेल | anger | anger | joy 0.08 sadness 0.41 anger 0.72 | address | medium | jail threat |

## 4024 · Ekkasi — Yabesh Thapa

Song gold: **sadness** (negative) — plea not to leave mid-heartbreak

| idx | x | text | label | model | probs (j/s/a) | cue | diff | note |
|----:|--:|------|-------|-------|---------------|-----|------|------|
| 0 | 1 | सात समुन्द्र तरी आए तिम्रै छेउमा | neutral | sadness | joy 0.12 sadness 0.74 anger 0.00 | context_only | medium | devotion odyssey; mixed |
| 1 | 2 | यसरी नचिने झै गरी नसताउ न | sadness | sadness | joy 0.12 sadness 0.74 anger 0.00 | address | medium | don't-ignore plea |
| 2 | 2 | माया नभए पनि एकै छिन बस है, सँगै | sadness | sadness | joy 0.09 sadness 0.76 anger 0.01 | address | medium | stay-a-moment plea |
| 3 | 2 | यादहरु बिताउन चहिन्न पिरती | sadness | sadness | joy 0.09 sadness 0.76 anger 0.01 | context_only | medium | memories need no love; wistful |
| 4 | 2 | तै पनि मुटु खोजी बस अलि कति | sadness | sadness | joy 0.05 sadness 0.84 anger 0.04 | metaphor | medium | heart keeps searching |
| 5 | 2 | थाहा छ अलि अलि छु म पनि स्वर्थी नै, आफै | sadness | sadness | joy 0.05 sadness 0.84 anger 0.04 | context_only | medium | self-blame |
| 6 | 3 | नजानु मलाई छोडी यो भिडमा | sadness | sadness | joy 0.03 sadness 0.94 anger 0.06 | address | easy | don't-leave plea |
| 7 | 3 | नजानु मुटु तोडी आज एकै छिनमा | sadness | sadness | joy 0.03 sadness 0.94 anger 0.07 | address | easy | don't-break-heart plea |
| 8 | 3 | ए निष्ठुरी सानी सुस्तरी माया मार है | sadness | sadness | joy 0.05 sadness 0.91 anger 0.07 | address | medium | cruel-one plea; accusatory |
| 9 | 3 | फेरी दुख्छ यो मुटु बेसरी | sadness | sadness | joy 0.05 sadness 0.91 anger 0.07 | lexical | easy | heart hurts |
| 10 | 3 | छाडी तिमी गए, एक्कासी | sadness | sadness | joy 0.07 sadness 0.87 anger 0.06 | lexical | medium | sudden departure |
| 11 | 1 | सात समुन्द्र तरी आए तिम्रै छेउ मा | neutral | sadness | joy 0.10 sadness 0.82 anger 0.05 | context_only | medium | devotion odyssey variant |