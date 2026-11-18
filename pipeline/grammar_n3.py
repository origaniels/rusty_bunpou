"""N3 grammar points (original explanations; `ex` sentences are only used by the tests)."""
import re

from grammar_n4 import _volitional
from patterns import ARU, NARU, SURU, _tail, first_lemma, first_pos, point, prev_is, prev_not


def compound(noun_suffix, suffix_lemma):
    """Match a compound noun ending in `noun_suffix` (読みかけ, 焼きたて) or verb stem + suffix token."""
    def m(toks):
        out = []
        for j, t in enumerate(toks):
            if t.p1 == "名詞" and t.lemma.endswith(noun_suffix) and len(t.s) > 2:
                out.append((j, j + 1, None))
            elif t.lemma == suffix_lemma and j > 0 and toks[j - 1].p1 == "動詞" and toks[j - 1].cf.startswith("連用形"):
                out.append((j - 1, j + 1, j - 1))
        return out
    return m


def m_you_to_suru(toks):
    out = []
    for a, b, h in _volitional(toks):
        if b + 1 < len(toks) and toks[b].s == "と" and toks[b + 1].lemma == "為る":
            out.append((a, _tail(toks, b + 2), h))
    return out


def P(*a, **k):
    point("N3", *a, **k)


NEG = r"(?:ない|ません|なかった|ず|ぬ)"

# ---------------------------------------------------------------- attempts, decisions, rules
P("you_to_suru", "〜ようとする", "try to; be about to", "Verb (volitional) + とする",
  """Volitional + とする means trying to do something, or being just about to: 出かけようとした時、電話が
  鳴った (just as I was about to leave, the phone rang). ようとしない = won't even try.""",
  "", "ドアを開けようとしましたが、開きませんでした。", custom=m_you_to_suru)
P("koto_ni_shite_iru", "〜ことにしている", "make it a rule to", "Verb (dictionary / ない) + ことにしている",
  """ことにしている describes a personal rule or habit you decided on: 夜は甘いものを食べないことにしている
  (I make it a rule not to eat sweets at night).""",
  r"ことにして(?:いる|い|おり)", "毎朝走ることにしています。", after="v", tail=True)
P("koto_ni_natte_iru", "〜ことになっている", "it's arranged / the rule is that", "Verb + ことになっている",
  """ことになっている describes an arrangement or rule set by others: ここでは靴を脱ぐことになっている
  (the rule is that you take your shoes off here).""",
  # 困ったことになっている = be in trouble
  r"(?<!困った)(?<!面倒な)(?<!大変な)(?<!厄介な)ことになって(?:いる|い|おり)", "会議は三時に始まることになっています。",
  after="v", tail=True)
P("koto_wa_nai", "〜ことはない", "there's no need to", "Verb (dictionary) + ことはない",
  """ことはない means "there's no need to": 心配することはない (there's nothing to worry about).""",
  r"ことは(?:ない|ありません)", "そんなに心配することはありません。", after="v",
  check=lambda t, i, k: i > 0 and t[i - 1].lemma != "た")  # たことはない = have never
P("koto_da", "〜ことだ (advice)", "should, the best thing is", "Verb (dictionary / ない) + ことだ",
  """ことだ gives advice, often from someone with experience: 上手になりたければ、毎日練習することだ
  (if you want to improve, practise every day).""",
  r"ことだ(?=[。！])", "合格したければ、毎日勉強することだ。", after="v",
  # advice, not "X is (a) thing that ...": 盗むのはいけないことだ, ということだ, たことだ
  check=lambda t, i, k: i > 0 and t[i - 1].lemma not in ("た", "だ", "言う", "いう")
  and not re.search(r"のは|という|と言う", "".join(x.s for x in t)))
P("beki", "〜べき", "should, ought to", "Verb (dictionary) + べきだ",
  """べき expresses what is right or expected: 約束は守るべきだ (you should keep your promises).
  する becomes するべき or すべき. べきではない = shouldn't.""",
  r"べき(?:だ|です|では|じゃ|だった|でした)?", "約束は守るべきです。", after="v")
P("shika_nai", "〜しかない", "have no choice but to", "Verb (dictionary) + しかない",
  """Dictionary form + しかない means there's only one option left: 歩いて帰るしかない (there's nothing for
  it but to walk home).""",
  r"(?<!で)しか(?:ない|ありません)", "終電がないので、歩いて帰るしかない。", after="v")  # でしかない = is merely
P("you_ga_nai", "〜ようがない", "there's no way to", "Verb stem + ようがない",
  """Verb stem + ようがない means it's impossible to do because there's no means: 連絡先が分からないので、
  連絡しようがない (I don't know his address, so there's no way to contact him).""",
  r"ようが(?:ない|ありません)", "住所が分からないので連絡しようがない。", pre="v?")

# ---------------------------------------------------------------- explanations & reasoning
P("wake_da", "〜わけだ", "that's why; no wonder", "Plain form + わけだ",
  """わけだ draws a logical conclusion: 一日中働いたんだから、疲れるわけだ (you worked all day, so no
  wonder you're tired).""",
  r"わけ(?:だ|です)", "一日中働いたのだから、疲れるわけだ。", after="nva")
P("wake_dewa_nai", "〜わけではない", "it doesn't mean that, not necessarily", "Plain form + わけではない",
  """わけではない denies a conclusion someone might draw: 嫌いなわけではない (it's not that I dislike it).""",
  r"わけで(?:は|も)(?:ない|ありません)|わけじゃない", "肉が嫌いなわけではありません。", after="nva")
P("wake_ga_nai", "〜わけがない", "there's no way that", "Plain form + わけがない",
  """わけがない strongly denies a possibility: 彼が嘘をつくわけがない (there's no way he'd lie).""",
  r"わけ(?:が|は)(?:ない|ありません)", "彼がそんなことを言うわけがない。", after="nva")
P("wake_ni_wa_ikanai", "〜わけにはいかない", "can't (for social/moral reasons)", "Verb + わけにはいかない",
  """わけにはいかない means you can't do something because it wouldn't be right: 明日は試験だから、
  遊んでいるわけにはいかない (I have an exam tomorrow, so I can't goof around).""",
  r"わけにはいか(?:ない|ず|ん|なかった)", "明日は試験なので、遊んでいるわけにはいかない。", after="v")
P("hazu_ga_nai", "〜はずがない", "can't be, there's no way", "Plain form + はずがない",
  """はずがない means something is impossible given the facts: 彼が知らないはずがない (he can't not know).""",
  r"はずが(?:ない|ありません)", "彼がそれを知らないはずがない。", after="nva")
P("ni_chigainai", "〜に違いない", "must be, no doubt", "Plain form / Noun + に違いない",
  """に違いない expresses strong conviction: 犯人はあの男に違いない (the culprit must be that man).""",
  r"に(?:違い|ちがい)(?:ない|ありません)", "犯人はあの男に違いない。", after="nva")
P("ni_kimatte_iru", "〜に決まっている", "certainly, bound to", "Plain form / Noun + に決まっている",
  """に決まっている is a confident (often subjective) "of course": そんなの嘘に決まっている (that's obviously a lie).""",
  r"に(?:決|き)まって(?:いる|い|る)", "そんなの嘘に決まっている。", after="nva", tail=True)
P("osore_ga_aru", "〜おそれがある", "there's a risk that", "Verb (dictionary) / Noun + の + おそれがある",
  """おそれがある warns of a bad possibility, typical of news: 台風が上陸するおそれがある (there's a risk the
  typhoon will make landfall).""",
  r"(?:恐れ|おそれ)が" + ARU, "大雨で川があふれるおそれがあります。", after="nv", tail=True)
P("mono_da", "〜ものだ", "used to; it's natural that", "Plain form + ものだ",
  """ものだ states a general truth (人は変わるものだ, people change) or, with た, fond memories:
  子供のころよくここで遊んだものだ (I often used to play here as a child).""",
  r"ものだ|もんだ", "子供のころは、よくこの川で泳いだものだ。", after="va")
P("you_na", "〜ような / 〜のような", "like, such as", "Noun + の + ような",
  """ような compares or gives an example: 夢のような話 (a dreamlike story), 日本のような国 (countries like
  Japan). Before verbs it becomes ように.""",
  r"(?:の)?ような", "まるで夢のような話です。", after="any", check=lambda t, i, k: any(x.lemma == "様" for x in t[i:k]))
P("rashii_typical", "〜らしい (typical)", "typical of, like a true", "Noun + らしい",
  """らしい after a noun means "typical of, befitting": 男らしい (manly), 春らしい天気 (real spring weather).""",
  r"らし(?:い|く|かっ|さ)", "今日は春らしい天気ですね。", after="n", check=first_pos("接尾辞"))
P("ppoi", "〜っぽい", "-ish, tends to", "Noun / verb stem / adj stem + っぽい",
  """っぽい means "-ish" or "tends to": 子供っぽい (childish), 忘れっぽい (forgetful), 白っぽい (whitish).""",
  r"っぽ(?:い|く|かっ)", "彼はちょっと子供っぽいところがある。", after="any")
P("okage_de", "〜おかげで", "thanks to", "Noun + の / plain form + おかげで",
  """おかげで gives a positive cause: 先生のおかげで合格できた (thanks to my teacher, I passed).""",
  r"おかげ(?:で|だ|です)", "先生のおかげで合格できました。", after="any")
P("sei_de", "〜せいで", "because of (blame)", "Noun + の / plain form + せいで",
  """せいで gives a cause you blame: 雨のせいで試合が中止になった (the game was cancelled because of the rain).""",
  r"せい(?:で|だ|です|か)", "雨のせいで試合が中止になった。", after="any", check=first_lemma("所為"))
P("kuse_ni", "〜くせに", "even though (critical)", "Plain form / Noun + の + くせに",
  """くせに is a critical "even though": 知っているくせに教えてくれない (he knows, yet won't tell me).""",
  r"くせに|癖に", "知っているくせに教えてくれない。", after="any")
P("noni_wish", "〜ばいい / 〜たらいい", "it would be good if, should", "Verb (ば / たら) + いい",
  """ばいい / たらいい suggest what to do: どうすればいいですか (what should I do?).""",
  r"(?:ば|たら)(?:いい|良い|よい)", "どうすればいいですか。", pre="va")

# ---------------------------------------------------------------- relations (に〜て family)
P("to_shite", "〜として", "as (in the role of)", "Noun + として",
  """として means "as, in the capacity of": 通訳として働く (work as an interpreter).""",
  r"として(?:は|も|の)?", "彼は通訳として働いています。", after="n")
P("ni_totte", "〜にとって", "for, to (someone's view)", "Noun + にとって",
  """にとって shows whose point of view: 私にとって家族が一番大切だ (for me, family matters most).""",
  r"にとって(?:は|も|の)?", "私にとって家族が一番大切です。", after="n")
P("ni_yotte", "〜によって / による", "by, depending on, due to", "Noun + によって",
  """によって marks the agent (in passives), a means, a cause, or variation: 国によって習慣が違う (customs
  differ depending on the country).""",
  r"によって|による|により", "国によって習慣が違います。", after="n")
P("ni_yoru_to", "〜によると", "according to", "Noun + によると / によれば",
  """によると gives the source of information: 天気予報によると明日は雨だ (according to the forecast, it'll
  rain tomorrow).""",
  r"によると|によれば", "天気予報によると明日は雨だそうです。", after="n")
P("ni_taishite", "〜に対して", "toward; in contrast to", "Noun + に対して",
  """に対して means "toward / against" (先生に対して失礼だ, rude toward the teacher) or "in contrast to".""",
  r"に(?:対|たい)(?:して|する|し)", "先生に対して失礼なことを言ってはいけない。", after="n")
P("ni_kanshite", "〜に関して", "regarding, concerning", "Noun + に関して",
  """に関して is a more formal について: この件に関して質問がある (I have a question regarding this matter).""",
  r"に(?:関|かん)(?:して|する|し)", "この件に関して質問があります。", after="n")
P("ni_kurabete", "〜に比べて", "compared to", "Noun + に比べて",
  """に比べて means "compared with": 去年に比べて今年は暖かい (this year is warmer compared to last year).""",
  r"に(?:比|くら)べ(?:て|る|ると)?", "去年に比べて今年は暖かいです。", after="n")
P("ni_shitagatte", "〜に従って", "as (A changes, B changes); following", "Noun / Verb + に従って",
  """に従って means "in accordance with" or "as ... so ...": 年をとるに従って体が弱くなる (as you age, your
  body weakens).""",
  # in kana, にしたがっている is almost always に + したがる (医者にしたがっている, wants to make him a
  # doctor), which the tagger also reads as 従う; 従っている in kanji is fine
  r"に(?:従(?:って|い)|したが(?:って(?!い)|い))", "年をとるに従って、体が弱くなる。", after="nv")
P("ni_tsurete", "〜につれて", "as (gradually)", "Verb (dictionary) / Noun + につれて",
  """につれて describes two things changing together: 時間がたつにつれて、悲しみも薄れた (as time passed,
  the sadness faded too).""",
  r"につれ(?:て)?", "時間がたつにつれて、悲しみも薄れていった。", after="nv")
P("ni_shite_wa", "〜にしては", "for (considering)", "Noun / plain form + にしては",
  """にしては says something is unexpected given a standard: 子供にしては上手だ (pretty good, for a child).""",
  r"にしては", "初めてにしては上手ですね。", after="any")
P("ni_shite_mo", "〜にしても", "even if, even granting", "Noun / plain form + にしても",
  """にしても concedes a point: 忙しいにしても電話くらいできるだろう (even if you're busy, you could at least
  call).""",
  r"にしても", "忙しいにしても、電話ぐらいできるでしょう。", after="nva")
P("wo_chuushin_ni", "〜を中心に", "centered on, focusing on", "Noun + を中心に",
  """を中心に means "centered on": 駅を中心に町が広がっている (the town spreads out around the station).""",
  r"を中心(?:に|として|と)", "駅を中心に町が広がっています。", after="n")
P("to_tomo_ni", "〜とともに", "together with; as", "Noun / Verb + とともに",
  """とともに means "together with" (家族とともに暮らす) or "as/along with" a change (時代とともに).""",
  r"と(?:とも|共)に", "家族とともに暮らしています。", after="nv")

# ---------------------------------------------------------------- emphasis & limitation
P("dake_de_naku", "〜だけでなく", "not only ... but also", "Noun / plain form + だけでなく",
  """だけでなく / ばかりでなく means "not only": 英語だけでなく、中国語も話せる (he speaks not only English but
  Chinese too).""",
  r"(?:だけ|ばかり)(?:で|じゃ)なく(?:て)?", "彼は英語だけでなく、中国語も話せます。", after="nva")
P("bakari_only", "〜ばかり (nothing but)", "nothing but, only", "Noun / Verb (て) + ばかり",
  """ばかり after a noun means "nothing but": 肉ばかり食べる (eat nothing but meat). てばかりいる describes
  doing something all the time: 寝てばかりいる.""",
  r"ばかり", "弟はゲームばかりしている。", after="n", neg=r"たばかり|だばかり|ばかりか|ばかりに|ばかりで")
P("te_bakari", "〜てばかりいる", "do nothing but", "Verb (て-form) + ばかりいる",
  """てばかりいる complains that someone does nothing but one thing: 寝てばかりいる (does nothing but sleep).""",
  r"[てで]ばかり(?:いる|い)", "弟は毎日遊んでばかりいる。", pre="v", tail=True)
P("sae", "〜さえ", "even; if only", "Noun + さえ",
  """さえ means "even": 子供でさえ知っている (even a child knows). With ば it means "if only": お金さえあれば
  (if only I had money).""",
  r"(?:で)?さえ", "そんなことは子供でさえ知っている。", after="n")
P("koso", "〜こそ", "precisely, it's ... that", "Noun + こそ",
  """こそ strongly emphasizes: 今度こそ勝つ (this time for sure I'll win), こちらこそ (likewise / it's me who
  should thank you).""",
  r"こそ", "今度こそ勝ちたいです。", after="any")
P("wa_mochiron", "〜はもちろん", "not to mention, of course", "Noun + はもちろん",
  """はもちろん means "A goes without saying, and B too": 英語はもちろん、フランス語も話せる (he speaks French,
  not to mention English). The second part usually contains も.""",
  r"はもちろん|はもちろんのこと", "英語はもちろん、フランス語も話せます。", after="n")
P("dekiru_dake", "できるだけ", "as much as possible", "できるだけ + Verb",
  """できるだけ means "as much as possible": できるだけ早く来てください (please come as soon as possible).""",
  r"できるだけ|出来るだけ", "できるだけ早く来てください。")
P("nakanaka", "なかなか〜ない", "not easily", "なかなか + negative",
  """なかなか with a negative means something doesn't happen easily: バスがなかなか来ない (the bus just won't
  come). With a positive it means "quite": なかなかおいしい.""",
  r"なかなか", "バスがなかなか来ない。", req=r"なかなか.*" + NEG)
P("kesshite", "決して〜ない", "never, by no means", "決して + negative",
  """決して (けっして) + negative is a strong "never": 決して諦めない (I'll never give up).""",
  r"(?:決|けっ)して", "決してあきらめません。", req=NEG)
P("tatoe_temo", "たとえ〜ても", "even if", "たとえ + Verb (て) + も",
  """たとえ emphasizes a following ても: たとえ雨が降っても行く (even if it rains, I'll go).""",
  r"たとえ|例え", "たとえ雨が降っても、行きます。", req=r"(?:ても|でも)")
P("ikura_temo", "いくら〜ても", "no matter how (much)", "いくら + Verb (て) + も",
  """いくら〜ても means "no matter how much": いくら食べても太らない (no matter how much I eat, I don't
  gain weight).""",
  r"いくら", "いくら食べても太らない。", req=r"いくら.*(?:ても|でも)")
P("kiri", "〜きり", "only; since (and no more)", "Noun / Verb (た) + きり",
  """きり means "only" (二人きり, just the two of us) or "since then, never again": 出かけたきり帰ってこない
  (went out and never came back).""",
  r"きり|っきり", "彼は出かけたきり帰ってこない。", after="any", check=first_pos("助詞"))
P("tte", "〜って", "(casual quote / topic)", "Plain form / Noun + って",
  """って is casual for と / という / は: 明日来るって (he says he'll come tomorrow), 田中さんって誰?
  (who's this Tanaka?).""",
  r"って", "彼は明日来るって言っていました。", after="any", check=first_pos("助詞"))
P("kke", "〜っけ", "(trying to remember)", "Plain form + っけ",
  """っけ asks yourself or others to confirm something you've forgotten: 会議は何時だっけ (what time was the
  meeting again?).""",
  r"っけ", "会議は何時だっけ。", after="any")
P("to_wa", "〜とは (definition)", "what is meant by", "Noun + とは",
  """とは introduces a definition: 「愛」とは何か (what is love?). It's a formal というのは.""",
  r"とは", "幸せとは何でしょうか。", after="n", neg=r"とは(?:言|限)")
P("to_iu_no_wa", "〜というのは", "(what is called) ...", "Noun / sentence + というのは",
  """というのは introduces something in order to explain or define it: 「積ん読」というのは、本を買っても読まないことだ ("tsundoku" means buying books and not reading them). It also gives a reason at the start of a sentence: というのは... (the thing is...).""",
  r"というのは|ってのは", "大人になるというのは、責任を持つことだ。", after="any")
P("to_iu_koto", "〜ということ", "the fact that", "Plain form + ということ",
  """ということ turns a sentence into a noun phrase: 彼が結婚したということを知らなかった (I didn't know that he
  had married).""",
  r"ということ", "彼が結婚したということを知りませんでした。", after="any")
P("to_iu_yori", "〜というより", "rather than (say)", "Noun / plain form + というより",
  """というより corrects a description: 涼しいというより寒い (it's not so much cool as cold).""",
  r"というより(?:も)?", "今日は涼しいというより寒い。", after="any")
P("to_itte_mo", "〜といっても", "although I say", "Plain form / Noun + といっても",
  """といっても qualifies what you said: 料理ができるといっても、簡単なものだけだ (I can cook, though only simple
  things).""",
  r"と(?:いっ|言っ)ても", "料理ができるといっても、簡単なものだけです。", after="any")
P("kawari_ni", "〜かわりに", "instead of; in exchange for", "Noun + の / Verb + かわりに",
  """かわりに means "instead of" (父のかわりに行く, go in my father's place) or "in exchange for".""",
  r"(?:かわり|代わり)に", "父のかわりに私が行きます。", after="any")

# ---------------------------------------------------------------- time
P("tabi_ni", "〜たびに", "every time", "Verb (dictionary) / Noun + の + たびに",
  """たびに means "every time": この歌を聞くたびに、母を思い出す (every time I hear this song, I think of
  my mother).""",
  r"(?:たび|度)に", "この歌を聞くたびに母を思い出します。", after="nv", check=lambda t, i, k: t[i].kana in ("たび", "たびに"))
P("totan", "〜たとたん", "the moment, as soon as", "Verb (た) + とたん(に)",
  """たとたん means something happened right as something else did: 家を出たとたん、雨が降り出した (the moment I
  left the house, it started raining).""",
  r"(?:とたん|途端)(?:に)?", "家を出たとたん、雨が降り出した。", pre="v", check=prev_is("た", "だ"))
P("saichuu", "〜最中に", "in the middle of", "Verb (ている) / Noun + の + 最中に",
  """最中 (さいちゅう) means "right in the middle of": 会議の最中に電話が鳴った (the phone rang in the middle
  of the meeting).""",
  r"最中(?:に|だ|です)?", "会議の最中に電話が鳴った。", after="any")
P("nai_uchi_ni", "〜ないうちに", "before (something happens)", "Verb (ない) + うちに",
  """ないうちに means "before something happens": 暗くならないうちに帰ろう (let's go home before it gets dark).""",
  r"ないうちに", "暗くならないうちに帰りましょう。", pre="va")
P("tokoro_de", "ところで", "by the way", "ところで、...",
  """ところで at the start of a sentence changes the subject: ところで、お昼はどうする? (by the way, what
  about lunch?).""",
  r"^ところで", "ところで、昼ご飯はどうしますか。")
P("igai", "〜以外", "except, other than", "Noun + 以外",
  """以外 (いがい) means "except": 日曜日以外は毎日働く (I work every day except Sunday).""",
  r"以外(?:に|は|の)?", "日曜日以外は毎日働いています。", after="n")

# ---------------------------------------------------------------- verb helpers
P("kiru", "〜きる", "do completely", "Verb stem + きる",
  """きる after a verb stem means "completely": 全部食べきった (ate it all). きれない = can't finish / too
  many to: 数えきれない (countless).""",
  r"(?:き|切)(?:る|れ|っ|り|ら)", "一日で本を読みきりました。", pre="v", tail=True, check=first_lemma("切る"))
P("kakeru", "〜かける / 〜かけ", "half-done, about to", "Verb stem + かける",
  """かける after a verb stem means "start and not finish": 読みかけの本 (a half-read book), 言いかけて
  やめた (started to say something and stopped).""",
  "", "読みかけの本が机の上にある。", custom=compound("掛け", "掛ける"))
P("dasu", "〜出す", "suddenly start", "Verb stem + 出す",
  """出す (だす) after a verb stem means "suddenly start": 急に泣き出した (suddenly burst into tears).""",
  r"(?:出|だ)(?:す|し|さ|せ)", "赤ちゃんが急に泣き出した。", pre="v", tail=True,
  check=lambda t, i, k: t[i].lemma == "出す" and i > 0 and t[i - 1].p1 == "動詞")
P("ppanashi", "〜っぱなし", "left (undone), continuously", "Verb stem + っぱなし",
  """っぱなし means leaving something in a state that should have changed: 電気がつけっぱなしだ (the light was
  left on).""",
  r"っぱなし|っ放し", "電気がつけっぱなしですよ。", pre="v")
P("te_tamaranai", "〜てたまらない", "unbearably, dying to", "Adj / Verb (て-form) + たまらない",
  """てたまらない expresses an overwhelming feeling: 暑くてたまらない (unbearably hot), 会いたくてたまらない
  (I'm dying to see you).""",
  r"[てで](?:たまら|堪ら)(?:ない|ん|なかった)", "今日は暑くてたまらない。", pre="va")
P("te_shou_ga_nai", "〜てしょうがない", "extremely, can't help", "Adj / Verb (て-form) + しょうがない",
  """てしょうがない / てしかたがない mean "terribly, can't help it": 眠くてしょうがない (I'm so sleepy).""",
  r"[てで](?:しょう|仕様|しかた|仕方)が(?:ない|ありません)", "朝から眠くてしょうがない。", pre="va")
P("ki_ga_suru", "〜気がする", "have a feeling that", "Plain form + 気がする",
  """気がする means "I have a feeling that": 誰かに見られている気がする (I feel like someone is watching me).""",
  r"(?:気|き)が" + SURU, "誰かに見られている気がします。", after="any", tail=True)
P("furi", "〜ふりをする", "pretend to", "Plain form / Noun + の + ふりをする",
  """ふりをする means "pretend": 寝ているふりをする (pretend to be asleep), 知らないふりをする (pretend not
  to know).""",
  r"(?:ふり|振り)を" + SURU, "弟は寝ているふりをしていた。", after="any", tail=True)
P("tokoro_datta", "〜ところだった", "almost, nearly", "Verb (dictionary) + ところだった",
  """ところだった means something almost happened: もう少しで遅刻するところだった (I was nearly late).""",
  r"ところだった", "もう少しで遅刻するところだった。", after="v")
P("nai_you_ni", "〜ないように", "so as not to", "Verb (ない) + ように",
  """ないように means "so as not to": 風邪をひかないように気をつけて (take care not to catch a cold).""",
  r"ないように", "風邪をひかないように気をつけてください。", pre="v")
P("nai_koto_wa_nai", "〜ないことはない", "it's not that ... not (can, after all)", "Verb (ない) + ことはない",
  """ないことはない is a cautious double negative: 行けないことはない (it's not that I can't go).""",
  r"ないことは(?:ない|ありません)", "行けないことはないですが、少し遠いです。", pre="va")
P("you_ni_omoeru", "〜ように見える", "looks as if", "Plain form / Noun + の + ように見える",
  """ように見える describes how something appears from the outside: 彼は疲れているように見える (he looks tired). After a noun use のように見える; そうに見える is a close, slightly more direct alternative.""",
  r"ように(?:見え|みえ)", "彼は疲れているように見えます。", after="any", tail=True)
P("gimi", "〜気味", "a bit, slightly (tendency)", "Noun / verb stem + 気味",
  """気味 (ぎみ) means "a touch of, tending to": 風邪気味 (a bit of a cold), 疲れ気味 (a little tired).""",
  r"(?:気味|ぎみ)", "今日はちょっと風邪気味です。", after="any")
P("gachi", "〜がち", "tend to", "Noun / verb stem + がち",
  """がち means "tend to (often, usually bad)": 病気がち (sickly), 忘れがち (tend to forget).""",
  r"がち", "冬は運動不足になりがちです。", after="any", check=first_pos("接尾辞"))
P("darake", "〜だらけ", "full of, covered with", "Noun + だらけ",
  """だらけ means "full of (something unpleasant)": 間違いだらけ (full of mistakes), 泥だらけ (covered in mud).""",
  r"だらけ", "この作文は間違いだらけだ。", after="n")
P("muke", "〜向け / 〜向き", "for (aimed at) / suited to", "Noun + 向け / 向き",
  """向け means "made for": 子供向けの本 (a book for children). 向き means "suited to": 初心者向きの山.""",
  r"(?:向|む)(?:け|き)", "これは子供向けの本です。", after="n", check=first_pos("接尾辞"))
P("goto_ni", "〜ごとに", "every, each", "Noun / Verb + ごとに",
  """ごとに means "every": 一時間ごとに (every hour), 会うごとに (each time we meet).""",
  r"(?:ごと|毎)に", "一時間ごとに薬を飲みます。", after="any")
P("juu", "〜中 (じゅう / ちゅう)", "throughout / in the middle of", "Noun + 中",
  """中 as じゅう means "throughout": 一日中 (all day), 世界中 (all over the world). As ちゅう it means "in the
  middle of": 会議中 (in a meeting).""",
  r"中", "その歌手は世界中で有名です。", after="n", check=lambda t, i, k: t[i].kana in ("じゅう", "ちゅう"))
P("teki", "〜的", "-ic, -al (adjective from noun)", "Noun + 的",
  """的 (てき) turns a noun into a な-adjective: 経済的 (economic), 国際的 (international).""",
  r"的(?:な|に|だ|です)?", "これは経済的な車です。", after="n")
P("tate", "〜たて", "freshly, just", "Verb stem + たて",
  """たて means "fresh from": 焼きたてのパン (freshly baked bread), 生まれたての赤ちゃん.""",
  "", "焼きたてのパンはおいしい。", custom=compound("立て", "立て"))
P("datte", "〜だって", "even; I hear; because", "Noun + だって",
  """だって is casual: "even" (子供だって分かる), "I hear" (雨だって), or at the start "but/because".""",
  r"だって", "そんなこと、子供だって分かるよ。", after="any")
P("nante", "〜なんて", "such a thing as (surprise/disdain)", "Noun / plain form + なんて",
  """なんて expresses surprise or contempt: 彼が来るなんて (who'd have thought he'd come!), 勉強なんて嫌い.""",
  r"なんて", "彼が来るなんて思わなかった。", after="any", check=first_pos("助詞"))
P("hodo", "〜ほど (extent)", "to the extent that", "Plain form + ほど",
  """ほど shows extent: 死ぬほど疲れた (I'm dead tired). ば〜ほど means "the more ... the more".""",
  r"ほど", "泣きたいほど嬉しかった。", after="va", neg=r"ほど.*(?:ない|ません)")
P("ba_hodo", "〜ば〜ほど", "the more ... the more", "Verb (ば) + Verb + ほど",
  """ば〜ほど means "the more ..., the more ...": 練習すればするほど上手になる (the more you practise, the
  better you get).""",
  r"ほど", "練習すればするほど上手になります。", after="va", req=r"ば[^、。]{1,8}ほど")
