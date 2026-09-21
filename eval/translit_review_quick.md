# Quick transliteration review

- `new_heldout`: 120 lines held out from teacher training. The
  **pipeline** output is pre-filled in `user_devanagari` (a review pass showed
  it beats the draft here); `draft` is a second opinion and `draft_agrees`
  marks where the two agree. Edit or delete what you disagree with.
- `legacy_consensus`: 33 legacy rows where the draft and the pipeline
  agree against the recorded gold (likely legacy errors). Set `user_devanagari` to
  the accepted form, or leave empty to keep the legacy label.

Non-lyric candidates (English-only lines, credit rows) are filtered out of the
sample. Full kit with all draft disagreements: `eval/translit_review.md`.

## new_heldout

### 001
- roman: `Din ra raatma timrai sapana`
- model: दिन र रातमा तिम्रै सपना
- draft: दिन रा रातमा तिमrai सपना (differs)

### 002
- roman: `Baisa ma phoole Mayako muskanma`
- model: बैसा मा फुले मायाको मुस्कानमा
- draft: बैसा मा फूले मायाको मुस्कानमा (differs)

### 003
- roman: `Kasailai Chadi Balidiyou Kasailai Jhari Mero Rang Anek`
- model: कसैलाई छाडी बालिदियौ कसैलाई झरी मेरो रंग अनेक
- draft: कसलाई छाडी बलिदियौ कसलाई झरी मेरो रङ्ग अनेक (differs)

### 004
- roman: `Jati bhulu bhanda, timilai nai rojcha) - x2`
- model: जति भुलु भन्दा, तिमीलाई नै रोज्छ) - एक्स2
- draft: जति भुलु भन्दा, तिमilai नै रोज्छ) - x2 (differs)

### 005
- roman: `Thaha chha timilai`
- model: थाहा छ तिमीलाई
- draft: थाह छ तिमीलाई (differs)

### 006
- roman: `Timi bina ma adhuro`
- model: तिमी बिना मा अधुरो
- draft: तिमी बिना म अधुरो (differs)

### 007
- roman: `Chuna tyo timro tyo wooth lai`
- model: चुना त्यो तिम्रो त्यो वुथ लाई
- draft: चुना त्यो तिम्रो त्यो ओठ लाई (differs)

### 008
- roman: `Samjihnchu Samjihnchu Samjihnchu`
- model: सम्जिन्छु सम्जिन्छु सम्जिन्छु
- draft: सम्झिन्छु सम्झिन्छु सम्झिन्छु (differs)

### 009
- roman: `Ahile Saal Yestai Bho Nana`
- model: अहिले साल यस्तै भो नाना
- draft: अहिले साल यस्तै भो नाना (agrees)

### 010
- roman: `ratri ko andheri bihani ko sunaulo`
- model: रात्री को अन्धेरी बिहानि को सुनौलो
- draft: रात्री को अन्धेरी बिहानी को सुनाउलो (differs)

### 011
- roman: `Timro sparsha samahalera`
- model: तिम्रो स्पर्श समाहालेर
- draft: तिम्रो स्पर्श समाहलेर (differs)

### 012
- roman: `Maya Ma Rahecha Ke Saro Bisa`
- model: माया मा रहेछ के सारो बिसा
- draft: माया मा रहेचा के सारो बिसा (differs)

### 013
- roman: `Kasai Lie Dekhauna Hoina`
- model: कसै Lie देखाउन होइन
- draft: कसै लिए देखाउना होइना (differs)

### 014
- roman: `K Chaldai Cha Vanana`
- model: क चल्दै छ भनना
- draft: के चल्दै छ भनना (differs)

### 015
- roman: `Pachhuto ra darle jyanai jana la thyo`
- model: पछुतो र दरले ज्यानै जान ला थियो
- draft: पछुतो रा दर्ले ज्यानै जाना ल थ्यो (differs)

### 016
- roman: `Janti liyi aaunu hajur`
- model: जन्ती लियी आउनु हजुर
- draft: जन्ती लियी आउनु हजुर (agrees)

### 017
- roman: `Niswartha maya garthey uslai`
- model: निस्वार्थ माया गर्थे उसलाई
- draft: निस्वार्थ माया गार्थे उस्लाई (differs)

### 018
- roman: `Rahena ma aafu mai`
- model: रहेन मा आफू म
- draft: रहेना म आफू मै (differs)

### 019
- roman: `Maghi hai mela ma dil basyo`
- model: माघी है मेला मा दिल बस्यो
- draft: माघी है मेला मा दिल बस्यो (agrees)

### 020
- roman: `Prem ko yo nagari, yo mero rajdhani`
- model: प्रेम को यो नगरी, यो मेरो राजधानी
- draft: प्रेम को यो नगरी, यो मेरो राजधानी (agrees)

### 021
- roman: `Jhamakkai sanjha paryo`
- model: झमक्कै साँझ पर्यो
- draft: झमक्कै साँझ पर्यो (agrees)

### 022
- roman: `K Ho K Vo Thahai Payeena) - 2`
- model: क हो क भो थाहै पायीन) - 2
- draft: के हो के भो थाहाइ पाएना) - 2 (differs)

### 023
- roman: `Timi Bina Mero Jiwan Ma`
- model: तिमी बिना मेरो जीवन मा
- draft: तिमी बिना मेरो जीवन मा (agrees)

### 024
- roman: `Timi chau, timro pyaro manche cha`
- model: तिमी छौ, तिम्रो प्यारो मान्छे छ
- draft: तिमी छौ, तिम्रो प्यारो मान्छे छ (agrees)

### 025
- roman: `Badheko Ribbona`
- model: बढेको रिब्बोना
- draft: बाधेको रिबोना (differs)

### 026
- roman: `timi timi`
- model: तिमी तिमी
- draft: तिमी तिमी (agrees)

### 027
- roman: `Aahai Bholi K k Hola`
- model: आहै भोली क क होला
- draft: आहै भोलि के क् होला (differs)

### 028
- roman: `Yaha Chalne Nai Ho Yesta`
- model: यहा चल्ने नै हो येस्ता
- draft: याहा चलने नै हो यस्ता (differs)

### 029
- roman: `Dhuka lai na birsi rakhnu`
- model: ढुका लाइ ना बिर्सी राख्नु
- draft: ढुका लाइ ना बिर्सी राख्नु (agrees)

### 030
- roman: `Chahiye Bela Koile pani Feri Saath Diyena`
- model: चाहिए बेला कोइले पनि फेरी साथ दियेन
- draft: चाहिएको बेला कोइले पनि फेरी साथ दिएन (differs)

### 031
- roman: `Eh Baba Malai Kasto Karma Diyeu`
- model: एह बाबा मलाई कस्तो कर्म दियेउ
- draft: ए बाबा मलाई कस्तो कर्म दियौ (differs)

### 032
- roman: `Hera sundari yo mann mero saacho chha`
- model: हेरा सुन्दरी यो मन्न मेरो साचो छ
- draft: हेरा सुन्दरी यो मन मेरो साँचो छ (differs)

### 033
- roman: `Sworga Jastai Gharko`
- model: स्वर्ग जस्तै घरको
- draft: स्वर्ग जस्तै घरको (agrees)

### 034
- roman: `Ramro ta maile pani sochekai ho`
- model: राम्रो ता मैले पनि सोचेकै हो
- draft: राम्रो त मैले पनि सोचेकै हो (differs)

### 035
- roman: `Hey Laaz Namana Aru Ko Odhau Rato Malai Baruko`
- model: Hey लाज नमाना अरु को ओढाउ रातो मलाई बारुको
- draft: हे लाज नमाना अरू को ओढाऊ रातो मलाई बारुको (differs)

### 036
- roman: `Nepali Music Ko`
- model: नेपाली Music को
- draft:  (differs)

### 037
- roman: `Timilai nai kurda kurdai bitla hai yo jindagi`
- model: तिमीलाई नै कुर्दा कुर्दै बित्ला है यो जिन्दगी
- draft: तिमीलाई नै कुर्दै कुर्दै बित्ला है यो जिन्दगी (differs)

### 038
- roman: `Timro mannaima`
- model: तिम्रो मान्नैमा
- draft: तिम्रो मनमैना (differs)

### 039
- roman: `Eklai behosima`
- model: एकलाई बेहोसीमा
- draft: एकलै बेहोसीमा (differs)

### 040
- roman: `Aye Jiwan Ma Sanga Ekchin Kura Gara`
- model: आये जीवन मा सँग एकछिन कुरा गर
- draft: ऐ जीवन म सँग एकचिन कुरा गर (differs)

### 041
- roman: `Mero maana bhitra ka harek khushi hau`
- model: मेरो माना भित्र का हरेक खुसी हौ
- draft: मेरो मान भित्र का हरेक खुसी hau (differs)

### 042
- roman: `Ae ho ra maya,`
- model: आए हो र माया,
- draft: ए हो र माया, (differs)

### 043
- roman: `Nachdai Aauchan Timi Tirai`
- model: नाच्दै आउँछन् तिमी तिरै
- draft: नाच्दै आउँछन् तिमी तिरै (agrees)

### 044
- roman: `Basi rahenay chu sadhai timrai pratikchiya nai`
- model: बसी रहेनय छु सधैँ तिम्रै प्रतीक्चीय नै
- draft: बसी रहने छु सधैँ तिम्रै प्रतिक्रिया नै (differs)

### 045
- roman: `Mayalu Timi Hau Ki Khai Kunni`
- model: मायालु तिमी हाउ कि खै कुन्नी
- draft: मायालु तिमी हौ कि खै कुन्नी (differs)

### 046
- roman: `Sahara Bina Timro Ke Jindagi`
- model: सहारा बिना तिम्रो के जिन्दगी
- draft: सहारा बिना तिम्रो के जिन्दगी (agrees)

### 047
- roman: `Jaha jau timi tyahi hune chhu ma`
- model: जहाँ जाउ तिमी त्यही हुने छु मा
- draft: जहाँ जाऊँ तिमी त्यहीँ हुने छु म (differs)

### 048
- roman: `Tairinchau ta wori pari`
- model: तैरिन्छौ ता वोरी पारी
- draft: तैरिन्छौ त वरी परी (differs)

### 049
- roman: `Lyrics Hemanta Ghimire`
- model: Lyrics हेमन्त घिमिरे
- draft: Lyrics हेमन्त घिमिरे (agrees)

### 050
- roman: `Dui Thopa Aanshu Liyera`
- model: दुई थोपा आँसु लिएर
- draft: दुई थोपा आँसु लिएर (agrees)

### 051
- roman: `Yeti saro chha ra`
- model: येती सारो छ र
- draft: येति सारो छ र (differs)

### 052
- roman: `Timro Samu Aakash Pani`
- model: तिम्रो सामु आकाश पनि
- draft: तिम्रो सामु आकाश पनि (agrees)

### 053
- roman: `Mai Saachu Kasari`
- model: मै साचु कसरी
- draft: मै साचु कसरी (agrees)

### 054
- roman: `Ho katai mero naam timle koreko ta hoina ni`
- model: हो कतै मेरो नाम तिम्ले कोरेको ता होइन नि
- draft: हो कतै मेरो नाम तिम्ले कोरेको त होइन नि (differs)

### 055
- roman: `Manma Yo Bela`
- model: मनमा यो बेला
- draft: मनमा यो बेला (agrees)

### 056
- roman: `aayau samipai jaba timi nidari ma`
- model: आयौ समीपै जब तिमी निदारी मा
- draft: आायौ समिपै जबा तिमी निदारी मा (differs)

### 057
- roman: `Timi lai nai, sumpidiyen yo mann.`
- model: तिमी लाइ नै, सुम्पिदियें यो मन्न.
- draft: तिमी लाइ नै, सुम्पिदियेन यो मन्न। (differs)

### 058
- roman: `Timi navaye aru ko holaaa...`
- model: तिमी नभए अरु को होला...
- draft: तिमी नभये अरू को होलाaa... (differs)

### 059
- roman: `Chhoralai banune re dherai thulo manchhe`
- model: छोरालाई बनुने रे धेरै ठूलो मान्छे
- draft: छोरालाई बानुने रे धेरै ठुलो मान्छे (differs)

### 060
- roman: `Jhuto nai cha timro tyo maya`
- model: झुटो नै छ तिम्रो त्यो माया
- draft: झुटो नै छ तिम्रो त्यो माया (agrees)

### 061
- roman: `Chamro mato mathi`
- model: चाम्रो माटो माथि
- draft: चम्रो माटो माथि (differs)

### 062
- roman: `Saanjh Dhaldai Chha`
- model: साँझ ढल्दै छ
- draft: साँझ ढल्दै छ (agrees)

### 063
- roman: `Chura dhago pote, lali oothma, lali ootha ma`
- model: चुरा धागो पोते, लाली ओठमा, लाली ओठ मा
- draft: चुरा धागो पोते, लाली ओठ्म, लाली ओठा मा (differs)

### 064
- roman: `Yo Dui Aatma Ko Mel Ho`
- model: यो दुई आत्मा को मेल हो
- draft: यो दुई आत्मा को मेल हो (agrees)

### 065
- roman: `Duniyalai Dekhaunu Chaina`
- model: दुनियालाई देखाउनु छैन
- draft: दुनियालाई देखाउनु छैन (agrees)

### 066
- roman: `Kahile vetum va chha?`
- model: कहिले भेटम भ छ?
- draft: कहिले भेटुम वा छ? (differs)

### 067
- roman: `Kinarai Na Bheti Eh Rakheko`
- model: किनारै ना भेटी एह राखेको
- draft: किनारै ना भेटी Eh राखेको (differs)

### 068
- roman: `Na lajai dinu`
- model: ना लजाइ दिनु
- draft: न लजाई दिनु (differs)

### 069
- roman: `Hami Sangae Nai Rachaula`
- model: हामी संगै नै रचौला
- draft: हामी सँगै नै रचौला (differs)

### 070
- roman: `Timro naam, timro aawaaj, timro nyano nyano sparsha,`
- model: तिम्रो नाम, तिम्रो आवाज, तिम्रो न्यानो न्यानो स्पर्श,
- draft: तिम्रो नाम, तिम्रो आवाज्, तिम्रो न्यानो न्यानो स्पर्श, (differs)

### 071
- roman: `Bhayo bhane kahaani`
- model: भयो भने कहानी
- draft: भयो भने कहानी (agrees)

### 072
- roman: `Hamro naya album back again`
- model: हाम्रो नया album back again
- draft:  (differs)

### 073
- roman: `Line Producer: Gagan Shrestha`
- model: Line Producer: गगन श्रेष्ठ
- draft:  (differs)

### 074
- roman: `Manko Khusi Vanda Pani`
- model: मनको खुसी भन्दा पनि
- draft: मनको खुसी भन्दा पनि (agrees)

### 075
- roman: `Kath kahani baba lai halna lyiejo`
- model: काठ कहानी बाबा लाइ हाल्न ल्यिएजो
- draft: कथ कहानी बाबा लाइ हल्न ल्यिएजो (differs)

### 076
- roman: `kaha gai metu ma`
- model: कहाँ गाइ मेटु मा
- draft: कहाँ गई मेटु म (differs)

### 077
- roman: `Timi Aauchau Ki Bhani`
- model: तिमी आउँछौ कि भनि
- draft: तिमी आउँछौ कि भनी (differs)

### 078
- roman: `Plij navana hai hunna`
- model: प्लिज नभन है हुन्न
- draft: Plij नभना है हुन्न (differs)

### 079
- roman: `Kaha hunu teti matra ghar bhitrako naatak`
- model: कहाँ हुनु तेती मात्र घर भित्रको नाटक
- draft: कहाँ हुनु तेति मात्र घर भित्रको नाटक (differs)

### 080
- roman: `Sunnya Garya Chu Timro`
- model: सुन्न्या गर्या छु तिम्रो
- draft: सुन्ऱ्या गर्या छु तिम्रो (differs)

### 081
- roman: `(Uff, Timro dhatne bani le`
- model: (यूएफएफ, तिम्रो धात्ने बानी ले
- draft:  (differs)

### 082
- roman: `Jamara Ra Tika Lagai Hidne Sundar Jodi - 2`
- model: जमरा रा टिका लगाई हिड्ने सुन्दर जोडी - 2
- draft: जमरा र टीका लगाई हिड्ने सुन्दर जोडी - 2 (differs)

### 083
- roman: `Ramro aankhama khulchha ramrai sansara`
- model: राम्रो आँखामा खुल्छ राम्रै संसार
- draft: राम्रो आँखमा खुल्छ राम्रै संसारा (differs)

### 084
- roman: `(Mutu Satau Na Sanu`
- model: (मुटु सतौ ना सानु
- draft: (मुटु सटाउ ना सानु (differs)

### 085
- roman: `Sagara poudera tarne chhu`
- model: सागरा पौडेर तर्ने छु
- draft: सागरै पौडेर तारने छु (differs)

### 086
- roman: `Chema garnu thulo`
- model: चेमा गर्नु ठूलो
- draft: क्षेमा गर्नु ठूलो (differs)

### 087
- roman: `Mutu Bhitra Oo Basekai Hunchha`
- model: मुटु भित्र ओ बसेकै हुन्छ
- draft: मुटु भित्र ओ बसेकै हुन्छ (agrees)

### 088
- roman: `Daiko ghadi haataima larilai`
- model: दाइको घडी हातैमा लरीलाई
- draft: दाइको घडी हातैमा लरिलाई (differs)

### 089
- roman: `Pahile ta sochthe lagyo account matra`
- model: पहिले ता सोच्थे लाग्यो एकाउन्ट मात्र
- draft: पहिले त सोच्थे लाग्यो account मात्र (differs)

### 090
- roman: `Gareki Thiye Jatan`
- model: गरेकी थिये जतन
- draft: गरेकी थिये जतन (agrees)

### 091
- roman: `Ma ta euta bhanai matra ho`
- model: मा त एउटा भनाइ मात्र हो
- draft: म त एउटा भनाइ मात्र हो (differs)

### 092
- roman: `Yi Aankha Bhiji Rakhne Bho Sandhai Nai`
- model: यी आँखा भिजी राख्ने भो सँधै नै
- draft: यी आँखा भिजी राख्ने भो सधैं नै (differs)

### 093
- roman: `Jati tada janchhu ma, uti najik aai dinchha`
- model: जति टाढा जान्छु मा, उति नजिक आइ दिन्छ
- draft: जति टाढा जान्छु म, उति नजिक आइ दिन्छ (differs)

### 094
- roman: `Timi Sangai Baki Jindagani Mero`
- model: तिमी सँगै बाकी जिन्दगानी मेरो
- draft: तिमी सँगै बाकी जिन्दगानी मेरो (agrees)

### 095
- roman: `Yekchin ko lagi timile sochyau bhane`
- model: येक्छिन् को लागि तिमीले सोच्यौ भने
- draft: एकचिन को लागि तिमीले सोच्याउ भने (differs)

### 096
- roman: `Samjhi lyauda aashu bahanchha`
- model: सम्झी ल्याउदा आँसु बहन्छ
- draft: सम्झी ल्याउदा आँशु बहान्छ (differs)

### 097
- roman: `Fulera fulharule dharti sajau aaja X 2`
- model: फुलेर फूलहरूले धर्ती सजाउ आज एक्स 2
- draft: फुलेर फुलहरूले धरती सजाउ आज X 2 (differs)

### 098
- roman: `Kina maan lai chalaunu, kina malai chunu`
- model: किन मान लाइ चलाउनु, किन मलाई चुनु
- draft: किन मान लाई चलाउनु, किन मलाई छुणु (differs)

### 099
- roman: `Kasto hunchha hamro sansar?`
- model: कस्तो हुन्छ हाम्रो संसार?
- draft: कस्तो हुन्छ हाम्रो संसार? (agrees)

### 100
- roman: `Uta Phakaayeko Ho Ki`
- model: उता फकाएको हो कि
- draft: उता फुकाएको हो की (differs)

### 101
- roman: `Dina Ra Raat Ek Hune`
- model: दिना रा रात एक हुने
- draft: दिना रा रात एक हुने (agrees)

### 102
- roman: `Ho yo jamana paisa ko`
- model: हो यो जमाना पैसा को
- draft: हो यो जमाना पैसा को (agrees)

### 103
- roman: `Manaune Sochyachu Hey Rati Ma Sapana`
- model: मनाउने सोच्याचु Hey राती मा सपना
- draft: मनाउने सोच्याचु हे रति मा सपना (differs)

### 104
- roman: `Hami nepali ko pakhuri ma) - 2`
- model: हामी नेपाली को पाखुरी मा) - 2
- draft: हामी नेपाली को पखुरी मा) - 2 (differs)

### 105
- roman: `Khai kasarai aaun, khai kasari aaun maya`
- model: खै कसरै आउन, खै कसरी आउन माया
- draft: खै कसरै आउन, खै कसरी आउन माया (agrees)

### 106
- roman: `Bitdai gaye ko jawani lai`
- model: बित्दै गए को जवानी लाई
- draft: बित्दै गये को जवानी लाइ (differs)

### 107
- roman: `Bhayeni balai chaina unlai j hos`
- model: भयेनी बलाई छैन उनलाई जे होस्
- draft: भयेनि बालै चैन। उनलाइ ज होस् (differs)

### 108
- roman: `Paindaina kina jeevan saathi rojeko`
- model: पाइँदैन किन जीवन साथी रोजेको
- draft: पाइदैन किन जीवन साथी रोजेको (differs)

### 109
- roman: `Nata kara le nai timilai`
- model: नाटा करा ले नै तिमीलाई
- draft: नता करा ले नै तिमीलाई (differs)

### 110
- roman: `Yo Chaati Ma Joon Maan Cha`
- model: यो छाती मा जुन मान छ
- draft: यो छाती मा जुन मान छ (agrees)

### 111
- roman: `Pyari Roonai Maan Chaina Desha Chodi`
- model: प्यारी रुनै मान छैन देश छोडी
- draft: प्यारी रुनाइ मान छैन देश छोडी (differs)

### 112
- roman: `Fallin And Walkin We're Not Exaggeratin`
- model: फल्लिन And वाल्किन We're Not एक्सागरेटिन
- draft:  (differs)

### 113
- roman: `Murali dhuna bhuleko chaina`
- model: मुरली धुना भुलेको छैन
- draft: मुरली धुन भुलेको छैन (differs)

### 114
- roman: `Chin Chin Chin Chin Chin Haath Ko`
- model: चिन चिन चिन चिन चिन हात को
- draft: छिन छिन छिन छिन छिन हात को (differs)

### 115
- roman: `U Pyaari Chhe`
- model: उ प्यारी छे
- draft: उ प्यारी छे (agrees)

### 116
- roman: `Goon mero jaandaina`
- model: गुन मेरो जाँदैन
- draft: गुन मेरो जाँदैन (agrees)

### 117
- roman: `Gautam Thapa`
- model: गौतम थापा
- draft: गौतम थापा (agrees)

### 118
- roman: `Sandhai Naya Jindagilai`
- model: सँधै नया जिन्दगीलाई
- draft: सधैँ नयाँ जिन्दगीलाई (differs)

### 119
- roman: `Hasda Ta Jhanai Ni Hurukkai Pareko`
- model: हास्दा ता झनै नि हुरुक्कै परेको
- draft: हाँस्दा त झनै नि हुरुक्कै परेको (differs)

### 120
- roman: `Geet pani timro laagi nai gaaune chhu`
- model: गीत पनि तिम्रो लागी नै गाउने छु
- draft: गीत पनि तिम्रो लागि नै गाउने छु (differs)

## legacy_consensus

### tl_0105
- roman: `gham kati ghamailo`
- gold:  घाम लाग्यो घमाइलो
- model: घाम कति घमाइलो

### tl_0135
- roman: `Yadama Na Aau`
- gold:  यादमा नआऊ
- model: यादमा ना आउ

### tl_0133
- roman: `Baru Aai Sataune Gara`
- gold:  बरु आई मलाई सताउने गर
- model: बरु आइ सताउने गर

### tl_0054
- roman: `Sanjha Pakha Chautari Ma`
- gold:  साँझपख चौतारीमा
- model: साँझ पाखा चौतारी मा

### tl_0143
- roman: `Maan Kholi Dekhaune Gara`
- gold:  मन खोली मलाई देखाउने गर
- model: मान खोली देखाउने गर

### tl_0073
- roman: `timi kahile narunu`
- gold:  तिमी कहिल्यै नरुनू
- model: तिमी कहिले नरुनु

### tl_0058
- roman: `Timilai Nalai Bhachaina`
- gold:  तिमीलाई न ल्याई भा छैन
- model: तिमीलाई नलाई भाछैन

### tl_0055
- roman: `Budha Pakha Bhet Huda`
- gold:  बुढापाका भेट हुँदा
- model: बुढा पाखा भेट हुदा

### tl_0042
- roman: `Maski Maski Hidera Jane Le`
- gold:  मस्कीमस्की हिँडेर जानेले
- model: मस्की मस्की हिडेर जाने ले

### tl_0059
- roman: `Tarki Tarki Hidera Jane Le`
- gold:  तर्कीतर्की हिँडेर जानेले
- model: तर्की तर्की हिडेर जाने ले

### tl_0068
- roman: `sapana le saath dida`
- gold:  सपनाले साथ दिँदा
- model: सपना ले साथ दिदा

### tl_0092
- roman: `Timro maan ho ki dhunga ho`
- gold:  तिम्रो मन हो कि ढुंगा हो
- model: तिम्रो मान हो कि ढुङ्गा हो

### tl_0123
- roman: `pakhuri ma daam cha ni`
- gold:  पाखुरीमा दम छ नि
- model: पाखुरी मा दाम छ नि

### tl_0060
- roman: `Farki Farki Hasera Herne Le`
- gold:  फर्कीफर्की हाँसेर हेर्नेले
- model: फर्की फर्की हासेर हेर्ने ले

### tl_0139
- roman: `Manchhe Ke Ke Bhanchhan Malai`
- gold:  मान्छे के के भन्छन् तिमीलाई
- model: मान्छे के के भन्छन् मलाई

### tl_0048
- roman: `Luki Luki Herche Malai`
- gold:  लुकीलुकी हेर्छे मलाई
- model: लुकी लुकी हेर्चे मलाई

### tl_0111
- roman: `Khola jastai bagau hami`
- gold:  खोला जस्तै बगौं हामी
- model: खोला जस्तै बगाउ हामी

### tl_0056
- roman: `Buhari Ko Gharma Khacho Cha`
- gold:  बुहारीको घरमा खाँचो छ
- model: बुहारी को घरमा खाचो छ

### tl_0034
- roman: `Khusi chau hami chau jaha`
- gold:  खुसी छौँ हामी छौँ जहाँ
- model: खुसी छौ हामी छौ जहाँ

### tl_0043
- roman: `Musu Musu Hasera Herne Le`
- gold:  मुसुमुसु हासेर हेर्नेले
- model: मुसु मुसु हासेर हेर्ने ले

### tl_0102
- roman: `Timlai sadhai daaki rahancha`
- gold:  तिमीलाई सधैं डाकी रहन्छ
- model: तिमलाई सधैँ डाकी रहन्छ

### tl_0033
- roman: `Paschatap chaina kunai yaha`
- gold:  पश्चात्ताप छैन कुनै यहाँ
- model: पश्चाताप छैन कुनै यहाँ

### tl_0110
- roman: `Timi pirati ko chata odau na`
- gold:  तिमी पिरतीको छाता ओढाउ न
- model: तिमी पिरती को छाता ओडाउ न

### tl_0020
- roman: `Tyo bhanda aru ke nai chahincha`
- gold:  त्योभन्दा अरू के नै चाहिन्छ
- model: त्यो भन्दा अरु के नै चाहिन्छ

### tl_0036
- roman: `Hamro bare kura`
- gold:  हाम्रोबारे कुरा
- model: हाम्रो बारे कुरा

### tl_0063
- roman: `timi tadha huda`
- gold:  तिमी टाढा हुँदा
- model: तिमी टाढा हुदा

### tl_0064
- roman: `dherai dukha lagcha`
- gold:  धेरै दुःख लाग्छ
- model: धेरै दुख लाग्छ

### tl_0075
- roman: `timi bichalit nahunu`
- gold:  तिमी बिचलित नहुनू
- model: तिमी बिचलित नहुनु

### tl_0204
- roman: `Yi jadibuti aushadhi banauna prayog garinchha`
- gold:  यी जडिबुटी औषधी बनाउन प्रयोग गरिन्छ
- model: यी जडीबुटी औषधि बनाउन प्रयोग गरिन्छ

### tl_0148
- roman: `Himalaya parbatiya ra tarai`
- gold:  हिमालय पर्वतीय र तराई
- model: हिमालय पर्बतीय र तराई

### tl_0047
- roman: `Usko Hamro Bhet Hunda`
- gold:  उस्को हाम्रो भेट हुँदा
- model: उसको हाम्रो भेट हुँदा

### tl_0076
- roman: `Soche chau timro mero sambandha`
- gold:  सोचेछौ तिम्रो मेरो सम्बन्ध
- model: सोचे छौ तिम्रो मेरो सम्बन्ध

### tl_0201
- roman: `Yi rukhaharu niryat gari Nepalko aamdani badhauna sakinchha`
- gold:  यी रूखहरू निर्यात गरी नेपालको आम्दानी बढाउन सकिन्छ
- model: यी रुखहरू निर्यात गरी नेपालको आम्दानी बढाउन सकिन्छ
