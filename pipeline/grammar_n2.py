"""N2 grammar points (original explanations; `ex` sentences are only used by the tests)."""
import re

from grammar_n4 import _volitional

# nouns for people (or groups / pets), for points that take someone's point of view
PEOPLE = {"親", "両親", "子供", "子ども", "子", "母", "父", "母親", "父親", "彼", "彼女", "私", "僕", "俺", "先生",
          "学生", "生徒", "客", "お客", "人", "夫", "妻", "主人", "社員", "会社", "店", "犬", "猫", "大人", "若者",
          "老人", "日本人", "外国人", "相手", "本人", "家族", "息子", "娘", "兄", "姉", "弟", "妹", "友達", "友人",
          "上司", "部下", "患者", "医者", "選手", "読者", "消費者", "市民", "国民", "政府", "女性", "男性", "あなた"}


def _literal_ataru(t, i, k):
    """当たる in its own senses: be hit by (流れ弾に当たって), be exposed to (風に当たる), handle (任務に
    あたっている), ask (ジェーンにあたってみる)."""
    if i > 0 and t[i - 1].lemma in ("火", "日", "日光", "髪", "顔", "頭", "体", "ボール", "風", "雨", "霧", "夜霧",
                                     "雪", "弾", "流れ弾", "光", "日差し", "任務", "任", "事件"):
        return True
    rest = "".join(x.s for x in t[k:])
    return bool(re.match(r"(?:い|み|く|もら|貰|しま)", rest))


PLACES = {"空", "飛行機", "宇宙", "遠く", "上", "窓", "山", "外", "下", "横", "遠方", "船", "ここ", "そこ",
          "あそこ", "丘", "屋上", "塔", "月"}


def _seen_from_a_place(t, i, k):
    """から見ると is only "from the viewpoint of" after a person or a viewpoint word (観点, 立場 ...);
    空から見ると / 飛行機から見ると are literally "seen from up there"."""
    if not any(x.lemma == "見る" for x in t[i:k]):
        return False
    return not (i > 0 and (is_person(t[i - 1]) or t[i - 1].lemma in ("観点", "見地", "立場", "目", "視点")))


def is_person(t):
    """Token naming a person or group: 子供, 田中さん, 私たち, a proper noun, a personal pronoun."""
    if t.lemma in PEOPLE or t.s in PEOPLE or t.p2 == "固有名詞":
        return True
    if t.s.endswith(("さん", "たち", "達", "側", "ら")) or t.lemma in ("さん", "たち", "達", "側"):
        return True
    return t.p1 == "代名詞" and t.s not in ("何", "なに", "なん", "誰", "だれ", "どれ", "これ", "それ", "あれ",
                                          "ここ", "そこ", "あそこ", "どこ")
from patterns import ARU, NARU, SURU, first_lemma, first_pos, point, prev_is


def m_you_dewa_nai_ka(toks):
    out = []
    text = [t.s for t in toks]
    for a, b, h in _volitional(toks):
        rest = "".join(text[b:b + 4])
        for tail in ("ではないか", "じゃないか", "ではありませんか", "じゃありませんか"):
            if rest.startswith(tail):
                n, acc = b, ""
                while acc != tail:
                    acc += text[n]
                    n += 1
                    if len(acc) > len(tail):
                        break
                if acc == tail:
                    out.append((a, n, h))
    return out


def P(*a, **k):
    point("N2", *a, **k)


NEG = r"(?:ない|ません|なかった|ず|ぬ)"

# ---------------------------------------------------------------- conditions & premises
P("ue_de", "〜上で", "after; in (doing), for", "Verb (た) / Noun + の + 上で",
  """上で (うえで) means "after doing" (よく考えた上で決める, decide after thinking carefully) or "in the process
  of / for": 生活する上で大切なこと.""",
  r"(?:上|うえ)で(?:は|も|の)?", "よく考えた上で決めてください。", after="v", check=lambda t, i, k: t[i].kana == "うえ")
P("ue_wa", "〜上は", "now that, since", "Verb (dictionary / た) + 上は",
  """上は (うえは) means "now that (so I must)": 約束した上は、守らなければならない (now that I've promised, I
  must keep it).""",
  r"(?:上|うえ)は", "約束した上は、必ず守ります。", after="v", check=lambda t, i, k: t[i].kana == "うえ")
P("ijou_wa", "〜以上(は)", "since, now that", "Plain form + 以上(は)",
  """以上は (いじょうは) means "since / given that": 引き受けた以上、最後までやる (since I took it on, I'll see
  it through).""",
  r"以上(?:は)?(?=、)", "引き受けた以上、最後までやります。", after="v")
P("kara_ni_wa", "〜からには", "since, now that", "Plain form + からには",
  """からには means "since (I've done this), I must ...": 日本に来たからには、日本語を覚えたい.""",
  r"からには", "日本に来たからには、日本語を覚えたい。", after="any")
P("sai", "〜際(に)", "when, on the occasion of", "Verb / Noun + の + 際(に)",
  """際 (さい) is a formal "when": お降りの際は足元にご注意ください (please watch your step when getting off).""",
  r"際(?:に|は|の)?", "お帰りの際は、忘れ物にご注意ください。", after="any", check=lambda t, i, k: t[i].kana == "さい")
P("ni_saishite", "〜に際して", "on the occasion of", "Noun / Verb + に際して",
  """に際して means "at the time of (an important event)": 出発に際して挨拶をした (I said a few words on
  departure).""",
  r"に(?:際|さい)(?:して|し)", "出発に際して、皆さんに挨拶をしました。", after="nv")
P("ni_atatte", "〜にあたって", "at the time of, when (starting)", "Noun / Verb + にあたって",
  """にあたって means "when undertaking (something important)": 開店にあたって準備をする.""",
  # not 火に当たる (warm oneself), 祖母にあたります (is my grandmother), 髪に当たって (hit)
  r"に(?:あた|当た)(?:って|り)(?!ま)", "新しい生活を始めるにあたって、目標を立てました。", after="nv",
  check=lambda t, i, k: not _literal_ataru(t, i, k),
  neg=r"が[^、。]*に(?:あた|当た)って")
P("to_sureba", "〜とすれば / 〜としたら", "if (we assume)", "Plain form + とすれば",
  """とすれば / とすると / としたら mean "assuming that": 明日行くとしたら、何時がいい? (if we go tomorrow, what
  time is good?).""",
  # not 別とすれば (apart from), ひょっとしたら (maybe), 〜ようとすれば (try to)
  r"(?<!別)(?<!ひょっ)(?<!ひょ)(?<!よう)(?<!こう)(?<!そう)と(?:すれば|すると|したら)", "明日行くとしたら、何時がいいですか。",
  after="any")
P("to_naru_to", "〜となると", "when it comes to; if it becomes", "Noun / plain form + となると",
  """となると means "when it comes to / if it's the case that": 留学となると、お金がかかる.""",
  r"となると|となれば|となったら", "留学となると、お金がかかります。", after="any")
P("to_ieba", "〜といえば", "speaking of", "Noun + といえば",
  """といえば picks up a topic just mentioned: 京都といえば、お寺が有名だ (speaking of Kyoto, it's famous for
  its temples).""",
  # not なんと言えば (how to say), どちらかと言えば (if anything), 私はと言えば
  r"(?<!なん)(?<!何)(?<!どちらか)(?<!どっちか)(?<!は)と(?:いえ|言え)ば", "京都といえば、お寺が有名です。", after="any")
P("kara_to_itte", "〜からといって", "just because", "Plain form + からといって",
  """からといって denies an easy conclusion: 高いからといって、いいものとは限らない (just because it's expensive
  doesn't mean it's good).""",
  r"からといって|からって", "高いからといって、いいものとは限らない。", after="any")
P("kara_koso", "〜からこそ", "precisely because", "Plain form + からこそ",
  """からこそ stresses the reason: 好きだからこそ厳しくする (I'm strict precisely because I care).""",
  r"からこそ", "好きだからこそ、厳しく言うのです。", after="any")
P("kara_suru_to", "〜からすると", "from the viewpoint of, judging from", "Noun + からすると / からすれば",
  """からすると means "judging from / from the standpoint of": 親からすると、子供はいつまでも子供だ.""",
  r"から(?:すると|すれば|見ると|見れば|みると|みれば)", "あの様子からすると、何かあったようだ。", after="n",
  check=lambda t, i, k: not _seen_from_a_place(t, i, k))
P("kara_shite", "〜からして", "even (starting with); judging from", "Noun + からして",
  """からして means "to begin with even": 名前からして怪しい (even the name is suspicious).""",
  r"からして(?!もら|貰)", "あの店は名前からして怪しい。", after="n")  # 人からしてもらう
P("ni_shitara", "〜にしたら", "from the standpoint of", "Noun (person) + にしたら / にすれば",
  """にしたら / にすれば take another person's point of view: 子供にしたら、つまらない話だろう.""",
  r"に(?:したら|すれば|してみれば)", "子供にしたら、つまらない話でしょう。", after="n",
  check=lambda t, i, k: i > 0 and is_person(t[i - 1]))  # someone's point of view, not 〜にする
P("nai_kagiri", "〜ない限り", "unless", "Verb (ない) + 限り",
  """ない限り (かぎり) means "unless": 謝らない限り許さない (I won't forgive you unless you apologize).""",
  r"ない(?:限|かぎ)り", "謝らない限り、許しません。", pre="va")
P("kagiri", "〜限り", "as long as; as far as", "Plain form + 限り(は)",
  """限り means "as long as" (生きている限り, as long as I live) or "as far as" (私の知る限り, as far as I know).""",
  r"(?:限|かぎ)り(?:は|では)?", "私の知る限り、彼は正直な人です。", after="va", neg=r"ない(?:限|かぎ)り")

# ---------------------------------------------------------------- contrast & concession
P("ippou", "〜一方(で)", "while, on the other hand", "Plain form + 一方(で)",
  """一方で contrasts two sides: 都会は便利な一方で、物価が高い (cities are convenient, but prices are high).""",
  r"一方(?:で|では)", "都会は便利な一方で、物価が高い。", after="any")
P("hanmen", "〜反面", "on the other hand", "Plain form + 反面",
  """反面 (はんめん) shows a downside of the same thing: この仕事は楽しい反面、責任も重い.""",
  r"反面", "この仕事は楽しい反面、責任も重いです。", after="any")
P("mono_no", "〜ものの", "although", "Plain form + ものの",
  """ものの means "although (but in reality...)": 買ったものの、一度も使っていない (I bought it, but haven't used
  it once).""",
  r"ものの", "買ったものの、一度も使っていません。", after="va",
  # もの + の (必要なものの大半, 甘いものの量): the concessive ものの is followed by a clause, not a noun
  check=lambda t, i, k: k < len(t) and (t[k].s == "、" or t[k].p1 not in ("名詞", "接尾辞", "代名詞", "助詞"))
  and not (i > 0 and (t[i - 1].s == "な" or t[i - 1].lemma == "言う"))  # 率直なものの, というものの
  and t[k].lemma not in ("有る", "言う", "良い") and not t[k].s.startswith(("言い方", "見方", "考え方", "よさ")))
P("ni_mo_kakawarazu", "〜にもかかわらず", "despite, in spite of", "Noun / plain form + にもかかわらず",
  """にもかかわらず means "despite": 雨にもかかわらず、たくさんの人が来た (despite the rain, many people came).""",
  r"にも(?:かかわ|関わ|拘)らず", "雨にもかかわらず、たくさんの人が来ました。", after="any")
P("nagara_mo", "〜ながらも", "although, while", "Verb stem / adj + ながらも",
  """ながらも means "although": 狭いながらも楽しい我が家 (our home, small but happy).""",
  r"ながらも", "狭いながらも、楽しい我が家です。", after="any")
P("tsutsu_mo", "〜つつも", "although (doing)", "Verb stem + つつも",
  """つつも is a written "although (while doing)": 体に悪いと知りつつも、タバコがやめられない (although I know it is bad for me, I can't quit smoking). It usually involves knowing or thinking one thing while doing the opposite.""",
  r"つつも", "体に悪いと知りつつも、タバコがやめられない。", pre="v")
P("tsutsu", "〜つつ", "while (doing)", "Verb stem + つつ",
  """つつ is a written ながら: 景色を楽しみつつ歩く (walk while enjoying the view).""",
  r"つつ(?!も|あ)", "景色を楽しみつつ歩きました。", pre="v")
P("tsutsu_aru", "〜つつある", "be in the process of", "Verb stem + つつある",
  """つつある describes an ongoing change: 地球の気温は上がりつつある (the earth's temperature is rising).""",
  r"つつ" + ARU, "地球の気温は上がりつつある。", pre="v", tail=True)
P("wari_ni", "〜わりに(は)", "considering, for", "Plain form / Noun + の + わりに",
  """わりに means "considering": 値段のわりにおいしい (tasty, considering the price).""",
  r"(?:わり|割)に(?:は)?(?!合)", "この店は値段のわりにおいしい。", after="any")  # 割に合わない
P("ni_shiro", "〜にしろ / 〜にせよ", "even if; whether ... or", "Plain form / Noun + にしろ",
  """にしろ / にせよ mean "even if" or, repeated, "whether A or B": 行くにしろ行かないにしろ連絡して.""",
  r"(?:にしろ|にせよ)(?![^。]*(?:にしろ|にせよ))", "行くにしろ行かないにしろ、連絡してください。", after="any",
  check=lambda t, i, k: i > 0 and t[i - 1].lemma != "様" and (k >= len(t) or t[k].p1 != "補助記号" or t[k].s == "、")
  and not (k < len(t) and t[k].s in ("よ", "と", "って", "とか")))  # 大概にしろよ: imperative of する
P("ta_tokoro_de", "〜たところで", "even if (it's no use)", "Verb (た) + ところで",
  """たところで means "even if you do (it won't help)": 今から急いだところで間に合わない.""",
  r"ところで(?=、)", "今から急いだところで、間に合わないだろう。", pre="v", check=prev_is("た", "だ"),
  # "even if you do, it's no use": the rest is negative or futile (not 信号を渡ったところで、止めて)
  req=r"ところで、[^。]*(?:ない|無駄|むだ|駄目|だめ|ダメ|ならな|ません|しょうがな|仕方)")
P("dokoro_ka", "〜どころか", "far from; let alone", "Noun / plain form + どころか",
  """どころか means "far from (the opposite is true)": 休むどころか、ますます忙しくなった.""",
  r"どころか", "休むどころか、ますます忙しくなった。", after="any")
P("dokoro_dewa_nai", "〜どころではない", "this is no time for", "Noun / Verb + どころではない",
  """どころではない means there's no room for something: 忙しくて旅行どころではない (I'm too busy to even think of
  travelling).""",
  r"どころ(?:では|じゃ)(?:ない|ありません)", "忙しくて、旅行どころではない。", after="any")
P("bakari_ka", "〜ばかりか", "not only ... but even", "Noun / plain form + ばかりか",
  """ばかりか means "not only ... but also (even more)": 彼は英語ばかりか、中国語も話せる.""",
  r"ばかりか", "彼は英語ばかりか、中国語も話せる。", after="any")
P("bakari_ni", "〜ばかりに", "simply because (bad result)", "Plain form + ばかりに",
  """ばかりに gives a cause that led to a bad result: 嘘をついたばかりに、信用を失った (just because I lied, I
  lost their trust).""",
  r"ばかりに", "嘘をついたばかりに、信用を失った。", after="any")
P("bakari_da", "〜一方だ / 〜ばかりだ", "keep (getting worse)", "Verb (dictionary) + 一方だ",
  """一方だ / ばかりだ describe a change continuing in one direction: 物価は上がる一方だ (prices just keep
  rising).""",
  r"(?:一方|ばかり)(?:だ|です)", "物価は上がる一方だ。", after="v",
  check=lambda t, i, k: i > 0 and t[i - 1].cf.startswith(("終止形", "連体形")) and t[i - 1].lemma != "た")
P("mo_kamawazu", "〜もかまわず", "without caring about", "Noun + もかまわず",
  """もかまわず means "without minding": 人目もかまわず泣いた (cried without caring who saw).""",
  r"も(?:かまわ|構わ)ず", "彼女は人目もかまわず泣いた。", after="any")
P("wa_tomokaku", "〜はともかく", "leaving aside", "Noun + はともかく",
  """はともかく sets a point aside: 味はともかく、量が多い (taste aside, the portions are big).""",
  r"はともかく(?:として)?", "味はともかく、量が多い店です。", after="n")
P("wa_motoyori", "〜はもとより", "not to mention", "Noun + はもとより",
  """はもとより means "not to mention, let alone" and is a more formal はもちろん: 子供はもとより大人も楽しめる (adults can enjoy it, not to mention children). The second part usually contains も.""",
  r"はもとより", "子供はもとより、大人も楽しめます。", after="n")

# ---------------------------------------------------------------- relations (formal)
P("ni_kakawarazu", "〜にかかわらず", "regardless of", "Noun + にかかわらず",
  """にかかわらず means "regardless of": 年齢にかかわらず参加できる (anyone can join, regardless of age).""",
  r"に(?:かかわ|関わ|拘)らず", "年齢にかかわらず、誰でも参加できます。", after="any")
P("wo_towazu", "〜を問わず", "regardless of", "Noun + を問わず",
  """を問わず (とわず) means "regardless of": 男女を問わず (regardless of gender).""",
  r"を(?:問|と)わず", "経験を問わず、誰でも応募できます。", after="n")
P("ni_kagirazu", "〜に限らず", "not only", "Noun + に限らず",
  """に限らず (かぎらず) means "not limited to": 若者に限らず、お年寄りにも人気がある (it is popular not only with young people but with the elderly too). The second half widens the scope, typically with も.""",
  r"に(?:限|かぎ)らず", "若者に限らず、お年寄りにも人気があります。", after="n")
P("ni_kagiru", "〜に限る", "nothing beats", "Noun / Verb + に限る",
  """に限る means "X is the best": 夏はビールに限る (nothing beats beer in summer).""",
  r"に(?:限|かぎ)る", "暑い日は冷たいビールに限る。", after="nv")
P("ni_kagitte", "〜に限って", "of all (times/people); only", "Noun + に限って",
  """に限って means "of all times / only (unexpectedly)": 急いでいる時に限って、バスが来ない.""",
  r"に(?:限|かぎ)って", "急いでいる時に限って、バスが来ない。", after="n")
P("ni_sugi_nai", "〜に過ぎない", "merely, no more than", "Noun / plain form + に過ぎない",
  """に過ぎない (すぎない) means "nothing more than": それは噂に過ぎない (it's only a rumor).""",
  r"に(?:過|す)ぎ(?:ない|ません)", "それはただの噂に過ぎない。", after="any")
P("ni_kuwaete", "〜に加えて", "in addition to", "Noun + に加えて",
  """に加えて (くわえて) means "in addition to": 雨に加えて風も強くなった (on top of the rain, the wind got stronger too). It is written or formal; casual speech would use それに or だけじゃなく.""",
  r"に(?:加|くわ)え(?:て)?", "雨に加えて、風も強くなってきた。", after="n")
P("ni_tomonatte", "〜に伴って", "along with, as", "Noun / Verb + に伴って",
  """に伴って (ともなって) describes things changing together: 人口の増加に伴って、問題も増えた.""",
  r"に(?:伴|ともな)(?:って|い|う)", "人口の増加に伴って、問題も増えた。", after="nv")
P("ni_oujite", "〜に応じて", "according to, in response to", "Noun + に応じて",
  """に応じて (おうじて) means "depending on / in response to": 能力に応じて給料を払う.""",
  r"に(?:応|おう)じ(?:て|た)?", "能力に応じて給料が決まります。", after="n")
P("ni_sotte", "〜に沿って", "along; in line with", "Noun + に沿って",
  """に沿って (そって) means "along" (川に沿って歩く) or "in line with" (計画に沿って進める).""",
  r"に(?:沿|そ)(?:って|った|う)", "川に沿って歩きました。", after="n")
P("ni_motozuite", "〜に基づいて", "based on", "Noun + に基づいて",
  """に基づいて (もとづいて) means "based on": 事実に基づいた映画 (a film based on facts).""",
  r"に(?:基|もと)づ(?:いて|いた|く|き)", "これは事実に基づいた話です。", after="n")
P("wo_moto_ni", "〜をもとに", "based on (using as material)", "Noun + をもとに",
  """をもとに means "based on, using X as material": 経験をもとに小説を書いた (I wrote a novel based on my experience). Compare に基づいて, which means "in accordance with" rules or facts.""",
  r"を(?:もと|基|元)に(?:して)?", "自分の経験をもとに小説を書いた。", after="n")
P("wo_tooshite", "〜を通して / 〜を通じて", "through, via; throughout", "Noun + を通して",
  """を通して (とおして) / を通じて (つうじて) mean "through (a means)" or "throughout (a period)".""",
  r"を(?:通|とお|つう)(?:して|じて|じ)", "友人を通して彼と知り合いました。", after="n")
P("wo_megutte", "〜をめぐって", "concerning (a dispute)", "Noun + をめぐって",
  """をめぐって means "over / around (an issue people argue about)": 遺産をめぐって争う.""",
  r"を(?:めぐ|巡)(?:って|る)", "遺産をめぐって、兄弟が争っている。", after="n")
P("wo_hajime", "〜をはじめ", "starting with, including", "Noun + をはじめ",
  """をはじめ means "beginning with (as the main example)": 社長をはじめ、社員全員が集まった.""",
  r"を(?:はじめ|始め)(?:として|とする)?", "社長をはじめ、社員全員が集まった。", after="n")
P("ni_hanshite", "〜に反して", "contrary to", "Noun + に反して",
  """に反して (はんして) means "contrary to, against": 予想に反して、試合に負けた (contrary to expectations, we lost the game). It is used with expectations, wishes or rules; before a noun it becomes に反する.""",
  r"に(?:反|はん)(?:して|し|する)", "予想に反して、試合に負けた。", after="n")
P("ni_sakidatte", "〜に先立って", "prior to", "Noun + に先立って",
  """に先立って (さきだって) means "before (as preparation)": 試合に先立って開会式が行われた.""",
  r"に(?:先立|さきだ)(?:って|ち)", "試合に先立って、開会式が行われた。", after="nv")
P("ni_watatte", "〜にわたって", "over, throughout (a range)", "Noun + にわたって",
  """にわたって means "spanning (a long time / wide area)": 三日間にわたって会議が開かれた.""",
  r"に(?:わた|渡)(?:って|り|る)", "三日間にわたって会議が開かれた。", after="n")
P("ni_kakete", "〜にかけて", "through, over (from ... to)", "Noun + にかけて",
  """から〜にかけて means "from ... through ..." for a stretch of time or space with fuzzy edges: 夜から朝にかけて雨が降る (it will rain from night into the morning). Compare から〜まで, which has clear end points.""",
  r"にかけて(?:は)?", "夜から朝にかけて雨が降るでしょう。", after="n")
P("ni_oite", "〜において", "in, at (formal)", "Noun + において",
  """において is a formal で: 会議は大阪において行われる (the conference will be held in Osaka).""",
  r"において|における|においては", "会議は東京において行われます。", after="n")
P("ni_mukete", "〜に向けて", "toward, for", "Noun + に向けて",
  """に向けて (むけて) means "toward (a goal or target)": 試験に向けて勉強している (I'm studying for the exam). It can also mean "aimed at" people: 若者に向けたメッセージ (a message for young people).""",
  r"に(?:向|む)け(?:て)?", "来月の試験に向けて勉強しています。", after="n")
P("wo_kikkake_ni", "〜をきっかけに", "taking ... as a chance", "Noun + をきっかけに",
  """をきっかけに means "with X as the trigger / taking X as the occasion": 留学をきっかけに料理を始めた (studying abroad got me into cooking). を契機に and を機に are more formal variants.""",
  r"を(?:きっかけ|契機|機)に(?:して)?", "留学をきっかけに、料理を始めました。", after="any")
P("wo_nozoite", "〜を除いて", "except for", "Noun + を除いて",
  """を除いて (のぞいて) means "except for": 日曜日を除いて毎日営業している (we're open every day except Sunday). It is a formal 以外; を除き is the written variant.""",
  r"を(?:除|のぞ)(?:いて|き|く)", "日曜日を除いて、毎日営業しています。", after="n")
P("nuki", "〜抜きで / 〜を抜きにして", "without, leaving out", "Noun + 抜きで",
  """抜き (ぬき) means "without": 朝ご飯抜きで出かけた (went out without breakfast).""",
  r"(?:抜|ぬ)き(?:で|に|の|には)", "朝ご飯抜きで出かけました。", after="n")
P("irai", "〜以来", "since", "Verb (て) / Noun + 以来",
  """以来 (いらい) means "ever since": 卒業して以来、彼に会っていない (I haven't seen him since we graduated). After a verb it takes the て-form; after a noun it attaches directly: 先月以来.""",
  r"以来", "卒業して以来、彼に会っていません。", after="any")
P("sue_ni", "〜末(に)", "after (a long process), finally", "Verb (た) / Noun + の + 末に",
  """末に (すえに) means "at the end of (a long process)": よく考えた末に、会社を辞めた (after thinking it over carefully, I quit my job). It attaches to a past verb or to Noun + の, and the result can be good or bad.""",
  r"(?:末|すえ)(?:に|の)?", "よく考えた末に、会社を辞めることにした。", after="any",
  check=lambda t, i, k: t[i].kana == "すえ")
P("ageku", "〜あげく", "in the end (after much trouble)", "Verb (た) / Noun + の + あげく",
  """あげく means "after all that (unfortunately)": さんざん迷ったあげく、何も買わなかった.""",
  r"(?:あげく|挙句|挙げ句)(?:に|の果て)?", "さんざん迷ったあげく、何も買わなかった。", after="any")
P("shidai", "〜次第", "as soon as; depending on", "Verb stem / Noun + 次第",
  """次第 (しだい) means "as soon as" (着き次第連絡する) or "depending on" (天気次第だ).""",
  r"次第(?:で|だ|です|では)?", "駅に着き次第、連絡します。", after="any")
P("ue_ni", "〜上に", "on top of, besides", "Plain form + 上に",
  """上に (うえに) adds something in the same direction: この店は安い上においしい (this place is cheap and tasty
  too).""",
  r"(?:上|うえ)に", "この店は安い上に、おいしい。", after="va", check=lambda t, i, k: t[i].kana == "うえ")

# ---------------------------------------------------------------- ability, difficulty, tendency
P("kanenai", "〜かねない", "might (bad result)", "Verb stem + かねない",
  """かねない warns that something bad could happen: そんな運転では事故を起こしかねない.""",
  r"かね(?:ない|ません)", "そんな運転では、事故を起こしかねない。", pre="v")
P("kaneru", "〜かねる", "can't (politely)", "Verb stem + かねる",
  """かねる politely refuses: そのご質問にはお答えしかねます (I'm afraid I can't answer that question).""",
  r"かね(?:る|ます)", "そのご質問にはお答えしかねます。", pre="v", check=first_lemma("兼ねる"))
P("gatai", "〜がたい", "hard to (emotionally)", "Verb stem + がたい",
  """がたい means something is hard to accept or do: 信じがたい話 (a hard-to-believe story).""",
  r"がた(?:い|く)", "それは信じがたい話です。", pre="v", check=first_lemma("難い"))
P("zurai", "〜づらい", "hard to (physically, awkward)", "Verb stem + づらい",
  """づらい means "hard/uncomfortable to do": この靴は歩きづらい (these shoes are hard to walk in).""",
  r"づら(?:い|く|かっ)", "この靴は歩きづらいです。", pre="v")
P("kkonai", "〜っこない", "there's no way", "Verb stem + っこない",
  """っこない is a casual "no way": そんなの、できっこない (no way I can do that).""",
  r"っこない", "そんなの、できっこないよ。", pre="v")
P("eru", "〜得る", "can, possible", "Verb stem + 得る (うる / える)",
  """得る (うる / える) after a verb stem means "can, possible": ありうる (possible), 考えうる (conceivable).
  The negative is えない: ありえない.""",
  r"(?:得|う|え)(?:る|ない|ません)", "それは十分ありうることだ。", pre="v", check=first_lemma("得る"))
P("nuku", "〜抜く", "do to the end", "Verb stem + 抜く",
  """抜く (ぬく) after a verb stem means "all the way through": 最後まで走り抜いた (ran to the very end).""",
  r"(?:抜|ぬ)(?:く|き|い|か)", "彼は最後まで走り抜いた。", pre="v", tail=True,
  check=lambda t, i, k: t[i].lemma == "抜く" and i > 0 and t[i - 1].p1 == "動詞")
P("ge", "〜げ", "seemingly, looking", "Adj stem + げ",
  """げ after an adjective stem means "looking (that way)": 寂しげな顔 (a lonely-looking face).""",
  r"げ(?:な|に|だ)?", "彼女は寂しげな顔をしていた。", pre="a", check=first_pos("接尾辞"))
P("zaru_wo_enai", "〜ざるを得ない", "have no choice but to", "Verb (ない-stem) + ざるを得ない",
  """ざるを得ない (えない) means "cannot help but": 中止せざるを得ない (we have no choice but to cancel).
  する becomes せざる.""",
  r"ざるを(?:得|え)(?:ない|ません|なかった)", "雨のため、試合を中止せざるを得ない。", pre="v?")
P("zuni_wa_irarenai", "〜ずにはいられない", "can't help doing", "Verb (ない-stem) + ずにはいられない",
  """ずにはいられない / ないではいられない mean "can't help but": 笑わずにはいられなかった (I couldn't help laughing). It describes an urge you can't hold back; する becomes せずにはいられない.""",
  r"(?:ずには|ないでは)いられ(?:ない|ません|なかった)", "その話を聞いて、笑わずにはいられなかった。", pre="v")
P("hoka_nai", "〜ほかない", "have no choice but", "Verb (dictionary) + ほかない",
  """ほかない / よりほかない mean "there's nothing to do but": 待つほかない (all we can do is wait).""",
  r"(?:より)?(?:ほか|他)(?:は)?(?:ない|ありません)|ほかしかたがない", "今は待つほかない。", after="v")
P("made_mo_nai", "〜までもない", "there's no need to", "Verb (dictionary) + までもない",
  """までもない means "it goes without (doing)": 言うまでもない (needless to say).""",
  r"までも(?:ない|ありません|なく)", "言うまでもないことです。", after="v")
P("nai_koto_ni_wa", "〜ないことには", "unless", "Verb (ない) + ことには",
  """ないことには means "unless (we do this, nothing can happen)": 食べてみないことには、分からない.""",
  r"ないことには", "実際に食べてみないことには、分からない。", pre="va")
P("mai", "〜まい", "won't, probably not", "Verb (dictionary) + まい",
  """まい is a written negative will/guess: 二度と行くまい (I'll never go again), 雨は降るまい.""",
  r"まい(?!か)", "もう二度とあの店には行くまい。", after="v", check=first_pos("助動詞"))
P("you_dewa_nai_ka", "〜ようではないか", "let's (appeal)", "Verb (volitional) + ではないか",
  """ようではないか is a strong appeal to a group: みんなで頑張ろうではないか (let's all give it our best!).""",
  "", "みんなで力を合わせようではないか。", custom=m_you_dewa_nai_ka)

# ---------------------------------------------------------------- mono / koto expressions
P("mono_nara", "〜ものなら", "if (it were possible)", "Verb (potential / volitional) + ものなら",
  """ものなら means "if (unlikely) ...": できるものなら、もう一度やり直したい (if only I could, I'd do it over).""",
  r"ものなら|もんなら", "できるものなら、もう一度やり直したい。", after="v")
P("mono_ka", "〜ものか", "no way (I'll ...)", "Plain form + ものか",
  """ものか (もんか) is an emphatic "never!": 二度と行くものか (I'll never go there again!).""",
  r"ものか|もんか", "あんな店、二度と行くものか。", after="va")
P("mono_dakara", "〜ものだから", "because (excuse)", "Plain form + ものだから",
  """ものだから gives a reason, often as an excuse: 道が混んでいたものだから、遅れてしまった (the roads were jammed, you see, so I was late). In casual speech it becomes もんだから or もので.""",
  r"ものだから|もんだから|もので", "道が混んでいたものだから、遅れてしまいました。", after="va")
P("mono_ga_aru", "〜ものがある", "there is something (feeling)", "Plain form + ものがある",
  """ものがある expresses an impression: 彼の歌には人を感動させるものがある (there's something moving in his songs).""",
  r"ものが" + ARU, "彼の歌には人の心を動かすものがある。", after="va", tail=True)
P("mono_dewa_nai", "〜ものではない", "you shouldn't", "Verb (dictionary) + ものではない",
  """ものではない gives social advice: 人の悪口を言うものではない (you shouldn't speak ill of others).""",
  r"もの(?:では|じゃ)(?:ない|ありません)", "人の悪口を言うものではない。", after="v")
P("koto_ka", "〜ことか", "how (very)!", "Question word ... + ことか",
  """ことか expresses strong emotion: どんなに心配したことか (how worried I was!).""",
  r"ことか(?=[。！])", "どんなに心配したことか。", after="va")
P("koto_dakara", "〜ことだから", "knowing (him), since it's", "Noun + の + ことだから",
  """ことだから gives a reason based on someone's character: 彼のことだから、また遅れるだろう.""",
  r"ことだから", "あの人のことだから、また遅れて来るだろう。", after="any")
P("koto_naku", "〜ことなく", "without (ever) doing", "Verb (dictionary) + ことなく",
  """ことなく means "without": 休むことなく働き続けた (worked on without a break).""",
  r"ことなく", "彼は休むことなく働き続けた。", after="v")
P("koto_ni", "〜ことに", "(I find it) ... that", "Adj / Verb (た) + ことに",
  """ことに expresses the speaker's feeling about a fact: 残念なことに、雨が降ってきた (unfortunately, it started
  to rain).""",
  r"ことに(?=、)", "残念なことに、雨が降ってきた。", after="va")
P("koto_kara", "〜ことから", "from the fact that", "Plain form + ことから",
  """ことから gives the basis of a judgment or name: 富士山が見えることから、この町は富士見と呼ばれる.""",
  r"ことから", "富士山が見えることから、この町は富士見と呼ばれている。", after="any")
P("to_iu_mono_da", "〜というものだ", "that's what (it is)", "Plain form + というものだ",
  """というものだ gives a general verdict about how something is: それが人生というものだ (that's life). It often sounds like a conclusion or mild lecture; というものではない denies such a generalization.""",
  r"というもの(?:だ|です)", "それが人生というものだ。", after="any")
P("to_iu_koto_da", "〜ということだ (hearsay)", "I hear that, they say", "Plain form + ということだ",
  """ということだ / とのことだ report information: 会議は中止だということだ (I hear the meeting is cancelled).""",
  r"ということ(?:だ|です)|とのこと(?:だ|です)", "会議は中止になったということです。", after="any")
P("to_itta", "〜といった", "such as", "Noun + といった + Noun",
  """といった lists examples: 寿司や天ぷらといった日本料理 (Japanese food such as sushi and tempura).""",
  r"といった", "寿司や天ぷらといった日本料理が好きです。", after="any")
P("ka_no_you", "〜かのように", "as if", "Plain form + かのように",
  """かのように means "as if (but not really)": 何もなかったかのように笑った (laughed as if nothing had happened).""",
  r"かのよう(?:に|な|だ)", "彼は何もなかったかのように笑った。", after="any")
P("dake_atte", "〜だけあって", "as you'd expect from", "Plain form / Noun + だけあって",
  """だけあって means "as expected of": プロだけあって、上手だ (as you'd expect from a pro, he's good).""",
  r"だけ(?:あって|のことはある|のことはあります)", "プロだけあって、さすがに上手だ。", after="any")
P("dake_ni", "〜だけに", "all the more because", "Plain form / Noun + だけに",
  """だけに means "precisely because (so all the more)": 期待していただけに、がっかりした.""",
  r"だけに(?=、)", "期待していただけに、がっかりした。", after="any")
P("amari_excess", "〜あまり", "so much that", "Noun + の / Verb + あまり",
  """あまり (in this use) means "from too much ...": 緊張のあまり、何も言えなかった (I was so nervous I couldn't
  speak).""",
  r"あまり(?=、)", "緊張のあまり、何も言えなかった。", after="any",
  check=lambda t, i, k: i > 0 and (t[i - 1].s == "の" or t[i - 1].p1 in ("動詞", "助動詞")))

# ---------------------------------------------------------------- adverbs
P("sasuga", "さすが", "as expected", "さすが(に / は)",
  """さすが expresses that something lives up to expectations: さすがプロだ (that's a pro for you).""",
  r"さすが(?:に|は)?", "さすがプロですね。")
P("semete", "せめて", "at least", "せめて ...",
  """せめて means "at least (it's the minimum I'd want)": せめて一日休みたい (I'd like at least a day off).""",
  r"せめて", "せめて一日だけでも休みたい。")
P("mushiro", "むしろ", "rather", "むしろ ...",
  """むしろ means "rather, if anything": 涼しいというより、むしろ寒い (it's not so much cool as cold, if anything). It picks the more accurate of two options, often after より or というより.""",
  r"むしろ", "今日は涼しいというより、むしろ寒い。")
P("kanarazushimo", "必ずしも〜ない", "not necessarily", "必ずしも + negative",
  """必ずしも〜ない means "not always / not necessarily": 高いものが必ずしもいいとは限らない.""",
  r"必ずしも|かならずしも", "高いものが必ずしもいいとは限らない。", req=NEG)
P("douse", "どうせ", "anyway (resigned)", "どうせ ...",
  """どうせ expresses resignation: どうせ間に合わない (we won't make it anyway).""",
  r"どうせ", "どうせ間に合わないから、ゆっくり行こう。")
P("douyara", "どうやら", "it seems (finally)", "どうやら ...",
  """どうやら means "apparently, it seems (judging from the situation)": どうやら雨が降りそうだ (it looks like it's going to rain). It is usually followed by らしい, ようだ or そうだ.""",
  r"どうやら", "どうやら雨が降りそうだ。")
P("yohodo", "よほど", "very, greatly (must have been)", "よほど ...",
  """よほど means "very much (judging from the evidence)": よほど疲れていたのだろう (he must have been very tired).""",
  r"よほど|余程", "よほど疲れていたのだろう。")
P("toutei", "到底〜ない", "by no means, utterly not", "到底 + negative",
  """到底 (とうてい) + negative means "absolutely cannot, by no means": 到底間に合わない (there's no way we'll make it). It stresses that something is impossible, often with できない or 無理.""",
  r"到底|とうてい", "今からでは到底間に合わない。", req=NEG)
