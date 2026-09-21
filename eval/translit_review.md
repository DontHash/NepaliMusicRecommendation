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
- draft: (pending)

### tl_0113 · cer 0.4375 · short
- roman: `machi marau jalaima`
- gold:  माछी मारौ जालैमा
- model: माची मराउ जलाइमा
- draft: माछी मराउ जालैमा

### tl_0009 · cer 0.4062 · medium
- roman: `Timi prati maya badhdocha`
- gold:  तिमीप्रति माया बढ्दो छ (बढ्दो छ)
- model: तिमी प्रति माया बढ्दोचा
- draft: तिमी प्रति माया बढ्दोछ

### tl_0080 · cer 0.375 · short
- roman: `Hey maanis`
- gold:  हे मानिस
- model: Hey मानिस
- draft: (pending)

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
- draft: (pending)

### tl_0127 · cer 0.2941 · short
- roman: `sampati lai aayindaina`
- gold:  सम्पत्तिलाई आइदैन
- model: सम्पत्ति लाइ आयिँदैन
- draft: सम्पति लाइ आयइन्दैन

### tl_0132 · cer 0.2903 · medium
- roman: `Timro Tadako Mahi Pugena Malai`
- gold:  तिम्रो टाढाको म्वाइँ पुगेन मलाई
- model: तिम्रो तडको महि पुगेन मलाई
- draft: तिम्रो तादको माही पुगेन मलाई

### tl_0112 · cer 0.2857 · medium
- roman: `pirati ko talai ma`
- gold:  पिरतीको तालैमा
- model: पिरती को तलाई मा
- draft: पिरती को तलाइ मा

### tl_0133 · cer 0.2857 · medium
- roman: `Baru Aai Sataune Gara`
- gold:  बरु आई मलाई सताउने गर
- model: बरु आइ सताउने गर
- draft: बरु आइ सताउने गर

### tl_0011 · cer 0.2812 · medium
- roman: `Kasari basyo kunni maya khoi`
- gold:  कसरी बस्यो कुन्नि माया, खै, आ—हा
- model: कसरी बस्यो कुन्नी माया खोइ
- draft: कसरी बस्यो कुन्नि माया खोई

### tl_0028 · cer 0.2727 · medium
- roman: `Na na na na`
- gold:  ना—ना ना—ना
- model: ना ना ना न
- draft: (pending)

### tl_0054 · cer 0.2667 · medium
- roman: `Sanjha Pakha Chautari Ma`
- gold:  साँझपख चौतारीमा
- model: साँझ पाखा चौतारी मा
- draft: साँझ पाखा चौतारी मा

### tl_0143 · cer 0.2609 · medium
- roman: `Maan Kholi Dekhaune Gara`
- gold:  मन खोली मलाई देखाउने गर
- model: मान खोली देखाउने गर
- draft: मान खोली देखाउने गर

### tl_0117 · cer 0.2308 · medium
- roman: `Sindur lauchau ki nai bhana na`
- gold:  सिन्दुर लाउँछौं कि नाई भनन
- model: सिन्दुर लाउछौ कि नै भन ना
- draft: सिन्दुर लाउछौ कि नै भन न

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
- draft: भै माया नमरे नी काइले हो

### tl_0070 · cer 0.2 · short
- roman: `bipanale jhaskai dida`
- gold:  विपनाले झस्काइ दिँदा
- model: बिपनाले झस्कै दिदा
- draft: बिपनाले झस्काइ दिदा

### tl_0140 · cer 0.2 · medium
- roman: `Maanle Je Je Bhanchha`
- gold:  मनले के के भन्छ
- model: मानले जे जे भन्छ
- draft: मान्ले जे जे भन्छ

### tl_0002 · cer 0.1923 · medium
- roman: `Mero haat samai kahi door jana`
- gold:  मेरो हात समाई कहीँ दूर जान
- model: मेरो हात समाइ कही डुर जाना
- draft: मेरो हात समाई कही दूर जान

### tl_0053 · cer 0.1905 · medium
- roman: `Jhuto Maya Layera Jane Le`
- gold:  झूटो माया लाएर जानेले
- model: झुटो माया लायेर जाने ले
- draft: झुटो माया लायर जाने ले

### tl_0128 · cer 0.1905 · medium
- roman: `maya garchau ki nai vana na`
- gold:  माया गर्छौ कि नाई भनन
- model: माया गर्छौ कि नै भन ना
- draft: माया गर्छौ कि नाइ वन ना

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
- draft: हाँ हाँ हाँ हाँ

### tl_0114 · cer 0.1818 · medium
- roman: `huncha ki nai hunna vana na`
- gold:  हुन्छ कि नाइ हुन्न भनन
- model: हुन्छ कि नै हुन्न भन ना
- draft: हुन्छ कि नाइ हुन्न भन न

### tl_0136 · cer 0.1818 · medium
- roman: `Tanneriko Sapana Jastai Swadama Na Aau`
- gold:  तन्नेरीको सपनाजस्तै विस्वादमा नआऊ
- model: तन्नेरीको सपना जस्तै स्वादमा ना आउ
- draft: तान्नेरिको सपना जस्तै स्वादमा ना आउ

### tl_0057 · cer 0.1739 · medium
- roman: `Dharo Dharma Yo Kura Sancho Cha`
- gold:  धरोधर्म यो कुरा साँचो छ
- model: धारो धर्म यो कुरा सान्चो छ
- draft: धारो धर्म यो कुरा साचो छ

### tl_0004 · cer 0.1667 · medium
- roman: `Achanak badliyo manau tyo mero hoina`
- gold:  अचानक बद्लियो, मानौँ, त्यो मेरो होइन
- model: अचानक बदलियो मनाउ त्यो मेरो होइन
- draft: अचानक बदलीयो मनाऊ त्यो मेरो होइन

### tl_0046 · cer 0.1667 · medium
- roman: `Kahile Kahin Bazar Ma`
- gold:  कहिले काहीँ बजारमा
- model: कहिले कहिँ बजार मा
- draft: कहिले कहिन बजार मा

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
- draft: नलुकै मान्का सारा बिम्बहरु

### tl_0122 · cer 0.1579 · medium
- roman: `Ma pani k ma kaam chu ni`
- gold:  म पनि केमा कम छु नि
- model: मा पनि क मा काम छु नि
- draft: म पनि के मा काम छु नि

### tl_0015 · cer 0.1562 · medium
- roman: `Maile sumpi diye sabai timrai naamma`
- gold:  मैले सुम्पिदिएँ सबै तिम्रै नाममा
- model: मैले सुम्पी दिए सबै तिम्रै नाम्म
- draft: मैले सुम्पी दिएँ सबै तिम्रै नाम्मा

### tl_0049 · cer 0.1538 · medium
- roman: `U Jaba Bolaunche Jiskaudai`
- gold:  ऊ जब बोलाउँछे जिस्क्याउँदै
- model: उ जब बोलाउँछे जिस्काउदै
- draft: उ जबा बोलाउन्चे जिस्काउदै

### tl_0107 · cer 0.15 · medium
- roman: `Timi ra ma ghumna jaau na`
- gold:  तिमी र म घुम्न जाउँन
- model: तिमी र मा घुम्न जाऊ न
- draft: तिमी र म घुम्न जाऊ न

### tl_0044 · cer 0.1481 · medium
- roman: `Pagal Banaki Che Ghayal Banaki Che`
- gold:  पागल बनाकी छे घायल बनाकी छे
- model: पागल बनकी चे घायल बनकी चे
- draft: पागल बनाकी छे घाइयल बनाकी छे

### tl_0050 · cer 0.1481 · medium
- roman: `Ankha Haru Sankaunche Jhimkaudai`
- gold:  आँखाहरू सन्काउछे झिम्काउँदै
- model: आँखा हरु सन्काउँछे झिम्काउदै
- draft: आँखा हरु सङ्काउन्चे झिमकाउदै

### tl_0003 · cer 0.1429 · medium
- roman: `Beglai bho mero yo duniya hijo bhanda`
- gold:  बेग्लै भो मेरो यो दुनियाँ हिजोभन्दा
- model: बेगलाई भो मेरो यो दुनिया हिजो भन्दा
- draft: बेग््लै भो मेरो यो दुनियाँ हिजो भन्दा

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
- draft: फेरि किन मलाई बेरर्थाइमा

### tl_0013 · cer 0.129 · medium
- roman: `Bhabishyako mitho kalpana bhulisakyou`
- gold:  भविष्यको मीठो कल्पना बुनिसक्यौँ
- model: भबिष्यको मीठो कल्पना भुलिसक्यौ
- draft: भविष्यको मीठो कल्पना भुुलिसक्यौँ

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
- draft: मलाई पागल बनाकी छे घाइयल बनाकी छे

### tl_0059 · cer 0.125 · medium
- roman: `Tarki Tarki Hidera Jane Le`
- gold:  तर्कीतर्की हिँडेर जानेले
- model: तर्की तर्की हिडेर जाने ले
- draft: तर्की तर्की हिडेर जाने ले

### tl_0068 · cer 0.125 · medium
- roman: `sapana le saath dida`
- gold:  सपनाले साथ दिँदा
- model: सपना ले साथ दिदा
- draft: सपना ले साथ दिदा

### tl_0092 · cer 0.125 · medium
- roman: `Timro maan ho ki dhunga ho`
- gold:  तिम्रो मन हो कि ढुंगा हो
- model: तिम्रो मान हो कि ढुङ्गा हो
- draft: तिम्रो मान हो कि ढुङ्गा हो

### tl_0123 · cer 0.125 · medium
- roman: `pakhuri ma daam cha ni`
- gold:  पाखुरीमा दम छ नि
- model: पाखुरी मा दाम छ नि
- draft: पाखुरी मा दाम छ नि

### tl_0115 · cer 0.12 · medium
- roman: `Ani jaal ma eklai parchau ki`
- gold:  अनि जालमा एक्लै पार्छौ कि
- model: अनि जाल मा एकलै पर्छौ कि
- draft: अनि जाल मा एकलै पर्छौ की

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
- draft: फर्की फर्की हासेर हेर्ने ले

### tl_0149 · cer 0.1124 · long
- roman: `Hamro deshma jadoma dherai chiso ra sukhha hunchha ra garmima andhibehari barsha ra badhipahiro hunachhan`
- gold:  हाम्रो देशमा जाडोमा धेरै चिसो र सुख्खा हुन्छ र गर्मीमा आँधीबेहरी बर्षा र बाढिपहिरो हुनछन्
- model: हाम्रो देशमा जाडोमा धेरै चिसो र सुख्ह हुन्छ रा गर्मीमा अन्धिबेहरी बर्ष र बढीपहिरो हुनछन्
- draft: हाम्रो देशमा जाडोमा धेरै चिसो र सुख्खा हुन्छ र गर्मीमा आन्धिबेहारी बर्ष र बाढीपहिरो हुनाछन्

### tl_0006 · cer 0.1111 · medium
- roman: `Maile bhuli diye yo sara jamana`
- gold:  मैले भुलिदिएँ यो सारा जमाना
- model: मैले भुली दिए यो सारा जमाना
- draft: मैले भुली दिएँ यो सारा जमाना

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
- draft: साञ्चो कुरा भन मलाई

### tl_0155 · cer 0.1111 · medium
- roman: `Lumbini Gorkha Janakpur Kathmandu prakhyat udaharanaharu hun`
- gold:  लुम्बिनी गोरखा जनकपुर काठमाडौं प्रख्यात उदाहरणहरू हुन्
- model: लुम्बिनी गोर्खा जनकपुर काठमाण्डु प्रख्यात उदाहरणाहरू हुन्
- draft: लुम्बिनी गोर्खा जनकपुर काठमाडौं प्रख्यात उदाहरणहरु हुन्

### tl_0160 · cer 0.1111 · medium
- roman: `Yaha dherai jati ra dharmaka manis baschan`
- gold:  यहाँ धेरै जाति र धर्मका मानिस बस्छन्
- model: यहा धेरै जति र धर्मका मानिस बस्चन
- draft: यहाँ धेरै जाति र धर्मका मानिस बस्छन्

### tl_0017 · cer 0.1081 · long
- roman: `Bhalai choto hola yaha sabai drishya atauna lai`
- gold:  भलै छोटो होला यहाँ सबै दृष्य अटाउनलाई
- model: भलाई छोटो होला यहाँ सबै दृश्य अटाउन लाई
- draft: भलै छोटो होला यहाँ सबै दृश्य अटाउन लाई

### tl_0159 · cer 0.1081 · medium
- roman: `Urvara ra ardra dakshin kshetra sahari chha`
- gold:  उर्वर र आर्द्र दक्षिणी क्षेत्र शहरी छ
- model: उर्वरा र अर्द्र दक्षिण क्षेत्र सहरी छ
- draft: उर्बरा र आर्द्रा दक्षिण क्षेत्र सहरी छ

### tl_0016 · cer 0.1053 · long
- roman: `Upahar swaroop yo tasbeer maya garne haru lai`
- gold:  उपहारस्वरूप यो तस्बीर माया गर्नेहरूलाई
- model: उपहार स्वरूप यो तस्बीर माया गर्ने हरु लाई
- draft: उपहार स्वरूप यो तस्बिर माया गर्ने हरु लाई

### tl_0018 · cer 0.1053 · long
- roman: `Jindagi narahos rahi rahanecha yesma kaid pal haru`
- gold:  जिन्दगी नरहोस् रहिरहनेछ यसमा कैद पलहरू
- model: जिन्दगी नरहोस् रहि रहनेछ येसमा कैद पल हरु
- draft: जिन्दगी नरहोस रही रहनेछ यसमा कैद पल हरु

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
- draft: हेर मलाई समाउ यो हात

### tl_0048 · cer 0.1 · medium
- roman: `Luki Luki Herche Malai`
- gold:  लुकीलुकी हेर्छे मलाई
- model: लुकी लुकी हेर्चे मलाई
- draft: लुकी लुकी हेर्चे मलाई

### tl_0072 · cer 0.1 · medium
- roman: `kalpi kalpi roye bhane`
- gold:  कल्पी कल्पी रोएँ भने
- model: कल्पी कल्पी रोये भने
- draft: कल्पी कल्पी रोए भने

### tl_0111 · cer 0.1 · medium
- roman: `Khola jastai bagau hami`
- gold:  खोला जस्तै बगौं हामी
- model: खोला जस्तै बगाउ हामी
- draft: खोला जस्तै बगाउ हामी

### tl_0162 · cer 0.1 · long
- roman: `Hamro lokapriya khanaharu dal bhat dindo gunrdruk ityadi hun`
- gold:  हाम्रो लोकप्रिय खानाहरू दाल भाट डिन्डो गुनर्दुक इत्यादि हुन्
- model: हाम्रो लोकप्रिय खानाहरू दाल भात दिन्दो गुणर्द्रुक इत्यादि हुन्
- draft: हाम्रो लोकप्रिय खानाहरू दाल भात दिँडो गुन्द्रुक इत्यादि हुन्

### tl_0056 · cer 0.0952 · medium
- roman: `Buhari Ko Gharma Khacho Cha`
- gold:  बुहारीको घरमा खाँचो छ
- model: बुहारी को घरमा खाचो छ
- draft: बुहारी को घरमा खाचो छ

### tl_0129 · cer 0.0952 · medium
- roman: `Timi ra ma ghumna jau na`
- gold:  तिमी र म घुम्न जाउँ न
- model: तिमी र मा घुम्न जाउ न
- draft: तिमी रा म घुम्न जाउ ना

### tl_0034 · cer 0.0909 · medium
- roman: `Khusi chau hami chau jaha`
- gold:  खुसी छौँ हामी छौँ जहाँ
- model: खुसी छौ हामी छौ जहाँ
- draft: खुसी छौ हामी छौ जहाँ

### tl_0097 · cer 0.0909 · short
- roman: `Hawahuri sanga`
- gold:  हावाहुरीसँग
- model: हावाहुरी सँग
- draft: हावाहुरीसँग

### tl_0191 · cer 0.0909 · long
- roman: `Yasko sathai Annapurna Kanchanjangha Lotse Manaslu Yalungkad Makalu Machapuchhre aadi himalaharu pani Nepalma chhan`
- gold:  यसका साथै अन्नपूर्ण कञ्चनजङ्घा लोत्से मनासलु यालुङकाड मकालु माछापुच्छे आदि हिमालहरू पनि नेपालमा छन्
- model: यसको साथै अन्नपूर्ण कञ्चनजंघा लोत्से मनस्लु यालुङकड मकालु माछापुछ्रे आदि हिमालाहरू पनि नेपालमा छन्
- draft: यास्को साथै अन्नपूर्ण कञ्चनजङ्घा ल्होत्से मनास्लु यालुङकड मकालु माछापुच्छ्रे आदि हिमालहरू पनि नेपालमा छन्

### tl_0043 · cer 0.087 · medium
- roman: `Musu Musu Hasera Herne Le`
- gold:  मुसुमुसु हासेर हेर्नेले
- model: मुसु मुसु हासेर हेर्ने ले
- draft: मुसु मुसु हासेर हेर्ने ले

### tl_0052 · cer 0.087 · medium
- roman: `Jali Rumal Chadera Janera`
- gold:  जाली रुमाल छाडेर जानेले
- model: जाली रुमाल छाडेर जानेर
- draft: जाली रुमाल चडेर जानेर

### tl_0102 · cer 0.087 · medium
- roman: `Timlai sadhai daaki rahancha`
- gold:  तिमीलाई सधैं डाकी रहन्छ
- model: तिमलाई सधैँ डाकी रहन्छ
- draft: तिमलाई सधैँ डाकी रहन्छ

### tl_0033 · cer 0.0833 · medium
- roman: `Paschatap chaina kunai yaha`
- gold:  पश्चात्ताप छैन कुनै यहाँ
- model: पश्चाताप छैन कुनै यहाँ
- draft: पश्चाताप छैन कुनै यहाँ

### tl_0110 · cer 0.0833 · medium
- roman: `Timi pirati ko chata odau na`
- gold:  तिमी पिरतीको छाता ओढाउ न
- model: तिमी पिरती को छाता ओडाउ न
- draft: तिमी पिरती को छाता ओडाउ न

### tl_0200 · cer 0.0833 · medium
- roman: `Yaha bibhinna prajatika rukhaharu painchha`
- gold:  यहां विभिन्न प्रजातिका रूखहरू पाइन्छ
- model: यहा बिभिन्न प्रजातिका रुखहरू पाइन्छ
- draft: यहाँ विभिन्न प्रजातिको रुखहरू पाइन्छ

### tl_0192 · cer 0.0826 · long
- roman: `Hamro deshko himalma phalam sun chandi abhrakh chunadhunga sisa gandhak marble soda sidhenaun birenaun khari aadika khani chhan`
- gold:  हाम्रो देशको हिमालमा फलाम सुन चाँदी अभ्रख चुनढुङ्गा सिसा गन्धक मार्बल सोडा सिधेनुन विरेनुन खरी आदिका खानी छन्
- model: हाम्रो देशको हिमालमा फलाम सुन चण्डी अभ्रख चुनाढुङ्गा सिसा गन्धक मार्बल सोडा सिधेनौं बिरेनौं खरी आदिका खानी छन्
- draft: हाम्रो देशको हिमालमा फलाम सुन चाँदी अभ्रख चुनढुङ्गा सिसा गन्धक मार्बल सोडा सिधेनुन बिरेनुन खारी आदि का खानी छन

### tl_0145 · cer 0.0806 · long
- roman: `China uttarpatti awasthit chha ra paschim purva ra dakshin Bharatle dhakeko chha`
- gold:  चीन उतरपट्टि अवस्थित छ र पश्चिम पुर्व र दक्षिण भारतले ढाकेको छ
- model: चिना उत्तरपट्टि अवस्थित छ र पश्चिम पूर्व र दक्षिण भारतले ढाकेको छ
- draft: चिन उत्तरपत्ति अवस्थित छ र पछिम पुर्व र दक्षिण भारतले ढाकेको छ

### tl_0161 · cer 0.08 · medium
- roman: `Lagbhag saya bhashaharu bolinchhan`
- gold:  लगभग सय भाषाहरु बोलिन्छन्
- model: लगभाग सय भाषाहरू बोलिन्छन्
- draft: लगभग सय भाषाहरू बोलिन्छन्

### tl_0164 · cer 0.08 · long
- roman: `Nepal sano chha tara prakritik srotsadhanma dhani chha tara arthik awasthale garda garib chha`
- gold:  नेपाल सानो छ तर प्राकृतिक स्रोतसाधनमा धनी छ तर आर्थिक अवस्थाले गर्दा गरीब छ
- model: नेपाल सानो छ तारा प्राकृतिक स्रोत्साधनमा धनी छ तारा आर्थिक अवस्थाले गर्दा गरिब छ
- draft: नेपाल सानो छ तारा प्राकृतिक स्रोतसाधनमा धनी छ तर आर्थिक अवस्थाले गर्दा गरिब छ

### tl_0158 · cer 0.0781 · long
- roman: `Sabha bhanda aglo Sagarmatha Angrejima Mount Everest ko rupma chininchha`
- gold:  सब भन्दा अग्लो सगरमाथा अंग्रेजीमा माउन्ट एभरेष्टको रूपमा चिनिन्छ
- model: सभा भन्दा अग्लो सगरमाथा अंग्रेजीमा माउन्ट इभरेस्ट को रूपमा चिनिन्छ
- draft: सभ भन्दा अग्लो सगरमाथा अङ्ग्रेजीमा Mount Everest को रुपमा चिनिन्छ

### tl_0021 · cer 0.0769 · medium
- roman: `Euta maya garne byakti lai`
- gold:  एउटा माया गर्ने व्यक्तिलाई
- model: एउटा माया गर्ने ब्यक्ति लाई
- draft: एउटा माया गर्ने ब्याक्ती लाई

### tl_0089 · cer 0.0769 · short
- roman: `Kahile huri sanga`
- gold:  कहिले हुरीसँग
- model: कहिले हुरी सँग
- draft: कहिले हुरीसँग

### tl_0137 · cer 0.0769 · medium
- roman: `Pritiko Phool Tipnu Parchha Bhane`
- gold:  प्रीतिको फूल टिप्नपर्छ भने
- model: प्रीतिको फूल टिप्नु पर्छ भने
- draft: प्रितिको फूल टिपनु पर्छ भने

### tl_0138 · cer 0.0769 · medium
- roman: `Kada Dekhi Darai Nabhagne Gara`
- gold:  काँडा देखि डराई नभाग्ने गर
- model: काडा देखि दराई नभाग्ने गर
- draft: काद देखि दराइ नभग्ने गर

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
- draft: कहिले पहिरोसँग

### tl_0099 · cer 0.0714 · short
- roman: `suna mero dhadkan`
- gold:  सुन मेरो धड्कन
- model: सुना मेरो धड्कन
- draft: सुना मेरो ढड्कन

### tl_0193 · cer 0.07 · long
- roman: `Yaha yarchagumba jasta prakritik jadibuti chhan bhane yak yeti chauri gai kasturi jasta jantu pani raheka chhan`
- gold:  यहाँ यार्चागुम्बा जस्ता प्राकृतिक जडिबुटी छन् भने याक यति चौरी गाई कस्तुरी जस्ता जन्तु पनि रहेका छन्
- model: यहा यार्चागुम्बा जस्ता प्राकृतिक जडीबुटी छन भने याक येती चौरी गाइ कस्तुरी जस्ता जन्तु पनि रहेका छन
- draft: यहाँ यार्सागुम्बा जस्ता प्राकृतिक जडीबुटी छन् भने याक यती चौँरी गाई कस्तुरी जस्ता जन्तु पनि रहेका छन्

### tl_0183 · cer 0.0698 · long
- roman: `Pani vishwakai pranilai banchanka lagi nabhai nahune dainik upabhogma parne prakritik sampada ho`
- gold:  पानी विश्वकै प्राणीलाई बाँच्नका लागि नभई नहुने दैनिक उपभोगमा पर्ने प्राकृतिक सम्पदा हो
- model: पनि विश्वकै प्राणीलाई बञ्चनका लागि नभै नहुने दैनिक उपभोगमा पर्ने प्राकृतिक सम्पदा हो
- draft: पानी विश्वकै प्राणि लाई बाँच्नका लागि नभई नहुने दैनिक उपभोगमा पर्ने प्राकृतिक सम्पदा हो

### tl_0086 · cer 0.069 · medium
- roman: `Ma hu prakriti malai bachna deu`
- gold:  म हुँ प्रकृति मलाई बाँच्न देउ
- model: मा हु प्रकृति मलाई बाँच्न देउ
- draft: म हुँ प्रकृति मलाई बाँच्न देउ

### tl_0202 · cer 0.0688 · long
- roman: `Tara paisaka lagi marihatte garera aafno sukhsubidhaka lagi aafno santanko bhabisyasangai kheldai lobhi ra papiharu le Nepalko charkose jhadi ra bibhinna pahadma bhaeka jangal phadani gari basti basalna suru gareka chhan`
- gold:  तर पैसाका लागि मरिहत्ते गरेर आफ्नो सुखसुविधाका लागि आफ्‌नो सन्तानको भविष्यसंगै खेल्दै लोभी र पापीहरूले नेपालको चारकोसे झाडी र विभिन्न पहाडमा भएका जङ्गल फडानी गरी वस्ती बसाल्न सुरु गरेका छन्
- model: तारा पैसाका लागि मरिहत्ते गरेर आफ्नो सुखसुबिधाका लागि आफ्नो सन्तानको भबिष्यसँगै खेल्दै लोभी र पापीहरू ले नेपालको चर्कोसे झाडी र बिभिन्न पहाडमा भएका जंगल फडानी गरी बस्ती बसाल्न सुरु गरेका छन्
- draft: तारा पैसाका लागि मरीहत्ते गरेर आफ्नो सुखसुविधाका लागि आफ्नो सन्तानको भविष्यसँगै खेल्दै लोभी रा पापीहरू ले नेपालको चारकोसे झाडी रा विभिन्न पहाडमा भएका जङ्गल फडानी गरी बस्ती बसाल्न सुरु गरेका छन्

### tl_0153 · cer 0.0682 · long
- roman: `Hamisanga hariyo upatyaka sundar pani jharna aadi chha`
- gold:  हामीसँग हरियो उपत्यका सुन्दर पानी झरना आदि छ
- model: हामीसँग हरियो उपत्यका सुन्दर पनि झर्ना आदि छ
- draft: हामिसँग हरियो उपत्यका सुन्दर पानी झर्ना आदि छ

### tl_0184 · cer 0.0682 · long
- roman: `Yasko prayog pyas metna sharir ra lugaka mayal milkauna sinchai garna ra bijuli utpadanma bhaeko chha`
- gold:  यसको प्रयोग प्यास मेट्न शरीर र लुगाका मयल मिल्काउन सिंचाइ गर्न र विजुली उत्पादनमा भएको छ
- model: यसको प्रयोग प्यास मेट्न शरीर र लुगाका मायल मिल्काउन सिन्छै गर्न र बिजुली उत्पादनमा भएको छ
- draft: यास्को प्रयोग प्यास मेट्न शरीर र लुगाका मयल मिल्काउन सिँचाइ गर्न र बिजुली उत्पादनमा भएको छ

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
- draft: नेपालको जङ्गलमा हर्रो बर्रो अमला तेजपात ऐँसेलु चुत्रो पाँचऔँले जस्ता जडीबुटी पाइन्छ

### tl_0197 · cer 0.0615 · long
- roman: `Nepalko Pokharama Phewatal Beganastal raheka chhan bhane Surkheta Bulbule tal Chitwanma Nandbhauju Kasara Gadwal Tamorhaila jasta talharu raheka chhan`
- gold:  नेपालको पोखरामा फेवाताल वेगनासताल रहेका छन् भने सुर्खेतमा बुलबुले ताल चितवनमा नन्दभाउजू कसरा गडवाल तमोरघैला जस्ता तालहरू रहेका छन्
- model: नेपालको पोखरामा फेवाताल बेगनास्तल रहेका छन भने सुर्खेता बुलबुले ताल चितवनमा नन्दभाउजु कसरा गडवाल तमोरहैला जस्ता तालहरू रहेका छन
- draft: नेपालको पोखरामा फेवाताल बेगनासताल रहेका छन् भने सुर्खेतमा बुलबुले ताल चितवनमा नन्दभाउजु कसरा गडवाल तमोरहैला जस्ता तालहरू रहेका छन्

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
- draft: हिमाली उत्तरमा बिश्वका चौध उच्चतम् पहाढुमद्द्ये आठ छन

### tl_0195 · cer 0.0577 · long
- roman: `Taltalaiya ra jharnharu pani Nepalka prakritik sampada hun`
- gold:  तालतलैया र झरनाहरू पनि नेपालका प्राकृतिक सम्पदा हुन्
- model: तालतालैया र झर्नहरू पनि नेपालका प्राकृतिक सम्पदा हुन्
- draft: टाल्टल्याया र झरनाहरू पनि नेपालका प्राकृतिक सम्पदा हुन्

### tl_0204 · cer 0.0571 · medium
- roman: `Yi jadibuti aushadhi banauna prayog garinchha`
- gold:  यी जडिबुटी औषधी बनाउन प्रयोग गरिन्छ
- model: यी जडीबुटी औषधि बनाउन प्रयोग गरिन्छ
- draft: यी जडीबुटी औषधि बनाउन प्रयोग गरिन्छ

### tl_0091 · cer 0.0556 · short
- roman: `tyati pani bujdainau`
- gold:  त्यति पनि बुझ्दैनौ
- model: त्यति पनि बुज्दैनौ
- draft: (pending)

### tl_0185 · cer 0.0538 · long
- roman: `Nepalma paniko strot Asia mahadeshma nai pahilo ra vishwama Brazil pachadiko dosro sthanma raheko chha`
- gold:  नेपालमा पानीको स्रोत एसिया महादेशमा नै पहिलो र विश्वमा ब्राजिल पछाडिको दोस्रो स्थानमा रहेको छ
- model: नेपालमा पानीको स्ट्रोट एसिया महादेशमा नै पहिलो र विश्वमा ब्राजिल पचाडीको दोस्रो स्थानमा रहेको छ
- draft: नेपालमा पानीको स्रोत एसिया महादेशमा नै पहिलो र विश्वमा ब्राजिल पछाडिको दोस्रो स्थानमा रहेको छ

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
- draft: सङ्गै बसे जस्तो लाग्छ

### tl_0189 · cer 0.0488 · long
- roman: `Nepalko uttar dishama purvadekhi paschimsamda paredka sipahi himali shrinkhala ubhieka chhan`
- gold:  नेपालको उत्तर दिशामा पूर्वदेखि पश्चिमसम्म परेडका सिपाही हिमाली श्रृंखला उभिएका छन्
- model: नेपालको उत्तर दिशामा पूर्वदेखि पश्चिमसम्दा परेडका सिपाही हिमाली शृंखला उभिएका छन्
- draft: नेपालको उत्तर दिशामा पूर्वदेखि पश्चिम् सम्म पारेडका सिपाही हिमाली शृङ्खला उभिएका छन्

### tl_0037 · cer 0.0476 · medium
- roman: `Jati j cha mero timi hau`
- gold:  जति—जे छ मेरो तिमी हौ
- model: जति जे छ मेरो तिमी हौ
- draft: जति ज छ मेरो तिमी हौ

### tl_0148 · cer 0.0476 · medium
- roman: `Himalaya parbatiya ra tarai`
- gold:  हिमालय पर्वतीय र तराई
- model: हिमालय पर्बतीय र तराई
- draft: हिमालय पर्बतीय र तराई

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
- draft: दिन दुइगुना रात चौगुना

### tl_0101 · cer 0.0435 · medium
- roman: `Ekchin pachi suna yasko aawaj`
- gold:  एकछिन पछि सुन यसको आवाज
- model: एकछिन पछि सुना यसको आवाज
- draft: एकछिन पछि सुना यास्का आवाज

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
- draft: नेपालको हिमाल पहाडमा नागबेली बानी बग्ने त्रिशूली कर्णाली मस्याङ्दी काली गण्डकी अरुण तमोर जस्ता नदी पानीको प्रमुख भण्डार हुन्

### tl_0076 · cer 0.0385 · medium
- roman: `Soche chau timro mero sambandha`
- gold:  सोचेछौ तिम्रो मेरो सम्बन्ध
- model: सोचे छौ तिम्रो मेरो सम्बन्ध
- draft: सोचे छौ तिम्रो मेरो सम्बन्ध

### tl_0205 · cer 0.038 · long
- roman: `Hamilai prakritile himalko chiso lek pahadka hariya van ani taraiko urvara phot dieko chha`
- gold:  हामीलाई प्रकृतिले हिमालको चिसो लेक पहाडका हरिया वन अनि तराईको उर्वर फॉट दिएको छ
- model: हामीलाई प्रकृतिले हिमालको चिसो लेक पहाडका हरिया भन अनि तराईको उर्वरा फोट दिएको छ
- draft: हामीलाई प्रकृतिले हिमालको चिसो लेक पहाडका हरिया वन अनि तराईको उर्वरा फँट दिएको छ

### tl_0098 · cer 0.0345 · medium
- roman: `eklai parnu parne mero jindagi`
- gold:  एक्लै पर्नुपर्ने मेरो जिन्दगी
- model: एक्लै पर्नु पर्ने मेरो जिन्दगी
- draft: एकलै पर्नु पर्ने मेरो जिन्दगी

### tl_0096 · cer 0.0323 · medium
- roman: `eklai bachnu parne mero jindagi`
- gold:  एक्लै बाँच्नुपर्ने मेरो जिन्दगी
- model: एक्लै बाँच्नु पर्ने मेरो जिन्दगी
- draft: एकलै बाँच्नु पर्ने मेरो जिन्दगी

### tl_0178 · cer 0.0311 · long
- roman: `Ajha spashta shabdama bhanda Nepalma paine himal pahad tarai taramandal nadinala taltalaiya upatyaka jharna jal vayu khanij padartha jivjantu vanaspati nai hamra prakritik sampada hun`
- gold:  अझ स्पष्ट शब्दमा भन्दा नेपालमा पाइने हिमाल पहाड तराई तारामण्डल नदीनाला तालतलैया उपत्यका झरना जल वायु खनिज पदार्थ जीवजन्तु वनस्पति नै हाम्रा प्राकृतिक सम्पदा हुन्
- model: अझ स्पष्ट शब्दमा भन्दा नेपालमा पाइने हिमाल पहाड तराई तारामण्डल नदिनाला तालतालैया उपत्यका झर्ना जल भयु खनिज पदार्थ जीवजन्तु वनस्पति नै हाम्रा प्राकृतिक सम्पदा हुन्
- draft: अझ स्पष्ट शब्दमा भन्दा नेपालमा पाइने हिमाल पहाड तराई तरामण्डल नदीनाला टल्ताल्याया उपत्यका झरना जल वायु खनिज पदार्थ जीवजन्तु वनस्पति नै हाम्रा प्राकृतिक सम्पदा हुन्

### tl_0012 · cer 0.0303 · medium
- roman: `Mayako yasto modma hami aaipugyou`
- gold:  मायाको यस्तो मोडमा हामी आइपुग्यौँ
- model: मायाको यस्तो मोडमा हामी आइपुग्यौ
- draft: मायाको यस्तो मोडमा हामी आइपुग्यौँ

### tl_0196 · cer 0.0303 · long
- roman: `Nepali bhumima se Phoksundo Chhhorolpa Tilicho Rara jasta tanharu chhan jasle tyaha pugne pratyek paryataklai swarga pugeko aabhas dieko chha`
- gold:  नेपाली भूमिमा से फोक्सुन्डो च्छोरोल्पा तिलिचो रारा जस्ता तानहरू छन् जसले त्यहाँ पुग्ने प्रत्येक पर्यटकलाई स्वर्ग पुगेको आभास दिएको छ
- model: नेपाली भूमिमा से फोक्सुण्डो छोरोल्पा तिलिचो रारा जस्ता तानहरू छन जसले त्यहाँ पुग्ने प्रत्येक पर्यटकलाई स्वर्ग पुगेको आभास दिएको छ
- draft: नेपाली भूमिमा से फोक्सुण्डो छ्होरोल्पा तिलिचो रारा जस्ता टान्हरु छन जसले त्यहाँ पुग्ने प्रत्येक पर्यटकलाई स्वर्ग पुगेको आभास दिएको छ

### tl_0190 · cer 0.0294 · long
- roman: `Vishwako sarvochcha shikhar Sagarmatha Nepalko mahattwapurna prakritik sampada ho`
- gold:  विश्वको सर्वोच्च शिखर सगरमाथा नेपालको महत्वपूर्ण प्राकृतिक सम्पदा हो
- model: विश्वको सर्वोच्च शिखर सगरमाथा नेपालको महत्त्वपूर्ण प्राकृतिक सम्पदा हो
- draft: विश्वको सर्वोच्च शिखर सगरमाथा नेपालको महत्वपूर्ण प्राकृतिक सम्पदा हो

### tl_0180 · cer 0.0292 · long
- roman: `Yi prakritik sampadabata manisle ekatir bharpura manoranjan prapta gareka chhan bhane arkotir manisko mihineta paurakh buddhi kshamata yasma pokhinda yinaibata manisle jibanma pran dhanta rogko upchar garna bideshi mudra arjan gari arthoparjan garna saksham baneka chhan`
- gold:  यी प्राकृतिक सम्पदाबाट मानिसले एकातिर भरपुर मनोरञ्जन प्राप्त गरेका छन् भने अर्कोतिर मानिसको मिहिनेत पौरख बुद्धि क्षमता यसमा पोखिंदा यिनैबाट मानिसले जीवनमा प्राण धान्त रोगको उपचार गर्न विदेशी मुद्रा आर्जन गरी अर्थोपार्जन गर्न सक्षम बनेका छन्
- model: यी प्राकृतिक सम्पदाबाट मानिसले एकातिर भरपुरा मनोरञ्जन प्राप्त गरेका छन भने अर्कोतिर मानिसको मिहिनेता पौरख बुद्धि क्षमता यसमा पोखिंदा यिनैबाट मानिसले जीबनमा प्राण धन्त रोगको उपचार गर्न बिदेशी मुद्रा अर्जन गरी अर्थोपार्जन गर्न सक्षम बनेका छन्
- draft: यी प्राकृतिक सम्पदाबाट मानिसले एकतिर भरपूर मनोरञ्जन प्राप्त गरेका छन् भने अर्कोतिर मानिसको मिहिनेत पौरख बुद्धि क्षमता यस्मा पोखिंदा यिनैबाट मानिसले जीवनमा प्राण धन्ता रोगको उपचार गर्न विदेशी मुद्रा आर्जन गरी अर्थोपार्जन गर्न सक्षम बनेका छन्

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
- draft: यो प्राकृतिक सौन्दर्य र स्रोतहरु मा धनी छ

### tl_0208 · cer 0.0244 · medium
- roman: `Nepaliko bhagya badali bhabisya banauna aawashyak chha`
- gold:  नेपालीको भाग्य बदली भविष्य बनाउन आवश्यक छ
- model: नेपालीको भाग्य बदली भबिष्य बनाउन आवश्यक छ
- draft: नेपालीको भाग्य बदली भविष्य बनाउन आवश्यक छ

### tl_0144 · cer 0.0238 · long
- roman: `Mero desh Nepal dui deshharu dwara gherieko chha`
- gold:  मेरो देश नेपाल दुई देशहरु द्वारा घेरिएको छ
- model: मेरो देश नेपाल दुई देशहरू द्वारा घेरिएको छ
- draft: मेरो देश नेपाल दुई देशहरु द्वारा घेरीएको छ

### tl_0198 · cer 0.0238 · long
- roman: `Yi tan hernaka lagi matra ramra chhainan nauka vihar garna jal vihar garna pani upayukta chhan`
- gold:  यी तान हेर्नका लागि मात्र राम्रा छैनन् नौका विहार गर्न जल बिहार गर्न पनि उपयुक्त छन्
- model: यी तन हेर्नका लागि मात्र राम्रा छैनन् नौका विहार गर्न जल विहार गर्न पनि उपयुक्त छन्
- draft: यी टान hernaka लागि मात्र राम्रा छैannan नौका विहार गर्न जल विहार गर्न पनि उपयुक्त छन

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
- draft: यिनले नेपालको गौरव बढाउनु का साथै यinko सदुपयोग गर्न सकेको खण्डमा नेपाल विश्वकै धनी राष्ट्रको पक्त्तिमा पर्न सक्ने सम्भावना पनि छ

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
- draft: (pending)

## Draft disagrees with the legacy gold (148 rows)

These are the rows worth a human decision: either the legacy label is
wrong (we already confirmed several) or the draft is. Set
`user_devanagari` to the accepted form and explain in `user_note`.

### tl_0116 · draft cer 0.4545
- roman: `ajkalto mai chadchau ki`
- gold:  अच्कल्टो मै छाड्छौं कि
- draft: आजकल्तो मै चढछौ की
- model: आजकल्तो मै चड्छौ कि

### tl_0127 · draft cer 0.4118
- roman: `sampati lai aayindaina`
- gold:  सम्पत्तिलाई आइदैन
- draft: सम्पति लाइ आयइन्दैन
- model: सम्पत्ति लाइ आयिँदैन

### tl_0009 · draft cer 0.375
- roman: `Timi prati maya badhdocha`
- gold:  तिमीप्रति माया बढ्दो छ (बढ्दो छ)
- draft: तिमी प्रति माया बढ्दोछ
- model: तिमी प्रति माया बढ्दोचा

### tl_0103 · draft cer 0.3636
- roman: `Haa Haa Haaa Haaa`
- gold:  हा हा हा हा
- draft: हाँ हाँ हाँ हाँ
- model: हा हा हाँ हाँ

### tl_0105 · draft cer 0.3529
- roman: `gham kati ghamailo`
- gold:  घाम लाग्यो घमाइलो
- draft: घाम कति घमाइलो
- model: घाम कति घमाइलो

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

### tl_0049 · draft cer 0.3077
- roman: `U Jaba Bolaunche Jiskaudai`
- gold:  ऊ जब बोलाउँछे जिस्क्याउँदै
- draft: उ जबा बोलाउन्चे जिस्काउदै
- model: उ जब बोलाउँछे जिस्काउदै

### tl_0050 · draft cer 0.2963
- roman: `Ankha Haru Sankaunche Jhimkaudai`
- gold:  आँखाहरू सन्काउछे झिम्काउँदै
- draft: आँखा हरु सङ्काउन्चे झिमकाउदै
- model: आँखा हरु सन्काउँछे झिम्काउदै

### tl_0112 · draft cer 0.2857
- roman: `pirati ko talai ma`
- gold:  पिरतीको तालैमा
- draft: पिरती को तलाइ मा
- model: पिरती को तलाई मा

### tl_0133 · draft cer 0.2857
- roman: `Baru Aai Sataune Gara`
- gold:  बरु आई मलाई सताउने गर
- draft: बरु आइ सताउने गर
- model: बरु आइ सताउने गर

### tl_0158 · draft cer 0.2812
- roman: `Sabha bhanda aglo Sagarmatha Angrejima Mount Everest ko rupma chininchha`
- gold:  सब भन्दा अग्लो सगरमाथा अंग्रेजीमा माउन्ट एभरेष्टको रूपमा चिनिन्छ
- draft: सभ भन्दा अग्लो सगरमाथा अङ्ग्रेजीमा Mount Everest को रुपमा चिनिन्छ
- model: सभा भन्दा अग्लो सगरमाथा अंग्रेजीमा माउन्ट इभरेस्ट को रूपमा चिनिन्छ

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

### tl_0143 · draft cer 0.2609
- roman: `Maan Kholi Dekhaune Gara`
- gold:  मन खोली मलाई देखाउने गर
- draft: मान खोली देखाउने गर
- model: मान खोली देखाउने गर

### tl_0011 · draft cer 0.25
- roman: `Kasari basyo kunni maya khoi`
- gold:  कसरी बस्यो कुन्नि माया, खै, आ—हा
- draft: कसरी बस्यो कुन्नि माया खोई
- model: कसरी बस्यो कुन्नी माया खोइ

### tl_0136 · draft cer 0.2424
- roman: `Tanneriko Sapana Jastai Swadama Na Aau`
- gold:  तन्नेरीको सपनाजस्तै विस्वादमा नआऊ
- draft: तान्नेरिको सपना जस्तै स्वादमा ना आउ
- model: तन्नेरीको सपना जस्तै स्वादमा ना आउ

### tl_0125 · draft cer 0.24
- roman: `sun chadi le timlai varula`
- gold:  सुनचाँदीले तिमीलाई भरौंला
- draft: सुन चादी ले तिम्लाई भरुला
- model: सुन छाडी ले तिम्लाई भरुला

### tl_0142 · draft cer 0.24
- roman: `Nalukai Maanka Sara Bimbaharu`
- gold:  नलुकाई मनका सारा विम्बहरू
- draft: नलुकै मान्का सारा बिम्बहरु
- model: नलुकै मानका सारा बिम्बहरू

### tl_0138 · draft cer 0.2308
- roman: `Kada Dekhi Darai Nabhagne Gara`
- gold:  काँडा देखि डराई नभाग्ने गर
- draft: काद देखि दराइ नभग्ने गर
- model: काडा देखि दराई नभाग्ने गर

### tl_0157 · draft cer 0.2308
- roman: `Himali uttarma vishwaka chaudha uchchatam pahadharumaddhye aath chhan`
- gold:  हिमाली उत्तरमा विश्वका १४ उच्चतम पहाडहरूमध्ये आठ छन्
- draft: हिमाली उत्तरमा बिश्वका चौध उच्चतम् पहाढुमद्द्ये आठ छन
- model: हिमाली उत्तरमा विश्वका चौध उच्चतम पहाडहरूमध्ये आठ छन्

### tl_0132 · draft cer 0.2258
- roman: `Timro Tadako Mahi Pugena Malai`
- gold:  तिम्रो टाढाको म्वाइँ पुगेन मलाई
- draft: तिम्रो तादको माही पुगेन मलाई
- model: तिम्रो तडको महि पुगेन मलाई

### tl_0046 · draft cer 0.2222
- roman: `Kahile Kahin Bazar Ma`
- gold:  कहिले काहीँ बजारमा
- draft: कहिले कहिन बजार मा
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

### tl_0004 · draft cer 0.1944
- roman: `Achanak badliyo manau tyo mero hoina`
- gold:  अचानक बद्लियो, मानौँ, त्यो मेरो होइन
- draft: अचानक बदलीयो मनाऊ त्यो मेरो होइन
- model: अचानक बदलियो मनाउ त्यो मेरो होइन

### tl_0117 · draft cer 0.1923
- roman: `Sindur lauchau ki nai bhana na`
- gold:  सिन्दुर लाउँछौं कि नाई भनन
- draft: सिन्दुर लाउछौ कि नै भन न
- model: सिन्दुर लाउछौ कि नै भन ना

### tl_0128 · draft cer 0.1905
- roman: `maya garchau ki nai vana na`
- gold:  माया गर्छौ कि नाई भनन
- draft: माया गर्छौ कि नाइ वन ना
- model: माया गर्छौ कि नै भन ना

### tl_0113 · draft cer 0.1875
- roman: `machi marau jalaima`
- gold:  माछी मारौ जालैमा
- draft: माछी मराउ जालैमा
- model: माची मराउ जलाइमा

### tl_0058 · draft cer 0.1818
- roman: `Timilai Nalai Bhachaina`
- gold:  तिमीलाई न ल्याई भा छैन
- draft: तिमीलाई नलाई भाछैन
- model: तिमीलाई नलाई भाछैन

### tl_0198 · draft cer 0.1786
- roman: `Yi tan hernaka lagi matra ramra chhainan nauka vihar garna jal vihar garna pani upayukta chhan`
- gold:  यी तान हेर्नका लागि मात्र राम्रा छैनन् नौका विहार गर्न जल बिहार गर्न पनि उपयुक्त छन्
- draft: यी टान hernaka लागि मात्र राम्रा छैannan नौका विहार गर्न जल विहार गर्न पनि उपयुक्त छन
- model: यी तन हेर्नका लागि मात्र राम्रा छैनन् नौका विहार गर्न जल विहार गर्न पनि उपयुक्त छन्

### tl_0052 · draft cer 0.1739
- roman: `Jali Rumal Chadera Janera`
- gold:  जाली रुमाल छाडेर जानेले
- draft: जाली रुमाल चडेर जानेर
- model: जाली रुमाल छाडेर जानेर

### tl_0078 · draft cer 0.1739
- roman: `Feri kina malai berthaima`
- gold:  फेरि किन मलाई ब्यर्थैमा
- draft: फेरि किन मलाई बेरर्थाइमा
- model: फेरी किन मलाई बेर्थैमा

### tl_0101 · draft cer 0.1739
- roman: `Ekchin pachi suna yasko aawaj`
- gold:  एकछिन पछि सुन यसको आवाज
- draft: एकछिन पछि सुना यास्का आवाज
- model: एकछिन पछि सुना यसको आवाज

### tl_0030 · draft cer 0.1667
- roman: `Nachutos hamro darilo sath`
- gold:  नछुटोस् हाम्रो दरिलो साथ
- draft: नचुतोस हाम्रो दरीलो साथ
- model: नछुटोस् हाम्रो दरिलो साथ

### tl_0055 · draft cer 0.1667
- roman: `Budha Pakha Bhet Huda`
- gold:  बुढापाका भेट हुँदा
- draft: बुढा पाखा भेट हुदा
- model: बुढा पाखा भेट हुदा

### tl_0119 · draft cer 0.1667
- roman: `bhai maya namare ni kaile ho`
- gold:  भै माया नमारे नि कैले हो
- draft: भै माया नमरे नी काइले हो
- model: भाइ माया नमरे नि कहिले हो

### tl_0115 · draft cer 0.16
- roman: `Ani jaal ma eklai parchau ki`
- gold:  अनि जालमा एक्लै पार्छौ कि
- draft: अनि जाल मा एकलै पर्छौ की
- model: अनि जाल मा एकलै पर्छौ कि

### tl_0131 · draft cer 0.16
- roman: `Kahile Kahi Maya Pani Dekhaune Gara`
- gold:  कहिले माया पनि देखाउने गर
- draft: कहिले कही माया पनि देखाउने गर
- model: कहिले कहि माया पनि देखाउने गर

### tl_0035 · draft cer 0.1579
- roman: `Bhanne le bhanos garos`
- gold:  भन्नेले भनोस् गरोस्
- draft: भन्ने ले भनोस गरोस
- model: भन्ने ले भनोस् गरोस्

### tl_0021 · draft cer 0.1538
- roman: `Euta maya garne byakti lai`
- gold:  एउटा माया गर्ने व्यक्तिलाई
- draft: एउटा माया गर्ने ब्याक्ती लाई
- model: एउटा माया गर्ने ब्यक्ति लाई

### tl_0137 · draft cer 0.1538
- roman: `Pritiko Phool Tipnu Parchha Bhane`
- gold:  प्रीतिको फूल टिप्नपर्छ भने
- draft: प्रितिको फूल टिपनु पर्छ भने
- model: प्रीतिको फूल टिप्नु पर्छ भने

### tl_0053 · draft cer 0.1429
- roman: `Jhuto Maya Layera Jane Le`
- gold:  झूटो माया लाएर जानेले
- draft: झुटो माया लायर जाने ले
- model: झुटो माया लायेर जाने ले

### tl_0099 · draft cer 0.1429
- roman: `suna mero dhadkan`
- gold:  सुन मेरो धड्कन
- draft: सुना मेरो ढड्कन
- model: सुना मेरो धड्कन

### tl_0129 · draft cer 0.1429
- roman: `Timi ra ma ghumna jau na`
- gold:  तिमी र म घुम्न जाउँ न
- draft: तिमी रा म घुम्न जाउ ना
- model: तिमी र मा घुम्न जाउ न

### tl_0031 · draft cer 0.1364
- roman: `Dekhne le dekhos sunos`
- gold:  देख्नेले देखोस् सुनोस्
- draft: देख्ने ले देखोस सुनोस
- model: देख्ने ले देखोस् सुनोस्

### tl_0159 · draft cer 0.1351
- roman: `Urvara ra ardra dakshin kshetra sahari chha`
- gold:  उर्वर र आर्द्र दक्षिणी क्षेत्र शहरी छ
- draft: उर्बरा र आर्द्रा दक्षिण क्षेत्र सहरी छ
- model: उर्वरा र अर्द्र दक्षिण क्षेत्र सहरी छ

### tl_0062 · draft cer 0.1333
- roman: `kehi chota lagda`
- gold:  केही चोट लाग्दा
- draft: केहि चोटा लाग्दा
- model: केही चोट लाग्दा

### tl_0016 · draft cer 0.1316
- roman: `Upahar swaroop yo tasbeer maya garne haru lai`
- gold:  उपहारस्वरूप यो तस्बीर माया गर्नेहरूलाई
- draft: उपहार स्वरूप यो तस्बिर माया गर्ने हरु लाई
- model: उपहार स्वरूप यो तस्बीर माया गर्ने हरु लाई

### tl_0018 · draft cer 0.1316
- roman: `Jindagi narahos rahi rahanecha yesma kaid pal haru`
- gold:  जिन्दगी नरहोस् रहिरहनेछ यसमा कैद पलहरू
- draft: जिन्दगी नरहोस रही रहनेछ यसमा कैद पल हरु
- model: जिन्दगी नरहोस् रहि रहनेछ येसमा कैद पल हरु

### tl_0057 · draft cer 0.1304
- roman: `Dharo Dharma Yo Kura Sancho Cha`
- gold:  धरोधर्म यो कुरा साँचो छ
- draft: धारो धर्म यो कुरा साचो छ
- model: धारो धर्म यो कुरा सान्चो छ

### tl_0145 · draft cer 0.129
- roman: `China uttarpatti awasthit chha ra paschim purva ra dakshin Bharatle dhakeko chha`
- gold:  चीन उतरपट्टि अवस्थित छ र पश्चिम पुर्व र दक्षिण भारतले ढाकेको छ
- draft: चिन उत्तरपत्ति अवस्थित छ र पछिम पुर्व र दक्षिण भारतले ढाकेको छ
- model: चिना उत्तरपट्टि अवस्थित छ र पश्चिम पूर्व र दक्षिण भारतले ढाकेको छ

### tl_0042 · draft cer 0.125
- roman: `Maski Maski Hidera Jane Le`
- gold:  मस्कीमस्की हिँडेर जानेले
- draft: मस्की मस्की हिडेर जाने ले
- model: मस्की मस्की हिडेर जाने ले

### tl_0059 · draft cer 0.125
- roman: `Tarki Tarki Hidera Jane Le`
- gold:  तर्कीतर्की हिँडेर जानेले
- draft: तर्की तर्की हिडेर जाने ले
- model: तर्की तर्की हिडेर जाने ले

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

### tl_0092 · draft cer 0.125
- roman: `Timro maan ho ki dhunga ho`
- gold:  तिम्रो मन हो कि ढुंगा हो
- draft: तिम्रो मान हो कि ढुङ्गा हो
- model: तिम्रो मान हो कि ढुङ्गा हो

### tl_0123 · draft cer 0.125
- roman: `pakhuri ma daam cha ni`
- gold:  पाखुरीमा दम छ नि
- draft: पाखुरी मा दाम छ नि
- model: पाखुरी मा दाम छ नि

### tl_0088 · draft cer 0.1176
- roman: `tyatinai jhan marchau`
- gold:  त्यति नै झन मर्छौ
- draft: त्यतिनै झन मार्छौ
- model: त्यतिनै झन मर्चौ

### tl_0162 · draft cer 0.1167
- roman: `Hamro lokapriya khanaharu dal bhat dindo gunrdruk ityadi hun`
- gold:  हाम्रो लोकप्रिय खानाहरू दाल भाट डिन्डो गुनर्दुक इत्यादि हुन्
- draft: हाम्रो लोकप्रिय खानाहरू दाल भात दिँडो गुन्द्रुक इत्यादि हुन्
- model: हाम्रो लोकप्रिय खानाहरू दाल भात दिन्दो गुणर्द्रुक इत्यादि हुन्

### tl_0023 · draft cer 0.1154
- roman: `Timi nai hau malai maya garne`
- gold:  तिमी नै हौ मलाई माया गर्ने
- draft: तिमी नै hau मलाई माया गर्ने
- model: तिमी नै हौ मलाई माया गर्ने

### tl_0060 · draft cer 0.1154
- roman: `Farki Farki Hasera Herne Le`
- gold:  फर्कीफर्की हाँसेर हेर्नेले
- draft: फर्की फर्की हासेर हेर्ने ले
- model: फर्की फर्की हासेर हेर्ने ले

### tl_0195 · draft cer 0.1154
- roman: `Taltalaiya ra jharnharu pani Nepalka prakritik sampada hun`
- gold:  तालतलैया र झरनाहरू पनि नेपालका प्राकृतिक सम्पदा हुन्
- draft: टाल्टल्याया र झरनाहरू पनि नेपालका प्राकृतिक सम्पदा हुन्
- model: तालतालैया र झर्नहरू पनि नेपालका प्राकृतिक सम्पदा हुन्

### tl_0074 · draft cer 0.1111
- roman: `milan nabhai bite bhane`
- gold:  मिलन नभइ बितेँ भने
- draft: मिलन नभई बिते भने
- model: मिलन नभै बिते भने

### tl_0139 · draft cer 0.1111
- roman: `Manchhe Ke Ke Bhanchhan Malai`
- gold:  मान्छे के के भन्छन् तिमीलाई
- draft: मान्छे के के भन्छन् मलाई
- model: मान्छे के के भन्छन् मलाई

### tl_0141 · draft cer 0.1111
- roman: `Sancho Kura Bhana Malai`
- gold:  साँचो कुरा भन मलाई
- draft: साञ्चो कुरा भन मलाई
- model: सान्चो कुरा भन मलाई

### tl_0130 · draft cer 0.1071
- roman: `Ye Malai Maya Garchhau Bhanne Hajura`
- gold:  ए मलाई माया गर्छु भन्ने हजुर
- draft: ये मलाई माया गर्छौ भन्ने हजुर
- model: ये मलाई माया गर्छौ भन्ने हजुरा

### tl_0122 · draft cer 0.1053
- roman: `Ma pani k ma kaam chu ni`
- gold:  म पनि केमा कम छु नि
- draft: म पनि के मा काम छु नि
- model: मा पनि क मा काम छु नि

### tl_0124 · draft cer 0.1053
- roman: `sampati kamayincha ni`
- gold:  सम्पत्ति कमाइन्छ नि
- draft: सम्पति कमाइन्छ नि
- model: सम्पत्ति कमायिन्छ नि

### tl_0048 · draft cer 0.1
- roman: `Luki Luki Herche Malai`
- gold:  लुकीलुकी हेर्छे मलाई
- draft: लुकी लुकी हेर्चे मलाई
- model: लुकी लुकी हेर्चे मलाई

### tl_0069 · draft cer 0.1
- roman: `sangai base jasto lagcha`
- gold:  संगै बसे जस्तो लाग्छ
- draft: सङ्गै बसे जस्तो लाग्छ
- model: सँगै बसे जस्तो लाग्छ

### tl_0070 · draft cer 0.1
- roman: `bipanale jhaskai dida`
- gold:  विपनाले झस्काइ दिँदा
- draft: बिपनाले झस्काइ दिदा
- model: बिपनाले झस्कै दिदा

### tl_0107 · draft cer 0.1
- roman: `Timi ra ma ghumna jaau na`
- gold:  तिमी र म घुम्न जाउँन
- draft: तिमी र म घुम्न जाऊ न
- model: तिमी र मा घुम्न जाऊ न

### tl_0111 · draft cer 0.1
- roman: `Khola jastai bagau hami`
- gold:  खोला जस्तै बगौं हामी
- draft: खोला जस्तै बगाउ हामी
- model: खोला जस्तै बगाउ हामी

### tl_0120 · draft cer 0.1
- roman: `O Nisthuri`
- gold:  ओ निष्ठूरी
- draft: ओ निष्ठुरी
- model: ओ निस्थुरी

### tl_0013 · draft cer 0.0968
- roman: `Bhabishyako mitho kalpana bhulisakyou`
- gold:  भविष्यको मीठो कल्पना बुनिसक्यौँ
- draft: भविष्यको मीठो कल्पना भुुलिसक्यौँ
- model: भबिष्यको मीठो कल्पना भुलिसक्यौ

### tl_0037 · draft cer 0.0952
- roman: `Jati j cha mero timi hau`
- gold:  जति—जे छ मेरो तिमी हौ
- draft: जति ज छ मेरो तिमी हौ
- model: जति जे छ मेरो तिमी हौ

### tl_0056 · draft cer 0.0952
- roman: `Buhari Ko Gharma Khacho Cha`
- gold:  बुहारीको घरमा खाँचो छ
- draft: बुहारी को घरमा खाचो छ
- model: बुहारी को घरमा खाचो छ

### tl_0015 · draft cer 0.0938
- roman: `Maile sumpi diye sabai timrai naamma`
- gold:  मैले सुम्पिदिएँ सबै तिम्रै नाममा
- draft: मैले सुम्पी दिएँ सबै तिम्रै नाम्मा
- model: मैले सुम्पी दिए सबै तिम्रै नाम्म

## New candidate lines for gold v2

### new_001 · Manko Rani — Sugam Pokhrel
- roman: `Din ra raatma timrai sapana`
- model: दिन र रातमा तिम्रै सपना
- draft: दिन रा रातमा तिमrai सपना

### new_002 · Anganai Bhari — Amrit Gurung
- roman: `Baisa ma phoole Mayako muskanma`
- model: बैसा मा फुले मायाको मुस्कानमा
- draft: बैसा मा फूले मायाको मुस्कानमा

### new_003 · Baadal — Purna Rai & Dajubhaiharu
- roman: `Kasailai Chadi Balidiyou Kasailai Jhari Mero Rang Anek`
- model: कसैलाई छाडी बालिदियौ कसैलाई झरी मेरो रंग अनेक
- draft: कसलाई छाडी बलिदियौ कसलाई झरी मेरो रङ्ग अनेक

### new_004 · Thahai Napai Maya Basecha — Nabin K Bhattarai
- roman: `Jati bhulu bhanda, timilai nai rojcha) - x2`
- model: जति भुलु भन्दा, तिमीलाई नै रोज्छ) - एक्स2
- draft: जति भुलु भन्दा, तिमilai नै रोज्छ) - x2

### new_005 · Sath Sadhainko — Sushant Kc, Uniq Poet
- roman: `Thaha chha timilai`
- model: थाहा छ तिमीलाई
- draft: थाह छ तिमीलाई

### new_006 · Aau Re — Prasanna Dhoj Pradhan
- roman: `Timi bina ma adhuro`
- model: तिमी बिना मा अधुरो
- draft: तिमी बिना म अधुरो

### new_007 · Jyotsna Lyrics by Swoopna Suman — Swoopna Suman
- roman: `Chuna tyo timro tyo wooth lai`
- model: चुना त्यो तिम्रो त्यो वुथ लाई
- draft: चुना त्यो तिम्रो त्यो ओठ लाई

### new_008 · Kataa Kataa — The Edge Band Nepal | Jeewan Gurung
- roman: `Samjihnchu Samjihnchu Samjihnchu`
- model: सम्जिन्छु सम्जिन्छु सम्जिन्छु
- draft: सम्झिन्छु सम्झिन्छु सम्झिन्छु

### new_009 · Karnali Ka Chhaila — Nepathya
- roman: `Ahile Saal Yestai Bho Nana`
- model: अहिले साल यस्तै भो नाना
- draft: अहिले साल यस्तै भो नाना

### new_010 · Jindagi Ko K Bharosha - Karna Das [Chords] - Paan Ko Pat
- roman: `ratri ko andheri bihani ko sunaulo`
- model: रात्री को अन्धेरी बिहानि को सुनौलो
- draft: रात्री को अन्धेरी बिहानी को सुनाउलो

### new_011 · Maya Dherai samjana - Bekcha Official — Bekcha
- roman: `Timro sparsha samahalera`
- model: तिम्रो स्पर्श समाहालेर
- draft: तिम्रो स्पर्श समाहलेर

### new_012 · Mayama Raichha K Saro — Prajakta Shukre
- roman: `Maya Ma Rahecha Ke Saro Bisa`
- model: माया मा रहेछ के सारो बिसा
- draft: माया मा रहेचा के सारो बिसा

### new_013 · Timi Mero Maan Ma — Nepsydez
- roman: `Kasai Lie Dekhauna Hoina`
- model: कसै Lie देखाउन होइन
- draft: कसै लिए देखाउना होइना

### new_014 · Rausi Layo — Jamesy
- roman: `K Chaldai Cha Vanana`
- model: क चल्दै छ भनना
- draft: के चल्दै छ भनना

### new_015 · Thik Chha
- roman: `Pachhuto ra darle jyanai jana la thyo`
- model: पछुतो र दरले ज्यानै जान ला थियो
- draft: पछुतो रा दर्ले ज्यानै जाना ल थ्यो

### new_016 · Mayale Boleko — Sugam Pokhrel
- roman: `Janti liyi aaunu hajur`
- model: जन्ती लियी आउनु हजुर
- draft: जन्ती लियी आउनु हजुर

### new_017 · Hamro Kahani (Ballad Version) lyrics / Neetesh Jung Kunwar — Neetesh Jung Kunwar
- roman: `Niswartha maya garthey uslai`
- model: निस्वार्थ माया गर्थे उसलाई
- draft: निस्वार्थ माया गार्थे उस्लाई

### new_018 · Baaf [बाफ] — Sujan Chapagain & Bidhya Tiwari
- roman: `Rahena ma aafu mai`
- model: रहेन मा आफू म
- draft: रहेना म आफू मै

### new_019 · Hey Hajur — Dr Pilot
- roman: `Maghi hai mela ma dil basyo`
- model: माघी है मेला मा दिल बस्यो
- draft: माघी है मेला मा दिल बस्यो

### new_020 · rajdhani — dhurba shrestha
- roman: `Prem ko yo nagari, yo mero rajdhani`
- model: प्रेम को यो नगरी, यो मेरो राजधानी
- draft: प्रेम को यो नगरी, यो मेरो राजधानी

### new_021 · Timi Aauchauki Bhani — Sunil Giri
- roman: `Jhamakkai sanjha paryo`
- model: झमक्कै साँझ पर्यो
- draft: झमक्कै साँझ पर्यो

### new_022 · Pal Pal Timrai — Sukmit Gurung
- roman: `K Ho K Vo Thahai Payeena) - 2`
- model: क हो क भो थाहै पायीन) - 2
- draft: के हो के भो थाहाइ पाएना) - 2

### new_023 · Yo Dil Mero — Edge Band
- roman: `Timi Bina Mero Jiwan Ma`
- model: तिमी बिना मेरो जीवन मा
- draft: तिमी बिना मेरो जीवन मा

### new_024 · Timi Nai Hau — Official
- roman: `Timi chau, timro pyaro manche cha`
- model: तिमी छौ, तिम्रो प्यारो मान्छे छ
- draft: तिमी छौ, तिम्रो प्यारो मान्छे छ

### new_025 · Kalo Keshma Relimai — Dinesh Dhakal
- roman: `Badheko Ribbona`
- model: बढेको रिब्बोना
- draft: बाधेको रिबोना

### new_026 · Mero Mann maa — Naren Limbu
- roman: `timi timi`
- model: तिमी तिमी
- draft: तिमी तिमी

### new_027 · Kalo Keshma Relimai — Dinesh Dhakal
- roman: `Aahai Bholi K k Hola`
- model: आहै भोली क क होला
- draft: आहै भोलि के क् होला

### new_028 · Kal Dhara — Mr. D | Eleena Chauhan
- roman: `Yaha Chalne Nai Ho Yesta`
- model: यहा चल्ने नै हो येस्ता
- draft: याहा चलने नै हो यस्ता

### new_029 · Bipul chettri- Aashish Official — Bipul Chettri
- roman: `Dhuka lai na birsi rakhnu`
- model: ढुका लाइ ना बिर्सी राख्नु
- draft: ढुका लाइ ना बिर्सी राख्नु

### new_030 · samaya — 555 chirag khadka
- roman: `Chahiye Bela Koile pani Feri Saath Diyena`
- model: चाहिए बेला कोइले पनि फेरी साथ दियेन
- draft: चाहिएको बेला कोइले पनि फेरी साथ दिएन

### new_031 · Ma Afnai Aganma — Yash Kumar
- roman: `Eh Baba Malai Kasto Karma Diyeu`
- model: एह बाबा मलाई कस्तो कर्म दियेउ
- draft: ए बाबा मलाई कस्तो कर्म दियौ

### new_032 · Basa Sundari - Bro-Sis Band — Blog
- roman: `Hera sundari yo mann mero saacho chha`
- model: हेरा सुन्दरी यो मन्न मेरो साचो छ
- draft: हेरा सुन्दरी यो मन मेरो साँचो छ

### new_033 · Suseli Le Basantalai — Udit Narayan
- roman: `Sworga Jastai Gharko`
- model: स्वर्ग जस्तै घरको
- draft: स्वर्ग जस्तै घरको

### new_034 · Thaha Chhaian — Vten (Samir Ghising)
- roman: `Ramro ta maile pani sochekai ho`
- model: राम्रो ता मैले पनि सोचेकै हो
- draft: राम्रो त मैले पनि सोचेकै हो

### new_035 · Chhuk Chhuke Relaima — Khem Century & Madhu Rashaili
- roman: `Hey Laaz Namana Aru Ko Odhau Rato Malai Baruko`
- model: Hey लाज नमाना अरु को ओढाउ रातो मलाई बारुको
- draft: हे लाज नमाना अरू को ओढाऊ रातो मलाई बारुको

### new_036 · Janu Cha Malai — The Unity
- roman: `Nepali Music Ko`
- model: नेपाली Music को
- draft: (pending)

### new_037 · Mellow : Rohit Shakya X Sajjan Raj Vaidya Official — Sajjan Raj Vaidya
- roman: `Timilai nai kurda kurdai bitla hai yo jindagi`
- model: तिमीलाई नै कुर्दा कुर्दै बित्ला है यो जिन्दगी
- draft: तिमीलाई नै कुर्दै कुर्दै बित्ला है यो जिन्दगी

### new_038 · Gurasai Fulyo — 1974 AD
- roman: `Timro mannaima`
- model: तिम्रो मान्नैमा
- draft: तिम्रो मनमैना

### new_039 · Chulesima — Sanjeev Singh
- roman: `Eklai behosima`
- model: एकलाई बेहोसीमा
- draft: एकलै बेहोसीमा

### new_040 · Jiwan
- roman: `Aye Jiwan Ma Sanga Ekchin Kura Gara`
- model: आये जीवन मा सँग एकछिन कुरा गर
- draft: ऐ जीवन म सँग एकचिन कुरा गर

### new_041 · Aparibhasit — Swapnil Sharma, Swar
- roman: `Mero maana bhitra ka harek khushi hau`
- model: मेरो माना भित्र का हरेक खुसी हौ
- draft: मेरो मान भित्र का हरेक खुसी hau

### new_042 · A Hora Maya — Himal Sagar, Anu Chaudhary
- roman: `Ae ho ra maya,`
- model: आए हो र माया,
- draft: ए हो र माया,

### new_043 · Putali Aau — Ankita Pun
- roman: `Nachdai Aauchan Timi Tirai`
- model: नाच्दै आउँछन् तिमी तिरै
- draft: नाच्दै आउँछन् तिमी तिरै

### new_044 · Timro Pratiksa — Shallum Lama
- roman: `Basi rahenay chu sadhai timrai pratikchiya nai`
- model: बसी रहेनय छु सधैँ तिम्रै प्रतीक्चीय नै
- draft: बसी रहने छु सधैँ तिम्रै प्रतिक्रिया नै

### new_045 · Juni — Sajjan Raj Vaidya
- roman: `Mayalu Timi Hau Ki Khai Kunni`
- model: मायालु तिमी हाउ कि खै कुन्नी
- draft: मायालु तिमी हौ कि खै कुन्नी

### new_046 · Mero Hajura — Swoopna Suman | Abhigya Ghimire
- roman: `Sahara Bina Timro Ke Jindagi`
- model: सहारा बिना तिम्रो के जिन्दगी
- draft: सहारा बिना तिम्रो के जिन्दगी

### new_047 · Tada Najai Deu — Sanjay Shrestha
- roman: `Jaha jau timi tyahi hune chhu ma`
- model: जहाँ जाउ तिमी त्यही हुने छु मा
- draft: जहाँ जाऊँ तिमी त्यहीँ हुने छु म

### new_048 · Suna Kaanchi lyrics by Sajjan Raj Vaidya — Sajjan Raj Vaidya
- roman: `Tairinchau ta wori pari`
- model: तैरिन्छौ ता वोरी पारी
- draft: तैरिन्छौ त वरी परी

### new_049 · SAMJHANA MA NA AAU Lyrics / Sugam pokhrel — Sugam Pokharel
- roman: `Lyrics Hemanta Ghimire`
- model: Lyrics हेमन्त घिमिरे
- draft: Lyrics हेमन्त घिमिरे

### new_050 · Maya Timilai — Sabin Rai
- roman: `Dui Thopa Aanshu Liyera`
- model: दुई थोपा आँसु लिएर
- draft: दुई थोपा आँसु लिएर

### new_051 · Farki Aauna Lyrics / Lisson Khadka & Bekcha — Lisson khadka
- roman: `Yeti saro chha ra`
- model: येती सारो छ र
- draft: येति सारो छ र

### new_052 · Pagal Ma Banna Sakchu — Sworup Raj Acharya
- roman: `Timro Samu Aakash Pani`
- model: तिम्रो सामु आकाश पनि
- draft: तिम्रो सामु आकाश पनि

### new_053 · Phoolako Thunga — Tara Devi
- roman: `Mai Saachu Kasari`
- model: मै साचु कसरी
- draft: मै साचु कसरी

### new_054 · Katai Mero Naam — Udit Narayan
- roman: `Ho katai mero naam timle koreko ta hoina ni`
- model: हो कतै मेरो नाम तिम्ले कोरेको ता होइन नि
- draft: हो कतै मेरो नाम तिम्ले कोरेको त होइन नि

### new_055 · Hamro School — Sugam Pokhrel
- roman: `Manma Yo Bela`
- model: मनमा यो बेला
- draft: मनमा यो बेला

### new_056 · Na Birse Timilai — Anju Panta
- roman: `aayau samipai jaba timi nidari ma`
- model: आयौ समीपै जब तिमी निदारी मा
- draft: आायौ समिपै जबा तिमी निदारी मा

### new_057 · Chitthi Bhitra Lyrics - Sajjan Raj Vaidya — Sajjan Raj Vaidya
- roman: `Timi lai nai, sumpidiyen yo mann.`
- model: तिमी लाइ नै, सुम्पिदियें यो मन्न.
- draft: तिमी लाइ नै, सुम्पिदियेन यो मन्न।

### new_058 · Ukali Chadhda — Ambar Gurung
- roman: `Timi navaye aru ko holaaa...`
- model: तिमी नभए अरु को होला...
- draft: तिमी नभये अरू को होलाaa...

### new_059 · Samajko Kura — Samriddhi Rai
- roman: `Chhoralai banune re dherai thulo manchhe`
- model: छोरालाई बनुने रे धेरै ठूलो मान्छे
- draft: छोरालाई बानुने रे धेरै ठुलो मान्छे

### new_060 · Parkhai Ko pida — Kaman Man Singh
- roman: `Jhuto nai cha timro tyo maya`
- model: झुटो नै छ तिम्रो त्यो माया
- draft: झुटो नै छ तिम्रो त्यो माया

### new_061 · Hariyo Dada Mathi — Dharmaraj Thapa
- roman: `Chamro mato mathi`
- model: चाम्रो माटो माथि
- draft: चम्रो माटो माथि

### new_062 · Chopiyeko Satya — Yama Buddha
- roman: `Saanjh Dhaldai Chha`
- model: साँझ ढल्दै छ
- draft: साँझ ढल्दै छ

### new_063 · E Kanchi — Nima Rumba
- roman: `Chura dhago pote, lali oothma, lali ootha ma`
- model: चुरा धागो पोते, लाली ओठमा, लाली ओठ मा
- draft: चुरा धागो पोते, लाली ओठ्म, लाली ओठा मा

### new_064 · Euta Chittiko — The Axe
- roman: `Yo Dui Aatma Ko Mel Ho`
- model: यो दुई आत्मा को मेल हो
- draft: यो दुई आत्मा को मेल हो

### new_065 · Paribhasa — Purna Rai & Dajubhaiharu
- roman: `Duniyalai Dekhaunu Chaina`
- model: दुनियालाई देखाउनु छैन
- draft: दुनियालाई देखाउनु छैन

### new_066 · Mero yad aa chha? — Sujata KC || Shishir Bhandari
- roman: `Kahile vetum va chha?`
- model: कहिले भेटम भ छ?
- draft: कहिले भेटुम वा छ?

### new_067 · Eklo Mann — Sushant Ghimire
- roman: `Kinarai Na Bheti Eh Rakheko`
- model: किनारै ना भेटी एह राखेको
- draft: किनारै ना भेटी Eh राखेको

### new_068 · Bhare Auchu Sapanima — Ananda Karki, Devika Bandana
- roman: `Na lajai dinu`
- model: ना लजाइ दिनु
- draft: न लजाई दिनु

### new_069 · Dhun — Rockheads Nepal
- roman: `Hami Sangae Nai Rachaula`
- model: हामी संगै नै रचौला
- draft: हामी सँगै नै रचौला

### new_070 · Mooskaan Lyrics - Sajjan Raj Vaidya — Sajjan Raj Vaidya
- roman: `Timro naam, timro aawaaj, timro nyano nyano sparsha,`
- model: तिम्रो नाम, तिम्रो आवाज, तिम्रो न्यानो न्यानो स्पर्श,
- draft: तिम्रो नाम, तिम्रो आवाज्, तिम्रो न्यानो न्यानो स्पर्श,

### new_071 · Chahidaina Satai Juni — Anil Singh
- roman: `Bhayo bhane kahaani`
- model: भयो भने कहानी
- draft: भयो भने कहानी

### new_072 · Ma Yesto Chu — Girish N Pranil
- roman: `Hamro naya album back again`
- model: हाम्रो नया album back again
- draft: (pending)

### new_073 · Hukum Baksiyos lyrics / Melina Rai/ Bishal rai — Melina Rai
- roman: `Line Producer: Gagan Shrestha`
- model: Line Producer: गगन श्रेष्ठ
- draft: (pending)

### new_074 · Sangai Juine — Sworup Raj Acharya
- roman: `Manko Khusi Vanda Pani`
- model: मनको खुसी भन्दा पनि
- draft: मनको खुसी भन्दा पनि

### new_075 · Aaijo Nidari — Nepathya
- roman: `Kath kahani baba lai halna lyiejo`
- model: काठ कहानी बाबा लाइ हाल्न ल्यिएजो
- draft: कथ कहानी बाबा लाइ हल्न ल्यिएजो

### new_076 · Achanolai Thaha Hola — Ram Krishna Dhakal
- roman: `kaha gai metu ma`
- model: कहाँ गाइ मेटु मा
- draft: कहाँ गई मेटु म

### new_077 · Sanjha Ko Bela — COD
- roman: `Timi Aauchau Ki Bhani`
- model: तिमी आउँछौ कि भनि
- draft: तिमी आउँछौ कि भनी

### new_078 · Karodaulai Herera — Pramod Kharel, Tika Prasain
- roman: `Plij navana hai hunna`
- model: प्लिज नभन है हुन्न
- draft: Plij नभना है हुन्न

### new_079 · Katha | VTEN ft. Dharmendra Sewan — VTEN
- roman: `Kaha hunu teti matra ghar bhitrako naatak`
- model: कहाँ हुनु तेती मात्र घर भित्रको नाटक
- draft: कहाँ हुनु तेति मात्र घर भित्रको नाटक

### new_080 · Hyatteri Lyrics by Sajjan Raj Vaidya — Sajjan Raj Vaidya
- roman: `Sunnya Garya Chu Timro`
- model: सुन्न्या गर्या छु तिम्रो
- draft: सुन्ऱ्या गर्या छु तिम्रो

### new_081 · Paisa Sapati पैसा सापटी lyrics / Badri Pangeni & Rachana Rimal — Rachana Rimal
- roman: `(Uff, Timro dhatne bani le`
- model: (यूएफएफ, तिम्रो धात्ने बानी ले
- draft: (pending)

### new_082 · Lahurelai Chadbad — Karna Das
- roman: `Jamara Ra Tika Lagai Hidne Sundar Jodi - 2`
- model: जमरा रा टिका लगाई हिड्ने सुन्दर जोडी - 2
- draft: जमरा र टीका लगाई हिड्ने सुन्दर जोडी - 2

### new_083 · Phool Ko Aankhama — Ani Choying Dolma
- roman: `Ramro aankhama khulchha ramrai sansara`
- model: राम्रो आँखामा खुल्छ राम्रै संसार
- draft: राम्रो आँखमा खुल्छ राम्रै संसारा

### new_084 · Khulaudai Othama Lali — Dipak Limbu
- roman: `(Mutu Satau Na Sanu`
- model: (मुटु सतौ ना सानु
- draft: (मुटु सटाउ ना सानु

### new_085 · Ma Audai Chu — The Axe
- roman: `Sagara poudera tarne chhu`
- model: सागरा पौडेर तर्ने छु
- draft: सागरै पौडेर तारने छु

### new_086 · Ko Chha Yaha Ghati Badi (को छ यहाँ घटिबढी ?) lyrics / Astha raut — Aastha Raut
- roman: `Chema garnu thulo`
- model: चेमा गर्नु ठूलो
- draft: क्षेमा गर्नु ठूलो

### new_087 · Dukcha Chati — Manila Sotang
- roman: `Mutu Bhitra Oo Basekai Hunchha`
- model: मुटु भित्र ओ बसेकै हुन्छ
- draft: मुटु भित्र ओ बसेकै हुन्छ

### new_088 · Dashain Ayo — Udit Narayan, Deepa Narayan Jha
- roman: `Daiko ghadi haataima larilai`
- model: दाइको घडी हातैमा लरीलाई
- draft: दाइको घडी हातैमा लरिलाई

### new_089 · Eco Ni Lagyo — Karishma Bista
- roman: `Pahile ta sochthe lagyo account matra`
- model: पहिले ता सोच्थे लाग्यो एकाउन्ट मात्र
- draft: पहिले त सोच्थे लाग्यो account मात्र

### new_090 · Kasle Choryo Yo Man — Udit Narayan
- roman: `Gareki Thiye Jatan`
- model: गरेकी थिये जतन
- draft: गरेकी थिये जतन

### new_091 · BHANAI - Tribal Rain Official — Tribal Rain
- roman: `Ma ta euta bhanai matra ho`
- model: मा त एउटा भनाइ मात्र हो
- draft: म त एउटा भनाइ मात्र हो

### new_092 · Nadukheko Mann — Deepak Bajracharya
- roman: `Yi Aankha Bhiji Rakhne Bho Sandhai Nai`
- model: यी आँखा भिजी राख्ने भो सँधै नै
- draft: यी आँखा भिजी राख्ने भो सधैं नै

### new_093 · Safalta — Aastha Band
- roman: `Jati tada janchhu ma, uti najik aai dinchha`
- model: जति टाढा जान्छु मा, उति नजिक आइ दिन्छ
- draft: जति टाढा जान्छु म, उति नजिक आइ दिन्छ

### new_094 · Mitho Sapana — Prajina
- roman: `Timi Sangai Baki Jindagani Mero`
- model: तिमी सँगै बाकी जिन्दगानी मेरो
- draft: तिमी सँगै बाकी जिन्दगानी मेरो

### new_095 · Swatantra Jeevan — Robin Tamang
- roman: `Yekchin ko lagi timile sochyau bhane`
- model: येक्छिन् को लागि तिमीले सोच्यौ भने
- draft: एकचिन को लागि तिमीले सोच्याउ भने

### new_096 · Aaja — Adrian Pradhan
- roman: `Samjhi lyauda aashu bahanchha`
- model: सम्झी ल्याउदा आँसु बहन्छ
- draft: सम्झी ल्याउदा आँशु बहान्छ

### new_097 · Lagcha Mann Herirahu — Ananda Karki
- roman: `Fulera fulharule dharti sajau aaja X 2`
- model: फुलेर फूलहरूले धर्ती सजाउ आज एक्स 2
- draft: फुलेर फुलहरूले धरती सजाउ आज X 2

### new_098 · Din Dhalcha Sanjha Parcha — Nabin K Bhattarai
- roman: `Kina maan lai chalaunu, kina malai chunu`
- model: किन मान लाइ चलाउनु, किन मलाई चुनु
- draft: किन मान लाई चलाउनु, किन मलाई छुणु

### new_099 · Mero yad aa chha? — Sujata KC || Shishir Bhandari
- roman: `Kasto hunchha hamro sansar?`
- model: कस्तो हुन्छ हाम्रो संसार?
- draft: कस्तो हुन्छ हाम्रो संसार?

### new_100 · Kya Bore Bhayo — Yogeshwar Amatya
- roman: `Uta Phakaayeko Ho Ki`
- model: उता फकाएको हो कि
- draft: उता फुकाएको हो की

### new_101 · Suna Bhanana — Udit Narayan, Deepa Narayan Jha
- roman: `Dina Ra Raat Ek Hune`
- model: दिना रा रात एक हुने
- draft: दिना रा रात एक हुने

### new_102 · Dubo Phulyo OFFICIAL LYRICS — Dayahang Rai, Upasana Singh, Karma, Wilson
- roman: `Ho yo jamana paisa ko`
- model: हो यो जमाना पैसा को
- draft: हो यो जमाना पैसा को

### new_103 · Mayale Mai Tirai Heri Bhanideu I Love You — Shanti Shree Pariyar | Umesh Muskan
- roman: `Manaune Sochyachu Hey Rati Ma Sapana`
- model: मनाउने सोच्याचु Hey राती मा सपना
- draft: मनाउने सोच्याचु हे रति मा सपना

### new_104 · Yo Karma Bhumi — Deepak Kharel
- roman: `Hami nepali ko pakhuri ma) - 2`
- model: हामी नेपाली को पाखुरी मा) - 2
- draft: हामी नेपाली को पखुरी मा) - 2

### new_105 · Lajjawati Jhar — Mahesh Kafle, Asmita Adhikari
- roman: `Khai kasarai aaun, khai kasari aaun maya`
- model: खै कसरै आउन, खै कसरी आउन माया
- draft: खै कसरै आउन, खै कसरी आउन माया

### new_106 · Gayo Gayo Jawani Gayo — Babin Pradhan
- roman: `Bitdai gaye ko jawani lai`
- model: बित्दै गए को जवानी लाई
- draft: बित्दै गये को जवानी लाइ

### new_107 · Strain — VTEN
- roman: `Bhayeni balai chaina unlai j hos`
- model: भयेनी बलाई छैन उनलाई जे होस्
- draft: भयेनि बालै चैन। उनलाइ ज होस्

### new_108 · Kati Din Bite — Sugam Pokhrel
- roman: `Paindaina kina jeevan saathi rojeko`
- model: पाइँदैन किन जीवन साथी रोजेको
- draft: पाइदैन किन जीवन साथी रोजेको

### new_109 · Dhurwa tara - lyrics / Purna Rai — Purna rai
- roman: `Nata kara le nai timilai`
- model: नाटा करा ले नै तिमीलाई
- draft: नता करा ले नै तिमीलाई

### new_110 · Suskera — Sajjan Raj Vaidya
- roman: `Yo Chaati Ma Joon Maan Cha`
- model: यो छाती मा जुन मान छ
- draft: यो छाती मा जुन मान छ

### new_111 · Pardeshi Hunai Man Chhaina — Khem Century & Shanti Shree Pariyar
- roman: `Pyari Roonai Maan Chaina Desha Chodi`
- model: प्यारी रुनै मान छैन देश छोडी
- draft: प्यारी रुनाइ मान छैन देश छोडी

### new_112 · Tihar Song — Axata Adhikari
- roman: `Fallin And Walkin We're Not Exaggeratin`
- model: फल्लिन And वाल्किन We're Not एक्सागरेटिन
- draft: (pending)

### new_113 · Tiriri Murali Bajyo Banaima — Prabesh Man Shakya
- roman: `Murali dhuna bhuleko chaina`
- model: मुरली धुना भुलेको छैन
- draft: मुरली धुन भुलेको छैन

### new_114 · Bujhe Hunchha Kura — Melina Rai
- roman: `Chin Chin Chin Chin Chin Haath Ko`
- model: चिन चिन चिन चिन चिन हात को
- draft: छिन छिन छिन छिन छिन हात को

### new_115 · Sanibar Ko Din — Udit Narayan
- roman: `U Pyaari Chhe`
- model: उ प्यारी छे
- draft: उ प्यारी छे

### new_116 · Furfuri — Kuma Sagar
- roman: `Goon mero jaandaina`
- model: गुन मेरो जाँदैन
- draft: गुन मेरो जाँदैन

### new_117 · Timilai Herne Bani Paryo Female Version Lyrics / Annu Chaudhary — Annu Chaudhary
- roman: `Gautam Thapa`
- model: गौतम थापा
- draft: गौतम थापा

### new_118 · Pirati Aafai Hudo Raicha — Udit Narayan
- roman: `Sandhai Naya Jindagilai`
- model: सँधै नया जिन्दगीलाई
- draft: सधैँ नयाँ जिन्दगीलाई

### new_119 · Chaubandi Choli — Phiroj Shyangden
- roman: `Hasda Ta Jhanai Ni Hurukkai Pareko`
- model: हास्दा ता झनै नि हुरुक्कै परेको
- draft: हाँस्दा त झनै नि हुरुक्कै परेको

### new_120 · Manko Rani — Sugam Pokhrel
- roman: `Geet pani timro laagi nai gaaune chhu`
- model: गीत पनि तिम्रो लागी नै गाउने छु
- draft: गीत पनि तिम्रो लागि नै गाउने छु
