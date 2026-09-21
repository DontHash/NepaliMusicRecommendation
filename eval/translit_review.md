# Transliteration gold review kit

- gold lines: 208 (model errors: 163)
- gold words: 743 (model errors: 221)
- new candidate lines for gold v2: 120 (held out from teacher training)

`draft_devanagari` is a second model's opinion (see
`scripts/draft_translit_review.py`) so you can accept or correct rather
than translate from scratch. Only `user_devanagari` feeds gold v2.
Rubric: `eval/translit_policy.md`.

## Gold lines with model errors (worst first)

### tl_0022 · cer 0.4783 · long
- roman: `Ho no no na na na na na`
- gold:  Ho no—no ना ना—ना—ना—ना
- model: हो नो नो ना ना ना ना न
- draft: Ho no no na na na na na

### tl_0113 · cer 0.4375 · short
- roman: `machi marau jalaima`
- gold:  माछी मारौ जालैमा
- model: माची मराउ जलाइमा
- draft: माची मारौ जलैमा

### tl_0009 · cer 0.4062 · medium
- roman: `Timi prati maya badhdocha`
- gold:  तिमीप्रति माया बढ्दो छ (बढ्दो छ)
- model: तिमी प्रति माया बढ्दोचा
- draft: तिमी प्रति माया बढ्दोछ

### tl_0080 · cer 0.375 · short
- roman: `Hey maanis`
- gold:  हे मानिस
- model: Hey मानिस
- draft: हे मानिस

### tl_0105 · cer 0.3529 · short
- roman: `gham kati ghamailo`
- gold:  घाम लाग्यो घमाइलो
- model: घाम कति घमाइलो
- draft: घाम कति घमाइलो

### tl_0135 · cer 0.3333 · short
- roman: `Yadama Na Aau`
- gold:  यादमा नआऊ
- model: यादमा ना आउ
- draft: यादमा ना आउ

### tl_0125 · cer 0.32 · medium
- roman: `sun chadi le timlai varula`
- gold:  सुनचाँदीले तिमीलाई भरौंला
- model: सुन छाडी ले तिम्लाई भरुला
- draft: सुन चादी ले तिम्लाई भरुला

### tl_0116 · cer 0.3182 · medium
- roman: `ajkalto mai chadchau ki`
- gold:  अच्कल्टो मै छाड्छौं कि
- model: आजकल्तो मै चड्छौ कि
- draft: आजकल्तो मै चढछौ की

### tl_0010 · cer 0.3143 · medium
- roman: `Praya samjhanchu ma timilai`
- gold:  प्रायः सम्झन्छु म तिमीलाई (तिमीलाई)
- model: प्रया सम्झन्छु मा तिमीलाई
- draft: प्राय सम्झन्छु म तिमीलाई

### tl_0120 · cer 0.3 · short
- roman: `O Nisthuri`
- gold:  ओ निष्ठूरी
- model: ओ निस्थुरी
- draft: ओ निष्ठुरी

### tl_0126 · cer 0.2941 · short
- roman: `Sun chadi chahindaina`
- gold:  सुनचाँदी चाहिंदैन
- model: सुन छाडी चाहिँदैन
- draft: सुन चादी चाहindaina

### tl_0127 · cer 0.2941 · short
- roman: `sampati lai aayindaina`
- gold:  सम्पत्तिलाई आइदैन
- model: सम्पत्ति लाइ आयिँदैन
- draft: सम्पति लाइ आयिन्दैना

### tl_0132 · cer 0.2903 · medium
- roman: `Timro Tadako Mahi Pugena Malai`
- gold:  तिम्रो टाढाको म्वाइँ पुगेन मलाई
- model: तिम्रो तडको महि पुगेन मलाई
- draft: तिम्रो तादको माहि पुगेना मलाई

### tl_0112 · cer 0.2857 · medium
- roman: `pirati ko talai ma`
- gold:  पिरतीको तालैमा
- model: पिरती को तलाई मा
- draft: पिरती को तलाइ मा

### tl_0133 · cer 0.2857 · medium
- roman: `Baru Aai Sataune Gara`
- gold:  बरु आई मलाई सताउने गर
- model: बरु आइ सताउने गर
- draft: बारु आई सताउने गर

### tl_0011 · cer 0.2812 · medium
- roman: `Kasari basyo kunni maya khoi`
- gold:  कसरी बस्यो कुन्नि माया, खै, आ—हा
- model: कसरी बस्यो कुन्नी माया खोइ
- draft: कसरी बस्यो कुन्नि माया खोई

### tl_0028 · cer 0.2727 · medium
- roman: `Na na na na`
- gold:  ना—ना ना—ना
- model: ना ना ना न
- draft: Na na na na

### tl_0054 · cer 0.2667 · medium
- roman: `Sanjha Pakha Chautari Ma`
- gold:  साँझपख चौतारीमा
- model: साँझ पाखा चौतारी मा
- draft: साँझ पाखा चौतारी मा

### tl_0143 · cer 0.2609 · medium
- roman: `Maan Kholi Dekhaune Gara`
- gold:  मन खोली मलाई देखाउने गर
- model: मान खोली देखाउने गर
- draft: मान खोल्दि देखाउने गर

### tl_0117 · cer 0.2308 · medium
- roman: `Sindur lauchau ki nai bhana na`
- gold:  सिन्दुर लाउँछौं कि नाई भनन
- model: सिन्दुर लाउछौ कि नै भन ना
- draft: सिन्दुर लाउँछौ कि नै भना ना

### tl_0073 · cer 0.2222 · short
- roman: `timi kahile narunu`
- gold:  तिमी कहिल्यै नरुनू
- model: तिमी कहिले नरुनु
- draft: तिमी कहिले नरुनु

### tl_0039 · cer 0.2083 · medium
- roman: `Oh no no yeah timi nai hau`
- gold:  Oh no—no yeah तिमी नै हौ
- model: Oh नो नो yeah तिमी नै हौ
- draft: Oh no no yeah तिमी नै हौ

### tl_0119 · cer 0.2083 · medium
- roman: `bhai maya namare ni kaile ho`
- gold:  भै माया नमारे नि कैले हो
- model: भाइ माया नमरे नि कहिले हो
- draft: भै माया नमारे नि काहिले हो

### tl_0070 · cer 0.2 · short
- roman: `bipanale jhaskai dida`
- gold:  विपनाले झस्काइ दिँदा
- model: बिपनाले झस्कै दिदा
- draft: बिपनाने झस्काइ दिदा

### tl_0140 · cer 0.2 · medium
- roman: `Maanle Je Je Bhanchha`
- gold:  मनले के के भन्छ
- model: मानले जे जे भन्छ
- draft: मान्ले जे जे भन्छ

### tl_0002 · cer 0.1923 · medium
- roman: `Mero haat samai kahi door jana`
- gold:  मेरो हात समाई कहीँ दूर जान
- model: मेरो हात समाइ कही डुर जाना
- draft: मेरो हात समाई कही दूर जाना

### tl_0053 · cer 0.1905 · medium
- roman: `Jhuto Maya Layera Jane Le`
- gold:  झूटो माया लाएर जानेले
- model: झुटो माया लायेर जाने ले
- draft: झुटो माया लाएर जाने ले

### tl_0128 · cer 0.1905 · medium
- roman: `maya garchau ki nai vana na`
- gold:  माया गर्छौ कि नाई भनन
- model: माया गर्छौ कि नै भन ना
- draft: माया गर्छौ कि नै भन ना

### tl_0066 · cer 0.1875 · short
- roman: `testai huna sakcha`
- gold:  त्यस्तै हुन सक्छ
- model: तेस्तै हुना सक्छ
- draft: तेस्तै हुन सक्छ

### tl_0134 · cer 0.1875 · medium
- roman: `Bhawanama Na Aau Timi`
- gold:  भावनामा नआऊ तिमी
- model: भावनामा ना आउ तिमी
- draft: भवानामा ना आउ तिमी

### tl_0058 · cer 0.1818 · short
- roman: `Timilai Nalai Bhachaina`
- gold:  तिमीलाई न ल्याई भा छैन
- model: तिमीलाई नलाई भाछैन
- draft: तिमीलाई नलाई भाछैन

### tl_0095 · cer 0.1818 · short
- roman: `Ujaad mausamma`
- gold:  उजाड मौसममा
- model: उजाड मौसम्म
- draft: उजाड मौसममा

### tl_0103 · cer 0.1818 · medium
- roman: `Haa Haa Haaa Haaa`
- gold:  हा हा हा हा
- model: हा हा हाँ हाँ
- draft: हाँ हाँ हाहाँ हाहाँ

### tl_0114 · cer 0.1818 · medium
- roman: `huncha ki nai hunna vana na`
- gold:  हुन्छ कि नाइ हुन्न भनन
- model: हुन्छ कि नै हुन्न भन ना
- draft: हुन्छ कि नै हुन्न भन ना

### tl_0136 · cer 0.1818 · medium
- roman: `Tanneriko Sapana Jastai Swadama Na Aau`
- gold:  तन्नेरीको सपनाजस्तै विस्वादमा नआऊ
- model: तन्नेरीको सपना जस्तै स्वादमा ना आउ
- draft: तान्येरिको सपना जस्तै स्वादमा ना आउ

### tl_0057 · cer 0.1739 · medium
- roman: `Dharo Dharma Yo Kura Sancho Cha`
- gold:  धरोधर्म यो कुरा साँचो छ
- model: धारो धर्म यो कुरा सान्चो छ
- draft: धारो धर्म यो कुरा साँचो छ

### tl_0004 · cer 0.1667 · medium
- roman: `Achanak badliyo manau tyo mero hoina`
- gold:  अचानक बद्लियो, मानौँ, त्यो मेरो होइन
- model: अचानक बदलियो मनाउ त्यो मेरो होइन
- draft: अचानक बद्लियो मनाऊ त्यो मेरो होइन

### tl_0046 · cer 0.1667 · medium
- roman: `Kahile Kahin Bazar Ma`
- gold:  कहिले काहीँ बजारमा
- model: कहिले कहिँ बजार मा
- draft: कहिलै कहिँ बजार मा

### tl_0055 · cer 0.1667 · medium
- roman: `Budha Pakha Bhet Huda`
- gold:  बुढापाका भेट हुँदा
- model: बुढा पाखा भेट हुदा
- draft: बुढा पाखा भेट हुदा

### tl_0071 · cer 0.1667 · medium
- roman: `chota ajhai balji dincha`
- gold:  चोट अझै बल्झिदिन्छ
- model: चोट अझै बल्जी दिन्छ
- draft: चोटा अझै बल्जी दिन्छ

### tl_0131 · cer 0.16 · medium
- roman: `Kahile Kahi Maya Pani Dekhaune Gara`
- gold:  कहिले माया पनि देखाउने गर
- model: कहिले कहि माया पनि देखाउने गर
- draft: कहिले कही माया पनि देखाउने गर

### tl_0142 · cer 0.16 · medium
- roman: `Nalukai Maanka Sara Bimbaharu`
- gold:  नलुकाई मनका सारा विम्बहरू
- model: नलुकै मानका सारा बिम्बहरू
- draft: नलुकाइ मान्का सारा बिम्बहरू

### tl_0122 · cer 0.1579 · medium
- roman: `Ma pani k ma kaam chu ni`
- gold:  म पनि केमा कम छु नि
- model: मा पनि क मा काम छु नि
- draft: म पनि के मा काम छु नि

### tl_0015 · cer 0.1562 · medium
- roman: `Maile sumpi diye sabai timrai naamma`
- gold:  मैले सुम्पिदिएँ सबै तिम्रै नाममा
- model: मैले सुम्पी दिए सबै तिम्रै नाम्म
- draft: मैले सुम्पी दिए सबै तिम्रै नाम्मा

### tl_0049 · cer 0.1538 · medium
- roman: `U Jaba Bolaunche Jiskaudai`
- gold:  ऊ जब बोलाउँछे जिस्क्याउँदै
- model: उ जब बोलाउँछे जिस्काउदै
- draft: उ जबा बोलाउन्चे जिस्काउदै

### tl_0107 · cer 0.15 · medium
- roman: `Timi ra ma ghumna jaau na`
- gold:  तिमी र म घुम्न जाउँन
- model: तिमी र मा घुम्न जाऊ न
- draft: तिमी रा मा घुम्न जाउ ना

### tl_0044 · cer 0.1481 · medium
- roman: `Pagal Banaki Che Ghayal Banaki Che`
- gold:  पागल बनाकी छे घायल बनाकी छे
- model: पागल बनकी चे घायल बनकी चे
- draft: पागल बनाकी छे घाइटल बनाकी छे

### tl_0050 · cer 0.1481 · medium
- roman: `Ankha Haru Sankaunche Jhimkaudai`
- gold:  आँखाहरू सन्काउछे झिम्काउँदै
- model: आँखा हरु सन्काउँछे झिम्काउदै
- draft: आँखा हरु शंकाउन्चे झिमकाउदै

### tl_0003 · cer 0.1429 · medium
- roman: `Beglai bho mero yo duniya hijo bhanda`
- gold:  बेग्लै भो मेरो यो दुनियाँ हिजोभन्दा
- model: बेगलाई भो मेरो यो दुनिया हिजो भन्दा
- draft: बेग्लै भो मेरो यो दुनिया हिजो भन्दा

### tl_0104 · cer 0.1429 · medium
- roman: `Paari tyo dadama hera`
- gold:  पारी त्यो डाँडामा हेर
- model: पारी त्यो दादामा हेर
- draft: पारी त्यो डाँडामा हेर

### tl_0108 · cer 0.1429 · medium
- roman: `Ani gham le malai sataula`
- gold:  अनि घामले मलाई सताउला
- model: अनि घाम ले मलाई सतौला
- draft: अनि घाम ले मलाई सताउला

### tl_0130 · cer 0.1429 · medium
- roman: `Ye Malai Maya Garchhau Bhanne Hajura`
- gold:  ए मलाई माया गर्छु भन्ने हजुर
- model: ये मलाई माया गर्छौ भन्ने हजुरा
- draft: ये मलाई माया गर्छौ भन्ने हजुर

### tl_0087 · cer 0.1333 · short
- roman: `Malai jati marchau`
- gold:  मलाई जति मार्छौ
- model: मलाई जति मर्चौ
- draft: मलाई जति मार्छौ

### tl_0078 · cer 0.1304 · medium
- roman: `Feri kina malai berthaima`
- gold:  फेरि किन मलाई ब्यर्थैमा
- model: फेरी किन मलाई बेर्थैमा
- draft: फेरि किन मलाई बार्थाइमा

### tl_0013 · cer 0.129 · medium
- roman: `Bhabishyako mitho kalpana bhulisakyou`
- gold:  भविष्यको मीठो कल्पना बुनिसक्यौँ
- model: भबिष्यको मीठो कल्पना भुलिसक्यौ
- draft: भविष्यको मिठो कल्पना भुलिसक्यौ

### tl_0038 · cer 0.125 · short
- roman: `Malai afno bhanne`
- gold:  मलाई आफ्नो भन्ने
- model: मलाई अफनो भन्ने
- draft: मलाई आफ्नो भन्ने

### tl_0042 · cer 0.125 · medium
- roman: `Maski Maski Hidera Jane Le`
- gold:  मस्कीमस्की हिँडेर जानेले
- model: मस्की मस्की हिडेर जाने ले
- draft: मस्की मस्की हिडेर जाने ले

### tl_0045 · cer 0.125 · medium
- roman: `Malai Pagal Banaki Che Ghayal Banaki Che`
- gold:  मलाई पागल बनाकी छे घायल बनाकी छे
- model: मलाई पागल बनकी चे घायल बनकी चे
- draft: मलाई पागल बनाकी छे घाइटल बनाकी छे

### tl_0059 · cer 0.125 · medium
- roman: `Tarki Tarki Hidera Jane Le`
- gold:  तर्कीतर्की हिँडेर जानेले
- model: तर्की तर्की हिडेर जाने ले
- draft: तर्कि तर्कि हिडेर जाने ले

### tl_0068 · cer 0.125 · medium
- roman: `sapana le saath dida`
- gold:  सपनाले साथ दिँदा
- model: सपना ले साथ दिदा
- draft: सपना ले साथ दिदा

### tl_0092 · cer 0.125 · medium
- roman: `Timro maan ho ki dhunga ho`
- gold:  तिम्रो मन हो कि ढुंगा हो
- model: तिम्रो मान हो कि ढुङ्गा हो
- draft: तिम्रो मान हो कि ढुंगा हो

### tl_0123 · cer 0.125 · medium
- roman: `pakhuri ma daam cha ni`
- gold:  पाखुरीमा दम छ नि
- model: पाखुरी मा दाम छ नि
- draft: पाखुरी मा दाम छ नि

### tl_0115 · cer 0.12 · medium
- roman: `Ani jaal ma eklai parchau ki`
- gold:  अनि जालमा एक्लै पार्छौ कि
- model: अनि जाल मा एकलै पर्छौ कि
- draft: अनि जाल मा एक्लै पर्छौ की

### tl_0121 · cer 0.12 · medium
- roman: `bhai bhuli najanu ni kahile ho`
- gold:  भै भूली नजानु नि कहिले हो
- model: भाइ भुली नजानु नि कहिले हो
- draft: भै भुली नजानु नि कहिले हो

### tl_0088 · cer 0.1176 · short
- roman: `tyatinai jhan marchau`
- gold:  त्यति नै झन मर्छौ
- model: त्यतिनै झन मर्चौ
- draft: त्यतिनै झन मार्छौ

### tl_0060 · cer 0.1154 · medium
- roman: `Farki Farki Hasera Herne Le`
- gold:  फर्कीफर्की हाँसेर हेर्नेले
- model: फर्की फर्की हासेर हेर्ने ले
- draft: फर्कि फर्कि हासेर हेर्ने ले

### tl_0149 · cer 0.1124 · long
- roman: `Hamro deshma jadoma dherai chiso ra sukhha hunchha ra garmima andhibehari barsha ra badhipahiro hunachhan`
- gold:  हाम्रो देशमा जाडोमा धेरै चिसो र सुख्खा हुन्छ र गर्मीमा आँधीबेहरी बर्षा र बाढिपहिरो हुनछन्
- model: हाम्रो देशमा जाडोमा धेरै चिसो र सुख्ह हुन्छ रा गर्मीमा अन्धिबेहरी बर्ष र बढीपहिरो हुनछन्
- draft: हाम्रो देशमा जडोमा धेरै चिसो रा सुक्खा हुन्छ रा गर्मिमा अन्धिबेहारी बर्षा रा बधिपाहिरो हुनाछन

### tl_0006 · cer 0.1111 · medium
- roman: `Maile bhuli diye yo sara jamana`
- gold:  मैले भुलिदिएँ यो सारा जमाना
- model: मैले भुली दिए यो सारा जमाना
- draft: मैले भुली दिए यो सारा जमाना

### tl_0074 · cer 0.1111 · medium
- roman: `milan nabhai bite bhane`
- gold:  मिलन नभइ बितेँ भने
- model: मिलन नभै बिते भने
- draft: मिलन नभई बिते भने

### tl_0139 · cer 0.1111 · medium
- roman: `Manchhe Ke Ke Bhanchhan Malai`
- gold:  मान्छे के के भन्छन् तिमीलाई
- model: मान्छे के के भन्छन् मलाई
- draft: मान्छे के के भन्छन् मलाई

### tl_0141 · cer 0.1111 · medium
- roman: `Sancho Kura Bhana Malai`
- gold:  साँचो कुरा भन मलाई
- model: सान्चो कुरा भन मलाई
- draft: सान्चो कुरा भना मलाई

### tl_0155 · cer 0.1111 · medium
- roman: `Lumbini Gorkha Janakpur Kathmandu prakhyat udaharanaharu hun`
- gold:  लुम्बिनी गोरखा जनकपुर काठमाडौं प्रख्यात उदाहरणहरू हुन्
- model: लुम्बिनी गोर्खा जनकपुर काठमाण्डु प्रख्यात उदाहरणाहरू हुन्
- draft: लुम्बिनी गोर्खा जनकपुर काठमाडौं प्रख्यात उदाहरणहरू हुन

### tl_0160 · cer 0.1111 · medium
- roman: `Yaha dherai jati ra dharmaka manis baschan`
- gold:  यहाँ धेरै जाति र धर्मका मानिस बस्छन्
- model: यहा धेरै जति र धर्मका मानिस बस्चन
- draft: यहाँ धेरै जाति रा धर्मका मानिस बस्चन

### tl_0017 · cer 0.1081 · long
- roman: `Bhalai choto hola yaha sabai drishya atauna lai`
- gold:  भलै छोटो होला यहाँ सबै दृष्य अटाउनलाई
- model: भलाई छोटो होला यहाँ सबै दृश्य अटाउन लाई
- draft: भलाई छोटो होला यहाँ सबै दृश्य अटाउन लाई

### tl_0159 · cer 0.1081 · medium
- roman: `Urvara ra ardra dakshin kshetra sahari chha`
- gold:  उर्वर र आर्द्र दक्षिणी क्षेत्र शहरी छ
- model: उर्वरा र अर्द्र दक्षिण क्षेत्र सहरी छ
- draft: उर्बरा रा आर्द्रा दखिन क्षेत्र सहरी छ

### tl_0016 · cer 0.1053 · long
- roman: `Upahar swaroop yo tasbeer maya garne haru lai`
- gold:  उपहारस्वरूप यो तस्बीर माया गर्नेहरूलाई
- model: उपहार स्वरूप यो तस्बीर माया गर्ने हरु लाई
- draft: उपहार स्वरूप यो तस्बीर माया गर्ने हरु लाई

### tl_0018 · cer 0.1053 · long
- roman: `Jindagi narahos rahi rahanecha yesma kaid pal haru`
- gold:  जिन्दगी नरहोस् रहिरहनेछ यसमा कैद पलहरू
- model: जिन्दगी नरहोस् रहि रहनेछ येसमा कैद पल हरु
- draft: जिन्दगी नरहोस रही रहनेछ येस्मा कैद पल हरु

### tl_0124 · cer 0.1053 · short
- roman: `sampati kamayincha ni`
- gold:  सम्पत्ति कमाइन्छ नि
- model: सम्पत्ति कमायिन्छ नि
- draft: सम्पति कमाइन्छ नि

### tl_0085 · cer 0.1034 · medium
- roman: `Ma hu prakriti malai hasna deu`
- gold:  म हुँ प्रकृति मलाई हाँस्न देउ
- model: मा हु प्रकृति मलाई हास्न देउ
- draft: म हुँ प्रकृति मलाई हास्न देउ

### tl_0029 · cer 0.1 · medium
- roman: `Hera malai samau yo haat`
- gold:  हेर मलाई समाऊ यो हात
- model: हेरा मलाई समाउ यो हात
- draft: हेर मलाई समाऊ यो हात

### tl_0048 · cer 0.1 · medium
- roman: `Luki Luki Herche Malai`
- gold:  लुकीलुकी हेर्छे मलाई
- model: लुकी लुकी हेर्चे मलाई
- draft: लुकि लुकि हेर्चे मलाई

### tl_0072 · cer 0.1 · medium
- roman: `kalpi kalpi roye bhane`
- gold:  कल्पी कल्पी रोएँ भने
- model: कल्पी कल्पी रोये भने
- draft: कल्पि कल्पि रोए भने

### tl_0111 · cer 0.1 · medium
- roman: `Khola jastai bagau hami`
- gold:  खोला जस्तै बगौं हामी
- model: खोला जस्तै बगाउ हामी
- draft: खोला जस्तै बगाउ हामी

### tl_0162 · cer 0.1 · long
- roman: `Hamro lokapriya khanaharu dal bhat dindo gunrdruk ityadi hun`
- gold:  हाम्रो लोकप्रिय खानाहरू दाल भाट डिन्डो गुनर्दुक इत्यादि हुन्
- model: हाम्रो लोकप्रिय खानाहरू दाल भात दिन्दो गुणर्द्रुक इत्यादि हुन्
- draft: हाम्रो लोकप्रिय खानाहरू दाल भात ढिँडो गुन्द्रुक इत्यादि हुन्

### tl_0056 · cer 0.0952 · medium
- roman: `Buhari Ko Gharma Khacho Cha`
- gold:  बुहारीको घरमा खाँचो छ
- model: बुहारी को घरमा खाचो छ
- draft: बुहारी को घरमा खाचो छ

### tl_0129 · cer 0.0952 · medium
- roman: `Timi ra ma ghumna jau na`
- gold:  तिमी र म घुम्न जाउँ न
- model: तिमी र मा घुम्न जाउ न
- draft: तिमी रा मा घुम्न जाउ ना

### tl_0034 · cer 0.0909 · medium
- roman: `Khusi chau hami chau jaha`
- gold:  खुसी छौँ हामी छौँ जहाँ
- model: खुसी छौ हामी छौ जहाँ
- draft: खुसी छौ हामी छौ जहाँ

### tl_0097 · cer 0.0909 · short
- roman: `Hawahuri sanga`
- gold:  हावाहुरीसँग
- model: हावाहुरी सँग
- draft: हावाहुरी सँग

### tl_0191 · cer 0.0909 · long
- roman: `Yasko sathai Annapurna Kanchanjangha Lotse Manaslu Yalungkad Makalu Machapuchhre aadi himalaharu pani Nepalma chhan`
- gold:  यसका साथै अन्नपूर्ण कञ्चनजङ्घा लोत्से मनासलु यालुङकाड मकालु माछापुच्छे आदि हिमालहरू पनि नेपालमा छन्
- model: यसको साथै अन्नपूर्ण कञ्चनजंघा लोत्से मनस्लु यालुङकड मकालु माछापुछ्रे आदि हिमालाहरू पनि नेपालमा छन्
- draft: यसको साथै अन्नपूर्ण कञ्चनजङ्घा ल्होत्से मनास्लु यालुङकद मकालु माछापुच्छ्रे आदि हिमालहरू पनि नेपालमा छन्

### tl_0043 · cer 0.087 · medium
- roman: `Musu Musu Hasera Herne Le`
- gold:  मुसुमुसु हासेर हेर्नेले
- model: मुसु मुसु हासेर हेर्ने ले
- draft: मुसु मुसु हासेर हेर्ने ले

### tl_0052 · cer 0.087 · medium
- roman: `Jali Rumal Chadera Janera`
- gold:  जाली रुमाल छाडेर जानेले
- model: जाली रुमाल छाडेर जानेर
- draft: जाली रुमाल चढेर जानेर

### tl_0102 · cer 0.087 · medium
- roman: `Timlai sadhai daaki rahancha`
- gold:  तिमीलाई सधैं डाकी रहन्छ
- model: तिमलाई सधैँ डाकी रहन्छ
- draft: तिम्लाई सधैँ डाकी रहन्छ

### tl_0033 · cer 0.0833 · medium
- roman: `Paschatap chaina kunai yaha`
- gold:  पश्चात्ताप छैन कुनै यहाँ
- model: पश्चाताप छैन कुनै यहाँ
- draft: पश्चाताप छैन कुनै यहाँ

### tl_0110 · cer 0.0833 · medium
- roman: `Timi pirati ko chata odau na`
- gold:  तिमी पिरतीको छाता ओढाउ न
- model: तिमी पिरती को छाता ओडाउ न
- draft: तिमी पिरती को छाता ओडाउ ना

### tl_0200 · cer 0.0833 · medium
- roman: `Yaha bibhinna prajatika rukhaharu painchha`
- gold:  यहां विभिन्न प्रजातिका रूखहरू पाइन्छ
- model: यहा बिभिन्न प्रजातिका रुखहरू पाइन्छ
- draft: यहाँ विभिन्न प्रजातिको रुखहरू पाइन्छ

### tl_0192 · cer 0.0826 · long
- roman: `Hamro deshko himalma phalam sun chandi abhrakh chunadhunga sisa gandhak marble soda sidhenaun birenaun khari aadika khani chhan`
- gold:  हाम्रो देशको हिमालमा फलाम सुन चाँदी अभ्रख चुनढुङ्गा सिसा गन्धक मार्बल सोडा सिधेनुन विरेनुन खरी आदिका खानी छन्
- model: हाम्रो देशको हिमालमा फलाम सुन चण्डी अभ्रख चुनाढुङ्गा सिसा गन्धक मार्बल सोडा सिधेनौं बिरेनौं खरी आदिका खानी छन्
- draft: हाम्रो देशको हिमालमा फलाम सुन चाँदी अभ्रख चुनाढुङ्गा सिसा गन्धक मार्बल सोडा सिधेनुन बिरेनुन खारी आदिमा खानी छन्

### tl_0145 · cer 0.0806 · long
- roman: `China uttarpatti awasthit chha ra paschim purva ra dakshin Bharatle dhakeko chha`
- gold:  चीन उतरपट्टि अवस्थित छ र पश्चिम पुर्व र दक्षिण भारतले ढाकेको छ
- model: चिना उत्तरपट्टि अवस्थित छ र पश्चिम पूर्व र दक्षिण भारतले ढाकेको छ
- draft: चिन उत्तरपत्ति अवस्थीत छ रा पस्चिम पुर्व रा दखिन भारत्ले ढाकेको छ

### tl_0161 · cer 0.08 · medium
- roman: `Lagbhag saya bhashaharu bolinchhan`
- gold:  लगभग सय भाषाहरु बोलिन्छन्
- model: लगभाग सय भाषाहरू बोलिन्छन्
- draft: लगभग सय भाषाहरू बोलिन्छन्

### tl_0164 · cer 0.08 · long
- roman: `Nepal sano chha tara prakritik srotsadhanma dhani chha tara arthik awasthale garda garib chha`
- gold:  नेपाल सानो छ तर प्राकृतिक स्रोतसाधनमा धनी छ तर आर्थिक अवस्थाले गर्दा गरीब छ
- model: नेपाल सानो छ तारा प्राकृतिक स्रोत्साधनमा धनी छ तारा आर्थिक अवस्थाले गर्दा गरिब छ
- draft: नेपाल सानो छ तर प्राकृतिक स्रोतसाधनमा धनी छ तर आर्थिक अवस्थाले गर्दा गरीब छ

### tl_0158 · cer 0.0781 · long
- roman: `Sabha bhanda aglo Sagarmatha Angrejima Mount Everest ko rupma chininchha`
- gold:  सब भन्दा अग्लो सगरमाथा अंग्रेजीमा माउन्ट एभरेष्टको रूपमा चिनिन्छ
- model: सभा भन्दा अग्लो सगरमाथा अंग्रेजीमा माउन्ट इभरेस्ट को रूपमा चिनिन्छ
- draft: सभा भन्दा अग्लो सगरमाथा अन्ग्रेजिमा Mount Everest को रुपमा चिनिन्छ

### tl_0021 · cer 0.0769 · medium
- roman: `Euta maya garne byakti lai`
- gold:  एउटा माया गर्ने व्यक्तिलाई
- model: एउटा माया गर्ने ब्यक्ति लाई
- draft: एउटा माया गर्ने ब्याक्ति लाई

### tl_0089 · cer 0.0769 · short
- roman: `Kahile huri sanga`
- gold:  कहिले हुरीसँग
- model: कहिले हुरी सँग
- draft: कहिले हुरी सँग

### tl_0137 · cer 0.0769 · medium
- roman: `Pritiko Phool Tipnu Parchha Bhane`
- gold:  प्रीतिको फूल टिप्नपर्छ भने
- model: प्रीतिको फूल टिप्नु पर्छ भने
- draft: प्रितिको फूल टिपनु पर्छ भने

### tl_0138 · cer 0.0769 · medium
- roman: `Kada Dekhi Darai Nabhagne Gara`
- gold:  काँडा देखि डराई नभाग्ने गर
- model: काडा देखि दराई नभाग्ने गर
- draft: कडा देखी डराइ नभग्ने गर

### tl_0020 · cer 0.0741 · medium
- roman: `Tyo bhanda aru ke nai chahincha`
- gold:  त्योभन्दा अरू के नै चाहिन्छ
- model: त्यो भन्दा अरु के नै चाहिन्छ
- draft: त्यो भन्दा अरु के नै चाहिन्छ

### tl_0079 · cer 0.0741 · medium
- roman: `Metne kosish garchau harek din`
- gold:  मेट्ने कोशिस गर्छौ हरेक दिन
- model: मेट्ने कोसिश गर्छौ हरेक दिन
- draft: मेट्ने कोसिस गर्छौ हरेक दिन

### tl_0163 · cer 0.0741 · long
- roman: `Dashain Tihar Losar aadi sabhaibhanda lokapriya chadparvaharu hun`
- gold:  दशैं तिहार लोसार आदि सबैभन्दा लोकप्रिय चाडपर्वहरू हुन्
- model: दशैं तिहार लोसार आदि सभाइभन्दा लोकप्रिय चडपर्वहरू हुन्
- draft: दसैँ तिहार ल्होसार आदि सबैभन्दा लोकप्रिय चाडपर्वहरू हुन्

### tl_0090 · cer 0.0714 · short
- roman: `kahile pahiro sanga`
- gold:  कहिले पहिरोसँग
- model: कहिले पहिरो सँग
- draft: कहिले पहिरो सँग

### tl_0099 · cer 0.0714 · short
- roman: `suna mero dhadkan`
- gold:  सुन मेरो धड्कन
- model: सुना मेरो धड्कन
- draft: सुना मेरो धड्कन

### tl_0193 · cer 0.07 · long
- roman: `Yaha yarchagumba jasta prakritik jadibuti chhan bhane yak yeti chauri gai kasturi jasta jantu pani raheka chhan`
- gold:  यहाँ यार्चागुम्बा जस्ता प्राकृतिक जडिबुटी छन् भने याक यति चौरी गाई कस्तुरी जस्ता जन्तु पनि रहेका छन्
- model: यहा यार्चागुम्बा जस्ता प्राकृतिक जडीबुटी छन भने याक येती चौरी गाइ कस्तुरी जस्ता जन्तु पनि रहेका छन
- draft: यहाँ यार्सागुम्बा जस्ता प्राकृतिक जडीबुटी छन् भने याक यती चौँरी गाई कस्तुरी जस्ता जन्तु पनि रहेका छन्

### tl_0183 · cer 0.0698 · long
- roman: `Pani vishwakai pranilai banchanka lagi nabhai nahune dainik upabhogma parne prakritik sampada ho`
- gold:  पानी विश्वकै प्राणीलाई बाँच्नका लागि नभई नहुने दैनिक उपभोगमा पर्ने प्राकृतिक सम्पदा हो
- model: पनि विश्वकै प्राणीलाई बञ्चनका लागि नभै नहुने दैनिक उपभोगमा पर्ने प्राकृतिक सम्पदा हो
- draft: पानी विश्वका प्राणीलाई बाँच्नका लागि नभई नहुने दैनिक उपभोगमा पर्ने प्राकृतिक सम्पदा हो

### tl_0086 · cer 0.069 · medium
- roman: `Ma hu prakriti malai bachna deu`
- gold:  म हुँ प्रकृति मलाई बाँच्न देउ
- model: मा हु प्रकृति मलाई बाँच्न देउ
- draft: म हुँ प्रकृति मलाई बाच्न देउ

### tl_0202 · cer 0.0688 · long
- roman: `Tara paisaka lagi marihatte garera aafno sukhsubidhaka lagi aafno santanko bhabisyasangai kheldai lobhi ra papiharu le Nepalko charkose jhadi ra bibhinna pahadma bhaeka jangal phadani gari basti basalna suru gareka chhan`
- gold:  तर पैसाका लागि मरिहत्ते गरेर आफ्नो सुखसुविधाका लागि आफ्‌नो सन्तानको भविष्यसंगै खेल्दै लोभी र पापीहरूले नेपालको चारकोसे झाडी र विभिन्न पहाडमा भएका जङ्गल फडानी गरी वस्ती बसाल्न सुरु गरेका छन्
- model: तारा पैसाका लागि मरिहत्ते गरेर आफ्नो सुखसुबिधाका लागि आफ्नो सन्तानको भबिष्यसँगै खेल्दै लोभी र पापीहरू ले नेपालको चर्कोसे झाडी र बिभिन्न पहाडमा भएका जंगल फडानी गरी बस्ती बसाल्न सुरु गरेका छन्
- draft: तर पैसाका लागि मरीहत्ते गरेर आफ्नो सुखसुविधाका लागि आफ्नो सन्तानको भविष्यसँगै खेल्दै लोभी रा पापीहरू ले नेपालको चारकोसे झाडी रा विभिन्न पहाडमा भएका जङ्गल फडानी गरी बस्ती बसाल्न सुरु गरेका छन्

### tl_0153 · cer 0.0682 · long
- roman: `Hamisanga hariyo upatyaka sundar pani jharna aadi chha`
- gold:  हामीसँग हरियो उपत्यका सुन्दर पानी झरना आदि छ
- model: हामीसँग हरियो उपत्यका सुन्दर पनि झर्ना आदि छ
- draft: हामिसंग हरियो उपत्यका सुन्दर पनि झर्ना आदि छ

### tl_0184 · cer 0.0682 · long
- roman: `Yasko prayog pyas metna sharir ra lugaka mayal milkauna sinchai garna ra bijuli utpadanma bhaeko chha`
- gold:  यसको प्रयोग प्यास मेट्न शरीर र लुगाका मयल मिल्काउन सिंचाइ गर्न र विजुली उत्पादनमा भएको छ
- model: यसको प्रयोग प्यास मेट्न शरीर र लुगाका मायल मिल्काउन सिन्छै गर्न र बिजुली उत्पादनमा भएको छ
- draft: यसको प्रयोग प्यास मेट्न शरीर र लुगाका मयल मिल्काउन सिँचाइ गर्न र बिजुली उत्पादनमा भएको छ

### tl_0036 · cer 0.0667 · short
- roman: `Hamro bare kura`
- gold:  हाम्रोबारे कुरा
- model: हाम्रो बारे कुरा
- draft: हाम्रो बारे कुरा

### tl_0063 · cer 0.0667 · short
- roman: `timi tadha huda`
- gold:  तिमी टाढा हुँदा
- model: तिमी टाढा हुदा
- draft: तिमी टाढा हुदा

### tl_0064 · cer 0.0667 · short
- roman: `dherai dukha lagcha`
- gold:  धेरै दुःख लाग्छ
- model: धेरै दुख लाग्छ
- draft: धेरै दुख लाग्छ

### tl_0203 · cer 0.0617 · long
- roman: `Nepalko jangalma harro barro amala tejpat aiselu chutro panchaule jasta jadibuti painchha`
- gold:  नेपालको जंगलमा हर्रो बर्रो अमला तेजपात ऐसेलु चुत्रो पाँचऔंले जस्ता जडिबुटी पाइन्छ
- model: नेपालको जंगलमा हर्रो बर्रो अमला तेजपात आइसेलु चुत्रो पाँचौले जस्ता जडीबुटी पाइन्छ
- draft: नेपालको जङ्गलमा हर्रो बरो अमला तेजपत्ता ऐँसेलु चुत्रो पाँचऔँले जस्ता जडीबुटी पाइन्छ

### tl_0197 · cer 0.0615 · long
- roman: `Nepalko Pokharama Phewatal Beganastal raheka chhan bhane Surkheta Bulbule tal Chitwanma Nandbhauju Kasara Gadwal Tamorhaila jasta talharu raheka chhan`
- gold:  नेपालको पोखरामा फेवाताल वेगनासताल रहेका छन् भने सुर्खेतमा बुलबुले ताल चितवनमा नन्दभाउजू कसरा गडवाल तमोरघैला जस्ता तालहरू रहेका छन्
- model: नेपालको पोखरामा फेवाताल बेगनास्तल रहेका छन भने सुर्खेता बुलबुले ताल चितवनमा नन्दभाउजु कसरा गडवाल तमोरहैला जस्ता तालहरू रहेका छन
- draft: नेपालको पोखरामा फेवाताल बेगनासताल रहेका छन् भने सुर्खेतमा बुलबुले ताल चितवनमा नन्दभाउजु कसरा गढवाल तमोरहैला जस्ता तालहरू रहेका छन्

### tl_0075 · cer 0.0588 · short
- roman: `timi bichalit nahunu`
- gold:  तिमी बिचलित नहुनू
- model: तिमी बिचलित नहुनु
- draft: तिमी बिचलित नहुनु

### tl_0188 · cer 0.0588 · long
- roman: `Nepalko arko mahattwapurna prakritik sampada himalaya shrinkhalaharu hun`
- gold:  नेपालको अर्को महत्त्वपूर्ण प्राकृतिक सम्पदा हिमालय श्रृङ्खलाहरू हुन्
- model: नेपालको अर्को महत्त्वपूर्ण प्राकृतिक सम्पदा हिमालय शृंखलाहरू हुन्
- draft: नेपालको अर्को महत्वपूर्ण प्राकृतिक सम्पदा हिमालय शृङ्खलाहरू हुन्

### tl_0157 · cer 0.0577 · long
- roman: `Himali uttarma vishwaka chaudha uchchatam pahadharumaddhye aath chhan`
- gold:  हिमाली उत्तरमा विश्वका १४ उच्चतम पहाडहरूमध्ये आठ छन्
- model: हिमाली उत्तरमा विश्वका चौध उच्चतम पहाडहरूमध्ये आठ छन्
- draft: हिमालि उत्तरमा विश्वका चौध उच्चतम् पहाधरुमद्ध्ये आठ छन

### tl_0195 · cer 0.0577 · long
- roman: `Taltalaiya ra jharnharu pani Nepalka prakritik sampada hun`
- gold:  तालतलैया र झरनाहरू पनि नेपालका प्राकृतिक सम्पदा हुन्
- model: तालतालैया र झर्नहरू पनि नेपालका प्राकृतिक सम्पदा हुन्
- draft: टालतलैया र झरनाहरू पनि नेपालका प्राकृतिक सम्पदा हुन्

### tl_0204 · cer 0.0571 · medium
- roman: `Yi jadibuti aushadhi banauna prayog garinchha`
- gold:  यी जडिबुटी औषधी बनाउन प्रयोग गरिन्छ
- model: यी जडीबुटी औषधि बनाउन प्रयोग गरिन्छ
- draft: यी जडीबुटी औषधि बनाउन प्रयोग गरिन्छ

### tl_0091 · cer 0.0556 · short
- roman: `tyati pani bujdainau`
- gold:  त्यति पनि बुझ्दैनौ
- model: त्यति पनि बुज्दैनौ
- draft: त्यति पनि बुझ्दिनाउ

### tl_0185 · cer 0.0538 · long
- roman: `Nepalma paniko strot Asia mahadeshma nai pahilo ra vishwama Brazil pachadiko dosro sthanma raheko chha`
- gold:  नेपालमा पानीको स्रोत एसिया महादेशमा नै पहिलो र विश्वमा ब्राजिल पछाडिको दोस्रो स्थानमा रहेको छ
- model: नेपालमा पानीको स्ट्रोट एसिया महादेशमा नै पहिलो र विश्वमा ब्राजिल पचाडीको दोस्रो स्थानमा रहेको छ
- draft: नेपालमा पानीको स्रोत एसिया महादेशमा नै पहिलो र विश्वमा ब्राजिल पछिल्लो दोस्रो स्थानमा रहेको छ

### tl_0035 · cer 0.0526 · medium
- roman: `Bhanne le bhanos garos`
- gold:  भन्नेले भनोस् गरोस्
- model: भन्ने ले भनोस् गरोस्
- draft: भन्ने ले भनोस गरोस

### tl_0166 · cer 0.0506 · long
- roman: `Chado nai vikas garnaka lagi aajdekhi hamile deshko sabai nagarikta bare sachet hunupardhachha`
- gold:  चाँडै नै विकास गर्नका लागि आजदेखि हामीले देशको सबै नागरिकता बारे सचेत हुनुपर्दछ
- model: छाडो नै विकास गर्नका लागि आजदेखि हामीले देशको सबै नागरिकता बारे सचेत हुनुपर्धछ
- draft: छिटो नै विकास गर्नका लागि आजदेखि हामीले देशको सबै नागरिकता बारे सचेत हुनुपर्दछ

### tl_0069 · cer 0.05 · medium
- roman: `sangai base jasto lagcha`
- gold:  संगै बसे जस्तो लाग्छ
- model: सँगै बसे जस्तो लाग्छ
- draft: संगै बासे जस्तो लाग्छ

### tl_0189 · cer 0.0488 · long
- roman: `Nepalko uttar dishama purvadekhi paschimsamda paredka sipahi himali shrinkhala ubhieka chhan`
- gold:  नेपालको उत्तर दिशामा पूर्वदेखि पश्चिमसम्म परेडका सिपाही हिमाली श्रृंखला उभिएका छन्
- model: नेपालको उत्तर दिशामा पूर्वदेखि पश्चिमसम्दा परेडका सिपाही हिमाली शृंखला उभिएका छन्
- draft: नेपालको उत्तर दिशामा पूर्वदेखि पश्चिमतर्फ परेका सिपाही हिमाली शृङ्खला उभिएका छन्

### tl_0037 · cer 0.0476 · medium
- roman: `Jati j cha mero timi hau`
- gold:  जति—जे छ मेरो तिमी हौ
- model: जति जे छ मेरो तिमी हौ
- draft: जाती ज छ मेरो तिमी hau

### tl_0148 · cer 0.0476 · medium
- roman: `Himalaya parbatiya ra tarai`
- gold:  हिमालय पर्वतीय र तराई
- model: हिमालय पर्बतीय र तराई
- draft: हिमालय पर्बतीय रा तराइ

### tl_0031 · cer 0.0455 · medium
- roman: `Dekhne le dekhos sunos`
- gold:  देख्नेले देखोस् सुनोस्
- model: देख्ने ले देखोस् सुनोस्
- draft: देख्ने ले देखोस सुनोस

### tl_0047 · cer 0.0455 · medium
- roman: `Usko Hamro Bhet Hunda`
- gold:  उस्को हाम्रो भेट हुँदा
- model: उसको हाम्रो भेट हुँदा
- draft: उसको हाम्रो भेट हुँदा

### tl_0008 · cer 0.0435 · medium
- roman: `Din duiguna raat chauguna`
- gold:  दिन दुईगुना, रात चौगुना
- model: दिन दुईगुना रात चौगुना
- draft: दिन दुईगुना रात चौगुना

### tl_0101 · cer 0.0435 · medium
- roman: `Ekchin pachi suna yasko aawaj`
- gold:  एकछिन पछि सुन यसको आवाज
- model: एकछिन पछि सुना यसको आवाज
- draft: एकछिन पछि सुना यास्को आवाज

### tl_0172 · cer 0.0417 · long
- roman: `Ra hami aafno arthik awastha niyantran garna sakchau`
- gold:  र हामी आफ्नो आर्थिक अवस्था नियन्त्रण गर्न सक्छौं
- model: रा हामी आफ्नो आर्थिक अवस्था नियन्त्रण गर्न सक्छौ
- draft: र हामी आफ्नो आर्थिक अवस्था नियन्त्रण गर्न सक्छौँ

### tl_0170 · cer 0.0408 · medium
- roman: `Tyasobhaye hamile yaslai vishwabhar prakashit garnuparnechha`
- gold:  त्यसोभए हामीले यसलाई विश्वभर प्रकाशित गर्नुपर्नेछ
- model: त्यसोभये हामीले यसलाई विश्वभर प्रकाशित गर्नुपर्नेछ
- draft: त्यसोभए हामीले यसलाई विश्वभर प्रकाशित गर्नुपर्नेछ

### tl_0186 · cer 0.0407 · long
- roman: `Nepalko himal pahadma nagabeli bani bagne Trishuli Karnali Mashyangdi Kali Gandaki Arun Tamor jasta nadi paniko pramukhk bhandar hun`
- gold:  नेपालको हिमाल पहाडमा नागबेली बनी बग्ने त्रिशुली कर्णाली मस्याङ्दी काली गण्डकी अरुण तमोर जस्ता नदी पानीका प्रमुख भण्डार हुन्
- model: नेपालको हिमाल पहाडमा नागबेली बानी बग्ने त्रिशूली कर्णाली मश्याङ्दी काली गण्डकी अरुण तमोर जस्ता नदी पानीको प्रमुखक भण्डार हुन्
- draft: नेपालको हिमाल पहाडमा नागबेली बनी बग्ने त्रिशूली कर्णाली मर्स्याङ्दी काली गण्डकी अरुण तमोर जस्ता नदी पानीका प्रमुख भण्डार हुन्

### tl_0076 · cer 0.0385 · medium
- roman: `Soche chau timro mero sambandha`
- gold:  सोचेछौ तिम्रो मेरो सम्बन्ध
- model: सोचे छौ तिम्रो मेरो सम्बन्ध
- draft: सोचे छौ तिम्रो मेरो सम्बन्ध

### tl_0205 · cer 0.038 · long
- roman: `Hamilai prakritile himalko chiso lek pahadka hariya van ani taraiko urvara phot dieko chha`
- gold:  हामीलाई प्रकृतिले हिमालको चिसो लेक पहाडका हरिया वन अनि तराईको उर्वर फॉट दिएको छ
- model: हामीलाई प्रकृतिले हिमालको चिसो लेक पहाडका हरिया भन अनि तराईको उर्वरा फोट दिएको छ
- draft: हामीलाई प्रकृतिले हिमालको चिसो लेक पहाडका हरिया वन अनि तराईको उर्वरा फोट दिएको छ

### tl_0098 · cer 0.0345 · medium
- roman: `eklai parnu parne mero jindagi`
- gold:  एक्लै पर्नुपर्ने मेरो जिन्दगी
- model: एक्लै पर्नु पर्ने मेरो जिन्दगी
- draft: एक्लै पर्नु पर्ने मेरो जिन्दगी

### tl_0096 · cer 0.0323 · medium
- roman: `eklai bachnu parne mero jindagi`
- gold:  एक्लै बाँच्नुपर्ने मेरो जिन्दगी
- model: एक्लै बाँच्नु पर्ने मेरो जिन्दगी
- draft: एक्लै बाँच्नु पर्ने मेरो जिन्दगी

### tl_0178 · cer 0.0311 · long
- roman: `Ajha spashta shabdama bhanda Nepalma paine himal pahad tarai taramandal nadinala taltalaiya upatyaka jharna jal vayu khanij padartha jivjantu vanaspati nai hamra prakritik sampada hun`
- gold:  अझ स्पष्ट शब्दमा भन्दा नेपालमा पाइने हिमाल पहाड तराई तारामण्डल नदीनाला तालतलैया उपत्यका झरना जल वायु खनिज पदार्थ जीवजन्तु वनस्पति नै हाम्रा प्राकृतिक सम्पदा हुन्
- model: अझ स्पष्ट शब्दमा भन्दा नेपालमा पाइने हिमाल पहाड तराई तारामण्डल नदिनाला तालतालैया उपत्यका झर्ना जल भयु खनिज पदार्थ जीवजन्तु वनस्पति नै हाम्रा प्राकृतिक सम्पदा हुन्
- draft: अझ स्पष्ट शब्दमा भन्दा नेपालमा पाइने हिमाल पहाड तराई तरामण्डल नदीनाला टालतलैया उपत्यका झरना जल वायु खनिज पदार्थ जीवजन्तु वनस्पति नै हाम्रा प्राकृतिक सम्पदा हुन्

### tl_0012 · cer 0.0303 · medium
- roman: `Mayako yasto modma hami aaipugyou`
- gold:  मायाको यस्तो मोडमा हामी आइपुग्यौँ
- model: मायाको यस्तो मोडमा हामी आइपुग्यौ
- draft: मायाको यस्तो मोडमा हामी आइपुग्यौ

### tl_0196 · cer 0.0303 · long
- roman: `Nepali bhumima se Phoksundo Chhhorolpa Tilicho Rara jasta tanharu chhan jasle tyaha pugne pratyek paryataklai swarga pugeko aabhas dieko chha`
- gold:  नेपाली भूमिमा से फोक्सुन्डो च्छोरोल्पा तिलिचो रारा जस्ता तानहरू छन् जसले त्यहाँ पुग्ने प्रत्येक पर्यटकलाई स्वर्ग पुगेको आभास दिएको छ
- model: नेपाली भूमिमा से फोक्सुण्डो छोरोल्पा तिलिचो रारा जस्ता तानहरू छन जसले त्यहाँ पुग्ने प्रत्येक पर्यटकलाई स्वर्ग पुगेको आभास दिएको छ
- draft: नेपाली भूमिमा फे फोक्सुण्डो छैरोल्पा रारा जस्ता तालहरू छन् जसले त्यहाँ पुग्ने प्रत्येक पर्यटकलाई स्वर्ग पुगेको आभास दिएको छ

### tl_0190 · cer 0.0294 · long
- roman: `Vishwako sarvochcha shikhar Sagarmatha Nepalko mahattwapurna prakritik sampada ho`
- gold:  विश्वको सर्वोच्च शिखर सगरमाथा नेपालको महत्वपूर्ण प्राकृतिक सम्पदा हो
- model: विश्वको सर्वोच्च शिखर सगरमाथा नेपालको महत्त्वपूर्ण प्राकृतिक सम्पदा हो
- draft: विश्वको सर्वोच्च शिखर सगरमाथा नेपालको महत्वपूर्ण प्राकृतिक सम्पदा हो

### tl_0180 · cer 0.0292 · long
- roman: `Yi prakritik sampadabata manisle ekatir bharpura manoranjan prapta gareka chhan bhane arkotir manisko mihineta paurakh buddhi kshamata yasma pokhinda yinaibata manisle jibanma pran dhanta rogko upchar garna bideshi mudra arjan gari arthoparjan garna saksham baneka chhan`
- gold:  यी प्राकृतिक सम्पदाबाट मानिसले एकातिर भरपुर मनोरञ्जन प्राप्त गरेका छन् भने अर्कोतिर मानिसको मिहिनेत पौरख बुद्धि क्षमता यसमा पोखिंदा यिनैबाट मानिसले जीवनमा प्राण धान्त रोगको उपचार गर्न विदेशी मुद्रा आर्जन गरी अर्थोपार्जन गर्न सक्षम बनेका छन्
- model: यी प्राकृतिक सम्पदाबाट मानिसले एकातिर भरपुरा मनोरञ्जन प्राप्त गरेका छन भने अर्कोतिर मानिसको मिहिनेता पौरख बुद्धि क्षमता यसमा पोखिंदा यिनैबाट मानिसले जीबनमा प्राण धन्त रोगको उपचार गर्न बिदेशी मुद्रा अर्जन गरी अर्थोपार्जन गर्न सक्षम बनेका छन्
- draft: यी प्राकृतिक सम्पदाबाट मानिसले एकतिर भरपूर मनोरञ्जन प्राप्त गरेका छन् भने अर्कोतिर मानिसको मिहिनेत पौरख बुद्धि क्षमता यसमा पोखिंदा यिनैबाट मानिसले जीवनमा प्राण धन्ता रोगको उपचार गर्न विदेशी मुद्रा आर्जन गरी अर्थोपार्जन गर्न सक्षम बनेका छन्

### tl_0175 · cer 0.0282 · long
- roman: `Prakritima sahaj rupma paine manisbata nabanaeka vastu prakritik sampada hun`
- gold:  प्रकृतिमा सहज रूपमा पाइने मानिसबाट नबनाइएका वस्तु प्राकृतिक सम्पदा हुन्
- model: प्रकृतिमा सहज रूपमा पाइने मानिसबाट नबनाएका भस्तु प्राकृतिक सम्पदा हुन्
- draft: प्रकृतिमा सहज रूपमा पाइने मानिसबाट नबनेका वस्तु प्राकृतिक सम्पदा हुन्

### tl_0181 · cer 0.027 · long
- roman: `Yasari prakritik sampada manislai sukhko barsha garaune sampattiko rupma raheko chha`
- gold:  यसरी प्राकृतिक सम्पदा मानिसलाई सुखको वर्षा गराउने सम्पत्तिको रूपमा रहेको छ
- model: यसरी प्राकृतिक सम्पदा मानिसलाई सुखको बर्ष गराउने सम्पत्तिको रूपमा रहेको छ
- draft: यसरी प्राकृतिक सम्पदा मानिसलाई सुखको वर्षा गराउने सम्पत्तिको रूपमा रहेको छ

### tl_0177 · cer 0.0261 · long
- roman: `Yo deshko bhugolma prakritibata jejasta vastuharu nishulka rupma hamile prapta gareka chau tinlai prakritik sampada bhaninchha`
- gold:  यो देशको भूगोलमा प्रकृतिबाट जेजस्ता वस्तुहरू निःशुल्क रूपमा हामीले प्राप्त गरेका छौं तिनलाई प्राकृतिक सम्पदा भनिन्छ
- model: यो देशको भूगोलमा प्रकृतिबाट जेजस्ता वस्तुहरू निशुल्क रूपमा हामीले प्राप्त गरेका छौ तीनलाई प्राकृतिक सम्पदा भनिन्छ
- draft: यो देशको भूगोलमा प्रकृतिबाट जेजस्ता वस्तुहरू निःशुल्क रूपमा हामीले प्राप्त गरेका छौँ तिनलाई प्राकृतिक सम्पदा भनिन्छ

### tl_0199 · cer 0.025 · medium
- roman: `Hariyo van pani Nepalko prakritik sampada ho`
- gold:  हरियो वन पनि नेपालको प्राकृतिक सम्पदा हो
- model: हरियो भन पनि नेपालको प्राकृतिक सम्पदा हो
- draft: हरियो वन पनि नेपालको प्राकृतिक सम्पदा हो

### tl_0150 · cer 0.0244 · long
- roman: `Yo prakritik saundarya ra srotaharu ma dhani chha`
- gold:  यो प्राकृतिक सौन्दर्य र स्रोतहरु मा धनी छ
- model: यो प्राकृतिक सौन्दर्य र स्रोतहरू मा धनी छ
- draft: यो प्राकृतिक सौन्दर्य रा स्रोताहरू मा धानी छ

### tl_0208 · cer 0.0244 · medium
- roman: `Nepaliko bhagya badali bhabisya banauna aawashyak chha`
- gold:  नेपालीको भाग्य बदली भविष्य बनाउन आवश्यक छ
- model: नेपालीको भाग्य बदली भबिष्य बनाउन आवश्यक छ
- draft: नेपालीको भाग्य बदली भविष्य बनाउन आवश्यक छ

### tl_0144 · cer 0.0238 · long
- roman: `Mero desh Nepal dui deshharu dwara gherieko chha`
- gold:  मेरो देश नेपाल दुई देशहरु द्वारा घेरिएको छ
- model: मेरो देश नेपाल दुई देशहरू द्वारा घेरिएको छ
- draft: मेरो देश नेपाल दुई देशहरू द्वारा घेरीएको छ

### tl_0198 · cer 0.0238 · long
- roman: `Yi tan hernaka lagi matra ramra chhainan nauka vihar garna jal vihar garna pani upayukta chhan`
- gold:  यी तान हेर्नका लागि मात्र राम्रा छैनन् नौका विहार गर्न जल बिहार गर्न पनि उपयुक्त छन्
- model: यी तन हेर्नका लागि मात्र राम्रा छैनन् नौका विहार गर्न जल विहार गर्न पनि उपयुक्त छन्
- draft: यी ताल हेर्नका लागि मात्र राम्रा छैनन् नौका विहार गर्न जल विहार गर्न पनि उपयुक्त छन्

### tl_0167 · cer 0.0204 · long
- roman: `Purush ra mahila dubai saman hun ra shiksha pradan gardachha`
- gold:  पुरुष र महिला दुबै समान हुन र शिक्षा प्रदान गर्दछ
- model: पुरुष र महिला दुबै समान हुन् र शिक्षा प्रदान गर्दछ
- draft: पुरुष र महिला दुवै समान हुन् र शिक्षा प्रदान गर्दछ

### tl_0201 · cer 0.02 · long
- roman: `Yi rukhaharu niryat gari Nepalko aamdani badhauna sakinchha`
- gold:  यी रूखहरू निर्यात गरी नेपालको आम्दानी बढाउन सकिन्छ
- model: यी रुखहरू निर्यात गरी नेपालको आम्दानी बढाउन सकिन्छ
- draft: यी रुखहरू निर्यात गरी नेपालको आम्दानी बढाउन सकिन्छ

### tl_0194 · cer 0.0159 · long
- roman: `Yinle Nepalko gaurav badhaunu ka sathai yinko sadupayog garna sakeko khandama Nepal vishwakai dhani rashtrako paktima parna sakne sambhavana pani chha`
- gold:  यिनले नेपालको गौरव बढाउनुका साथै यिनको सदुपयोग गर्न सकेको खण्डमा नेपाल विश्वकै धनी राष्ट्रको पक्तिमा पर्न सक्ने सम्भावना पनि छ
- model: यिनले नेपालको गौरव बढाउनु का साथै यिनको सदुपयोग गर्न सकेको खण्डमा नेपाल विश्वकै धनी राष्ट्रको पक्तिमा पार्न सक्ने सम्भावना पनि छ
- draft: यिनले नेपालको गौरव बढाउनु का साथै यिनको सदुपयोग गर्न सकेको खण्डमा नेपाल विश्वकै धनी राष्ट्रको पङ्क्तिमा पर्न सक्ने सम्भावना पनि छ

### tl_0171 · cer 0.0147 · long
- roman: `Jun pratyaksha wa apratyaksha rupma paryataklai aakarshit garna maddhat gardachha`
- gold:  जुन प्रत्यक्ष वा अप्रत्यक्ष रूपमा पर्यटकलाई आकर्षित गर्न मद्दत गर्दछ
- model: जुन प्रत्यक्ष वा अप्रत्यक्ष रूपमा पर्यटकलाई आकर्षित गर्न मद्धत गर्दछ
- draft: जुन प्रत्यक्ष वा अप्रत्यक्ष रूपमा पर्यटकलाई आकर्षित गर्न मद्दत गर्दछ

### tl_0182 · cer 0.0109 · long
- roman: `Yahi manisko jibanma upayog hune ra Nepalma payane prakritik sampadako barema yaha ullekh garieko chha`
- gold:  यही मानिसको जीवनमा उपयोग हुने र नेपालमा पायने प्राकृतिक सम्पदाको बारेमा यहाँ उल्लेख गरिएको छ
- model: यही मानिसको जीबनमा उपयोग हुने र नेपालमा पायने प्राकृतिक सम्पदाको बारेमा यहाँ उल्लेख गरिएको छ
- draft: याही मानिसको जीवनमा उपयोग हुने र नेपालमा पाइने प्राकृतिक सम्पदाको बारेमा यहाँ उल्लेख गरिएको छ

### tl_0168 · cer 0.0075 · long
- roman: `Sarkarle agrim karyakram lyaunu pardachha ra nagarik ra sarkar dubailai faida puryaune bibhinna suvidha pradan gari nagariklai sahayog garnupardachha`
- gold:  सरकारले अग्रिम कार्यक्रम ल्याउनु पर्दछ र नागरिक र सरकार दुबैलाई फाइदा पुर्‍याउने बिभिन्न सुविधा प्रदान गरी नागरिकलाई सहयोग गर्नुपर्दछ
- model: सरकारले अग्रिम कार्यक्रम ल्याउनु पर्दछ र नागरिक र सरकार दुबैलाई फाइदा पुर्याउने बिभिन्न सुविधा प्रदान गरी नागरिकलाई सहयोग गर्नुपर्दछ
- draft: सरकारले अग्रिम कार्यक्रम ल्याउनु पर्दछ र नागरिक र सरकार दुवैलाई फाइदा पुर्याउने विभिन्न सुविधा प्रदान गरी नागरिकलाई सहयोग गर्नुपर्दछ

## Draft disagrees with the legacy gold (160 rows)

These are the rows worth a human decision: either the legacy label is
wrong (we already confirmed several) or the draft is. Set
`user_devanagari` to the accepted form and explain in `user_note`.

### tl_0028 · draft cer 0.9091
- roman: `Na na na na`
- gold:  ना—ना ना—ना
- draft: Na na na na
- model: ना ना ना न

### tl_0103 · draft cer 0.7273
- roman: `Haa Haa Haaa Haaa`
- gold:  हा हा हा हा
- draft: हाँ हाँ हाहाँ हाहाँ
- model: हा हा हाँ हाँ

### tl_0022 · draft cer 0.6087
- roman: `Ho no no na na na na na`
- gold:  Ho no—no ना ना—ना—ना—ना
- draft: Ho no no na na na na na
- model: हो नो नो ना ना ना ना न

### tl_0126 · draft cer 0.5294
- roman: `Sun chadi chahindaina`
- gold:  सुनचाँदी चाहिंदैन
- draft: सुन चादी चाहindaina
- model: सुन छाडी चाहिँदैन

### tl_0127 · draft cer 0.5294
- roman: `sampati lai aayindaina`
- gold:  सम्पत्तिलाई आइदैन
- draft: सम्पति लाइ आयिन्दैना
- model: सम्पत्ति लाइ आयिँदैन

### tl_0116 · draft cer 0.4545
- roman: `ajkalto mai chadchau ki`
- gold:  अच्कल्टो मै छाड्छौं कि
- draft: आजकल्तो मै चढछौ की
- model: आजकल्तो मै चड्छौ कि

### tl_0009 · draft cer 0.375
- roman: `Timi prati maya badhdocha`
- gold:  तिमीप्रति माया बढ्दो छ (बढ्दो छ)
- draft: तिमी प्रति माया बढ्दोछ
- model: तिमी प्रति माया बढ्दोचा

### tl_0050 · draft cer 0.3704
- roman: `Ankha Haru Sankaunche Jhimkaudai`
- gold:  आँखाहरू सन्काउछे झिम्काउँदै
- draft: आँखा हरु शंकाउन्चे झिमकाउदै
- model: आँखा हरु सन्काउँछे झिम्काउदै

### tl_0105 · draft cer 0.3529
- roman: `gham kati ghamailo`
- gold:  घाम लाग्यो घमाइलो
- draft: घाम कति घमाइलो
- model: घाम कति घमाइलो

### tl_0037 · draft cer 0.3333
- roman: `Jati j cha mero timi hau`
- gold:  जति—जे छ मेरो तिमी हौ
- draft: जाती ज छ मेरो तिमी hau
- model: जति जे छ मेरो तिमी हौ

### tl_0135 · draft cer 0.3333
- roman: `Yadama Na Aau`
- gold:  यादमा नआऊ
- draft: यादमा ना आउ
- model: यादमा ना आउ

### tl_0010 · draft cer 0.3143
- roman: `Praya samjhanchu ma timilai`
- gold:  प्रायः सम्झन्छु म तिमीलाई (तिमीलाई)
- draft: प्राय सम्झन्छु म तिमीलाई
- model: प्रया सम्झन्छु मा तिमीलाई

### tl_0134 · draft cer 0.3125
- roman: `Bhawanama Na Aau Timi`
- gold:  भावनामा नआऊ तिमी
- draft: भवानामा ना आउ तिमी
- model: भावनामा ना आउ तिमी

### tl_0158 · draft cer 0.3125
- roman: `Sabha bhanda aglo Sagarmatha Angrejima Mount Everest ko rupma chininchha`
- gold:  सब भन्दा अग्लो सगरमाथा अंग्रेजीमा माउन्ट एभरेष्टको रूपमा चिनिन्छ
- draft: सभा भन्दा अग्लो सगरमाथा अन्ग्रेजिमा Mount Everest को रुपमा चिनिन्छ
- model: सभा भन्दा अग्लो सगरमाथा अंग्रेजीमा माउन्ट इभरेस्ट को रूपमा चिनिन्छ

### tl_0049 · draft cer 0.3077
- roman: `U Jaba Bolaunche Jiskaudai`
- gold:  ऊ जब बोलाउँछे जिस्क्याउँदै
- draft: उ जबा बोलाउन्चे जिस्काउदै
- model: उ जब बोलाउँछे जिस्काउदै

### tl_0143 · draft cer 0.3043
- roman: `Maan Kholi Dekhaune Gara`
- gold:  मन खोली मलाई देखाउने गर
- draft: मान खोल्दि देखाउने गर
- model: मान खोली देखाउने गर

### tl_0112 · draft cer 0.2857
- roman: `pirati ko talai ma`
- gold:  पिरतीको तालैमा
- draft: पिरती को तलाइ मा
- model: पिरती को तलाई मा

### tl_0133 · draft cer 0.2857
- roman: `Baru Aai Sataune Gara`
- gold:  बरु आई मलाई सताउने गर
- draft: बारु आई सताउने गर
- model: बरु आइ सताउने गर

### tl_0136 · draft cer 0.2727
- roman: `Tanneriko Sapana Jastai Swadama Na Aau`
- gold:  तन्नेरीको सपनाजस्तै विस्वादमा नआऊ
- draft: तान्येरिको सपना जस्तै स्वादमा ना आउ
- model: तन्नेरीको सपना जस्तै स्वादमा ना आउ

### tl_0159 · draft cer 0.2703
- roman: `Urvara ra ardra dakshin kshetra sahari chha`
- gold:  उर्वर र आर्द्र दक्षिणी क्षेत्र शहरी छ
- draft: उर्बरा रा आर्द्रा दखिन क्षेत्र सहरी छ
- model: उर्वरा र अर्द्र दक्षिण क्षेत्र सहरी छ

### tl_0054 · draft cer 0.2667
- roman: `Sanjha Pakha Chautari Ma`
- gold:  साँझपख चौतारीमा
- draft: साँझ पाखा चौतारी मा
- model: साँझ पाखा चौतारी मा

### tl_0140 · draft cer 0.2667
- roman: `Maanle Je Je Bhanchha`
- gold:  मनले के के भन्छ
- draft: मान्ले जे जे भन्छ
- model: मानले जे जे भन्छ

### tl_0132 · draft cer 0.2581
- roman: `Timro Tadako Mahi Pugena Malai`
- gold:  तिम्रो टाढाको म्वाइँ पुगेन मलाई
- draft: तिम्रो तादको माहि पुगेना मलाई
- model: तिम्रो तडको महि पुगेन मलाई

### tl_0011 · draft cer 0.25
- roman: `Kasari basyo kunni maya khoi`
- gold:  कसरी बस्यो कुन्नि माया, खै, आ—हा
- draft: कसरी बस्यो कुन्नि माया खोई
- model: कसरी बस्यो कुन्नी माया खोइ

### tl_0125 · draft cer 0.24
- roman: `sun chadi le timlai varula`
- gold:  सुनचाँदीले तिमीलाई भरौंला
- draft: सुन चादी ले तिम्लाई भरुला
- model: सुन छाडी ले तिम्लाई भरुला

### tl_0117 · draft cer 0.2308
- roman: `Sindur lauchau ki nai bhana na`
- gold:  सिन्दुर लाउँछौं कि नाई भनन
- draft: सिन्दुर लाउँछौ कि नै भना ना
- model: सिन्दुर लाउछौ कि नै भन ना

### tl_0145 · draft cer 0.2258
- roman: `China uttarpatti awasthit chha ra paschim purva ra dakshin Bharatle dhakeko chha`
- gold:  चीन उतरपट्टि अवस्थित छ र पश्चिम पुर्व र दक्षिण भारतले ढाकेको छ
- draft: चिन उत्तरपत्ति अवस्थीत छ रा पस्चिम पुर्व रा दखिन भारत्ले ढाकेको छ
- model: चिना उत्तरपट्टि अवस्थित छ र पश्चिम पूर्व र दक्षिण भारतले ढाकेको छ

### tl_0046 · draft cer 0.2222
- roman: `Kahile Kahin Bazar Ma`
- gold:  कहिले काहीँ बजारमा
- draft: कहिलै कहिँ बजार मा
- model: कहिले कहिँ बजार मा

### tl_0071 · draft cer 0.2222
- roman: `chota ajhai balji dincha`
- gold:  चोट अझै बल्झिदिन्छ
- draft: चोटा अझै बल्जी दिन्छ
- model: चोट अझै बल्जी दिन्छ

### tl_0073 · draft cer 0.2222
- roman: `timi kahile narunu`
- gold:  तिमी कहिल्यै नरुनू
- draft: तिमी कहिले नरुनु
- model: तिमी कहिले नरुनु

### tl_0052 · draft cer 0.2174
- roman: `Jali Rumal Chadera Janera`
- gold:  जाली रुमाल छाडेर जानेले
- draft: जाली रुमाल चढेर जानेर
- model: जाली रुमाल छाडेर जानेर

### tl_0146 · draft cer 0.2174
- roman: `Yo uttari golarddhama chha`
- gold:  यो उत्तरी गोलार्द्धमा छ
- draft: यो उत्तरि गोलर्धधामा छ
- model: यो उत्तरी गोलार्द्धमा छ

### tl_0157 · draft cer 0.2115
- roman: `Himali uttarma vishwaka chaudha uchchatam pahadharumaddhye aath chhan`
- gold:  हिमाली उत्तरमा विश्वका १४ उच्चतम पहाडहरूमध्ये आठ छन्
- draft: हिमालि उत्तरमा विश्वका चौध उच्चतम् पहाधरुमद्ध्ये आठ छन
- model: हिमाली उत्तरमा विश्वका चौध उच्चतम पहाडहरूमध्ये आठ छन्

### tl_0059 · draft cer 0.2083
- roman: `Tarki Tarki Hidera Jane Le`
- gold:  तर्कीतर्की हिँडेर जानेले
- draft: तर्कि तर्कि हिडेर जाने ले
- model: तर्की तर्की हिडेर जाने ले

### tl_0048 · draft cer 0.2
- roman: `Luki Luki Herche Malai`
- gold:  लुकीलुकी हेर्छे मलाई
- draft: लुकि लुकि हेर्चे मलाई
- model: लुकी लुकी हेर्चे मलाई

### tl_0107 · draft cer 0.2
- roman: `Timi ra ma ghumna jaau na`
- gold:  तिमी र म घुम्न जाउँन
- draft: तिमी रा मा घुम्न जाउ ना
- model: तिमी र मा घुम्न जाऊ न

### tl_0151 · draft cer 0.1964
- roman: `Yasma Koshi Gandaki ra Karnali jasta lamo ra chaunda nadiharu chhan`
- gold:  यसमा कोशी गण्डकी र कर्णाली जस्ता लामो र चौंडा नदीहरू छन्
- draft: यस्मा कोशी गन्डकी रा कर्नालि जस्ता लामो रा चौन्दा नदिहरू छन
- model: यसमा कोशी गण्डकी र कर्णाली जस्ता लामो र चौंडा नदीहरू छन्

### tl_0060 · draft cer 0.1923
- roman: `Farki Farki Hasera Herne Le`
- gold:  फर्कीफर्की हाँसेर हेर्नेले
- draft: फर्कि फर्कि हासेर हेर्ने ले
- model: फर्की फर्की हासेर हेर्ने ले

### tl_0138 · draft cer 0.1923
- roman: `Kada Dekhi Darai Nabhagne Gara`
- gold:  काँडा देखि डराई नभाग्ने गर
- draft: कडा देखी डराइ नभग्ने गर
- model: काडा देखि दराई नभाग्ने गर

### tl_0128 · draft cer 0.1905
- roman: `maya garchau ki nai vana na`
- gold:  माया गर्छौ कि नाई भनन
- draft: माया गर्छौ कि नै भन ना
- model: माया गर्छौ कि नै भन ना

### tl_0129 · draft cer 0.1905
- roman: `Timi ra ma ghumna jau na`
- gold:  तिमी र म घुम्न जाउँ न
- draft: तिमी रा मा घुम्न जाउ ना
- model: तिमी र मा घुम्न जाउ न

### tl_0018 · draft cer 0.1842
- roman: `Jindagi narahos rahi rahanecha yesma kaid pal haru`
- gold:  जिन्दगी नरहोस् रहिरहनेछ यसमा कैद पलहरू
- draft: जिन्दगी नरहोस रही रहनेछ येस्मा कैद पल हरु
- model: जिन्दगी नरहोस् रहि रहनेछ येसमा कैद पल हरु

### tl_0058 · draft cer 0.1818
- roman: `Timilai Nalai Bhachaina`
- gold:  तिमीलाई न ल्याई भा छैन
- draft: तिमीलाई नलाई भाछैन
- model: तिमीलाई नलाई भाछैन

### tl_0114 · draft cer 0.1818
- roman: `huncha ki nai hunna vana na`
- gold:  हुन्छ कि नाइ हुन्न भनन
- draft: हुन्छ कि नै हुन्न भन ना
- model: हुन्छ कि नै हुन्न भन ना

### tl_0149 · draft cer 0.1798
- roman: `Hamro deshma jadoma dherai chiso ra sukhha hunchha ra garmima andhibehari barsha ra badhipahiro hunachhan`
- gold:  हाम्रो देशमा जाडोमा धेरै चिसो र सुख्खा हुन्छ र गर्मीमा आँधीबेहरी बर्षा र बाढिपहिरो हुनछन्
- draft: हाम्रो देशमा जडोमा धेरै चिसो रा सुक्खा हुन्छ रा गर्मिमा अन्धिबेहारी बर्षा रा बधिपाहिरो हुनाछन
- model: हाम्रो देशमा जाडोमा धेरै चिसो र सुख्ह हुन्छ रा गर्मीमा अन्धिबेहरी बर्ष र बढीपहिरो हुनछन्

### tl_0078 · draft cer 0.1739
- roman: `Feri kina malai berthaima`
- gold:  फेरि किन मलाई ब्यर्थैमा
- draft: फेरि किन मलाई बार्थाइमा
- model: फेरी किन मलाई बेर्थैमा

### tl_0055 · draft cer 0.1667
- roman: `Budha Pakha Bhet Huda`
- gold:  बुढापाका भेट हुँदा
- draft: बुढा पाखा भेट हुदा
- model: बुढा पाखा भेट हुदा

### tl_0091 · draft cer 0.1667
- roman: `tyati pani bujdainau`
- gold:  त्यति पनि बुझ्दैनौ
- draft: त्यति पनि बुझ्दिनाउ
- model: त्यति पनि बुज्दैनौ

### tl_0141 · draft cer 0.1667
- roman: `Sancho Kura Bhana Malai`
- gold:  साँचो कुरा भन मलाई
- draft: सान्चो कुरा भना मलाई
- model: सान्चो कुरा भन मलाई

### tl_0131 · draft cer 0.16
- roman: `Kahile Kahi Maya Pani Dekhaune Gara`
- gold:  कहिले माया पनि देखाउने गर
- draft: कहिले कही माया पनि देखाउने गर
- model: कहिले कहि माया पनि देखाउने गर

### tl_0142 · draft cer 0.16
- roman: `Nalukai Maanka Sara Bimbaharu`
- gold:  नलुकाई मनका सारा विम्बहरू
- draft: नलुकाइ मान्का सारा बिम्बहरू
- model: नलुकै मानका सारा बिम्बहरू

### tl_0035 · draft cer 0.1579
- roman: `Bhanne le bhanos garos`
- gold:  भन्नेले भनोस् गरोस्
- draft: भन्ने ले भनोस गरोस
- model: भन्ने ले भनोस् गरोस्

### tl_0137 · draft cer 0.1538
- roman: `Pritiko Phool Tipnu Parchha Bhane`
- gold:  प्रीतिको फूल टिप्नपर्छ भने
- draft: प्रितिको फूल टिपनु पर्छ भने
- model: प्रीतिको फूल टिप्नु पर्छ भने

### tl_0070 · draft cer 0.15
- roman: `bipanale jhaskai dida`
- gold:  विपनाले झस्काइ दिँदा
- draft: बिपनाने झस्काइ दिदा
- model: बिपनाले झस्कै दिदा

### tl_0072 · draft cer 0.15
- roman: `kalpi kalpi roye bhane`
- gold:  कल्पी कल्पी रोएँ भने
- draft: कल्पि कल्पि रोए भने
- model: कल्पी कल्पी रोये भने

### tl_0152 · draft cer 0.1458
- roman: `Hamisanga Rupa Beganas ra Rara jasta thula talharu chhan`
- gold:  हामीसँग रुपा बेगनास र रारा जस्ता ठूला तालहरू छन्
- draft: हामिसंग रुप बेगनास रा रारा जस्ता थुला तालहरू छन
- model: हामीसँग रुपा बेगनास र रारा जस्ता ठूला तालहरू छन्

### tl_0148 · draft cer 0.1429
- roman: `Himalaya parbatiya ra tarai`
- gold:  हिमालय पर्वतीय र तराई
- draft: हिमालय पर्बतीय रा तराइ
- model: हिमालय पर्बतीय र तराई

### tl_0004 · draft cer 0.1389
- roman: `Achanak badliyo manau tyo mero hoina`
- gold:  अचानक बद्लियो, मानौँ, त्यो मेरो होइन
- draft: अचानक बद्लियो मनाऊ त्यो मेरो होइन
- model: अचानक बदलियो मनाउ त्यो मेरो होइन

### tl_0031 · draft cer 0.1364
- roman: `Dekhne le dekhos sunos`
- gold:  देख्नेले देखोस् सुनोस्
- draft: देख्ने ले देखोस सुनोस
- model: देख्ने ले देखोस् सुनोस्

### tl_0156 · draft cer 0.1356
- roman: `Nepal atyadhik vividh ra dhani bhugol sanskriti ra dharmharuko desh ho`
- gold:  नेपाल अत्यधिक विविध र धनी भूगोल संस्कृति र धर्महरूको देश हो
- draft: नेपाल अत्यधिक विविध रा धानी भुगोल सन्सकृति रा धर्महरूकि देश हो
- model: नेपाल अत्यधिक विविध र धनी भूगोल संस्कृति र धर्महरूको देश हो

### tl_0062 · draft cer 0.1333
- roman: `kehi chota lagda`
- gold:  केही चोट लाग्दा
- draft: केहि चोटा लाग्दा
- model: केही चोट लाग्दा

### tl_0101 · draft cer 0.1304
- roman: `Ekchin pachi suna yasko aawaj`
- gold:  एकछिन पछि सुन यसको आवाज
- draft: एकछिन पछि सुना यास्को आवाज
- model: एकछिन पछि सुना यसको आवाज

### tl_0013 · draft cer 0.129
- roman: `Bhabishyako mitho kalpana bhulisakyou`
- gold:  भविष्यको मीठो कल्पना बुनिसक्यौँ
- draft: भविष्यको मिठो कल्पना भुलिसक्यौ
- model: भबिष्यको मीठो कल्पना भुलिसक्यौ

### tl_0015 · draft cer 0.125
- roman: `Maile sumpi diye sabai timrai naamma`
- gold:  मैले सुम्पिदिएँ सबै तिम्रै नाममा
- draft: मैले सुम्पी दिए सबै तिम्रै नाम्मा
- model: मैले सुम्पी दिए सबै तिम्रै नाम्म

### tl_0030 · draft cer 0.125
- roman: `Nachutos hamro darilo sath`
- gold:  नछुटोस् हाम्रो दरिलो साथ
- draft: नाछुटोस हाम्रो दरीलो साथ
- model: नछुटोस् हाम्रो दरिलो साथ

### tl_0042 · draft cer 0.125
- roman: `Maski Maski Hidera Jane Le`
- gold:  मस्कीमस्की हिँडेर जानेले
- draft: मस्की मस्की हिडेर जाने ले
- model: मस्की मस्की हिडेर जाने ले

### tl_0066 · draft cer 0.125
- roman: `testai huna sakcha`
- gold:  त्यस्तै हुन सक्छ
- draft: तेस्तै हुन सक्छ
- model: तेस्तै हुना सक्छ

### tl_0068 · draft cer 0.125
- roman: `sapana le saath dida`
- gold:  सपनाले साथ दिँदा
- draft: सपना ले साथ दिदा
- model: सपना ले साथ दिदा

### tl_0110 · draft cer 0.125
- roman: `Timi pirati ko chata odau na`
- gold:  तिमी पिरतीको छाता ओढाउ न
- draft: तिमी पिरती को छाता ओडाउ ना
- model: तिमी पिरती को छाता ओडाउ न

### tl_0113 · draft cer 0.125
- roman: `machi marau jalaima`
- gold:  माछी मारौ जालैमा
- draft: माची मारौ जलैमा
- model: माची मराउ जलाइमा

### tl_0119 · draft cer 0.125
- roman: `bhai maya namare ni kaile ho`
- gold:  भै माया नमारे नि कैले हो
- draft: भै माया नमारे नि काहिले हो
- model: भाइ माया नमरे नि कहिले हो

### tl_0123 · draft cer 0.125
- roman: `pakhuri ma daam cha ni`
- gold:  पाखुरीमा दम छ नि
- draft: पाखुरी मा दाम छ नि
- model: पाखुरी मा दाम छ नि

### tl_0203 · draft cer 0.1235
- roman: `Nepalko jangalma harro barro amala tejpat aiselu chutro panchaule jasta jadibuti painchha`
- gold:  नेपालको जंगलमा हर्रो बर्रो अमला तेजपात ऐसेलु चुत्रो पाँचऔंले जस्ता जडिबुटी पाइन्छ
- draft: नेपालको जङ्गलमा हर्रो बरो अमला तेजपत्ता ऐँसेलु चुत्रो पाँचऔँले जस्ता जडीबुटी पाइन्छ
- model: नेपालको जंगलमा हर्रो बर्रो अमला तेजपात आइसेलु चुत्रो पाँचौले जस्ता जडीबुटी पाइन्छ

### tl_0115 · draft cer 0.12
- roman: `Ani jaal ma eklai parchau ki`
- gold:  अनि जालमा एक्लै पार्छौ कि
- draft: अनि जाल मा एक्लै पर्छौ की
- model: अनि जाल मा एकलै पर्छौ कि

### tl_0088 · draft cer 0.1176
- roman: `tyatinai jhan marchau`
- gold:  त्यति नै झन मर्छौ
- draft: त्यतिनै झन मार्छौ
- model: त्यतिनै झन मर्चौ

### tl_0162 · draft cer 0.1167
- roman: `Hamro lokapriya khanaharu dal bhat dindo gunrdruk ityadi hun`
- gold:  हाम्रो लोकप्रिय खानाहरू दाल भाट डिन्डो गुनर्दुक इत्यादि हुन्
- draft: हाम्रो लोकप्रिय खानाहरू दाल भात ढिँडो गुन्द्रुक इत्यादि हुन्
- model: हाम्रो लोकप्रिय खानाहरू दाल भात दिन्दो गुणर्द्रुक इत्यादि हुन्

### tl_0021 · draft cer 0.1154
- roman: `Euta maya garne byakti lai`
- gold:  एउटा माया गर्ने व्यक्तिलाई
- draft: एउटा माया गर्ने ब्याक्ति लाई
- model: एउटा माया गर्ने ब्यक्ति लाई

### tl_0023 · draft cer 0.1154
- roman: `Timi nai hau malai maya garne`
- gold:  तिमी नै हौ मलाई माया गर्ने
- draft: तिमी नै hau मलाई माया गर्ने
- model: तिमी नै हौ मलाई माया गर्ने

### tl_0153 · draft cer 0.1136
- roman: `Hamisanga hariyo upatyaka sundar pani jharna aadi chha`
- gold:  हामीसँग हरियो उपत्यका सुन्दर पानी झरना आदि छ
- draft: हामिसंग हरियो उपत्यका सुन्दर पनि झर्ना आदि छ
- model: हामीसँग हरियो उपत्यका सुन्दर पनि झर्ना आदि छ

### tl_0006 · draft cer 0.1111
- roman: `Maile bhuli diye yo sara jamana`
- gold:  मैले भुलिदिएँ यो सारा जमाना
- draft: मैले भुली दिए यो सारा जमाना
- model: मैले भुली दिए यो सारा जमाना

## New candidate lines for gold v2

### new_001 · Dashain Ayo — Udit Narayan, Deepa Narayan Jha
- roman: `Jamara ra rato tikai ma`
- model: जमरा र रातो टिकाइ मा
- draft: जमरा र रातो टीकाै मा

### new_002 · Ashma (A Confession) Official Lyrics- Neetesh J Kunwar — Blog
- roman: `Mero waiyat kura-kani suni`
- model: मेरो वैयत कुरा-कानी सुनी
- draft: मेरो वाइयात कुरा-कानी सुनी

### new_003 · Shishir Jhai — Adrian Pradhan
- roman: `bipana le ankha malai bharie diyo`
- model: बिपना ले आँखा मलाई भरिए दियो
- draft: बिपना ले आँखा मलाई भरिए दियो

### new_004 · Pardeshi Hunai Man Chhaina — Khem Century & Shanti Shree Pariyar
- roman: `Pardeshi Hunu Pardaina Timi Runu`
- model: परदेशी हुनु पर्दैन तिमी रुनु
- draft: पार्देशी हुनु पर्दैन तिमी रुनु

### new_005 · Mutu Dekhin — John Chamling Rai
- roman: `Hune ho ki hoina`
- model: हुने हो कि होइन
- draft: हुने हो कि होइन

### new_006 · Maya Sarhai Mahango — Hemant Sharma
- roman: `Sunne lai ta khyala, khyala`
- model: सुन्ने लाइ ता ख्याला, ख्याला
- draft: सुन्ने लाइ ता ख्याल, ख्याल

### new_007 · Bhana K Garu — COD
- roman: `Tenson Linu Chha Ra Kasko`
- model: टेन्सन लिनु छ रा कस्को
- draft: टेन्सन लिनु छ रा कास्को

### new_008 · Bipul Chettri- Gahiro Gahiro Official — Bipul Chettri
- roman: `Hidechu hidechu`
- model: हिडेछु हिडेछु
- draft: हिडेचु हिडेचु

### new_009 · YODDA - Khatra Barz — YODDA
- roman: `Jo Malai Ghrina Garna Samaye Khanaucha`
- model: जो मलाई घृणा गर्न समये खनाउछ
- draft: जो मलाई घृणा गर्न समय खानौचा

### new_010 · Bhanchu Ma — Sugam Pokhrel
- roman: `Chokho Maya Laayera`
- model: चोखो माया लाएर
- draft: चोखो माया लाएर

### new_011 · Nepal Haseko — Balen | Laaj Sharanam OST
- roman: `Nepali Ko Maan Haseko Herna Chahanchu`
- model: नेपाली को मान हासेको हेर्न चाहन्छु
- draft: नेपाली को मान हासेको हेर्न चाहन्छु

### new_012 · Bal Garera — Sworup Raj Acharya
- roman: `Bato Sabai Sajilo Ta`
- model: बाटो सबै सजिलो ता
- draft: बाटो सबै सजिलो ता

### new_013 · Biram — Purna Rai & Dajubhaiharu
- roman: `Kehi Barsha Haina Maya`
- model: केही बर्ष हैन माया
- draft: केही वर्ष हाइन माया

### new_014 · Nyasro — Almoda Rana Uprety
- roman: `Yeklai hunda yad aaunchha jhan`
- model: येकलाई हुन्दा याद आउँछ झन्
- draft: ऐक्लाई हुन्दा याद आउँछ झन

### new_015 · Changa Chet — Almoda Rana Uprety
- roman: `Chhutai Basaula`
- model: छुटाइ बसौला
- draft: छुट्टै बसौला

### new_016 · Joon Ta Lagyo Tarale — Bharati Ghimire
- roman: `Mitho mitho dhoon ma koili ko boli ma`
- model: मिठो मीठो धुन मा कोइली को बोली मा
- draft: मीठो मीठो धून मा कोइली को बोली मा

### new_017 · Siri Ma Siri Ni Kancha — Gyanu Rana
- roman: `(Suna Mero Nirmaya`
- model: (सुना मेरो निर्मया
- draft: (सुना मेरो निर्मया

### new_018 · Ma Ta Marchhu Kyare — Jagdish Samal
- roman: `Timro manko kunama`
- model: तिम्रो मनको कुनामा
- draft: तिम्रो मनको कुनामा

### new_019 · Chulesima — Sanjeev Singh
- roman: `Kina rakheu chokho mutu`
- model: किन राखेउ चोखो मुटु
- draft: किन राखेउ चोखो मुटु

### new_020 · Praye Sadhai Ma — The Axe
- roman: `Har juni ko saath lai`
- model: हर जुनी को साथ लाई
- draft: हर जुनी को साथ लाई

### new_021 · Chaina — Albatross
- roman: `Hijo ko aasha`
- model: हिजो को आशा
- draft: हिजो को आशा

### new_022 · Makhamali — Sujan Chapagain, Sunita Thegim
- roman: `Sai sai sai`
- model: साइ साइ साइ
- draft: साइ साइ साइ

### new_023 · Chhutyo Pirima — Eleena Chauhan Breakup Party Song
- roman: `Terae Kaaran Bandhan Ma Thiye Ma`
- model: तेरै कारण बन्धन मा थिये मा
- draft: तेरै कारण बन्धन मा थिए मा

### new_024 · Vhijyo Kapal — Urgen Dong & Samikshya Adhikari
- roman: `Ho Sannani Ko Vhijyo Kapaala`
- model: हो सन्नानी को भिज्यो कपाला
- draft: हो सन्नानी को भिज्यो कपाल

### new_025 · Aba Man Sangai Man — Sugam Pokharel, Anju Panta
- roman: `Timi matra hau manma basne`
- model: तिमी मात्र हौ मनमा बस्ने
- draft: तिमी मात्र हाउ मनमा बस्ने

### new_026 · Paribhasa — Purna Rai
- roman: `Mutu Nai Timro Kasto`
- model: मुटु नै तिम्रो कस्तो
- draft: मुटु नै तिम्रो कस्तो

### new_027 · Aayena Chinako Rail — Hari Giri 'Bimarsi', Banina Kirati
- roman: `Herda herdai timro muhar pasina po kahlkhal`
- model: हेर्दा हेर्दै तिम्रो मुहार पसिना पो कहलखाल
- draft: हेर्दा हेर्दै तिम्रो मुहार पसिना पो कलकल

### new_028 · Chodi Gaye Paap Lagla — Ram Krishna Dhakal
- roman: `Waari paari suskera`
- model: वारी पारी सुस्केर
- draft: वारी पारी सुस्केरा

### new_029 · Mero Hajura — Swoopna Suman | Abhigya Ghimire
- roman: `Timi Mai Bhuleko`
- model: तिमी मै भुलेको
- draft: तिमी मै भुलेको

### new_030 · Jyan Dina Raji — Kiran bhujel & Eleena Chauhan
- roman: `Ho dhan dekhai yo chhoriko maya painna`
- model: हो धन देखाइ यो छोरीको माया पाइन्न
- draft: हो धन देखाइ यो छोरीको माया पाइन्न

### new_031 · Chudaina Timro Mayale — 1974 AD
- roman: `Jhan jhan mutu ma aago dankincha`
- model: झन् झन मुटु म आगो डंकिन्छ
- draft: झन झन मुटु मा आगो दन्किन्छ

### new_032 · Hridaya Bhitra — Deepak Gurung
- roman: `Hmm. hmm`
- model: एचएमएम. एचएमएम
- draft: हम्. हम्म

### new_033 · Chaak — Purna Rai & Dajubhaiharu
- roman: `Hope Ta Aaudaina kohi`
- model: Hope ता आउदैन कोहि
- draft: Hope Ta Aaudaina kohi

### new_034 · Aash — Naren Limbu
- roman: `Maya gardaichhau ki`
- model: माया गर्दैछौ कि
- draft: माया गर्दैछौ कि

### new_035 · Rukum Maikot — Khusma Movie Song
- roman: `Maan Ko Kura Aaja Nai Kholideu`
- model: मान को कुरा आज नै खोलिदेउ
- draft: मान को कुरा आज नै खोलिदेउ

### new_036 · Mata door dekhi ayen — Deep Shrestha
- roman: `Sambodhan garda gardai gai gayou chodera - 2`
- model: सम्बोधन गर्दा गर्दै गाइ गायौ छोडेर - 2
- draft: सम्बोधन गर्दा गर्दै गई गायौ छोडेर - 2

### new_037 · Raat Vari ft. C.O.D — GXSOUL
- roman: `You Got Me Feeling like`
- model: You गोट Me Feeling like
- draft: You Got Me Feeling like

### new_038 · Sirima Siri Ni Kancha — Narayan Gopal
- roman: `(Suna mero nirmaya`
- model: (सुना मेरो निर्मया
- draft: (सुना मेरो निर्मaya

### new_039 · Bipul Chettri- Gahiro Gahiro Official — Bipul Chettri
- roman: `Birano birano`
- model: बिरानो बिरानो
- draft: बिरानो बिरानो

### new_040 · Timi Sanga Mero Nata — Benup Chhetri
- roman: `Timi Sanga Mero Saino`
- model: तिमी सँग मेरो साइनो
- draft: तिमी सँग मेरो साइनो

### new_041 · Ek Dui Teen - Oasis Thapa — Oasis Thapa
- roman: `Paach patak samjhauda maya`
- model: पाच पटक सम्झाउदा माया
- draft: पाच पटक सम्झाउदा माया

### new_042 · Gyan Bahadur Choro — Bidhan Shrestha
- roman: `naalaa paani pugchha`
- model: नाला पानी पुग्छ
- draft: नाआला पानी पुग्छ

### new_043 · Karnali Ka Chhaila — Nepathya
- roman: `Jiu Kati Jyunarai Laya`
- model: जिउ कति ज्युनारै लय
- draft: जिय कटि ज्युनरै लय

### new_044 · Suna Kina — Naren Limbu
- roman: `Mero vawana gahiriyera her ana`
- model: मेरो भवाना गहिरिएर her अना
- draft: मेरो भवना गहिरIYera हेर अना

### new_045 · Tadpinchu Samjhera — The Buds
- roman: `Timi Pheri Aau Na`
- model: तिमी फेरी आउ ना
- draft: तिमी फेरि आउ ना

### new_046 · Chaina Maile Timro — Karma Band
- roman: `Feri K Kurale Timro Maan Dukyo`
- model: फेरी क कुराले तिम्रो मान डुक्यो
- draft: फेरि क कुराले तिम्रो मान दुख्यो

### new_047 · Chattai Basyo Ni Maya lyrics / Rajan raj shiwakoti — Anju panta
- roman: `RAJENDRA SHRESTHA`
- model: राजेन्द्र श्रेष्ठ
- draft: RAJENDRA SHRESTHA

### new_048 · Chiso Chiso Hawa Ma — Robin Tamang
- roman: `Jhal jhal yaad aaunchha`
- model: झल झल याद आउँछ
- draft: झल झल याद आउँछ

### new_049 · Jane Bhaye Jau — Sudip Giri
- roman: `Maile Saas Fernai Nasake Pani`
- model: मैले सास फेर्नै नसके पनि
- draft: मैले सास फेर्नै नसके पनि

### new_050 · 5:55 Haasa — Chirag Khadka
- roman: `Mare Pachi Feri K Kee`
- model: मरे पछि फेरी क की
- draft: मरे पाची फेरि क की

### new_051 · Maya Pirim — Nishan Bhattarai, Manisha Pokhrel
- roman: `Chokho maya launa paye khamla dhindo aato`
- model: चोखो माया लाउन पाए खाम्ला ढिँडो आटो
- draft: चोखो माया लाउन पाए खाम्ला ढिँडो आँटो

### new_052 · Bihan Saberai — Axix Band
- roman: `yeuti bahini le`
- model: यौती बहिनी ले
- draft: येउटी बहिनी ले

### new_053 · Manko Rani — Sugam Pokhrel
- roman: `Timro mriga nayan`
- model: तिम्रो मृग नयन
- draft: तिम्रो मृग नयन

### new_054 · Tiharai Ayo — Lochan Bhattarai
- roman: `Bhailini... Bhailini`
- model: भैलिनी... भैलिनी
- draft: भैलिनि... भैलिनि

### new_055 · Kasle Choryo Yo Man — Udit Narayan
- roman: `Jhajhalko Yo Manma Aauchha`
- model: झझलको यो मनमा आउँछ
- draft: झझाल्को यो मनमा आउँछ

### new_056 · Maya Junalai  lyrics / Bekcha & Trishala Gurung — Trishala gurung
- roman: `Jun heri parkhi basa timi malai`
- model: जुन हेरी पर्खी बास तिमी मलाई
- draft: जुन हेरी पर्खी बास तिमी मलाई

### new_057 · Aaja Kina — Nepsydez
- roman: `kata gayou timi`
- model: कतै गायौ तिमी
- draft: कता गायौ तिमी

### new_058 · Bardali — Sushant Kc & Indrakala Rai
- roman: `Cha Swari Ma Kurdai Chu`
- model: छ स्वरी मा कुर्दै छु
- draft: छ स्वारि मा कुर्दै छु

### new_059 · O Suna Maya — Edge Band
- roman: `Timimai Haraauna Khojchhu Ma`
- model: तिमीमै हराउन खोज्छु मा
- draft: तिमिмай हराउन खोज्छु म

### new_060 · Ankha ma timro  by Ashtoast — Ash Toast
- roman: `timro muskan bata ghayel chu ma`
- model: तिम्रो मुस्कान बाट घायेल छु मा
- draft: तिम्रो मुस्कान बाट घायेल छु म

### new_061 · Malai Basurile Ruwayo — Anju Panta
- roman: `Autai Bana Beglai Maan Nacheko Chha Majura`
- model: आउटै बना बेगलाई मान नाचेको छ मजुरा
- draft: औटाइ बन बेग्लाई मान नाचेको छ मजुरा

### new_062 · Kasari — Yabesh Thapa
- roman: `Yeti bujhi dinu`
- model: येती बुझी दिनु
- draft: येती बुझी दिनु

### new_063 · A Hora Maya — Himal Sagar, Anu Chaudhary
- roman: `Ho barsha le vanchha timlai rujhauchhu`
- model: हो बर्ष ले भन्छ तिम्लाई रुझाउछु
- draft: हो बर्षा ले भन्छ तिमलाइ रुझाउँछु

### new_064 · Sathi Ho — Laure
- roman: `Raksi khutta paltara, jutta talkara`
- model: रक्सी खुट्टा पल्टरा, जुत्ता तलकारा
- draft: रक्सी खुट्टा पलतारा, जुट्टा तल्कारा

### new_065 · Mero Prem — Axix Band
- roman: `Malai yehi ramna chodideu`
- model: मलाई येही रम्न छोडिदेउ
- draft: मलाई येहि रमना छोडिदेउ

### new_066 · Ma Ta Marchu Kyare — Jagdish Samal
- roman: `Timro man ko kuna ma`
- model: तिम्रो मन को कुना मा
- draft: तिम्रो मन को कुना म

### new_067 · Bipul chettri- Aashish Official — Bipul Chettri
- roman: `Indreni rang ko cha`
- model: इन्द्रेणी रङ्ग को छ
- draft: इन्द्रेणी रंग को छ

### new_068 · Ek Dui Teen - Oasis Thapa — Oasis Thapa
- roman: `Lukau chhau kina bhanideu`
- model: लुकाउ छौ किन भनिदेउ
- draft: लुकाउ छौ किन भनिदेउ

### new_069 · Jyan Dina Raji — Kiran bhujel & Eleena Chauhan
- roman: `Mayako kura ke jiu jyan timrai ho`
- model: मायाको कुरा के ज्यू ज्यान तिम्रै हो
- draft: मायाको कुरा के जिय ज्यान तिम्रै हो

### new_070 · Pahad Jhuknu Parcha — Ram Thapa
- roman: `Ho Ho Ho`
- model: हो हो हो
- draft: हो हो हो

### new_071 · Suseli Le Basantalai — Udit Narayan
- roman: `Mausam Nai Ho Yesto`
- model: मौसम नै हो यस्तो
- draft: मौसम नै हो यस्तो

### new_072 · Shake Your Body — Nepsydez
- roman: `You know I like it I love it one more time just do it`
- model: You know I like it I love it one more time just do it
- draft: You know I like it I love it one more time just do it

### new_073 · Baby I Love You — Deepak Limbu
- roman: `Timro lagi kasam tayar chhu ma jeje garna ni`
- model: तिम्रो लागि कसम तयार छु म जेजे गर्न नि
- draft: तिम्रो लागि कसम तयार छु म जेजे गर्न नी

### new_074 · Block Hill — Nima Rumba
- roman: `Dil mero chori lagyo usko ruupa le he..`
- model: दिल मेरो छोरी लाग्यो उसको रुपा ले हे..
- draft: दिल मेरो चोरी लाग्यो उसको रूप ले हे..

### new_075 · Hawa Jastai -Lyrics and Chords - John Chamling Rai — Nepali Pop Songs
- roman: `Bujhauna khoje, bhani diye`
- model: बुझाउन खोजे, भनी दिए
- draft: बुझाउन खोजे, भनि दिए

### new_076 · Hami Dherai Sana Chau — Girish N Pranil
- roman: `Kati Basnu Gharma`
- model: कति बस्नु घरमा
- draft: कति बस्नु घरमा

### new_077 · Footpath Mero Ghar Lyrics Yama Buddha — Yama Buddha
- roman: `Sadhai mero sath chan`
- model: सधै मेरो साथ छान
- draft: सधै मेरो साथ छन

### new_078 · Jaba Koi Timro Thiyena — Karna Das
- roman: `Ke birsi diyeu godhuli sajha ko kasam`
- model: के बिर्सी दियेउ गोधूलि साझ को कसम
- draft: के बिर्सी दिएउ गोधुली साझा को कसम

### new_079 · Gauthali — गौंथली - / Samikshya Adhikari
- roman: `Madal:- Poshan Gharti Magar`
- model: मादल:- पोषण घर्ती मगर
- draft: Madal:- पोषण घर्ती मगर

### new_080 · thau kane 2.0 — ujan shakya
- roman: `Thau kane gana gana chhanta malachwona chhanta shyula chhan`
- model: थाउ काने गाना गाना छन्त मालाच्वोना छन्त श्युला छन्
- draft: ठाउ काने गाना गाना छान्ता मलाच्वोना छान्ता श्युला छन

### new_081 · Putali — Ashish Aviral |Eleena Chauhan
- roman: `uMAAAA Mero Laure`
- model: उमाआ मेरो लाउरे
- draft: uMAAAA मेरो लाहुरे

### new_082 · jiwan — the elements & ishan raj onta
- roman: `Nabirsa timi hausala`
- model: नबिर्स तिमी हौसला
- draft: नबिर्स तिमी हौसला

### new_083 · Sanibar Ko Din — Udit Narayan
- roman: `Sanibarko Din Bihani Pakha`
- model: सनिबारको दिन बिहानी पाखा
- draft: शनिबारको दिन बिहानि पाखा

### new_084 · Timi Ruda — Dhiraj Rai
- roman: `Pida le polne chati bhari`
- model: पिडा ले पोल्ने छाती भारि
- draft: पीडा ले पोल्ने छाती भरि

### new_085 · Cinema — ST MAN FT. SOMEA
- roman: `Mero High Vayo Meter 140`
- model: मेरो High भयो मिटर 140
- draft: मेरो High Vayo Meter 140

### new_086 · Mutu Dekhin — John Chamling Rai
- roman: `Maya garchu vanne mayalu`
- model: माया गर्छु भन्ने मायालु
- draft: माया गर्छु भन्ने मायालु

### new_087 · Herana Runcha Mana — Deepesh Kishor Bhattarai
- roman: `Din bityo raatai bityo nindra chaina ankhama`
- model: दिन बित्यो रातै बित्यो निन्द्रा छैन आँखामा
- draft: दिन बित्यो रातै बित्यो निन्द्रा छैन आँखामा

### new_088 · Ma Mauntama — Rocken Music, Om Bikram Bista
- roman: `Maya maya bhanda bhandai jindagi nai mero bitne ho ki`
- model: माया माया भन्दा भन्दै जिन्दगी नै मेरो बित्ने हो कि
- draft: माया माया भन्दा भन्दै जिन्दगी नै मेरो बित्ने हो की

### new_089 · Aparichit Bhaawanaa - Oasis Thapa — Oasis Thapa
- roman: `Lukeka bhaawanaa bujhi deau`
- model: लुकेका भावना बुझी देऔ
- draft: लुकेका भावना बुझी देउ

### new_090 · Timro Mero Sambandhako — Karna Das
- roman: `Paraye bhayi dine le`
- model: पराये भयी दिने ले
- draft: पराई भयी दिने ले

### new_091 · Fulako Thunga Hau Ki — Udit Narayan, Deepa Narayan Jha
- roman: `Na hasnu timi chandrama pani`
- model: ना हास्नु तिमी चन्द्रमा पनि
- draft: ना हस्नु तिमी चन्द्रमा पनि

### new_092 · Bhetyo Dharan Chhutyo Dhankuta lyrics / Prabisha adhikari — Sujan babu gurung
- roman: `Bina Cewa`
- model: बिना सीईवीए
- draft: बिना चेवा

### new_093 · Note Note — Hari Bansha Acharya, Sashi Rawal
- roman: `Kai Gayeni Bhetiyena`
- model: कै गयेनी भेटिएन
- draft: कै गएनी भेटियेन

### new_094 · Ali Alikati pida hudani — Nabin K Bhattarai
- roman: `Khai Ke Bhayo Malai Aajabholi`
- model: खै के भयो मलाई आजभोली
- draft: खै के भयो मलाई आजभोलि

### new_095 · PARAANA OFFICIAL LYRICS- A MERO HAJUR 3 — Anmol KC, Suhana Thapa
- roman: `Tana pani timrai nau manai timrai nau`
- model: ताना पनि तिम्रै नौ मनै तिम्रै नौ
- draft: तना पनि तिम्रै नाउ मनै तिम्रै नाउ

### new_096 · Lovi Najar — Hukke X Urgen Dong, Deepika Bayambu Ft Sanjana Gurung & Sarmila Tamang
- roman: `Pani Daudhae Aepugyou`
- model: पनि दौडाए आएपुग्यौ
- draft: पानी दौधाए एपugyou

### new_097 · Samaya — Almoda Rana Uprety
- roman: `Timi nai surubat, timi nai antya`
- model: तिमी नै सुरुबात, तिमी नै अन्त्य
- draft: तिमी नै सुरुवात, तिमी नै अन्त्य

### new_098 · Himalako Kakhama — Mira Rana
- roman: `Yo desh`
- model: यो देश
- draft: यो देश

### new_099 · Timro Aakha Ko Sagar Ma — Prakash Shrestha
- roman: `harek saajh ekdin`
- model: हरेक साझ एकदिन
- draft: हरेक साँझ एकदिन

### new_100 · Jindagi Ko K Bharosa — Karna Das
- roman: `Arkai Ko Nimti`
- model: अर्कै को निम्ति
- draft: अर्कै को निम्ति

### new_101 · Akashma Eklo Tara — Aruna Lama
- roman: `Kahila kahi timila pani`
- model: कहिला कही तिमिला पनि
- draft: कहिला कहि तिमीला पनि

### new_102 · Malai Vote Deu — Girish N Pranil
- roman: `Mero party ko X X X, mero chhunab chin-na X X X`
- model: मेरो party को एक्स एक्स एक्स, मेरो छुनब छिन-ना एक्स एक्स एक्स
- draft: मेरो party को X X X, मेरो छुनाब चिन-ना X X X

### new_103 · Rogai Pirati — Sunil Giri
- roman: `Thorai thorai jiune gareko chu`
- model: थोरै थोरै जिउने गरेको छु
- draft: थोरै थोरै जिउने गरेको छु

### new_104 · Namuna — Mingma Sherpa
- roman: `Mero maya timro maya`
- model: मेरो माया तिम्रो माया
- draft: मेरो माया तिम्रो माया

### new_105 · Jack Straw (Live At Philadelphia Civic Center, Philadelphia, PA, August 4-5, 1974) — Grateful Dead
- roman: `Cut his buddy down`
- model: कट हिस बडी down
- draft: Cut his buddy down

### new_106 · Katha — Vten, Dharmendra Sewan
- roman: `Chhaina ahile tagat yo mero bidho hatma`
- model: छैन अहिले तागत यो मेरो बिधो हातमा
- draft: छैन अहिले तागत यो मेरो बिढो हातमा

### new_107 · Akkha Cha — Sandip Bista Mr. D
- roman: `Technology Kada Napade Ni IT`
- model: टेक्नोलोजी काडा नपादे नि IT
- draft: Technology Kada Napade Ni IT

### new_108 · Okharbote Kaka — Prakash Ojha
- roman: `bhanchhan school napathaa`
- model: भन्छन् school नपठा
- draft: भन्छन् school नपाठा

### new_109 · Tirkha Lage Nirmaya — Udit Narayan, Deepa Narayan Jha
- roman: `Ho deuraaliko barpipalma`
- model: हो देउरालीको बरपिपलमा
- draft: हो देउरालिको बार्पिपालमा

### new_110 · Timi Yesai Lajayeu — Robin Sharma
- roman: `kohi chare jhai`
- model: कोही चरे झै
- draft: कोहि चारे झै

### new_111 · Kina Udas Baseki — Cool Pokhrel
- roman: `Banauna Ta Ke Sakthera`
- model: बनाउन ता के सक्थेर
- draft: बनाуна ता के सक्थेरा

### new_112 · Ekanta — Karma Band
- roman: `Birsidinu hai`
- model: बिर्सिदिनु है
- draft: बिर्सीदिनु है

### new_113 · Bhana K Garu — COD
- roman: `Baby Gal U Know It True`
- model: Baby गल उ Know It True
- draft: Baby Gal U Know It True

### new_114 · Sadhana — John Chamling Rai
- roman: `Timlai samjhi timlai samjhi`
- model: तिमलाई सम्झी तिम्लाई सम्झी
- draft: तिम्लाई सम्झी तिम्लाई सम्झी

### new_115 · Makhamali — Sujan Chapagain, Sunita Thegim
- roman: `Najarai ko karauti le retyo mutu rattakai`
- model: नजराई को करौटी ले रेट्यो मुटु रत्तकै
- draft: नजरै को करौती ले रट्यो मुटु रत्तकै

### new_116 · Chadai Aau — Sudip Gurung
- roman: `Aba chadai aau`
- model: अब छदै आउ
- draft: अब छडाइ आउ

### new_117 · Kaha Hideki — Kandara
- roman: `Sochnu Kina`
- model: सोच्नु किन
- draft: सोच्नु किन

### new_118 · Badal Sari — SWAR & JOHN RAI
- roman: `Aadhinae Aayeni Timrae Lagi....`
- model: आधिनै आयेनी तिम्रै लागि....
- draft: आधिनाए आएनी तिम्रै लागि....

### new_119 · Pari Gaau Ki Nakkali Kanchhi — Rabin Shrestha
- roman: `Sarai Nai Ramri Mori`
- model: सराइ नै राम्री मोरी
- draft: सरै नै राम्री मोरी

### new_120 · Ekata राष्ट्रिय गीत — Swar
- roman: `Ghama banera hera`
- model: घाम बनेर हेर
- draft: घाम बनेर हेर
