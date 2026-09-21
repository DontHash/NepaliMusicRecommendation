# Transliteration gold review kit

- gold lines: 208 (model errors: 188)
- gold words: 749 (model errors: 266)
- new candidate lines for gold v2: 120

Fill `user_devanagari` on `new_line` rows; correct `devanagari` in place on
`gold_line`/`gold_word` rows when the legacy label is wrong, and explain in
`user_note`. Rubric: `eval/translit_policy.md`.

## Gold lines with model errors (worst first)

### tl_0116 · cer 0.4545 · medium
- roman: `ajkalto mai chadchau ki`
- gold:  अच्कल्टो मै छाड्छौं कि
- model: आजकलतो मै चड्चौ की

### tl_0135 · cer 0.4444 · short
- roman: `Yadama Na Aau`
- gold:  यादमा नआऊ
- model: यादामा ना आउ

### tl_0113 · cer 0.4375 · short
- roman: `machi marau jalaima`
- gold:  माछी मारौ जालैमा
- model: माची मराउ जलाईमा

### tl_0022 · cer 0.4348 · long
- roman: `Ho no no na na na na na`
- gold:  Ho no—no ना ना—ना—ना—ना
- model: हो नो नो ना ना ना ना ना

### tl_0114 · cer 0.4091 · medium
- roman: `huncha ki nai hunna vana na`
- gold:  हुन्छ कि नाइ हुन्न भनन
- model: हुन्चा की नै हुन्न वना ना

### tl_0009 · cer 0.4062 · medium
- roman: `Timi prati maya badhdocha`
- gold:  तिमीप्रति माया बढ्दो छ (बढ्दो छ)
- model: तिमी प्रति माया बढ्दोचा

### tl_0117 · cer 0.3846 · medium
- roman: `Sindur lauchau ki nai bhana na`
- gold:  सिन्दुर लाउँछौं कि नाई भनन
- model: सिन्दुर लाउचाउ की नै भना ना

### tl_0128 · cer 0.381 · medium
- roman: `maya garchau ki nai vana na`
- gold:  माया गर्छौ कि नाई भनन
- model: माया गर्चौ की नै वना ना

### tl_0133 · cer 0.381 · medium
- roman: `Baru Aai Sataune Gara`
- gold:  बरु आई मलाई सताउने गर
- model: बारु आइ सताउने गरा

### tl_0080 · cer 0.375 · short
- roman: `Hey maanis`
- gold:  हे मानिस
- model: Hey मानिस

### tl_0122 · cer 0.3684 · medium
- roman: `Ma pani k ma kaam chu ni`
- gold:  म पनि केमा कम छु नि
- model: मा पानी के मा काम चु नी

### tl_0105 · cer 0.3529 · short
- roman: `gham kati ghamailo`
- gold:  घाम लाग्यो घमाइलो
- model: घाम कति घमाइलो

### tl_0127 · cer 0.3529 · short
- roman: `sampati lai aayindaina`
- gold:  सम्पत्तिलाई आइदैन
- model: सम्पति लाई आयिँदैन

### tl_0143 · cer 0.3478 · medium
- roman: `Maan Kholi Dekhaune Gara`
- gold:  मन खोली मलाई देखाउने गर
- model: माँ खोली देखाउने गरा

### tl_0071 · cer 0.3333 · medium
- roman: `chota ajhai balji dincha`
- gold:  चोट अझै बल्झिदिन्छ
- model: चोटा अझै बलजी दिन्चा

### tl_0115 · cer 0.32 · medium
- roman: `Ani jaal ma eklai parchau ki`
- gold:  अनि जालमा एक्लै पार्छौ कि
- model: अनी जाल मा एकलाई पर्चौ की

### tl_0125 · cer 0.32 · medium
- roman: `sun chadi le timlai varula`
- gold:  सुनचाँदीले तिमीलाई भरौंला
- model: सुन चादी ले टिमलाई वरुला

### tl_0034 · cer 0.3182 · medium
- roman: `Khusi chau hami chau jaha`
- gold:  खुसी छौँ हामी छौँ जहाँ
- model: खुसी चाउ हामी चाउ जहा

### tl_0058 · cer 0.3182 · short
- roman: `Timilai Nalai Bhachaina`
- gold:  तिमीलाई न ल्याई भा छैन
- model: तिमीलाई नलाई भचाइन

### tl_0010 · cer 0.3143 · medium
- roman: `Praya samjhanchu ma timilai`
- gold:  प्रायः सम्झन्छु म तिमीलाई (तिमीलाई)
- model: प्रया सम्झन्छु मा तिमीलाई

### tl_0123 · cer 0.3125 · medium
- roman: `pakhuri ma daam cha ni`
- gold:  पाखुरीमा दम छ नि
- model: पाखुरी मा दाम चा नी

### tl_0002 · cer 0.3077 · medium
- roman: `Mero haat samai kahi door jana`
- gold:  मेरो हात समाई कहीँ दूर जान
- model: मेरो हात समै कहि डुर जना

### tl_0120 · cer 0.3 · short
- roman: `O Nisthuri`
- gold:  ओ निष्ठूरी
- model: ओ निस्थुरी

### tl_0039 · cer 0.2917 · medium
- roman: `Oh no no yeah timi nai hau`
- gold:  Oh no—no yeah तिमी नै हौ
- model: Oh नो नो yeah तिमी नै हाउ

### tl_0037 · cer 0.2857 · medium
- roman: `Jati j cha mero timi hau`
- gold:  जति—जे छ मेरो तिमी हौ
- model: जाति जे चा मेरो तिमी हाउ

### tl_0112 · cer 0.2857 · medium
- roman: `pirati ko talai ma`
- gold:  पिरतीको तालैमा
- model: पिरती को तलाई मा

### tl_0011 · cer 0.2812 · medium
- roman: `Kasari basyo kunni maya khoi`
- gold:  कसरी बस्यो कुन्नि माया, खै, आ—हा
- model: कसरी बस्यो कुन्नी माया खोइ

### tl_0131 · cer 0.28 · medium
- roman: `Kahile Kahi Maya Pani Dekhaune Gara`
- gold:  कहिले माया पनि देखाउने गर
- model: कहिले कहि माया पानी देखाउने गरा

### tl_0007 · cer 0.2727 · short
- roman: `Jaba timi ayou`
- gold:  जब तिमी आयौ
- model: जबा तिमी आयोउ

### tl_0054 · cer 0.2667 · medium
- roman: `Sanjha Pakha Chautari Ma`
- gold:  साँझपख चौतारीमा
- model: साँझ पाखा चौतारी मा

### tl_0140 · cer 0.2667 · medium
- roman: `Maanle Je Je Bhanchha`
- gold:  मनले के के भन्छ
- model: माँले जे जे भन्छ

### tl_0124 · cer 0.2632 · short
- roman: `sampati kamayincha ni`
- gold:  सम्पत्ति कमाइन्छ नि
- model: सम्पति कमयिन्छ नी

### tl_0066 · cer 0.25 · short
- roman: `testai huna sakcha`
- gold:  त्यस्तै हुन सक्छ
- model: तेस्तै हुना सक्च

### tl_0081 · cer 0.25 · medium
- roman: `mero pani aatma cha`
- gold:  मेरो पनि आत्मा छ
- model: मेरो पानी आत्मा चा

### tl_0132 · cer 0.2258 · medium
- roman: `Timro Tadako Mahi Pugena Malai`
- gold:  तिम्रो टाढाको म्वाइँ पुगेन मलाई
- model: तिम्रो ताडाको महि पुगेन मलाई

### tl_0073 · cer 0.2222 · short
- roman: `timi kahile narunu`
- gold:  तिमी कहिल्यै नरुनू
- model: तिमी कहिले नरुनु

### tl_0136 · cer 0.2121 · medium
- roman: `Tanneriko Sapana Jastai Swadama Na Aau`
- gold:  तन्नेरीको सपनाजस्तै विस्वादमा नआऊ
- model: तन्नेरीको सपना जस्तै स्वादामा ना आउ

### tl_0092 · cer 0.2083 · medium
- roman: `Timro maan ho ki dhunga ho`
- gold:  तिम्रो मन हो कि ढुंगा हो
- model: तिम्रो माँ हो की ढुङ्गा हो

### tl_0110 · cer 0.2083 · medium
- roman: `Timi pirati ko chata odau na`
- gold:  तिमी पिरतीको छाता ओढाउ न
- model: तिमी पिरती को चाटा ओडाउ ना

### tl_0026 · cer 0.2 · short
- roman: `Timi nai hau`
- gold:  तिमी नै हौ
- model: तिमी नै हाउ

### tl_0063 · cer 0.2 · short
- roman: `timi tadha huda`
- gold:  तिमी टाढा हुँदा
- model: तिमी ताधा हुदा

### tl_0070 · cer 0.2 · short
- roman: `bipanale jhaskai dida`
- gold:  विपनाले झस्काइ दिँदा
- model: बिपनाले झस्कै दिदा

### tl_0087 · cer 0.2 · short
- roman: `Malai jati marchau`
- gold:  मलाई जति मार्छौ
- model: मलाई जाति मर्चौ

### tl_0107 · cer 0.2 · medium
- roman: `Timi ra ma ghumna jaau na`
- gold:  तिमी र म घुम्न जाउँन
- model: तिमी रा मा घुम्न जाउ ना

### tl_0142 · cer 0.2 · medium
- roman: `Nalukai Maanka Sara Bimbaharu`
- gold:  नलुकाई मनका सारा विम्बहरू
- model: नलुकै माँका सारा बिम्बहरू

### tl_0096 · cer 0.1935 · medium
- roman: `eklai bachnu parne mero jindagi`
- gold:  एक्लै बाँच्नुपर्ने मेरो जिन्दगी
- model: एकलाई बच्नु पर्ने मेरो जिन्दगी

### tl_0049 · cer 0.1923 · medium
- roman: `U Jaba Bolaunche Jiskaudai`
- gold:  ऊ जब बोलाउँछे जिस्क्याउँदै
- model: उ जबा बोलाउँछे जिस्काउदै

### tl_0053 · cer 0.1905 · medium
- roman: `Jhuto Maya Layera Jane Le`
- gold:  झूटो माया लाएर जानेले
- model: झुटो माया लयेर जाने ले

### tl_0056 · cer 0.1905 · medium
- roman: `Buhari Ko Gharma Khacho Cha`
- gold:  बुहारीको घरमा खाँचो छ
- model: बुहारी को घरमा खाचो चा

### tl_0104 · cer 0.1905 · medium
- roman: `Paari tyo dadama hera`
- gold:  पारी त्यो डाँडामा हेर
- model: पारी त्यो दादामा हेरा

### tl_0108 · cer 0.1905 · medium
- roman: `Ani gham le malai sataula`
- gold:  अनि घामले मलाई सताउला
- model: अनी घाम ले मलाई सतौला

### tl_0129 · cer 0.1905 · medium
- roman: `Timi ra ma ghumna jau na`
- gold:  तिमी र म घुम्न जाउँ न
- model: तिमी रा मा घुम्न जाउ ना

### tl_0134 · cer 0.1875 · medium
- roman: `Bhawanama Na Aau Timi`
- gold:  भावनामा नआऊ तिमी
- model: भावनामा ना आउ तिमी

### tl_0024 · cer 0.186 · long
- roman: `Timi nai hau timi nai hau timi nai hau timi nai hau`
- gold:  तिमी नै हौ तिमी नै हौ तिमी नै हौ तिमी नै हौ
- model: तिमी नै हाउ तिमी नै हाउ तिमी नै हाउ तिमी नै हाउ

### tl_0020 · cer 0.1852 · medium
- roman: `Tyo bhanda aru ke nai chahincha`
- gold:  त्योभन्दा अरू के नै चाहिन्छ
- model: त्यो भन्दा अरु के नै चाहिँचा

### tl_0028 · cer 0.1818 · medium
- roman: `Na na na na`
- gold:  ना—ना ना—ना
- model: ना ना ना ना

### tl_0097 · cer 0.1818 · short
- roman: `Hawahuri sanga`
- gold:  हावाहुरीसँग
- model: हावाहुरी संग

### tl_0103 · cer 0.1818 · medium
- roman: `Haa Haa Haaa Haaa`
- gold:  हा हा हा हा
- model: हा हा हाआ हाआ

### tl_0088 · cer 0.1765 · short
- roman: `tyatinai jhan marchau`
- gold:  त्यति नै झन मर्छौ
- model: त्यतिनै झन् मर्चौ

### tl_0126 · cer 0.1765 · short
- roman: `Sun chadi chahindaina`
- gold:  सुनचाँदी चाहिंदैन
- model: सुन चादी चाहिँदैन

### tl_0052 · cer 0.1739 · medium
- roman: `Jali Rumal Chadera Janera`
- gold:  जाली रुमाल छाडेर जानेले
- model: जाली रुमाल चडेर जानेर

### tl_0057 · cer 0.1739 · medium
- roman: `Dharo Dharma Yo Kura Sancho Cha`
- gold:  धरोधर्म यो कुरा साँचो छ
- model: धारो धर्म यो कुरा साँचो चा

### tl_0078 · cer 0.1739 · medium
- roman: `Feri kina malai berthaima`
- gold:  फेरि किन मलाई ब्यर्थैमा
- model: फेरी किना मलाई बर्थैमा

### tl_0102 · cer 0.1739 · medium
- roman: `Timlai sadhai daaki rahancha`
- gold:  तिमीलाई सधैं डाकी रहन्छ
- model: टिमलाई सधै डाकी रहन्च

### tl_0004 · cer 0.1667 · medium
- roman: `Achanak badliyo manau tyo mero hoina`
- gold:  अचानक बद्लियो, मानौँ, त्यो मेरो होइन
- model: अचानक बदलियो मनाउ त्यो मेरो होइन

### tl_0019 · cer 0.1667 · medium
- roman: `Timi chau timro pyaro manche cha`
- gold:  तिमी छौ तिम्रो प्यारो मान्छे छ
- model: तिमी चाउ तिम्रो प्यारो मान्छे चा

### tl_0033 · cer 0.1667 · medium
- roman: `Paschatap chaina kunai yaha`
- gold:  पश्चात्ताप छैन कुनै यहाँ
- model: पश्चाताप चैन कुनै यहा

### tl_0046 · cer 0.1667 · medium
- roman: `Kahile Kahin Bazar Ma`
- gold:  कहिले काहीँ बजारमा
- model: कहिले कहिँ बजार मा

### tl_0055 · cer 0.1667 · medium
- roman: `Budha Pakha Bhet Huda`
- gold:  बुढापाका भेट हुँदा
- model: बुढा पाखा भेट हुदा

### tl_0074 · cer 0.1667 · medium
- roman: `milan nabhai bite bhane`
- gold:  मिलन नभइ बितेँ भने
- model: मिलान नभै बिते भने

### tl_0091 · cer 0.1667 · short
- roman: `tyati pani bujdainau`
- gold:  त्यति पनि बुझ्दैनौ
- model: त्यति पानी बुज्दैनौ

### tl_0119 · cer 0.1667 · medium
- roman: `bhai maya namare ni kaile ho`
- gold:  भै माया नमारे नि कैले हो
- model: भाई माया नमरे नी कैले हो

### tl_0162 · cer 0.1667 · long
- roman: `Hamro lokapriya khanaharu dal bhat dindo gunrdruk ityadi hun`
- gold:  हाम्रो लोकप्रिय खानाहरू दाल भाट डिन्डो गुनर्दुक इत्यादि हुन्
- model: हाम्रो लोकप्रिय खानाहरू दल भात दिँदो गुणर्द्रुक इत्यादि हुन

### tl_0017 · cer 0.1622 · long
- roman: `Bhalai choto hola yaha sabai drishya atauna lai`
- gold:  भलै छोटो होला यहाँ सबै दृष्य अटाउनलाई
- model: भलाई चोटो होला यहा सबै दृश्य अटाउन लाई

### tl_0159 · cer 0.1622 · medium
- roman: `Urvara ra ardra dakshin kshetra sahari chha`
- gold:  उर्वर र आर्द्र दक्षिणी क्षेत्र शहरी छ
- model: उर्वरा रा अर्द्रा दक्षिण क्षेत्र सहरी छ

### tl_0013 · cer 0.1613 · medium
- roman: `Bhabishyako mitho kalpana bhulisakyou`
- gold:  भविष्यको मीठो कल्पना बुनिसक्यौँ
- model: भबिष्यको मिठो कल्पना भुलिसक्यौ

### tl_0121 · cer 0.16 · medium
- roman: `bhai bhuli najanu ni kahile ho`
- gold:  भै भूली नजानु नि कहिले हो
- model: भाई भुली नजानु नी कहिले हो

### tl_0161 · cer 0.16 · medium
- roman: `Lagbhag saya bhashaharu bolinchhan`
- gold:  लगभग सय भाषाहरु बोलिन्छन्
- model: लगभाग साया भाषाहरू बोलिन्छन्

### tl_0082 · cer 0.1579 · medium
- roman: `Malai pani kate dukhcha`
- gold:  मलाई पनि काटे दुख्छ
- model: मलाई पानी काटे दुख्च

### tl_0027 · cer 0.1538 · medium
- roman: `Oh timi nai hau`
- gold:  Oh तिमी नै हौ
- model: Oh तिमी नै हाउ

### tl_0060 · cer 0.1538 · medium
- roman: `Farki Farki Hasera Herne Le`
- gold:  फर्कीफर्की हाँसेर हेर्नेले
- model: फर्की फर्की हसेर हेर्ने ले

### tl_0076 · cer 0.1538 · medium
- roman: `Soche chau timro mero sambandha`
- gold:  सोचेछौ तिम्रो मेरो सम्बन्ध
- model: सोचे चाउ तिम्रो मेरो सम्बन्ध

### tl_0089 · cer 0.1538 · short
- roman: `Kahile huri sanga`
- gold:  कहिले हुरीसँग
- model: कहिले हुरी संग

### tl_0069 · cer 0.15 · medium
- roman: `sangai base jasto lagcha`
- gold:  संगै बसे जस्तो लाग्छ
- model: सँगै बसे जस्तो लाग्चा

### tl_0006 · cer 0.1481 · medium
- roman: `Maile bhuli diye yo sara jamana`
- gold:  मैले भुलिदिएँ यो सारा जमाना
- model: मैले भुली दिये यो सारा जमाना

### tl_0003 · cer 0.1429 · medium
- roman: `Beglai bho mero yo duniya hijo bhanda`
- gold:  बेग्लै भो मेरो यो दुनियाँ हिजोभन्दा
- model: बेगलाई भो मेरो यो दुनिया हिजो भन्दा

### tl_0090 · cer 0.1429 · short
- roman: `kahile pahiro sanga`
- gold:  कहिले पहिरोसँग
- model: कहिले पहिरो संग

### tl_0130 · cer 0.1429 · medium
- roman: `Ye Malai Maya Garchhau Bhanne Hajura`
- gold:  ए मलाई माया गर्छु भन्ने हजुर
- model: ये मलाई माया गर्छौ भन्ने हजुरा

### tl_0086 · cer 0.1379 · medium
- roman: `Ma hu prakriti malai bachna deu`
- gold:  म हुँ प्रकृति मलाई बाँच्न देउ
- model: मा हु प्रकृति मलाई बच्न देउ

### tl_0098 · cer 0.1379 · medium
- roman: `eklai parnu parne mero jindagi`
- gold:  एक्लै पर्नुपर्ने मेरो जिन्दगी
- model: एकलाई पर्नु पर्ने मेरो जिन्दगी

### tl_0149 · cer 0.1348 · long
- roman: `Hamro deshma jadoma dherai chiso ra sukhha hunchha ra garmima andhibehari barsha ra badhipahiro hunachhan`
- gold:  हाम्रो देशमा जाडोमा धेरै चिसो र सुख्खा हुन्छ र गर्मीमा आँधीबेहरी बर्षा र बाढिपहिरो हुनछन्
- model: हाम्रो देशमा जादोमा धेरै चिसो रा सुख्ह हुन्छ रा गर्मीमा अन्धिबेहरी बर्षा रा बढीपहिरो हुनछन्

### tl_0195 · cer 0.1346 · long
- roman: `Taltalaiya ra jharnharu pani Nepalka prakritik sampada hun`
- gold:  तालतलैया र झरनाहरू पनि नेपालका प्राकृतिक सम्पदा हुन्
- model: तालतालैया रा झर्नहरू पानी नेपालका प्राकृतिक सम्पदा हुन

### tl_0040 · cer 0.1333 · medium
- roman: `Timi nai hau yeah`
- gold:  तिमी नै हौ yeah
- model: तिमी नै हाउ yeah

### tl_0064 · cer 0.1333 · short
- roman: `dherai dukha lagcha`
- gold:  धेरै दुःख लाग्छ
- model: धेरै दुःख लाग्चा

### tl_0018 · cer 0.1316 · long
- roman: `Jindagi narahos rahi rahanecha yesma kaid pal haru`
- gold:  जिन्दगी नरहोस् रहिरहनेछ यसमा कैद पलहरू
- model: जिन्दगी नरहोस् रही रहनेछ येसमा कैद पाल हरू

### tl_0008 · cer 0.1304 · medium
- roman: `Din duiguna raat chauguna`
- gold:  दिन दुईगुना, रात चौगुना
- model: दिन दुईगुणा रात चौगुणा

### tl_0043 · cer 0.1304 · medium
- roman: `Musu Musu Hasera Herne Le`
- gold:  मुसुमुसु हासेर हेर्नेले
- model: मुसु मुसु हसेर हेर्ने ले

### tl_0101 · cer 0.1304 · medium
- roman: `Ekchin pachi suna yasko aawaj`
- gold:  एकछिन पछि सुन यसको आवाज
- model: एकचिन पचि सुना यसको आवाज

### tl_0155 · cer 0.1296 · medium
- roman: `Lumbini Gorkha Janakpur Kathmandu prakhyat udaharanaharu hun`
- gold:  लुम्बिनी गोरखा जनकपुर काठमाडौं प्रख्यात उदाहरणहरू हुन्
- model: लुम्बिनी गोर्खा जनकपुर काठमाण्डु प्रख्यात उदाहरणाहरू हुन

### tl_0005 · cer 0.125 · medium
- roman: `Jaba timi ayou mero bipanima`
- gold:  जब तिमी आयौ मेरो बिपनीमा
- model: जबा तिमी आयोउ मेरो बिपनीमा

### tl_0014 · cer 0.125 · medium
- roman: `Jaba timi ayou basna yo manma`
- gold:  जब तिमी आयौ बस्न यो मनमा
- model: जबा तिमी आयोउ बस्न यो मनमा

### tl_0015 · cer 0.125 · medium
- roman: `Maile sumpi diye sabai timrai naamma`
- gold:  मैले सुम्पिदिएँ सबै तिम्रै नाममा
- model: मैले सुम्पी दिये सबै तिम्रै नाममा

### tl_0042 · cer 0.125 · medium
- roman: `Maski Maski Hidera Jane Le`
- gold:  मस्कीमस्की हिँडेर जानेले
- model: मस्की मस्की हिडेर जाने ले

### tl_0059 · cer 0.125 · medium
- roman: `Tarki Tarki Hidera Jane Le`
- gold:  तर्कीतर्की हिँडेर जानेले
- model: तर्की तर्की हिडेर जाने ले

### tl_0068 · cer 0.125 · medium
- roman: `sapana le saath dida`
- gold:  सपनाले साथ दिँदा
- model: सपना ले साथ दिदा

### tl_0051 · cer 0.1176 · short
- roman: `Malai Ramailo Lagcha`
- gold:  मलाई रमाइलो लाग्छ
- model: मलाई रमाइलो लाग्चा

### tl_0084 · cer 0.1176 · medium
- roman: `Malai pani jiuna deu`
- gold:  मलाई पनि जिउन देउ
- model: मलाई पानी जिउन देउ

### tl_0094 · cer 0.1176 · medium
- roman: `Malai pani ramna deu`
- gold:  मलाई पनि रम्न देउ
- model: मलाई पानी रम्न देउ

### tl_0001 · cer 0.1154 · medium
- roman: `Jaba timi ayou mero jindagima`
- gold:  जब तिमी आयौ मेरो जिन्दगीमा
- model: जबा तिमी आयोउ मेरो जिन्दगीमा

### tl_0137 · cer 0.1154 · medium
- roman: `Pritiko Phool Tipnu Parchha Bhane`
- gold:  प्रीतिको फूल टिप्नपर्छ भने
- model: प्रीतिको फुल टिप्नु पर्छ भने

### tl_0138 · cer 0.1154 · medium
- roman: `Kada Dekhi Darai Nabhagne Gara`
- gold:  काँडा देखि डराई नभाग्ने गर
- model: काडा देखि दराई नभाग्ने गरा

### tl_0145 · cer 0.1129 · long
- roman: `China uttarpatti awasthit chha ra paschim purva ra dakshin Bharatle dhakeko chha`
- gold:  चीन उतरपट्टि अवस्थित छ र पश्चिम पुर्व र दक्षिण भारतले ढाकेको छ
- model: चिना उत्तरपट्टि अवस्थित छ रा पश्चिम पूर्व रा दक्षिण भारतले ढाकेको छ

### tl_0044 · cer 0.1111 · medium
- roman: `Pagal Banaki Che Ghayal Banaki Che`
- gold:  पागल बनाकी छे घायल बनाकी छे
- model: पगल बनाकी चे घायल बनाकी चे

### tl_0050 · cer 0.1111 · medium
- roman: `Ankha Haru Sankaunche Jhimkaudai`
- gold:  आँखाहरू सन्काउछे झिम्काउँदै
- model: आँखा हरू सन्काउँछे झिम्काउदै

### tl_0079 · cer 0.1111 · medium
- roman: `Metne kosish garchau harek din`
- gold:  मेट्ने कोशिस गर्छौ हरेक दिन
- model: मेट्ने कोसिश गर्चौ हरेक दिन

### tl_0139 · cer 0.1111 · medium
- roman: `Manchhe Ke Ke Bhanchhan Malai`
- gold:  मान्छे के के भन्छन् तिमीलाई
- model: मान्छे के के भन्छन् मलाई

### tl_0160 · cer 0.1111 · medium
- roman: `Yaha dherai jati ra dharmaka manis baschan`
- gold:  यहाँ धेरै जाति र धर्मका मानिस बस्छन्
- model: यहा धेरै जाति रा धर्मका मानिस बस्चन

### tl_0191 · cer 0.1111 · long
- roman: `Yasko sathai Annapurna Kanchanjangha Lotse Manaslu Yalungkad Makalu Machapuchhre aadi himalaharu pani Nepalma chhan`
- gold:  यसका साथै अन्नपूर्ण कञ्चनजङ्घा लोत्से मनासलु यालुङकाड मकालु माछापुच्छे आदि हिमालहरू पनि नेपालमा छन्
- model: यसको साथै अन्नपूर्ण कञ्चनजंघा लोत्से मनस्लु यालुङकाद मकालु माछापुछ्रे आदि हिमालाहरू पानी नेपालमा छन्

### tl_0200 · cer 0.1111 · medium
- roman: `Yaha bibhinna prajatika rukhaharu painchha`
- gold:  यहां विभिन्न प्रजातिका रूखहरू पाइन्छ
- model: यहा बिभिन्न प्रजातिका रुखाहरू पाइन्छ

### tl_0151 · cer 0.1071 · long
- roman: `Yasma Koshi Gandaki ra Karnali jasta lamo ra chaunda nadiharu chhan`
- gold:  यसमा कोशी गण्डकी र कर्णाली जस्ता लामो र चौंडा नदीहरू छन्
- model: यसमा कोशी गण्डकी रा कर्णाली जस्ता लामो रा चाउँदा नदीहरू छन्

### tl_0085 · cer 0.1034 · medium
- roman: `Ma hu prakriti malai hasna deu`
- gold:  म हुँ प्रकृति मलाई हाँस्न देउ
- model: मा हु प्रकृति मलाई हास्न देउ

### tl_0029 · cer 0.1 · medium
- roman: `Hera malai samau yo haat`
- gold:  हेर मलाई समाऊ यो हात
- model: हेरा मलाई समाउ यो हात

### tl_0048 · cer 0.1 · medium
- roman: `Luki Luki Herche Malai`
- gold:  लुकीलुकी हेर्छे मलाई
- model: लुकी लुकी हेर्चे मलाई

### tl_0072 · cer 0.1 · medium
- roman: `kalpi kalpi roye bhane`
- gold:  कल्पी कल्पी रोएँ भने
- model: कल्पी कल्पी रोये भने

### tl_0111 · cer 0.1 · medium
- roman: `Khola jastai bagau hami`
- gold:  खोला जस्तै बगौं हामी
- model: खोला जस्तै बगाउ हामी

### tl_0148 · cer 0.0952 · medium
- roman: `Himalaya parbatiya ra tarai`
- gold:  हिमालय पर्वतीय र तराई
- model: हिमालय पर्बतीय रा तराई

### tl_0045 · cer 0.0938 · medium
- roman: `Malai Pagal Banaki Che Ghayal Banaki Che`
- gold:  मलाई पागल बनाकी छे घायल बनाकी छे
- model: मलाई पगल बनाकी चे घायल बनाकी चे

### tl_0158 · cer 0.0938 · long
- roman: `Sabha bhanda aglo Sagarmatha Angrejima Mount Everest ko rupma chininchha`
- gold:  सब भन्दा अग्लो सगरमाथा अंग्रेजीमा माउन्ट एभरेष्टको रूपमा चिनिन्छ
- model: सभा भन्दा अग्लो सागरमाथा अंग्रेजीमा माउन्ट इभरेस्ट को रूपमा चिनिन्छ

### tl_0163 · cer 0.0926 · long
- roman: `Dashain Tihar Losar aadi sabhaibhanda lokapriya chadparvaharu hun`
- gold:  दशैं तिहार लोसार आदि सबैभन्दा लोकप्रिय चाडपर्वहरू हुन्
- model: दशैं तिहार लोसार आदि सभाइभन्दा लोकप्रिय चडपर्वहरू हुन

### tl_0192 · cer 0.0917 · long
- roman: `Hamro deshko himalma phalam sun chandi abhrakh chunadhunga sisa gandhak marble soda sidhenaun birenaun khari aadika khani chhan`
- gold:  हाम्रो देशको हिमालमा फलाम सुन चाँदी अभ्रख चुनढुङ्गा सिसा गन्धक मार्बल सोडा सिधेनुन विरेनुन खरी आदिका खानी छन्
- model: हाम्रो देशको हिमालमा फलाम सुन चण्डी अभ्रख चुनाढुङ्गा सिसा गन्धक मार्बल सोदा सिधेनौं बिरेनौं खरी आदिका खानी छन्

### tl_0065 · cer 0.0909 · medium
- roman: `malai jastai timilai pani`
- gold:  मलाई जस्तै तिमीलाई पनि
- model: मलाई जस्तै तिमीलाई पानी

### tl_0202 · cer 0.0899 · long
- roman: `Tara paisaka lagi marihatte garera aafno sukhsubidhaka lagi aafno santanko bhabisyasangai kheldai lobhi ra papiharu le Nepalko charkose jhadi ra bibhinna pahadma bhaeka jangal phadani gari basti basalna suru gareka chhan`
- gold:  तर पैसाका लागि मरिहत्ते गरेर आफ्नो सुखसुविधाका लागि आफ्‌नो सन्तानको भविष्यसंगै खेल्दै लोभी र पापीहरूले नेपालको चारकोसे झाडी र विभिन्न पहाडमा भएका जङ्गल फडानी गरी वस्ती बसाल्न सुरु गरेका छन्
- model: तारा पैसाका लागी मरिहत्ते गरेर आफ्नो सुखसुबिधाका लागी आफ्नो सन्तानको भबिस्यासँगै खेल्दै लोभी रा पापीहरू ले नेपालको चारकोसे झाडी रा बिभिन्न पहाडमा भएका जंगल फडानी गरी बस्ती बसाल्न सुरु गरेका छन्

### tl_0188 · cer 0.0882 · long
- roman: `Nepalko arko mahattwapurna prakritik sampada himalaya shrinkhalaharu hun`
- gold:  नेपालको अर्को महत्त्वपूर्ण प्राकृतिक सम्पदा हिमालय श्रृङ्खलाहरू हुन्
- model: नेपालको अरको महत्त्वपूर्ण प्राकृतिक सम्पदा हिमालय शृंखलाहरू हुन

### tl_0025 · cer 0.08 · medium
- roman: `Timi nai hau malai khusi dine`
- gold:  तिमी नै हौ मलाई खुसी दिने
- model: तिमी नै हाउ मलाई खुसी दिने

### tl_0164 · cer 0.08 · long
- roman: `Nepal sano chha tara prakritik srotsadhanma dhani chha tara arthik awasthale garda garib chha`
- gold:  नेपाल सानो छ तर प्राकृतिक स्रोतसाधनमा धनी छ तर आर्थिक अवस्थाले गर्दा गरीब छ
- model: नेपाल सानो छ तारा प्राकृतिक स्रोत्साधनमा धनी छ तारा आर्थिक अवस्थाले गर्दा गरिब छ

### tl_0016 · cer 0.0789 · long
- roman: `Upahar swaroop yo tasbeer maya garne haru lai`
- gold:  उपहारस्वरूप यो तस्बीर माया गर्नेहरूलाई
- model: उपहार स्वरूप यो तस्बीर माया गर्ने हरू लाई

### tl_0021 · cer 0.0769 · medium
- roman: `Euta maya garne byakti lai`
- gold:  एउटा माया गर्ने व्यक्तिलाई
- model: एउटा माया गर्ने ब्यक्ति लाई

### tl_0023 · cer 0.0769 · medium
- roman: `Timi nai hau malai maya garne`
- gold:  तिमी नै हौ मलाई माया गर्ने
- model: तिमी नै हाउ मलाई माया गर्ने

### tl_0083 · cer 0.0741 · medium
- roman: `Mero pani timro jastai man ho`
- gold:  मेरो पनि तिम्रो जस्तै मन हो
- model: मेरो पानी तिम्रो जस्तै मन हो

### tl_0208 · cer 0.0732 · medium
- roman: `Nepaliko bhagya badali bhabisya banauna aawashyak chha`
- gold:  नेपालीको भाग्य बदली भविष्य बनाउन आवश्यक छ
- model: नेपालीको भाग्य बदली भबिस्या बनाउन आवश्यक छ

### tl_0099 · cer 0.0714 · short
- roman: `suna mero dhadkan`
- gold:  सुन मेरो धड्कन
- model: सुना मेरो धड्कन

### tl_0036 · cer 0.0667 · short
- roman: `Hamro bare kura`
- gold:  हाम्रोबारे कुरा
- model: हाम्रो बारे कुरा

### tl_0062 · cer 0.0667 · short
- roman: `kehi chota lagda`
- gold:  केही चोट लाग्दा
- model: केही चोटा लाग्दा

### tl_0093 · cer 0.0667 · medium
- roman: `Mero pani timro jastai aatma ho`
- gold:  मेरो पनि तिम्रो जस्तै आत्मा हो
- model: मेरो पानी तिम्रो जस्तै आत्मा हो

### tl_0185 · cer 0.0645 · long
- roman: `Nepalma paniko strot Asia mahadeshma nai pahilo ra vishwama Brazil pachadiko dosro sthanma raheko chha`
- gold:  नेपालमा पानीको स्रोत एसिया महादेशमा नै पहिलो र विश्वमा ब्राजिल पछाडिको दोस्रो स्थानमा रहेको छ
- model: नेपालमा पानीको स्ट्रोट एसिया महादेशमा नै पहिलो रा विश्वमा ब्राजिल पचाडीको दोस्रो स्थानमा रहेको छ

### tl_0166 · cer 0.0633 · long
- roman: `Chado nai vikas garnaka lagi aajdekhi hamile deshko sabai nagarikta bare sachet hunupardhachha`
- gold:  चाँडै नै विकास गर्नका लागि आजदेखि हामीले देशको सबै नागरिकता बारे सचेत हुनुपर्दछ
- model: चादो नै विकास गर्नका लागी आजदेखि हामीले देशको सबै नागरिकता बारे सचेत हुनुपर्धछ

### tl_0172 · cer 0.0625 · long
- roman: `Ra hami aafno arthik awastha niyantran garna sakchau`
- gold:  र हामी आफ्नो आर्थिक अवस्था नियन्त्रण गर्न सक्छौं
- model: रा हामी आफ्नो आर्थिक अवस्था नियन्त्रण गर्न सक्चौ

### tl_0193 · cer 0.06 · long
- roman: `Yaha yarchagumba jasta prakritik jadibuti chhan bhane yak yeti chauri gai kasturi jasta jantu pani raheka chhan`
- gold:  यहाँ यार्चागुम्बा जस्ता प्राकृतिक जडिबुटी छन् भने याक यति चौरी गाई कस्तुरी जस्ता जन्तु पनि रहेका छन्
- model: यहा यार्चागुम्बा जस्ता प्राकृतिक जडीबुटी छन् भने याक येती चौरी गाई कस्तुरी जस्ता जन्तु पानी रहेका छन्

### tl_0075 · cer 0.0588 · short
- roman: `timi bichalit nahunu`
- gold:  तिमी बिचलित नहुनू
- model: तिमी बिचलित नहुनु

### tl_0183 · cer 0.0581 · long
- roman: `Pani vishwakai pranilai banchanka lagi nabhai nahune dainik upabhogma parne prakritik sampada ho`
- gold:  पानी विश्वकै प्राणीलाई बाँच्नका लागि नभई नहुने दैनिक उपभोगमा पर्ने प्राकृतिक सम्पदा हो
- model: पानी विश्वकै प्राणीलाई बञ्चनका लागी नभै नहुने दैनिक उपभोगमा पर्ने प्राकृतिक सम्पदा हो

### tl_0157 · cer 0.0577 · long
- roman: `Himali uttarma vishwaka chaudha uchchatam pahadharumaddhye aath chhan`
- gold:  हिमाली उत्तरमा विश्वका १४ उच्चतम पहाडहरूमध्ये आठ छन्
- model: हिमाली उत्तरमा विश्वका चौध उच्चतम पहाडहरूमध्ये आठ छन्

### tl_0204 · cer 0.0571 · medium
- roman: `Yi jadibuti aushadhi banauna prayog garinchha`
- gold:  यी जडिबुटी औषधी बनाउन प्रयोग गरिन्छ
- model: यी जडीबुटी औषधि बनाउन प्रयोग गरिन्छ

### tl_0184 · cer 0.0568 · long
- roman: `Yasko prayog pyas metna sharir ra lugaka mayal milkauna sinchai garna ra bijuli utpadanma bhaeko chha`
- gold:  यसको प्रयोग प्यास मेट्न शरीर र लुगाका मयल मिल्काउन सिंचाइ गर्न र विजुली उत्पादनमा भएको छ
- model: यसको प्रयोग प्यास मेट्न शरीर रा लुगाका मायल मिल्काउन सिंचाई गर्न रा बिजुली उत्पादनमा भएको छ

### tl_0141 · cer 0.0556 · medium
- roman: `Sancho Kura Bhana Malai`
- gold:  साँचो कुरा भन मलाई
- model: साँचो कुरा भना मलाई

### tl_0035 · cer 0.0526 · medium
- roman: `Bhanne le bhanos garos`
- gold:  भन्नेले भनोस् गरोस्
- model: भन्ने ले भनोस् गरोस्

### tl_0199 · cer 0.05 · medium
- roman: `Hariyo van pani Nepalko prakritik sampada ho`
- gold:  हरियो वन पनि नेपालको प्राकृतिक सम्पदा हो
- model: हरियो वन पानी नेपालको प्राकृतिक सम्पदा हो

### tl_0203 · cer 0.0494 · long
- roman: `Nepalko jangalma harro barro amala tejpat aiselu chutro panchaule jasta jadibuti painchha`
- gold:  नेपालको जंगलमा हर्रो बर्रो अमला तेजपात ऐसेलु चुत्रो पाँचऔंले जस्ता जडिबुटी पाइन्छ
- model: नेपालको जंगलमा हर्रो बर्रो अमाला तेजपात ऐसेलु चुत्रो पाँचौले जस्ता जडीबुटी पाइन्छ

### tl_0150 · cer 0.0488 · long
- roman: `Yo prakritik saundarya ra srotaharu ma dhani chha`
- gold:  यो प्राकृतिक सौन्दर्य र स्रोतहरु मा धनी छ
- model: यो प्राकृतिक सौन्दर्य रा स्रोतहरू मा धनी छ

### tl_0186 · cer 0.0488 · long
- roman: `Nepalko himal pahadma nagabeli bani bagne Trishuli Karnali Mashyangdi Kali Gandaki Arun Tamor jasta nadi paniko pramukhk bhandar hun`
- gold:  नेपालको हिमाल पहाडमा नागबेली बनी बग्ने त्रिशुली कर्णाली मस्याङ्दी काली गण्डकी अरुण तमोर जस्ता नदी पानीका प्रमुख भण्डार हुन्
- model: नेपालको हिमाल पहाडमा नागबेली बानी बग्ने त्रिशूली कर्णाली मश्याङ्दी काली गण्डकी अरुण तमोर जस्ता नदी पानीको प्रमुखक भण्डार हुन

### tl_0189 · cer 0.0488 · long
- roman: `Nepalko uttar dishama purvadekhi paschimsamda paredka sipahi himali shrinkhala ubhieka chhan`
- gold:  नेपालको उत्तर दिशामा पूर्वदेखि पश्चिमसम्म परेडका सिपाही हिमाली श्रृंखला उभिएका छन्
- model: नेपालको उत्तर दिशामा पूर्वदेखि पश्चिमसम्दा परेडका सिपाही हिमाली शृंखला उभिएका छन्

### tl_0198 · cer 0.0476 · long
- roman: `Yi tan hernaka lagi matra ramra chhainan nauka vihar garna jal vihar garna pani upayukta chhan`
- gold:  यी तान हेर्नका लागि मात्र राम्रा छैनन् नौका विहार गर्न जल बिहार गर्न पनि उपयुक्त छन्
- model: यी तान हेर्नका लागी मात्र राम्रा छैनन् नौका विहार गर्न जल विहार गर्न पानी उपयुक्त छन्

### tl_0197 · cer 0.0462 · long
- roman: `Nepalko Pokharama Phewatal Beganastal raheka chhan bhane Surkheta Bulbule tal Chitwanma Nandbhauju Kasara Gadwal Tamorhaila jasta talharu raheka chhan`
- gold:  नेपालको पोखरामा फेवाताल वेगनासताल रहेका छन् भने सुर्खेतमा बुलबुले ताल चितवनमा नन्दभाउजू कसरा गडवाल तमोरघैला जस्ता तालहरू रहेका छन्
- model: नेपालको पोखरामा फेवाताल बेगनास्तल रहेका छन् भने सुर्खेता बुलबुले ताल चितवनमा नन्दभाउजु कसरा गडवाल तमोरहैला जस्ता तालहरू रहेका छन्

### tl_0031 · cer 0.0455 · medium
- roman: `Dekhne le dekhos sunos`
- gold:  देख्नेले देखोस् सुनोस्
- model: देख्ने ले देखोस् सुनोस्

### tl_0047 · cer 0.0455 · medium
- roman: `Usko Hamro Bhet Hunda`
- gold:  उस्को हाम्रो भेट हुँदा
- model: उसको हाम्रो भेट हुँदा

### tl_0153 · cer 0.0455 · long
- roman: `Hamisanga hariyo upatyaka sundar pani jharna aadi chha`
- gold:  हामीसँग हरियो उपत्यका सुन्दर पानी झरना आदि छ
- model: हामीसँग हरियो उपत्यका सुन्दर पानी झर्न आदि छ

### tl_0190 · cer 0.0441 · long
- roman: `Vishwako sarvochcha shikhar Sagarmatha Nepalko mahattwapurna prakritik sampada ho`
- gold:  विश्वको सर्वोच्च शिखर सगरमाथा नेपालको महत्वपूर्ण प्राकृतिक सम्पदा हो
- model: विश्वको सर्वोच्च शिखर सागरमाथा नेपालको महत्त्वपूर्ण प्राकृतिक सम्पदा हो

### tl_0177 · cer 0.0435 · long
- roman: `Yo deshko bhugolma prakritibata jejasta vastuharu nishulka rupma hamile prapta gareka chau tinlai prakritik sampada bhaninchha`
- gold:  यो देशको भूगोलमा प्रकृतिबाट जेजस्ता वस्तुहरू निःशुल्क रूपमा हामीले प्राप्त गरेका छौं तिनलाई प्राकृतिक सम्पदा भनिन्छ
- model: यो देशको भूगोलमा प्रकृतिबाट जेजस्ता वस्तुहरू निशुल्क रूपमा हामीले प्राप्त गरेका चाउ तीनलाई प्राकृतिक सम्पदा भनिन्छ

### tl_0030 · cer 0.0417 · medium
- roman: `Nachutos hamro darilo sath`
- gold:  नछुटोस् हाम्रो दरिलो साथ
- model: नचुटोस् हाम्रो दरिलो साथ

### tl_0152 · cer 0.0417 · long
- roman: `Hamisanga Rupa Beganas ra Rara jasta thula talharu chhan`
- gold:  हामीसँग रुपा बेगनास र रारा जस्ता ठूला तालहरू छन्
- model: हामीसँग रूपा बेगनास रा रारा जस्ता ठूला तालहरू छन्

### tl_0167 · cer 0.0408 · long
- roman: `Purush ra mahila dubai saman hun ra shiksha pradan gardachha`
- gold:  पुरुष र महिला दुबै समान हुन र शिक्षा प्रदान गर्दछ
- model: पुरुष रा महिला दुबै समान हुन रा शिक्षा प्रदान गर्दछ

### tl_0170 · cer 0.0408 · medium
- roman: `Tyasobhaye hamile yaslai vishwabhar prakashit garnuparnechha`
- gold:  त्यसोभए हामीले यसलाई विश्वभर प्रकाशित गर्नुपर्नेछ
- model: त्यसोभये हामीले यसलाई विश्वभर प्रकाशित गर्नुपर्नेछ

### tl_0201 · cer 0.04 · long
- roman: `Yi rukhaharu niryat gari Nepalko aamdani badhauna sakinchha`
- gold:  यी रूखहरू निर्यात गरी नेपालको आम्दानी बढाउन सकिन्छ
- model: यी रुखाहरू निर्यात गरी नेपालको आम्दानी बढाउन सकिन्छ

### tl_0205 · cer 0.038 · long
- roman: `Hamilai prakritile himalko chiso lek pahadka hariya van ani taraiko urvara phot dieko chha`
- gold:  हामीलाई प्रकृतिले हिमालको चिसो लेक पहाडका हरिया वन अनि तराईको उर्वर फॉट दिएको छ
- model: हामीलाई प्रकृतिले हिमालको चिसो लेक पहाडका हरिया वन अनी तराईको उर्वरा फोट दिएको छ

### tl_0168 · cer 0.0376 · long
- roman: `Sarkarle agrim karyakram lyaunu pardachha ra nagarik ra sarkar dubailai faida puryaune bibhinna suvidha pradan gari nagariklai sahayog garnupardachha`
- gold:  सरकारले अग्रिम कार्यक्रम ल्याउनु पर्दछ र नागरिक र सरकार दुबैलाई फाइदा पुर्‍याउने बिभिन्न सुविधा प्रदान गरी नागरिकलाई सहयोग गर्नुपर्दछ
- model: सरकारले अग्रिम कार्यक्रम ल्याउनु पर्दछ रा नागरिक रा सरकार दुबैलाई फैदा पुर्याउने बिभिन्न सुविधा प्रदान गरी नागरिकलाई सहयोग गर्नुपर्दछ

### tl_0178 · cer 0.0373 · long
- roman: `Ajha spashta shabdama bhanda Nepalma paine himal pahad tarai taramandal nadinala taltalaiya upatyaka jharna jal vayu khanij padartha jivjantu vanaspati nai hamra prakritik sampada hun`
- gold:  अझ स्पष्ट शब्दमा भन्दा नेपालमा पाइने हिमाल पहाड तराई तारामण्डल नदीनाला तालतलैया उपत्यका झरना जल वायु खनिज पदार्थ जीवजन्तु वनस्पति नै हाम्रा प्राकृतिक सम्पदा हुन्
- model: अझा स्पष्ट शब्दमा भन्दा नेपालमा पाइने हिमाल पहाड तराई तारामण्डल नदिनाला तालतालैया उपत्यका झर्न जल वायु खनिज पदार्थ जीवजन्तु वनस्पति नै हाम्रा प्राकृतिक सम्पदा हुन

### tl_0156 · cer 0.0339 · long
- roman: `Nepal atyadhik vividh ra dhani bhugol sanskriti ra dharmharuko desh ho`
- gold:  नेपाल अत्यधिक विविध र धनी भूगोल संस्कृति र धर्महरूको देश हो
- model: नेपाल अत्यधिक विविध रा धनी भूगोल संस्कृति रा धर्महरूको देश हो

### tl_0182 · cer 0.0326 · long
- roman: `Yahi manisko jibanma upayog hune ra Nepalma payane prakritik sampadako barema yaha ullekh garieko chha`
- gold:  यही मानिसको जीवनमा उपयोग हुने र नेपालमा पायने प्राकृतिक सम्पदाको बारेमा यहाँ उल्लेख गरिएको छ
- model: यही मानिसको जीबनमा उपयोग हुने रा नेपालमा पायने प्राकृतिक सम्पदाको बारेमा यहा उल्लेख गरिएको छ

### tl_0012 · cer 0.0303 · medium
- roman: `Mayako yasto modma hami aaipugyou`
- gold:  मायाको यस्तो मोडमा हामी आइपुग्यौँ
- model: मायाको यस्तो मोडमा हामी आइपुग्यौ

### tl_0196 · cer 0.0303 · long
- roman: `Nepali bhumima se Phoksundo Chhhorolpa Tilicho Rara jasta tanharu chhan jasle tyaha pugne pratyek paryataklai swarga pugeko aabhas dieko chha`
- gold:  नेपाली भूमिमा से फोक्सुन्डो च्छोरोल्पा तिलिचो रारा जस्ता तानहरू छन् जसले त्यहाँ पुग्ने प्रत्येक पर्यटकलाई स्वर्ग पुगेको आभास दिएको छ
- model: नेपाली भूमिमा से फोक्सुण्डो छोरोल्पा तिलिचो रारा जस्ता तानहरू छन् जसले त्यहा पुग्ने प्रत्येक पर्यटकलाई स्वर्ग पुगेको आभास दिएको छ

### tl_0175 · cer 0.0282 · long
- roman: `Prakritima sahaj rupma paine manisbata nabanaeka vastu prakritik sampada hun`
- gold:  प्रकृतिमा सहज रूपमा पाइने मानिसबाट नबनाइएका वस्तु प्राकृतिक सम्पदा हुन्
- model: प्रकृतिमा सहज रूपमा पाइने मानिसबाट नबनाएका वस्तु प्राकृतिक सम्पदा हुन

### tl_0154 · cer 0.0278 · medium
- roman: `Yo dharmik ra aitihasik sampadama dhani chha`
- gold:  यो धार्मिक र ऐतिहासिक सम्पदामा धनी छ
- model: यो धार्मिक रा ऐतिहासिक सम्पदामा धनी छ

### tl_0206 · cer 0.0256 · long
- roman: `Yi hamro Nepal ra hami Nepaliko pewa ho`
- gold:  यी हाम्रो नेपाल र हामी नेपालीको पेवा हो
- model: यी हाम्रो नेपाल रा हामी नेपालीको पेवा हो

### tl_0180 · cer 0.025 · long
- roman: `Yi prakritik sampadabata manisle ekatir bharpura manoranjan prapta gareka chhan bhane arkotir manisko mihineta paurakh buddhi kshamata yasma pokhinda yinaibata manisle jibanma pran dhanta rogko upchar garna bideshi mudra arjan gari arthoparjan garna saksham baneka chhan`
- gold:  यी प्राकृतिक सम्पदाबाट मानिसले एकातिर भरपुर मनोरञ्जन प्राप्त गरेका छन् भने अर्कोतिर मानिसको मिहिनेत पौरख बुद्धि क्षमता यसमा पोखिंदा यिनैबाट मानिसले जीवनमा प्राण धान्त रोगको उपचार गर्न विदेशी मुद्रा आर्जन गरी अर्थोपार्जन गर्न सक्षम बनेका छन्
- model: यी प्राकृतिक सम्पदाबाट मानिसले एकातिर भरपुरा मनोरञ्जन प्राप्त गरेका छन् भने अर्कोतिर मानिसको मिहिनेता पौरख बुद्धि क्षमता यसमा पोखिंदा यिनैबाट मानिसले जीबनमा प्राण धन्त रोगको उपचार गर्न बिदेशी मुद्रा अर्जन गरी अर्थोपार्जन गर्न सक्षम बनेका छन्

### tl_0144 · cer 0.0238 · long
- roman: `Mero desh Nepal dui deshharu dwara gherieko chha`
- gold:  मेरो देश नेपाल दुई देशहरु द्वारा घेरिएको छ
- model: मेरो देश नेपाल दुई देशहरू द्वारा घेरिएको छ

### tl_0194 · cer 0.0238 · long
- roman: `Yinle Nepalko gaurav badhaunu ka sathai yinko sadupayog garna sakeko khandama Nepal vishwakai dhani rashtrako paktima parna sakne sambhavana pani chha`
- gold:  यिनले नेपालको गौरव बढाउनुका साथै यिनको सदुपयोग गर्न सकेको खण्डमा नेपाल विश्वकै धनी राष्ट्रको पक्तिमा पर्न सक्ने सम्भावना पनि छ
- model: यिनले नेपालको गौरव बढाउनु का साथै यिनको सदुपयोग गर्न सकेको खण्डमा नेपाल विश्वकै धनी राष्ट्रको पक्तिमा पर्न सक्ने सम्भावना पानी छ

### tl_0179 · cer 0.0222 · medium
- roman: `Yi prakritik sampada Nepalko akshaya bhandar hun`
- gold:  यी प्राकृतिक सम्पदा नेपालको अक्षय भण्डार हुन्
- model: यी प्राकृतिक सम्पदा नेपालको अक्षय भण्डार हुन

### tl_0171 · cer 0.0147 · long
- roman: `Jun pratyaksha wa apratyaksha rupma paryataklai aakarshit garna maddhat gardachha`
- gold:  जुन प्रत्यक्ष वा अप्रत्यक्ष रूपमा पर्यटकलाई आकर्षित गर्न मद्दत गर्दछ
- model: जुन प्रत्यक्ष वा अप्रत्यक्ष रूपमा पर्यटकलाई आकर्षित गर्न मद्धत गर्दछ

### tl_0181 · cer 0.0135 · long
- roman: `Yasari prakritik sampada manislai sukhko barsha garaune sampattiko rupma raheko chha`
- gold:  यसरी प्राकृतिक सम्पदा मानिसलाई सुखको वर्षा गराउने सम्पत्तिको रूपमा रहेको छ
- model: यसरी प्राकृतिक सम्पदा मानिसलाई सुखको बर्षा गराउने सम्पत्तिको रूपमा रहेको छ

## New candidate lines for gold v2

### new_001 · Tara Khaseuli — D Morcha
- roman: `Ramri Ramri Tarunilai`
- model: राम्री राम्री तरुणीलाई

### new_002 · Ja Ja Bhuichalo — Ananda Karki
- roman: `Bhoka lai anna deu`
- model: भोका लाई अन्न देउ

### new_003 · Mera Suit — Neha Kakkar | Tony Kakkar | Junior
- roman: `Ranga Do Ye Choli Saya`
- model: रङ्ग Do ये चोली साया

### new_004 · Haat Bandhi — Mohan Bhusal
- roman: `Ekanta Maa Eklai Musukka Haasera`
- model: एकान्त माआ एकलाई मुसुक्क हासेर

### new_005 · Yo Pokhara Mero — Laure
- roman: `Jyan bata turkeko tyo Pailo mailo`
- model: ज्यान बाटा तुर्केको त्यो पाइलो मैलो

### new_006 · A Hoi Bhani Bolako — Dr Pilot
- roman: `Kalilo joban, nagara doman`
- model: कालिलो जोबन, नगरा डोमन

### new_007 · Jay Nepal — Cobweb
- roman: `Shey Shey Shey`
- model: शे शे शे

### new_008 · "DALLI" - Brijesh Shrestha X Beyond (Official LYRICS) — Brijesh Shrestha
- roman: `Risauchau ho, risauchau ho, risauchau kina?`
- model: रिसाउछौ हो, रिसाउछौ हो, रिसाउछौ किना?

### new_009 · Chanchal Chanchal — Sugam Pokhrel
- roman: `Sayou Juni Bhanchha Man Le`
- model: सयोउ जुनी भन्छ मन ले

### new_010 · Chattai Basyo Ni Maya lyrics / Rajan raj shiwakoti — Anju panta
- roman: `Timro tyo mayale hurukkai paryo`
- model: तिम्रो त्यो मायाले हुरुक्कै पर्यो

### new_011 · Sakchau Bhane — Anil Singh
- roman: `Sakchau sajilai timile garna bida`
- model: सक्चौ सजीलाई तिमीले गर्न बिदा

### new_012 · 5:55 Ek Din — Chirag Khadka
- roman: `Jitko cha basna, bholiko aasma`
- model: जितको चा बस्न, भोलीको आसमा

### new_013 · Timro Baulai Salam Cha — Kumar Basnet
- roman: `Chori Maeta Base Rahe Anek Kura Jhulinchha`
- model: चोरी माएता बसे रहे अनेक कुरा झुलिन्छ

### new_014 · Rujhi Rujhi Hidne — Manoj Shrestha
- roman: `Banaai Mukh Lukaauchhau`
- model: बनाइ मुख लुकाउछौ

### new_015 · Hami Dherai Sana Chau — X-Mantra
- roman: `Yo Sanu Mutuma`
- model: यो सानु मुटुमा

### new_016 · Janam Janam Juila — Ananda Karki, Sunita Subba
- roman: `sakchhi chha hai pipalu ra bara`
- model: सक्छि छ हाइ पिपालु रा बारा

### new_017 · Ma Ta Mare — Kamal Khatri
- roman: `Sangai Jiune Baacha Kasam Aba Nakhaanu`
- model: सँगै जिउने बाचा कसम अबा नखाँउ

### new_018 · SAMJHANA MA NA AAU Lyrics / Sugam pokhrel — Sugam Pokharel
- roman: `Kori bati apsara jhai sapanama na aau`
- model: कोरी बाटी अप्सरा झै सपनामा ना आउ

### new_019 · Phuleki Thiye — Kunti Moktan
- roman: `Rahar Aafulai`
- model: रहर आफूलाई

### new_020 · Ma Mare Pani — Swar
- roman: `Haso rittiye aashu ko k dosh`
- model: हासो रित्तिये आशु को के दोष

### new_021 · Himal Chuchure — Nepathya
- roman: `eklai eklai kata tira laagyau`
- model: एकलाई एकलाई काटा तिरा लाग्यौ

### new_022 · Samjhi Baschhu — 1974 AD
- roman: `Timilai nai`
- model: तिमीलाई नै

### new_023 · Ma Yesto Chu — Girish N Pranil
- roman: `Ghar ma eaklai hunda blue film in the deck`
- model: घर मा एकलाई हुँदा ब्लु film in the डेक

### new_024 · Dashain Tihara — Sugam Pokhrel
- roman: `Uta Holan Ratai Nidhar`
- model: उता होलान रताई निधार

### new_025 · Baiguni Le Chade Pachi — Rajesh Payal Rai
- roman: `dhoka khaane maya laauna`
- model: धोका खाने माया लाउन

### new_026 · Ghar Ko Kura — Nepathya
- roman: `din dasa bigreko belaa`
- model: दिन दसा बिग्रेको बेला

### new_027 · Para Para — Fuba Tamang
- roman: `Dara Dara Namana Timi Timi...`
- model: दरा दरा नमाना तिमी तिमी...

### new_028 · Dekhana Champa — Krishna Kafle
- roman: `K Cha Ra Champa Tamra Mayama`
- model: के चा रा चम्पा ताम्रा मायामा

### new_029 · Basma chhaina mero man — Rajan Ishan
- roman: `yo kasto mitho dhun`
- model: यो कस्तो मिठो धुन

### new_030 · Jay Nepal — Cobweb
- roman: `Yo Hamro Desh`
- model: यो हाम्रो देश

### new_031 · Ustai Chha Maya lyrics / Chhewang Lama — Chhewang Lama
- roman: `Sangai jiuchhu marchhu bhanthyau`
- model: सँगै जिउछु मर्छु भन्थ्यौ

### new_032 · Suna Kaanchi lyrics by Sajjan Raj Vaidya — Sajjan Raj Vaidya
- roman: `Garnai paryo feri`
- model: गर्नै पर्यो फेरी

### new_033 · 5:55 : Maya (High Sessions) — Chirag Khadka
- roman: `Aideu timi ! Aideu timi!`
- model: आइदेउ तिमी ! आइदेउ तिमी!

### new_034 · Jaha Chan Buddha Ka Aakha — Rocken Music, Bhakta Raj Acharya
- roman: `Maya prakriti lo lagcha, kala bhasa ra bhes ko`
- model: माया प्रकृति लो लाग्चा, काला भासा रा भेस को

### new_035 · Baisa Chhada Dherai Sanga — Raju Lama
- roman: `dherai dherai kasam pani khaainchha`
- model: धेरै धेरै कसम पानी खाइन्छ

### new_036 · Vanna Aaudaina lyrics / Naren Limbu — Naren Limbhu
- roman: `mixed and mastered by : Bizu Karmcharya`
- model: mixed and mastered by : बिजु कर्मचार्य

### new_037 · Lumbini lyrics / Bishnu Khatri — Annu Chaudhary
- roman: `Female: Malai rojne dherai chan patra`
- model: Female: मलाई रोज्ने धेरै चान पत्र

### new_038 · Kali Pari — Tara Devi
- roman: `Hajur lai bhetau bhani aako bayal kheldai`
- model: हजुर लाई भेटौ भनी आको बयल खेल्दै

### new_039 · Timi Jaha Khusi — Deepesh Kishor Bhattarai
- roman: `Mero khusi timilai`
- model: मेरो खुसी तिमीलाई

### new_040 · Sajjan Raj Vaidya - Mayaloo Official — Sajjan Raj Vaidya
- roman: `Ma ta, yetai nai aljhirahen, timilai baato Kurirahen; shayad aaunchou timi bholi bhanayra, mayaloo.`
- model: मा ता, येतै नै अल्झिरहेँ, तिमीलाई बाटो कुरिरहेँ; शायद आउँचोउ तिमी भोली भनाय्र, मायालु.

### new_041 · Bipul Chettri- Junkeri Official — Bipul Chettri
- roman: `Recorded & Mixed by Anindo Bose at PlugNPlay Studios, India`
- model: रेकर्डेड & Mixed by अनिन्दो बोसे at प्लगनप्ले Studios, इन्डिया

### new_042 · Maya Pirim — Nishan Bhattarai, Manisha Pokhrel
- roman: `He yek yek jode dui, aakhir kuro uuhi`
- model: हे येक येक जोडे दुई, आखिर कुरो उउही

### new_043 · Timi Samu — Rodit Bhandari, Somea Baraili
- roman: `Khitiz pari ko maya ko hamro sansarma`
- model: खितिज पारी को माया को हाम्रो संसारमा

### new_044 · Samaya Ley — John & The Locals
- roman: `Hidi Saake Vanda vandae`
- model: हिडी साके वन्द वन्दाए

### new_045 · Jhuma (Jyalko Aaina) — Basanta Bishwokarma, Shanti Shree Pariyar
- roman: `Nahera na rajaile, mare lajaile)`
- model: नहेर ना रजाइले, मारे लजाइले)

### new_046 · Apurva Tamang- Sunideu Official — Apurva Tamang
- roman: `Samay ta biteko thaha hudaina timi sanga`
- model: समय ता बितेको थाहा हुदैन तिमी संग

### new_047 · Lajjawati Jhar — Mahesh Kafle, Asmita Adhikari
- roman: `Pachhi feri pachhutaudai yo man runa sakchha`
- model: पछि फेरी पछुताउदै यो मन रुना सक्छ

### new_048 · Preeti Basyo — Nima Rumba
- roman: `Prema bandhana ma jeevan phasyo`
- model: प्रेमा बन्धना मा जीवन फस्यो

### new_049 · Eh Saathi — Bipul Chettri
- roman: `Raata Pare Pachi Feri Bhetne Garthiyou`
- model: राता परे पचि फेरी भेट्ने गर्थियोउ

### new_050 · Sirko Topi Siraima — Manoj Shrestha
- roman: `Sir ko topi sirai ma, dhalki hindne tirai ma - 2`
- model: सिर को टोपी सिराई मा, ढल्की हिँड्ने तिरै मा - 2

### new_051 · Attitude — Clu Pokhrel
- roman: `Dam nam soche jastai kamairako chhu`
- model: डाम नाम सोचे जस्तै कमाइरको छु

### new_052 · Suna Kaanchi lyrics by Sajjan Raj Vaidya — Sajjan Raj Vaidya
- roman: `Timi lai dhaatera`
- model: तिमी लाई धातेर

### new_053 · Goreto Gaunko Duldai — Nepathya
- roman: `He He la la la la`
- model: हे हे ला ला ला ला

### new_054 · Je Chhau Timi — Swoopna Suman, Samir Shrestha
- roman: `Hawale udako mannparchha`
- model: हावाले उदाको मान्नपर्छ

### new_055 · OOH YEA by Sabin Karki -Beest — Sabin Karki - Beest
- roman: `Ooh yea! Malai kasto hereko`
- model: Ooh येआ! मलाई कस्तो हेरेको

### new_056 · Lolayeka Ti Thula — Gulam Ali Khan
- roman: `Saubhagyashalee Authi Timro Tyo Haat Ko Bhai - 2`
- model: सौभाग्यशाले औठी तिम्रो त्यो हात को भाई - 2

### new_057 · Malai Hera — Sabin Rai & The Pharaoh
- roman: `Malai Sodhanahahahau`
- model: मलाई सोधनाहहरू

### new_058 · Bhagyama Shree Chha — Rekha Pokhrel and Roshan Singh
- roman: `Diyou Chota Jindagi Bharako`
- model: दियोउ चोटा जिन्दगी भाराको

### new_059 · Musukka Haseko Photo Pathaideu — Khem Century & Kalpana Devkota
- roman: `Pathaideu Mai Herchu Muhaara Ghumto`
- model: पठाइदेऊ मै हेर्चु मुहारा घुम्टो

### new_060 · Suna Kina — Naren Limbu
- roman: `Yo maunata sunana ho....`
- model: यो मौनता सुनाना हो....

### new_061 · Timi Sanga Mero Nata — Benup Chhetri
- roman: `Sabako Manma Bacheko Cha`
- model: सबाको मनमा बचेको चा

### new_062 · Ke Maya Garnu Hunna Ra — Hemant Sharma
- roman: `Ma Kati Dhaunu Saanu Timrai Laagi Deurali`
- model: मा कति धाउनु साँउ तिम्रै लागी देउराली

### new_063 · Haat Bandhi — Mohan Bhusal
- roman: `Chhewaiko Guraas Fulne`
- model: छेवैको गुरास फुल्ने

### new_064 · If You Were Mine — GXSOUL
- roman: `Timi Jasto Kohi Xaina`
- model: तिमी जस्तो कोही चैन

### new_065 · Chiya Barima — The Axe
- roman: `Dhaka Saari Ma Maskera Hinda Choryo Yo Mana`
- model: ढाका सारी मा मस्केर हिँडा चोर्यो यो माना

### new_066 · Sajjan Raj Vaidya - Parkhaai — Sajjan Raj Vaidya
- roman: `Huna ta huney nai ho`
- model: हुना ता ह्युनी नै हो

### new_067 · First Date — Neetesh Jung Kunwar
- roman: `Sayed usle pani yestai`
- model: Sayed उसले पानी येस्तै

### new_068 · Choli Ramro — Kunti Moktan
- roman: `Maaya Mitho Tyo Mana Bhitra Ko`
- model: माया मिठो त्यो माना भित्र को

### new_069 · Maya Namara Mayalu — Prem Dhoj Pradhan
- roman: `Aa.. ha.. aa...`
- model: आ.. हा.. आ...

### new_070 · Albida — Asmit Regmi
- roman: `Timi aafukhusi je gara kehi sarta chhaina mero`
- model: तिमी आफूखुसी जे गरा केही सर्त छैन मेरो

### new_071 · Adhar Ma Aaja — Manila Sotang
- roman: `Ranga Li Tanamaaa..`
- model: रङ्ग ली तानामाआ..

### new_072 · Chattai Basyo Ni Maya lyrics / Rajan raj shiwakoti — Anju panta
- roman: `Mero mutu nai jalayeu`
- model: मेरो मुटु नै जलायेउ

### new_073 · Timi Sanga Najar Judhai — Pramod Kharel
- roman: `Tadha hunda aankha bata aanshu jharya yaad aayo`
- model: ताधा हुँदा आँखा बाटा आँशु झर्या याद आयो

### new_074 · Bistarale Polyo — Shanti Shree Pariyar | Hari Giri Bimarshi
- roman: `Maya K Bho Maan Nai Uthalputal Bhayo`
- model: माया के भो माँ नै उथलपुतल भयो

### new_075 · Nepali Hami — Nati Kaji
- roman: `Sansarma failiyo`
- model: संसारमा फैलियो

### new_076 · Nepal Haseko — Balen | Laaj Sharanam OST
- roman: `Ma Nepal Haseko`
- model: मा नेपाल हासेको

### new_077 · Pardeshi Hunai Man Chhaina — Khem Century & Shanti Shree Pariyar
- roman: `Desh Chodi Pardeshi Hunai Maan Chaina`
- model: देश चोडी परदेशी हुनै माँ चैन

### new_078 · Lai Lai Lai — Pramod Kharel
- roman: `Sapana Po Rahecha Jaha Janchae Sang Sangae`
- model: सपना पो रहेचा जहा जाँचाए साङ संगाए

### new_079 · Wari Jamuna Pari Jamuna — Khem Raj Gurung
- roman: `Mare Pachhi Ganga Jee Lai`
- model: मारे पछि गंगा जी लाई

### new_080 · Hatkadi — VTEN
- roman: `Taal Ma Baschu Matlab`
- model: ताल मा बस्चु मतलब

### new_081 · Timro Pratiksa — Shallum Lama
- roman: `Kina lagxa yo maya nai ho ke`
- model: किना लाग्छ यो माया नै हो के

### new_082 · Relli Mai — Tanka Budhathoki
- roman: `Kohi tuna sikaideuna`
- model: कोही तुना सिकाइदेउन

### new_083 · Dukha Diyera — Edge Band
- roman: `Jharna Laageko Aanshulai Aankhama Lukai`
- model: झर्न लागेको आँशुलाई आँखामा लुकाई

### new_084 · Adrishya Vhawana — Naren Limbu
- roman: `Timi nai chau yaha`
- model: तिमी नै चाउ यहा

### new_085 · Hey Hajur — Dr Pilot
- roman: `He hajur he hajur`
- model: हे हजुर हे हजुर

### new_086 · Neetesh Jung Kunwar - Kholai Khola (Official LYRICS) — Mr. Brownie
- roman: `Khai k ko maata lagyo hai ma maa`
- model: खै के को माता लाग्यो हाइ मा माआ

### new_087 · Yeti Dherai Maya Diyee — Narayan Gopal
- roman: `bato wara para phulne palas tipi sirma nalau`
- model: बाटो वारा पारा फुल्ने पलास टिपी सिरमा नलाउ

### new_088 · Yo Ta Maya Ho — Sugam Pokhrel
- roman: `Kina ho...`
- model: किना हो...

### new_089 · Achha Lekin London Ko — Shambujeet Baskota OST of Narashimha Avatar
- roman: `Hui Dekhi Ma Pani Ramaula Aacha`
- model: हुई देखि मा पानी रमौला आचा

### new_090 · Pani Paryo — Rohit John Chettry
- roman: `Mero haanso timi banideu`
- model: मेरो हाँसो तिमी बनिदेउ

### new_091 · Mohani Mayako Hoki — Kumar Kancha
- roman: `Jaha Mayale Aatma Lai`
- model: जहा मायाले आत्मा लाई

### new_092 · Bhet Bhayo Jogale — Dmarcha
- roman: `Maan Kina Dodare Ma Jasto Paidaina Ho`
- model: माँ किना दोदरे मा जस्तो पाइदैन हो

### new_093 · Badaluko Ghumtole — Yam Baral
- roman: `Phool jhai meri mayalu`
- model: फुल झै मेरी मायालु

### new_094 · Hamro Maya Ajambari Chha — Udit Narayan Jha, Purnima Shrestha
- roman: `Ful sanga bhamarako saino cha jasto`
- model: फुल संग भमराको साइनो चा जस्तो

### new_095 · Kanchi Mayalu — Cartoonz Crew
- roman: `Gali garne keta lai`
- model: गाली गर्ने केटा लाई

### new_096 · Yo Saanjh — Araj Keshav
- roman: `Bhujnu Chyou Tyehai Din Bhawan Yo Manko`
- model: भुज्नु च्योउ त्येहै दिन भवन यो मनको

### new_097 · Yes Pali Dashain Ma — Cool Pokhrel
- roman: `Usko haath bata paisa pathathe - 2`
- model: उसको हाथ बाटा पैसा पठाथे - 2

### new_098 · Sustari Sustari — ETHOS BAND
- roman: `Coz I feel like the love is going slowly`
- model: Coz I feel like the love is going slowly

### new_099 · Malai Vote Deu — Girish N Pranil
- roman: `Cash dinchhu, cheque dinchhu, Mercedes benz dinchhu`
- model: क्याश दिन्छु, चेक दिन्छु, मर्सिडेस बेन्ज दिन्छु

### new_100 · Dashain Tihar — Sugam Pokhrel
- roman: `Uta holan raatai ti nidhara`
- model: उता होलान रातै टीआई निधारा

### new_101 · Mero Sathi Haru Ko Maajh — Babin Pradhan
- roman: `Mero saathi haruko maajh`
- model: मेरो साथी हरूको माझ

### new_102 · Mayalu Sunana – Lyrics / Samir Shrestha — Samir Shrestha
- roman: `Mero yo mana ma`
- model: मेरो यो माना मा

### new_103 · Maya Marera — Samikshya Adhikari, Naresh Khati
- roman: `Timi Krishna ma timri Radha ho`
- model: तिमी कृष्ण मा तिम्री राधा हो

### new_104 · Sapana Ko Mayalu — The Elements
- roman: `Bujaunai sakina ishara le nai bujhideu`
- model: बुजाउनै सकिना इशारा ले नै बुझिदेउ

### new_105 · Ali Alikati pida hudani — Nabin K Bhattarai
- roman: `Timrai Kabita Lekhchhu) - x2`
- model: तिम्रै कबिता लेख्छु) - एक्स2

### new_106 · Aatma — Aastha Band
- roman: `Nyano kakhko maya paune`
- model: न्यानो काखको माया पाउने

### new_107 · Man Chade Maichyang Lai — Danny Denzongpa
- roman: `Tanera laanu pardaina`
- model: तानेर लानु पर्दैन

### new_108 · Suna Kina — Naren Limbu
- roman: `Dekhiraheko chhau ma timrai chheuma chhu ni`
- model: देखिरहेको छौ मा तिम्रै छेउमा छु नी

### new_109 · Aaja Bholi Timiley — Rajesh Payal Rai
- roman: `ho biraayeki risaayauki`
- model: हो बिरायेकी रिसायौकी

### new_110 · Tara Khaseuli — D Morcha
- roman: `Tehi Taalma Baule Pani`
- model: तेही तालमा बाउले पानी

### new_111 · Maya Pirim — Nishan Bhattarai, Manisha Pokhrel
- roman: `Aaudeu mero bui, puryaidimla uunhi`
- model: आउदेउ मेरो बुई, पुर्याइदिम्ला उन्ही

### new_112 · Ma Jiunu Ya Marnu — Sumit Pathak
- roman: `Yo juwanko yatra vari vari`
- model: यो जुवानको यात्रा वरी वरी

### new_113 · Hami Dherai Sana Chau — Girish N Pranil
- roman: `Sir Ko K Bhar`
- model: सिर को के भर

### new_114 · Badnaam Bhaye Ma — Sworup Raj Acharya
- roman: `Timi Mana Ya Namana Dhokebaaz`
- model: तिमी माना या नमाना धोकेबाज

### new_115 · Thik Chha
- roman: `Tyahi chyyan gare pran malai harna dinna`
- model: त्यहि च्यान गरे प्राण मलाई हर्न दिन्न

### new_116 · Himal Sari — Narayan Gopal, Aruna Lama
- roman: `Uchala Uchal Uchala Malai`
- model: उचाला उचाल उचाला मलाई

### new_117 · Katha | VTEN ft. Dharmendra Sewan — VTEN
- roman: `Testo haina naani timro janmai yesto bhaako`
- model: टेस्टो हैन नाँई तिम्रो जन्मै येस्तो भाको

### new_118 · Udhreko Choli — Indira Joshi
- roman: `(Sablai Side Laincha`
- model: (सबलाई Side लैंचा

### new_119 · Kasari / कसरी — Yabesh Thapa
- roman: `Pagal vai sake`
- model: पगल वै सके

### new_120 · Ekanta Cha Thau — COD
- roman: `Ekanta chha thaun,jane kunai baato chhaina`
- model: एकान्त छ ठाउँ,जाने कुनै बाटो छैन
