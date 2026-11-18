"""N1 grammar points (original explanations; `ex` sentences are only used by the tests)."""
from grammar_n3 import compound
from grammar_n4 import _volitional
from patterns import ARU, NARU, SURU, first_lemma, first_pos, point, prev_is


def m_you_ga(toks):
    return [(a, b + 1, h) for a, b, h in _volitional(toks)
            if b + 1 < len(toks) and toks[b].s in ("が", "と") and toks[b + 1].s == "、"]


# nouns for a situation or position someone is in (〜にあって)
SITUATIONS = {"状況", "立場", "地位", "時代", "社会", "世界", "環境", "場", "事態", "時期", "現代", "非常時", "国", "最中",
              "職", "任", "境遇", "逆境", "困難", "危機", "混乱", "戦時", "不況", "競争", "組織", "現場", "業界", "身"}


def P(*a, **k):
    point("N1", *a, **k)


NEG = r"(?:ない|ません|なかった|ず|ぬ)"

P("atte_no", "〜あっての", "only possible because of", "Noun + あっての + Noun",
  """AあってのB means B only exists thanks to A: お客様あっての商売 (a business exists only thanks to its
  customers).""",
  r"あっての", "お客様あっての商売です。", after="any")
P("ikan", "〜いかんで / いかんによって", "depending on", "Noun + (の) + いかんで",
  """いかんで means "depending on": 結果いかんで、計画を変える (we'll change the plan depending on the results).
  いかんにかかわらず / いかんを問わず = regardless of.""",
  r"(?:の)?いかん(?:で|によって|によっては|では|に(?:かかわ|関わ)らず|を問わず|による)", "試験の結果いかんで、進学が決まる。",
  after="n")
P("ni_itaru", "〜に至る / 〜に至って", "reach, come to; only when", "Noun / Verb + に至る",
  """に至る (いたる) means "reach (a serious point)": 事故は大事件に至った. に至って means "only when it came to".
  に至っては = as for (an extreme case).""",
  # in kana, にいたら / にいたって are usually に + いる (そこにいたら, if I were there): only 至 or いたる / いたり
  r"に(?:至(?:る|り|ら|って|った|っては)|いた(?:る|り))", "話し合いは結論に至らなかった。", after="nv", tail=True)
P("ni_itaru_made", "〜に至るまで", "even, down to", "Noun + に至るまで",
  """に至るまで means "all the way to (even the smallest)": 子供からお年寄りに至るまで.""",
  r"に(?:至|いた)るまで", "子供からお年寄りに至るまで、みんな参加した。", after="n")
P("kagiri_da", "〜限りだ", "extremely, I feel so", "Adj + 限りだ",
  """限りだ (かぎりだ) expresses a strong feeling: 嬉しい限りだ (I couldn't be happier).""",
  r"(?:限|かぎ)り(?:だ|です)", "皆さんに会えて、嬉しい限りです。", after="a")
P("katagata", "〜かたがた", "while also, as well as", "Noun + かたがた",
  """かたがた means doing one thing with another purpose: お礼かたがた伺います (I'll visit to thank you, too).""",
  r"かたがた", "お礼かたがた、ご挨拶に伺いました。", after="n")
P("katawara", "〜かたわら", "while (also doing, on the side)", "Noun + の / Verb + かたわら",
  """かたわら means doing one thing on the side while mainly doing another: 会社に勤めるかたわら、小説を書いている (alongside working at a company, he writes novels). It describes long-term activities, not momentary ones.""",
  r"かたわら|傍ら", "会社に勤めるかたわら、小説を書いている。", after="any",
  # "while also doing", not the place "beside" (猫がかたわらで眠る, その傍らに)
  check=lambda t, i, k: i > 0 and t[i - 1].s not in ("その", "が", "は", "を")
  and not (k < len(t) and t[k].s == "に") and not (k < len(t) and t[k].s == "で" and k + 1 < len(t) and t[k + 1].p1 == "動詞"))
P("gatera", "〜がてら", "while, on the way (also)", "Noun / Verb stem + がてら",
  """がてら means "while (also), as a side purpose": 散歩がてら、買い物をした (I went shopping while out for a walk). The first part is the main reason for going out; the second is done on the way.""",
  r"がてら", "散歩がてら、パンを買いに行った。", after="any")
P("ga_hayai_ka", "〜が早いか", "no sooner than", "Verb (dictionary) + が早いか",
  """が早いか means "no sooner than, the instant": ベルが鳴るが早いか、教室を飛び出した (the moment the bell rang, they rushed out of the classroom). It describes something that happens almost simultaneously, in the past.""",
  r"が早いか|がはやいか", "ベルが鳴るが早いか、生徒たちは教室を飛び出した。", after="v")
P("ya_ina_ya", "〜や否や", "as soon as", "Verb (dictionary) + や否や",
  """や否や (やいなや) means "the moment, as soon as": 家に着くや否や、雨が降り出した (as soon as I got home, it started raining). It is written style and describes something unexpected right after.""",
  r"や(?:否|いな)や", "家に着くや否や、雨が降り出した。", after="v")
P("sobakara", "〜そばから", "as soon as (repeatedly)", "Verb + そばから",
  """そばから describes something undone as soon as it's done: 覚えたそばから忘れてしまう.""",
  r"そばから", "単語を覚えたそばから忘れてしまう。", after="v")
P("kirai_ga_aru", "〜きらいがある", "tend to (bad)", "Verb / Noun + の + きらいがある",
  """きらいがある points out a bad tendency someone has: 彼は物事を大げさに言うきらいがある (he tends to exaggerate). It is a slightly formal criticism; the tendency is natural for that person, not deliberate.""",
  r"(?:きらい|嫌い)が" + ARU, "彼は物事を大げさに言うきらいがある。", after="any", tail=True)
P("kiwamaru", "〜極まる / 〜極まりない", "extremely", "な-adj + 極まる",
  """極まる / 極まりない mean "extremely (negative)": 失礼極まりない (incredibly rude).""",
  r"(?:極|きわ)ま(?:る|りない|りません)", "彼の態度は失礼極まりない。", after="any")
P("gotoku", "〜ごとく / 〜ごとき", "like, as", "Noun + の + ごとく",
  """ごとく / ごとき are written "like": 前述のごとく (as stated above), 夢のごとき日々.""",
  r"(?:ごと|如)(?:く|き|し)", "前に述べたごとく、計画は変更された。", after="any",
  check=lambda t, i, k: t[i].lemma in ("如し", "如く", "ごとし") or t[i].p1 == "助動詞")
P("koto_tote", "〜こととて", "because (apologetic)", "Plain form + こととて",
  """こととて gives an excuse, formal: 慣れぬこととて、失礼しました (I'm sorry, being unused to this).""",
  r"こととて", "慣れないこととて、失礼いたしました。", after="any")
P("koto_nashi_ni", "〜ことなしに", "without", "Verb (dictionary) + ことなしに",
  """ことなしに means "without (doing, it can't happen)": 努力することなしに成功はない.""",
  r"ことなし(?:に|には)", "努力することなしに、成功はない。", after="v")
P("shimatsu_da", "〜始末だ", "ended up (bad result)", "Verb (dictionary) + 始末だ",
  """始末だ (しまつだ) describes a bad end result after things go wrong: 遅刻ばかりして、ついにクビになる始末だ (always late, he ended up getting fired). It often follows ついに or とうとう and sounds exasperated.""",
  r"(?:始末|しまつ)(?:だ|です|だった|でした)", "彼は遅刻を繰り返し、ついには解雇される始末だ。", after="v")
P("zukume", "〜ずくめ", "entirely, full of", "Noun + ずくめ",
  """ずくめ means "nothing but": 黒ずくめの服 (dressed all in black), いいことずくめ.""",
  r"ずくめ", "今年はいいことずくめの一年だった。", after="n")
P("zu_ni_wa_okanai", "〜ずにはおかない", "will definitely, can't fail to", "Verb (ない-stem) + ずにはおかない",
  """ずにはおかない means something will inevitably happen: この映画は人を感動させずにはおかない.""",
  r"ずには(?:おか|置か)(?:ない|ぬ)|ないではおかない", "この映画は観客を感動させずにはおかない。", pre="v")
P("zu_ni_wa_sumanai", "〜ずにはすまない", "must (to be acceptable)", "Verb (ない-stem) + ずにはすまない",
  """ずにはすまない means you can't get away without doing something, because the situation demands it: 謝らずにはすまない (I'll have to apologize). ないではすまない is the same; する becomes せずには.""",
  r"(?:ずには|ないでは)(?:すま|済ま)(?:ない|ぬ)", "迷惑をかけたのだから、謝らずにはすまない。", pre="v")
P("tada_nomi", "ただ〜のみ", "only, just", "ただ + Noun / Verb + のみ",
  """ただ〜のみ is a written "only, nothing but": ただ祈るのみだ (all we can do is pray). のみ is the formal だけ, and ただ in front strengthens it.""",
  r"のみ(?:だ|です|である)?", "あとはただ結果を待つのみだ。", after="any", req=r"ただ")
P("tada_de_sae", "ただでさえ", "even at the best of times", "ただでさえ ...",
  """ただでさえ means "even normally (and now more so)": ただでさえ忙しいのに、仕事が増えた.""",
  r"ただでさえ", "ただでさえ忙しいのに、仕事が増えた。")
P("dani", "〜だに", "even (just)", "Noun / Verb + だに",
  """だに is a literary "even": 想像するだに恐ろしい (frightening even to imagine).""",
  # 予想だに / 想像するだに / 微動だに, not だ + に (盗んだに違いない, 今だに)
  r"だに", "想像するだに恐ろしい。", after="any",
  check=lambda t, i, k: i > 0 and (t[i - 1].lemma in ("予想", "想像", "微動", "夢", "考える", "聞く", "思う", "為る")
                                   or t[i - 1].s.endswith(("する", "える", "く"))))
P("tari_tomo", "〜たりとも", "not even (one)", "One + counter + たりとも",
  """たりとも + negative means "not even (one)": 一円たりとも無駄にできない (I can't waste even a single yen). It follows the smallest unit (一円, 一日, 一人) to stress that none at all is allowed.""",
  r"たりとも", "一円たりとも無駄にはできない。", after="any")
P("taru", "〜たる", "as a (proper)", "Noun + たる + Noun",
  """たる is a formal "being (as one should be)": 教師たる者 (anyone who is a teacher).""",
  r"(?<!最)たる(?=者|もの)", "教師たる者、学生の手本にならなければならない。", after="n",
  # not 飢えたる者 (classical verb form, tagged as a noun), 最たるもの
  check=lambda t, i, k: i > 0 and t[i - 1].p1 == "名詞" and t[i - 1].s not in ("飢え", "渇き", "生き", "死せ"))
P("de_are", "〜であれ", "whatever, even if", "Noun + であれ",
  """であれ means "whoever / whatever it is": 誰であれ、規則は守るべきだ (whoever you are, you should follow the rules). Repeated, AであれBであれ means "whether A or B". であろうと is a close variant.""",
  # not であれが (de + あれ "that"), 誠実であろうとはしてる (try to be)
  r"であれ(?![ばがをはも])|であろうと(?!は|し|す)", "誰であれ、規則は守るべきだ。", after="any")
P("te_kara_to_iu_mono", "〜てからというもの", "ever since", "Verb (て) + からというもの",
  """てからというもの means "ever since (a big change)": 子供が生まれてからというもの、生活が一変した.""",
  r"[てで]からというもの", "子供が生まれてからというもの、生活が一変した。", pre="v")
P("te_shikaru_beki", "〜てしかるべき", "ought to (naturally)", "Verb (て) + しかるべきだ",
  """てしかるべき means "it would be appropriate to": 謝ってしかるべきだ (he ought to apologize).""",
  r"[てで](?:しかる|然る)べき", "彼は謝ってしかるべきだ。", pre="v")
P("te_yamanai", "〜てやまない", "never stop (wishing)", "Verb (て) + やまない",
  """てやまない expresses a lasting wish: ご成功を願ってやみません (I sincerely wish you success).""",
  r"[てで](?:やま|止ま)(?:ない|ず|ぬ)|[てで]やみません", "皆様のご健康を願ってやみません。", pre="v")
P("te_wa_kanawanai", "〜てはかなわない", "can't stand", "Verb / adj (て) + はかなわない",
  """てはかなわない means "it's too much to bear": こう暑くてはかなわない (I can't stand this heat). It complains about a situation continuing; the casual form is ちゃかなわない.""",
  r"[てで]は(?:かなわ|敵わ)(?:ない|ん)|ちゃかなわない", "こう暑くてはかなわない。", pre="va")
P("to_aimatte", "〜と相まって", "combined with", "Noun + と相まって",
  """と相まって (あいまって) means "combined with, together with": 才能と努力が相まって、成功した (talent combined with hard work led to success). Two factors reinforce each other to produce the result.""",
  r"(?:相|あい)まって", "才能と努力が相まって、彼は成功した。", after="any", req=r"と")
P("to_atte", "〜とあって", "because (special situation)", "Noun / plain form + とあって",
  """とあって gives a special reason: 連休とあって、どこも混んでいる (it's a long weekend, so everywhere is crowded).""",
  r"とあって(?![いる])", "連休とあって、どこも混んでいる。", after="any")  # 靴とあっている = matches
P("to_areba", "〜とあれば", "if (it's for)", "Noun / plain form + とあれば",
  """とあれば means "if it's (for this special reason)": 子供のためとあれば、何でもする.""",
  r"とあれば", "子供のためとあれば、何でもします。", after="any")
P("to_ii_to_ii", "〜といい〜といい", "both ... and ...", "Noun + といい + Noun + といい",
  """AといいBといい evaluates two aspects: 味といい値段といい、申し分ない (both taste and price are perfect).""",
  r"といい(?=[^、。]{1,10}といい)", "味といい値段といい、申し分ない。", after="n")
P("to_iedomo", "〜といえども", "even though, even", "Noun / plain form + といえども",
  """といえども means "even (someone/something like X), although": 子供といえども、ルールは守るべきだ (even children should follow the rules). It is formal; casual speech would use でも or からといって.""",
  r"と(?:いえ|言え)ども", "子供といえども、ルールは守るべきだ。", after="any")
P("to_ittara_nai", "〜といったらない", "indescribably", "Adj / Noun + といったらない",
  """といったらない means "beyond words, indescribably": その時の嬉しさといったらなかった (my joy at that moment was beyond words). It follows a noun of feeling or quality, often ending in さ.""",
  r"と(?:いっ|言っ)たら(?:ない|なかった|ありゃしない)", "その時の嬉しさといったらなかった。", after="any")
P("to_kitara", "〜ときたら", "when it comes to (complaint)", "Noun + ときたら",
  """ときたら introduces a topic you complain about: うちの息子ときたら、遊んでばかりだ.""",
  r"ときたら", "うちの息子ときたら、遊んでばかりいる。", after="n")
P("tokoro_wo", "〜ところを", "while (you are) ...", "Plain form + ところを",
  """ところを is used politely about inconvenience: お忙しいところをすみません (sorry to bother you when you're
  busy).""",
  r"ところを(?=、|すみ|申し訳|ありがと|恐縮|わざわざ|お邪魔|失礼|ご|お)", "お忙しいところを、ありがとうございます。", after="any")
P("to_wa_surprise", "〜とは (surprise)", "who would have thought", "Plain form + とは",
  """Sentence-final とは shows surprise: まさか彼が犯人だったとは (who'd have thought he was the culprit!).""",
  r"とは(?=[。！]|！)", "まさか彼が犯人だったとは。", after="any")
P("to_bakari_ni", "〜とばかりに", "as if to say", "Quote + とばかりに",
  """とばかりに means "as if to say": 待ってましたとばかりに飛びついた (he jumped at it as if to say "I've been waiting for this"). It describes someone's attitude, not actual words.""",
  # とばかりに / とばかりの (as if to say), not とばかり思っていた (was sure that) or 〜のことばかり
  r"とばかり(?:に|の)", "彼は待ってましたとばかりに飛びついた。", after="any")
P("tomo_naru_to", "〜ともなると", "once it comes to (a higher level)", "Noun + ともなると",
  """ともなると means "when it comes to (that level)": 大学生ともなると、自分で考えなければならない.""",
  r"とも(?:なると|なれば)", "大学生ともなると、自分で考えなければならない。", after="n")
P("nai_made_mo", "〜ないまでも", "even if not", "Verb (ない) + までも",
  """ないまでも means "even if not (fully), at least": 毎日とは言わないまでも、週に一度は運動したい (if not every day, I want to exercise at least once a week). The second part gives a lower but still meaningful level.""",
  r"ないまでも", "毎日とは言わないまでも、週に一度は運動したい。", pre="va?")
P("nagara_ni", "〜ながらに", "while, as (from the start)", "Noun / verb stem + ながらに",
  """ながらに means "while still / since": 生まれながらに (from birth), 涙ながらに (in tears).""",
  r"ながら(?:に|の)", "彼女は涙ながらに話した。", after="any")
P("naku_shite", "〜なくして", "without", "Noun + なくして(は)",
  """なくして(は) means "without (X, it's impossible)": 努力なくして成功なし (no success without effort). It is formal and usually followed by a negative or by なし.""",
  r"なくして(?:は)?", "努力なくして成功はない。", after="n")
P("nashi_ni", "〜なしに", "without", "Noun + なしに",
  """なしに means "without": 許可なしに入ってはいけない (don't enter without permission).""",
  r"なし(?:に|では|で)", "許可なしに入ってはいけません。", after="n")
P("nara_dewa", "〜ならでは", "unique to, only (a ...) could", "Noun + ならでは",
  """ならでは means "only possible for": 京都ならではの景色 (scenery unique to Kyoto).""",
  r"ならでは(?:の)?", "これは京都ならではの景色です。", after="n")
P("nari", "〜なり", "as soon as", "Verb (dictionary) + なり",
  """なり means "the moment (and then something unexpected)": 部屋に入るなり、泣き出した.""",
  r"なり(?=、)", "彼女は部屋に入るなり、泣き出した。", after="v", check=first_pos("助詞"),
  neg=r"なり[^。]*なり")  # 煮るなり焼くなり = either ... or
P("nari_ni", "〜なりに", "in one's own way", "Noun / plain form + なりに",
  """なりに means "in one's own way (within limits)": 私なりに頑張った (I did my best in my own way).""",
  r"(?<!道)(?<!言い)なり(?:に|の)", "私なりに頑張ってみました。", after="any", check=first_pos("接尾辞"))  # 道なり, 言いなり
P("ni_atai_suru", "〜に値する", "be worth", "Noun / Verb + に値する",
  """に値する (あたいする) means "deserve": 尊敬に値する人 (a person worthy of respect).""",
  r"に(?:値|あたい)(?:する|しない|します)", "彼は尊敬に値する人物だ。", after="nv")
P("ni_atte", "〜にあって", "in (a situation)", "Noun + にあって",
  """にあって means "being in (a special situation or position)": 非常時にあって、冷静さを保つ (keep calm in an emergency). It is formal; にあっては and にあっても add contrast.""",
  r"にあって(?:は|も)?", "困難な状況にあって、彼は冷静だった。", after="n",
  # being in a situation or position, not 雨にあう (遭う, caught in), 近くにある, 君に会って
  check=lambda t, i, k: i > 0 and (t[i - 1].lemma in SITUATIONS or t[i - 1].s.endswith(("時", "下", "中", "期", "代"))))
P("ni_kakawaru", "〜にかかわる", "affect, concerning (serious)", "Noun + にかかわる",
  """にかかわる means "be related to / affect (something serious)": 命にかかわる病気.""",
  r"に(?:かかわ|関わ|係わ)(?:る|り(?!の|合|あ))", "これは命にかかわる問題だ。", after="n")  # not the noun 関わり
P("ni_kataku_nai", "〜に難くない", "it's not hard to", "Noun / Verb + に難くない",
  """に難くない (かたくない) means "it is not hard to": 想像に難くない (it's easy to imagine). It is used with a few verbs of understanding: 想像, 理解, 察する.""",
  r"に(?:難|かた)くない", "彼の苦労は想像に難くない。", after="nv")
P("ni_soku_shite", "〜に即して", "in accordance with", "Noun + に即して",
  """に即して (そくして) means "in line with (facts, rules, reality)": 事実に即して判断する (judge based on the facts). Before a noun it becomes に即した: 現実に即した計画.""",
  r"に(?:即|則)(?:して|した|し)", "事実に即して判断すべきだ。", after="n")
P("ni_taeru", "〜に堪える / 堪えない", "worth; unbearable", "Noun / Verb + に堪える",
  """に堪える (たえる) means "worthy of" (鑑賞に堪える); に堪えない means "can't bear" (見るに堪えない).""",
  r"に(?:堪|耐|た)え(?:る|ない|ません)", "その映像は見るに堪えないものだった。", after="nv")
P("ni_taru", "〜に足る", "worthy of, enough to", "Noun / Verb + に足る",
  """に足る (たる) means "worthy of, sufficient for": 信頼するに足る人物 (a person worthy of trust). It is formal; the negative is に足りない: 取るに足りない (trivial).""",
  r"に(?:足|た)(?:る|りる|らない)", "彼は信頼するに足る人物だ。", after="nv")
P("ni_hikikae", "〜にひきかえ", "in contrast to", "Noun + にひきかえ",
  """にひきかえ means "in (sharp) contrast to": 兄にひきかえ、弟はよく勉強する (unlike his older brother, the younger one studies hard). It often carries the speaker's judgment of one side.""",
  r"に(?:ひきかえ|引き換え|引き替え)", "兄にひきかえ、弟はよく勉強する。", after="any")
P("ni_mo_mashite", "〜にもまして", "even more than", "Noun + にもまして",
  """にもまして means "even more than": 以前にもまして元気になった (he's even healthier than before). 何にもまして means "above all else".""",
  r"にもまして|にも増して", "以前にもまして元気になった。", after="n")
P("no_itari", "〜の至り", "the height of", "Noun + の至り",
  """の至り (いたり) means "the utmost": 光栄の至りです (it is the greatest honor).""",
  r"の(?:至|いた)り", "このような賞をいただき、光栄の至りです。", after="n")
P("no_kiwami", "〜の極み", "the height of", "Noun + の極み",
  """の極み (きわみ) means "the peak, the height of": 贅沢の極み (the height of luxury). It is formal and also used for emotions: 感激の極み (overwhelmed with emotion).""",
  r"の(?:極|きわ)み", "これは贅沢の極みだ。", after="n")
P("wa_oroka", "〜はおろか", "let alone", "Noun + はおろか",
  """はおろか means "let alone, not to mention": 漢字はおろか、ひらがなも読めない (he can't even read hiragana, let alone kanji). The second part usually has も or さえ and a negative.""",
  r"はおろか", "漢字はおろか、ひらがなも読めない。", after="n")
P("ba_koso", "〜ばこそ", "precisely because", "Verb (ば) + こそ",
  """ばこそ stresses that something is precisely the reason: あなたのことを思えばこそ、注意するのです (it's precisely because I care about you that I warn you). It is a formal からこそ.""",
  r"ばこそ", "あなたのことを思えばこそ、注意するのです。", pre="va")
P("ba_sore_made", "〜ばそれまでだ", "if ..., that's the end of it", "Verb (ば) + それまでだ",
  """ばそれまでだ means "if that happens, it's all over": 死んでしまえばそれまでだ (once you're dead, that's the end of it). It stresses that all effort becomes pointless in that case.""",
  r"ばそれまで(?:だ|です)?", "どんなにお金があっても、死んでしまえばそれまでだ。", pre="v")
P("bekarazu", "〜べからず", "must not (signs)", "Verb (dictionary) + べからず",
  """べからず is a prohibition on signs: 芝生に入るべからず (keep off the grass).""",
  r"べから(?:ず|ざる)", "芝生に入るべからず。", after="v")
P("beku", "〜べく", "in order to", "Verb (dictionary) + べく",
  """べく is a written "in order to": 夢を実現すべく、努力を続けている (I keep working hard to make my dream come true). する becomes すべく; it isn't used for requests or commands.""",
  r"べく(?!も)", "夢を実現すべく、努力を続けている。", after="v")
P("beku_mo_nai", "〜べくもない", "can't possibly", "Verb (dictionary) + べくもない",
  """べくもない means "there's no way to": 知るべくもない (there's no way to know).""",
  r"べくもない", "そんなことは知るべくもない。", after="v")
P("majiki", "〜まじき", "should not (unacceptable)", "Verb + まじき + Noun",
  """まじき condemns behavior as unacceptable for someone in a role: 教師にあるまじき行為 (behavior unbecoming of a teacher). It usually appears as 〜にあるまじき + noun.""",
  r"まじき", "それは教師にあるまじき行為だ。", after="v")
P("made_da", "〜までだ", "will simply (if needed)", "Verb + までだ",
  """までだ means "I'll just (do that)": だめならやめるまでだ (if it doesn't work, I'll just quit).""",
  r"まで(?:だ|です|のことだ)", "反対されたら、一人でやるまでだ。", after="v")
P("mamire", "〜まみれ", "covered in", "Noun + まみれ",
  """まみれ means "covered in (something sticky/dirty)": 汗まみれ (covered in sweat), 泥まみれ.""",
  "", "子供たちは泥まみれになって遊んでいた。", custom=compound("塗れ", "塗れ"))
P("meku", "〜めく", "show signs of", "Noun + めく",
  """めく means "begin to look like": 春めいてきた (it's getting spring-like).""",
  r"め(?:く|いた|いて|き)", "だんだん春めいてきました。", after="n", check=first_pos("接尾辞"))
P("mo_sarukoto_nagara", "〜もさることながら", "not only ... but also", "Noun + もさることながら",
  """もさることながら means "A of course, but even more B": 味もさることながら、見た目も美しい.""",
  r"もさることながら", "味もさることながら、見た目も美しい。", after="n")
P("mono_wo", "〜ものを", "if only (regret)", "Plain form + ものを",
  """ものを expresses regret: 言ってくれればよかったものを (if only you had told me).""",
  r"ものを(?=[。、！])", "言ってくれれば手伝ったものを。", after="va")
P("wo_oite", "〜をおいて", "other than, besides", "Noun + をおいて + negative",
  """をおいて + negative means "apart from (X, there is no one/nothing)": 彼をおいて適任者はいない (there's no one better suited than him). It strongly praises X as the only choice.""",
  r"をおいて|を置いて", "この仕事は彼をおいて適任者はいない。", after="n", req=NEG)
P("wo_kagiri_ni", "〜を限りに", "as of, from ... on (no more)", "Noun + を限りに",
  """を限りに means "as of (and no longer)": 今日を限りに、タバコをやめる (as of today, I quit smoking). It marks the last time something happens.""",
  r"を(?:限|かぎ)りに", "今日を限りに、タバコをやめます。", after="n")
P("wo_kawakiri_ni", "〜を皮切りに", "starting with", "Noun + を皮切りに",
  """を皮切りに (かわきりに) means "starting with (and then many more)": 東京を皮切りに全国でコンサートを行う.""",
  r"を(?:皮切|かわき)りに", "東京を皮切りに、全国でコンサートを行う。", after="n")
P("wo_kinjienai", "〜を禁じ得ない", "can't help feeling", "Noun + を禁じ得ない",
  """を禁じ得ない (きんじえない) means "can't suppress (a feeling)": 怒りを禁じ得ない.""",
  r"を禁じ(?:得|え)(?:ない|ません|なかった)", "その知らせに、驚きを禁じ得なかった。", after="n")
P("wo_kanete", "〜を兼ねて", "also serving as", "Noun + を兼ねて",
  """を兼ねて (かねて) means "combined with (another purpose)": 趣味と実益を兼ねて.""",
  r"を(?:兼|か)ね(?:て)?", "運動を兼ねて、毎日歩いて通勤している。", after="n")
P("wo_fumaete", "〜を踏まえて", "based on, considering", "Noun + を踏まえて",
  """を踏まえて (ふまえて) means "taking into account, based on": 調査結果を踏まえて、計画を立てる (make a plan based on the survey results). It is common in business and formal writing.""",
  r"を(?:踏|ふ)まえ(?:て|た)?", "調査の結果を踏まえて、計画を立てる。", after="n")
P("wo_motte", "〜をもって", "with, by means of; as of", "Noun + をもって",
  """をもって is formal "with / by" or "as of": 本日をもって閉店いたします (we close as of today).""",
  r"をもって|を以て|を持って(?=閉|終|退|最)", "本日をもって閉店いたします。", after="n")
P("wo_monotomosezu", "〜をものともせず", "in defiance of", "Noun + をものともせず",
  """をものともせず means "undaunted by, in defiance of": 雨をものともせず、試合は続けられた (the game went on undeterred by the rain). It praises someone overcoming a difficulty.""",
  r"をものともせず", "彼は怪我をものともせず、最後まで戦った。", after="n")
P("wo_yoginaku", "〜を余儀なくされる", "be forced to", "Noun + を余儀なくされる",
  """を余儀なくされる (よぎなく) means "be forced to (by circumstances)": 計画は中止を余儀なくされた (the plan was forced to be cancelled). The active を余儀なくさせる means "force someone to".""",
  r"を余儀なく(?:され|させ)", "雨のため、試合は中止を余儀なくされた。", after="n", tail=True)
P("wo_yoso_ni", "〜をよそに", "ignoring, regardless of", "Noun + をよそに",
  """をよそに means "ignoring, paying no heed to": 親の心配をよそに、彼は旅に出た (ignoring his parents' worries, he set off on a journey). It is usually about other people's feelings or warnings.""",
  r"をよそに", "親の心配をよそに、彼は一人で旅に出た。", after="n")
P("n_ga_tame", "〜んがため", "in order to", "Verb (ない-stem) + んがため",
  """んがため is a literary "for the sake of": 勝たんがため (in order to win).""",
  r"んがため(?:に|の)?", "勝たんがために、彼は毎日練習した。", pre="v?")
P("n_bakari", "〜んばかり", "as if about to", "Verb (ない-stem) + んばかり",
  """んばかり means "almost, as if about to": 泣かんばかりの顔 (a face on the verge of tears).""",
  r"んばかり(?:に|の|だ)?", "彼女は泣かんばかりの顔をしていた。", pre="v")
P("yue", "〜ゆえ(に)", "because of (literary)", "Noun / plain form + ゆえに",
  """ゆえ (故) is a literary "because": 若さゆえの過ち (a mistake of youth).""",
  r"(?:ゆえ|故)(?:に|の)?", "若さゆえの過ちだった。", after="any", check=lambda t, i, k: t[i].kana == "ゆえ")
P("sura", "〜すら", "even", "Noun + (で)すら",
  """すら is a literary さえ ("even"): 名前すら知らない (I don't even know his name). After a person or place it often becomes ですら; it usually goes with a negative.""",
  r"(?:で)?すら", "彼は自分の名前すら書けない。", after="n")
P("ikani", "いかに", "how (ever)", "いかに ...",
  """いかに is a formal "how": いかに大切か (how important it is), いかに努力しても.""",
  r"いかに", "健康がいかに大切か、病気になって分かった。")
P("tomo_arou", "〜ともあろう", "someone (of such standing)", "Noun + ともあろう + Noun",
  """ともあろう criticizes someone who should know better given their position: 大臣ともあろう人が、そんなことを言うなんて (to think that a minister would say such a thing). It is followed by 人 or 者.""",
  r"ともあろう", "大臣ともあろう人が、そんなことを言うなんて。", after="n")
P("beshi", "〜べし", "should (literary)", "Verb + べし",
  """べし is a classical "should, must", seen in mottos and written rules: 学生は勉強すべし (students must study). する becomes すべし; the attributive form is べき.""",
  r"べし", "若者は大いに学ぶべし。", after="v")
P("zu_tomo", "〜ずとも", "even without", "Verb (ない-stem) + ずとも",
  """ずとも means "even if not": 言わずとも分かる (I understand without you saying it).""",
  r"ずとも", "言わずとも分かっている。", pre="v")
P("made_shite", "〜までして", "even going so far as", "Noun / Verb + までして",
  """までして means "going so far as (doing something extreme)": 借金までして車を買った (he even went into debt to buy a car). It often implies the speaker disapproves.""",
  r"までして", "借金までして、車を買う必要はない。", after="nv")
P("nai_dewa_sumanai", "〜ないではすまない", "can't get away without", "Verb (ない) + ではすまない",
  """ないではすまない means you must do it to settle the matter: 謝らないではすまない.""",
  r"ないでは(?:すま|済ま)(?:ない|ぬ)", "これは謝らないではすまないだろう。", pre="v")
P("ni_todomarazu", "〜にとどまらず", "not limited to", "Noun + にとどまらず",
  """にとどまらず means "not stopping at, not limited to": 国内にとどまらず、海外でも人気がある (it's popular not only in Japan but abroad too). It describes something spreading beyond a scope.""",
  r"に(?:とどま|留ま)らず", "その歌は国内にとどまらず、海外でも人気がある。", after="n")
P("nomi_narazu", "〜のみならず", "not only", "Noun / plain form + のみならず",
  """のみならず is a formal "not only (but also)": 日本のみならず、世界中で問題になっている (it's a problem not only in Japan but around the world). Casual equivalent: だけでなく.""",
  r"のみならず", "この問題は日本のみならず、世界中で起きている。", after="any")
P("kai", "〜甲斐がある", "worth it, rewarding", "Verb + 甲斐がある",
  """甲斐 (かい) means "worth": 頑張った甲斐があった (it was worth the effort). 甲斐がない = in vain.""",
  r"(?:甲斐|かい)が(?:ある|あっ|ない|なかっ)", "頑張った甲斐があった。", after="any", tail=True)
P("you_ga", "〜ようが / 〜ようと", "no matter (what/how)", "Verb (volitional) + が / と",
  """ようが / ようと mean "no matter": 何を言われようが、気にしない (no matter what people say, I don't care).""",
  "", "誰が何と言おうと、私は行く。", custom=m_you_ga)
