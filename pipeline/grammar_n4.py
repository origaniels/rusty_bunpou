"""N4 grammar points (original explanations; examples in `ex` are used by the tests only)."""
import re

from patterns import (ARU, IKU, KURU, NARU, SURU, _tail, all_of, first_lemma, first_pos, point, prev_cf,
                      prev_is, prev_not)


def _volitional(toks):
    """Volitional verb: 行こう (one token, 意志推量形) or 食べ + よう. Returns (start, end, head)."""
    out = []
    for j, t in enumerate(toks):
        if t.p1 == "動詞" and t.cf.startswith("意志推量形"):
            out.append((j, j + 1, j))
        elif t.p1 == "助動詞" and t.lemma in ("よう", "う") and j > 0 and toks[j - 1].p1 == "動詞":
            out.append((j - 1, j + 1, j - 1))
    return out


def m_volitional(toks):
    return [(a, b, h) for a, b, h in _volitional(toks)
            if b < len(toks) and (toks[b].p1 == "補助記号" or toks[b].s in ("よ", "か", "ぜ", "や"))]


def m_you_to_omou(toks):
    return [(a, b + 1, h) for a, b, h in _volitional(toks)
            if b + 1 < len(toks) and toks[b].s == "と" and toks[b + 1].lemma in ("思う", "考える")]


E_ROW = set("えけせてねへめれげべぺ")


def m_potential(toks):
    """Potential: ichidan + られる / godan e-row form (読める), "can" in the English (checked in build)."""
    out = []
    for j, t in enumerate(toks):
        if t.p1 == "助動詞" and t.lemma in ("られる", "れる") and j > 0 and toks[j - 1].p1 == "動詞":
            out.append((j - 1, _tail(toks, j + 1), j - 1))
        elif t.p1 == "動詞" and t.s and t.s[-1] in E_ROW and t.cf.startswith(("連用形", "未然形")) \
                and len(t.lemma) >= 2 and t.lemma[-1] in "うくすつぬむるぐぶ" and t.lemma[-2] not in E_ROW \
                and t.lemma not in ("為る", "出来る", "呉れる", "見える", "聞こえる"):
            out.append((j, _tail(toks, j + 1), j))
    return out


def P(*a, **k):
    point("N4", *a, **k)


# ---------------------------------------------------------------- conditionals
P("ba", "〜ば", "if (conditional)", "Verb/adj (ば-form)",
  """The ば-form states a condition: 安ければ買う (if it's cheap, I'll buy it). Verbs change their last
  u-sound to e + ば (行く → 行けば), い-adjectives take ければ. It often stresses what is needed for the result.""",
  r"ば", "安ければ買います。", pre="va", check=first_pos("助詞", "接続助詞"), neg=r"なければ")
P("tara", "〜たら", "if / when (once)", "Verb/adj (た-form) + ら",
  """たら is the most flexible "if/when": once the first thing happens, the second follows.
  帰ったら電話する (I'll call when I get home). Built from the た-form: 食べたら, 高かったら.""",
  r"(?:た|だ)ら", "家に帰ったら電話します。", pre="va", check=first_lemma("た"))
P("nara", "〜なら", "if (it's the case that); as for", "Noun / plain form + なら",
  """なら picks up a topic or situation and gives advice or a reaction to it: 日本に行くなら、京都が
  いい (if you're going to Japan, Kyoto is good). It is less about time order than たら.""",
  r"なら(?!ない|ず)", "日本に行くなら、京都がいいですよ。", after="nva", check=first_lemma("だ"))
P("to_cond", "〜と (whenever)", "when / whenever (natural result)", "Verb (dictionary form) + と",
  """と after a dictionary form describes a natural or automatic result: このボタンを押すと、
  ドアが開く (when you push this button, the door opens). The second part can't be a request or wish.""",
  r"と", "春になると、花が咲きます。", pre="va", check=all_of(first_pos("助詞", "接続助詞"), prev_cf("終止形")))
P("temo", "〜ても", "even if", "Verb/adj (て-form) + も",
  """ても means "even if / even though": 雨が降っても行く (I'll go even if it rains).
  After nouns and な-adjectives it becomes でも: 子供でも分かる.""",
  r"(?:て|で)も", "雨が降っても行きます。", pre="va", check=first_lemma("て"),
  neg=r"てもいい|でもいい|ても良い|てもかまわ|ても構わ")
P("ba_yokatta", "〜ばよかった", "should have, I wish I had", "Verb (ば-form) + よかった",
  """ばよかった expresses regret about something you didn't do: もっと勉強すればよかった
  (I should have studied more). たらよかった is a casual variant.""",
  r"ば(?:よかった|良かった)", "もっと勉強すればよかった。", pre="va")
P("tara_dou", "〜たらどう", "why don't you ...?", "Verb (た-form) + らどう(ですか)",
  """たらどう(ですか) is a friendly suggestion: 医者に行ったらどうですか (why don't you see a doctor?).""",
  # not たらどうする / どうなる / どうしよう (what to do / what happens if ...)
  r"(?:た|だ)らどう(?![しすなや思])", "少し休んだらどうですか。", pre="v")

# ---------------------------------------------------------------- appearance / hearsay / guessing
P("sou_look", "〜そう (looks like)", "looks like, seems about to", "Verb stem / adj stem + そう",
  """そう after a verb stem or adjective stem says how something looks: おいしそう (looks tasty),
  雨が降りそうだ (it looks like it's going to rain). いい becomes よさそう, ない becomes なさそう.""",
  r"そう", "このケーキはおいしそうですね。", pre="va",
  check=lambda t, i, k: t[i].p1 != "副詞" and i > 0 and not t[i - 1].cf.startswith(("終止形", "連体形"))
  and t[i - 1].s not in ("だ", "た"))
P("sou_hear", "〜そうだ (I heard)", "I heard that, they say", "Plain form + そうだ",
  """そうだ after a full plain-form sentence reports hearsay: 明日は雨が降るそうだ (I hear it will
  rain tomorrow). Unlike the "looks like" そう, it attaches to the dictionary/plain form.""",
  r"そう(?:だ|です)", "明日は雨が降るそうです。", after="va",
  check=lambda t, i, k: i > 0 and (t[i - 1].cf.startswith(("終止形", "連体形")) or t[i - 1].s in ("だ", "た")))
P("rashii", "〜らしい (apparently)", "apparently, it seems", "Plain form + らしい",
  """らしい reports what you infer from what you heard or saw: 彼は病気らしい (apparently he's sick).
  It sounds more objective and second-hand than ようだ.""",
  r"らし(?:い|かっ|く)", "彼は来ないらしい。", after="nva", check=first_pos("助動詞"), tail=True)
P("you_da", "〜ようだ", "seems, appears", "Plain form / Noun + の + ようだ",
  """ようだ gives a guess based on your own observation: 誰もいないようだ (it seems no one is here).
  Casual equivalent: みたいだ.""",
  r"よう(?:だ|です|でした|だった)", "誰もいないようです。", after="nva", check=first_lemma("様"))
P("mitai", "〜みたい", "seems, like", "Plain form / Noun + みたい",
  """みたい is the casual version of ようだ: 雨みたい (looks like rain), 子供みたいに (like a child).
  It attaches directly to nouns, without の.""",
  r"みたい", "まるで夢みたいだ。", after="nva")
P("kamoshirenai", "〜かもしれない", "might, maybe", "Plain form / Noun + かもしれない",
  """かもしれない means "might": 明日は雪かもしれない (it might snow tomorrow). Polite:
  かもしれません. Casual speech shortens it to かも.""",
  r"かもしれ(?:ない|ません|なかった)", "明日は雪かもしれません。", after="nva")
P("hazu", "〜はず", "should be, expected to", "Plain form / Noun + の + はず",
  """はず expresses a strong expectation based on facts: 彼はもう着いたはずだ (he should have arrived by
  now). はずがない means "there's no way that ...".""",
  r"はず(?:だ|です|だった|でした|なのに|では|じゃ)?", "彼はもう着いたはずです。", after="nva")
P("darou", "だろう", "probably (casual)", "Plain form / Noun + だろう",
  """だろう is the plain form of でしょう: 明日は晴れるだろう (it'll probably be sunny tomorrow).
  With a rising tone it asks for agreement: "right?".""",
  r"だろう", "明日は晴れるだろう。", after="nva")
P("n_desu", "〜んです", "(explaining / asking for an explanation)", "Plain form + んです / のです",
  """んです (のです) frames a sentence as an explanation or as background: 頭が痛いんです
  (it's that I have a headache). In questions it asks for an explanation: どうしたんですか.""",
  r"(?:ん|の)(?:です|だ)(?:か)?(?=[。？！、]|よ|ね|けど|が)", "頭が痛いんです。", after="va")
P("kana", "〜かな", "I wonder", "Plain form + かな",
  """かな at the end of a sentence means "I wonder": 明日晴れるかな (I wonder if it'll be sunny).
  It's casual; かしら is a softer (traditionally feminine) variant.""",
  r"か(?:な|なあ|しら)(?=[。？！]|$)", "明日は晴れるかな。", after="nva")

# ---------------------------------------------------------------- intention / plans
P("tsumori", "〜つもり", "intend to, plan to", "Verb (dictionary / ない) + つもり",
  """つもり expresses an intention: 来年日本へ行くつもりだ (I intend to go to Japan next year).
  ないつもり is "don't intend to"; つもりはない is a stronger "have no intention".""",
  r"つもり(?:だ|です|だった|でした|は|で)?", "来年日本へ行くつもりです。", after="v")
P("yotei", "〜予定", "plan to, scheduled to", "Verb (dictionary) / Noun + の + 予定",
  """予定 (よてい) is a fixed plan or schedule: 三時に着く予定だ (I'm scheduled to arrive at three).
  It sounds more official than つもり.""",
  r"予定(?:だ|です|だった|でした)", "三時に着く予定です。", after="nv")
P("you_to_omou", "〜ようと思う", "I'm thinking of (doing)", "Verb (volitional) + と思う",
  """The volitional form + と思う announces a decision or plan: 日本語を勉強しようと思う
  (I think I'll study Japanese). ようと思っている means it has been on your mind for a while.""",
  "", "日本語を勉強しようと思います。", custom=m_you_to_omou)
P("volitional", "〜よう (volitional)", "let's; I'll (casual)", "Verb (volitional form)",
  """The volitional form is the casual "let's": 行こう (let's go), 食べよう (let's eat). Godan verbs
  change u → ō (行く → 行こう), ichidan verbs add よう. It's the plain version of ましょう.""",
  "", "一緒に行こう。", custom=m_volitional)

# ---------------------------------------------------------------- て-form helpers
P("te_miru", "〜てみる", "try doing (to see)", "Verb (て-form) + みる",
  """てみる means "do and see": 着てみる (try it on), 食べてみたい (I want to try eating it).
  みる is written in kana here.""",
  r"[てで]み(?:る|れ|ろ|よ)?", "この服を着てみてもいいですか。", pre="v", tail=True,
  check=lambda t, i, k: t[i].lemma == "て" and t[i + 1].lemma == "見る")
P("te_shimau", "〜てしまう", "end up doing; do completely", "Verb (て-form) + しまう",
  """てしまう says an action is completely finished, often with regret: 財布をなくしてしまった
  (I went and lost my wallet). Casual: ちゃう / じゃう (なくしちゃった).""",
  r"[てで]しま(?:う|い|っ|わ|え|お)|(?:ちゃ|じゃ)(?:う|っ|い)", "財布をなくしてしまいました。", pre="v", tail=True)
P("te_oku", "〜ておく", "do in advance", "Verb (て-form) + おく",
  """ておく means doing something in preparation or leaving it that way: ホテルを予約しておく (book the
  hotel in advance). Casual: とく (予約しとく).""",
  r"[てで]お(?:く|き|い|か|け|こ)", "ホテルを予約しておきます。", pre="v", tail=True,
  check=lambda t, i, k: t[i].lemma == "て" and t[i + 1].lemma == "置く")
P("te_aru", "〜てある", "has been done (state)", "Transitive verb (て-form) + ある",
  """てある describes the state left by someone's deliberate action: 窓が開けてある (the window has been
  opened, and is open). The object usually takes が.""",
  r"[てで]" + ARU, "壁に絵がかけてあります。", pre="v", tail=True,
  # 会う is intransitive: 会ってある only comes from 運動会って being split as 運動 + 会っ + て
  check=lambda toks, i, k: toks[i].lemma == "て" and not (i > 0 and toks[i - 1].lemma == "会う"))
P("te_iku", "〜ていく", "go on doing; change from now on", "Verb (て-form) + いく",
  """ていく shows movement or change continuing away from now: これから寒くなっていく
  (it will keep getting colder). Also literal: 持っていく (take something along).""",
  r"[てで]" + IKU, "これからもっと寒くなっていきます。", pre="v", tail=True,
  check=lambda t, i, k: t[i].lemma == "て" and t[i + 1].lemma == "行く")
P("te_kuru", "〜てくる", "come to; start to; go and come back", "Verb (て-form) + くる",
  """てくる shows change up to now or movement toward the speaker: 日本語が分かってきた (I've started to
  understand Japanese), ちょっと買ってくる (I'll go buy it and come back).""",
  r"[てで]" + KURU, "だんだん暖かくなってきました。", pre="v", tail=True,
  check=lambda t, i, k: t[i].lemma == "て" and t[i + 1].lemma == "来る")
P("te_ageru", "〜てあげる", "do for someone", "Verb (て-form) + あげる",
  """てあげる means doing a favor for someone else: 妹に本を読んであげた (I read a book to my sister).
  Using it toward superiors can sound condescending.""",
  r"[てで]あげ", "妹に本を読んであげました。", pre="v", tail=True)
P("te_kureru", "〜てくれる", "someone does (for me)", "Verb (て-form) + くれる",
  """てくれる means someone does something for you (or your group): 友達が手伝ってくれた (a friend helped
  me). てくれませんか is a polite request.""",
  r"[てで]くれ", "友達が手伝ってくれました。", pre="v", tail=True)
P("te_morau", "〜てもらう", "have someone do (for me)", "Verb (て-form) + もらう",
  """てもらう means getting someone to do something for you: 先生に作文を直してもらった
  (I had my teacher correct my essay). The doer takes に.""",
  r"[てで]もら(?:う|い|っ|わ|え|お)", "先生に作文を直してもらいました。", pre="v", tail=True)
P("te_itadaku", "〜ていただけませんか", "could you please ...?", "Verb (て-form) + いただけませんか",
  """ていただけませんか is a very polite request: 窓を開けていただけませんか (could you please open the
  window?). It's the humble form of てもらえませんか.""",
  r"[てで]いただけ(?:ません|ない)(?:か|でしょうか)", "窓を開けていただけませんか。", pre="v")
P("te_hoshii", "〜てほしい", "want someone to do", "Verb (て-form) + ほしい",
  """てほしい expresses wanting someone else to do something: 早く帰ってきてほしい (I want you to come home
  early). The person takes に.""",
  r"[てで]ほし(?:い|かっ|く)", "もっとゆっくり話してほしいです。", pre="v")
P("te_yokatta", "〜てよかった", "I'm glad that", "Verb (て-form) + よかった",
  """てよかった means "I'm glad (that I did)": 日本に来てよかった (I'm glad I came to Japan).""",
  r"[てで](?:よかった|良かった)", "日本に来てよかったです。", pre="v")
P("tagaru", "〜たがる", "(someone else) wants to", "Verb stem + たがる",
  """たがる describes a third person's visible wish: 子供が外で遊びたがっている (the kids want to play
  outside). For your own wishes use たい.""",
  r"たが(?:る|り|っ|ら)", "子供が外で遊びたがっています。", pre="v", tail=True)
P("garu", "〜がる", "(someone) feels / shows", "Adj stem + がる",
  """がる turns a feeling adjective into a verb describing someone else's visible feeling:
  寒がる (act cold), 怖がる (be scared), ほしがる (want).""",
  r"が(?:る|り|っ|ら)", "妹は暗い所を怖がります。", pre="a", tail=True, check=first_pos("接尾辞"))

# ---------------------------------------------------------------- obligation / permission
P("naito", "〜ないといけない", "have to, must", "Verb (ない-form) + といけない",
  """ないといけない is a common spoken "must": もう帰らないといけない (I have to go home now).
  In casual speech the end is often dropped: 帰らないと.""",
  r"ないと(?:いけ(?:ない|ません)|だめ|ダメ)", "もう帰らないといけません。", pre="v")
P("nakute_wa", "〜なくてはいけない", "must, have to", "Verb (ない-form minus い) + くてはいけない/ならない",
  """なくてはいけない / なくてはならない mean "must": 薬を飲まなくてはいけない (I have to take my
  medicine). Casual contraction: なくちゃ.""",
  r"なくて(?:は)?(?:いけ|なら)(?:ない|ません)|なくちゃ|なきゃ", "薬を飲まなくてはいけません。", pre="v")
P("nakute_mo_ii", "〜なくてもいい", "don't have to", "Verb (ない-form minus い) + くてもいい",
  """なくてもいい means "don't need to": 明日は来なくてもいい (you don't have to come tomorrow).""",
  r"なくても(?:いい|よい|良い|かまわ|構わ)", "明日は来なくてもいいです。", pre="va")
P("temo_kamawanai", "〜てもかまわない", "it's fine if, don't mind", "Verb (て-form) + もかまわない",
  """てもかまわない gives permission like てもいい but sounds a little more formal or indifferent:
  ここに座ってもかまいませんか (do you mind if I sit here?).""",
  r"[てで]も(?:かま|構)(?:わない|わず|わん|いません)", "ここに座ってもかまいませんか。", pre="va")
P("cha_ikenai", "〜ちゃいけない", "mustn't (casual)", "Verb (て-form → ちゃ/じゃ) + いけない",
  """ちゃいけない / じゃいけない are the casual contraction of てはいけない: 触っちゃだめ (don't touch!).""",
  # なくちゃいけない is "must" (なくてはいけない), not "mustn't"
  r"(?<!なく)(?:ちゃ|じゃ)(?:いけ|だめ|ダメ)", "ここで泳いじゃいけないよ。", pre="v")

# ---------------------------------------------------------------- potential / passive / causative
P("potential", "Potential form", "can, be able to", "Verb (potential form)",
  """The potential form means "can": 食べられる (can eat), 読める (can read), 来られる, できる.
  Godan verbs change u → eru (書く → 書ける); ichidan verbs add られる. The object often takes が.""",
  "", "私は漢字が読めます。", custom=m_potential, en=r"\b(?:can|could|able|unable)\b")
P("koto_ga_dekiru", "〜ことができる", "can, be able to", "Verb (dictionary) + ことができる",
  """ことができる is a more formal "can": ピアノを弾くことができる (I can play the piano).""",
  r"ことが(?:でき)", "ピアノを弾くことができます。", pre="v", tail=True)
P("passive", "Passive form", "is done (by)", "Verb (passive form)",
  """The passive form (られる / れる) means something is done to the subject: 先生に褒められた (I was
  praised by the teacher). The doer takes に. It also expresses suffering: 雨に降られた (I got rained on).""",
  r"(?:られ|れ)", "私は先生に褒められました。", pre="v", tail=True, check=first_pos("助動詞"),
  en=r"\b(?:was|were|been|be|being|got|get)\s+\w+(?:ed|en|t)\b")
P("causative", "Causative form", "make / let someone do", "Verb (causative: させる / せる)",
  """The causative means "make or let someone do": 子供に野菜を食べさせる (make the child eat
  vegetables). 休ませてください = please let me rest.""",
  r"(?:させ|せ)(?!られ)", "母は私に野菜を食べさせました。", pre="v?", tail=True, check=first_pos("助動詞"),
  en=r"\b(?:made|make|makes|let|lets|allow|allowed|had)\b")
P("causative_passive", "Causative-passive", "be made to do", "Verb (させられる / される)",
  """The causative-passive means being made to do something (against your will): 毎日漢字を書かせられた
  (I was made to write kanji every day).""",
  r"させられ|せられ", "子供の時、ピアノを練習させられました。", pre="v?", tail=True)
P("sasete_kudasai", "〜させてください", "please let me", "Verb (causative て-form) + ください",
  """させてください politely asks for permission: ちょっと考えさせてください (please let me think a bit).""",
  r"(?:させ|せ)て(?:ください|下さい|もらえ|いただけ)", "ちょっと考えさせてください。", pre="v")

# ---------------------------------------------------------------- keigo
P("sonkeigo_verbs", "Honorific verbs (尊敬語)", "(respectful verbs)", "いらっしゃる, おっしゃる, 召し上がる ...",
  """Special honorific verbs raise the other person: いらっしゃる (be/go/come), おっしゃる (say),
  召し上がる (eat/drink), ご覧になる (see), なさる (do), くださる (give me).""",
  r"いらっしゃ(?:る|い|っ|ら)|おっしゃ(?:る|い|っ|ら)|(?:召し上が|めしあが)(?:る|り|っ|ら)|(?:ご覧|ごらん)に" + NARU
  + r"|なさ(?:る|い|っ|ら)", "先生は何とおっしゃいましたか。", tail=True)
P("kenjougo_verbs", "Humble verbs (謙譲語)", "(humble verbs)", "参る, 申す, いたす, 伺う, いただく ...",
  """Humble verbs lower the speaker: 参る (go/come), 申す (say), いたす (do), 伺う (visit/ask),
  いただく (receive/eat), 拝見する (see), おる (be).""",
  r"参(?:る|り|っ)|まい(?:る|り)|申(?:す|し)|(?:いた|致)(?:す|し)|伺(?:う|い|っ)|拝見|(?:いただ|頂)(?:く|き|い)",
  "明日、そちらに伺います。", tail=True, check=lambda t, i, k: t[i].p1 == "動詞" or t[i].lemma == "拝見")
P("o_ni_naru", "お〜になる", "(honorific action)", "お + Verb stem + になる",
  """お + verb stem + になる makes most verbs honorific: お帰りになる (go home), お待ちになる (wait).""",
  r"お[^、。]{1,4}?に" + NARU, "社長はもうお帰りになりました。", tail=True, check=first_pos("接頭辞"))
P("o_suru", "お〜する", "(humble action)", "お + Verb stem + する",
  """お + verb stem + する humbly describes what you do for someone: お持ちします (let me carry it),
  ご案内します (I'll show you around; ご for Sino-Japanese words).""",
  r"(?:お|ご)[^、。]{1,4}?" + SURU, "荷物をお持ちします。", tail=True,
  check=lambda t, i, k: t[i].p1 == "接頭辞" and k - i == 3 and t[i + 1].p1 in ("動詞", "名詞") and t[k - 1].lemma == "為る")
P("o_kudasai_keigo", "お〜ください", "please (honorific request)", "お + Verb stem + ください",
  """お + verb stem + ください is a polite request: お待ちください (please wait), ご注意ください.""",
  r"(?:お|ご)[^、。]{1,4}?(?:ください|下さい)", "少々お待ちください。", check=first_pos("接頭辞"))

# ---------------------------------------------------------------- change / decisions
P("you_ni_suru", "〜ようにする", "make sure to, try to", "Verb (dictionary / ない) + ようにする",
  """ようにする means making an effort to do something regularly: 毎日運動するようにしている
  (I make a point of exercising every day).""",
  r"ように" + SURU, "毎日野菜を食べるようにしています。", after="v", tail=True)
P("you_ni_naru", "〜ようになる", "come to (be able to)", "Verb (dictionary / ない) + ようになる",
  """ようになる describes a change in ability or habit: 日本語が話せるようになった (I've become able to
  speak Japanese).""",
  r"ように" + NARU, "日本語が話せるようになりました。", after="v", tail=True)
P("you_ni", "〜ように (so that)", "so that, in order to", "Verb (dictionary / ない) + ように",
  """ように gives a goal that isn't directly under your control: 忘れないようにメモする (I'll write it
  down so I don't forget). Compare ために, used for direct intentions.""",
  r"ように(?![なしすいおた言頼伝願])", "忘れないようにメモします。", after="v")
P("you_ni_iu", "〜ように言う", "tell someone to", "Verb (dictionary / ない) + ように言う",
  """ように言う reports a request or order: 先生に静かにするように言われた (the teacher told us to be quiet).""",
  r"ように(?=言|いっ|いわ|頼|伝え|注意)", "母に早く寝るように言われました。", after="v")
P("koto_ni_suru", "〜ことにする", "decide to", "Verb (dictionary / ない) + ことにする",
  """ことにする means deciding to do something: 来年留学することにした (I've decided to study abroad next
  year). ことにしている = it's my rule to ...""",
  r"ことに" + SURU, "来年留学することにしました。", after="v", tail=True)
P("koto_ni_naru", "〜ことになる", "it's been decided that", "Verb (dictionary / ない) + ことになる",
  """ことになる says something was decided (by others or circumstances): 来月転勤することになった
  (it's been decided I'll be transferred next month).""",
  r"ことに" + NARU, "来月、大阪に転勤することになりました。", after="v", tail=True)
def _koto_is_thing(t, i, k):
    """こと as "a thing (to do / to ask)" rather than "there are times when": 何もすることがない,
    お願いしたいことがある, 分からないことがあったら, 調べてることがある."""
    text = "".join(x.s for x in t)
    if re.search(r"何|なに|なん|他に|ほかに|たくさん|特に|いっぱい|[1１一]つ|いくつ|もっと"
                 r"|ならない|いけない|なきゃ|べき", text):
        return True
    prev = t[i - 1]
    # やること / すること (things to do), 変なこと (a strange thing)
    if prev.lemma in ("遣る", "為る") or prev.s == "な" or prev.p1 == "形状詞":
        return True
    if prev.lemma == "たい" or (prev.lemma in ("いる", "居る") and i > 1 and t[i - 2].s in ("て", "で")):
        return True
    if prev.s == "てる" or prev.s == "でる":
        return True
    rest = "".join(x.s for x in t[k - 1:])
    return bool(re.match(r"あ(?:ったら|ったの|れば|りまして|りましたら)", rest))


P("koto_ga_aru_some", "〜ことがある (sometimes)", "there are times when", "Verb (dictionary / ない) + ことがある",
  """Dictionary form + ことがある means "sometimes": 朝ご飯を食べないことがある (sometimes I don't eat
  breakfast). With the た-form it means past experience instead.""",
  r"ことが" + ARU, "時々、朝ご飯を食べないことがあります。", after="v", tail=True,
  check=lambda t, i, k: i > 0 and t[i - 1].lemma != "た" and not _koto_is_thing(t, i, k))
P("ku_suru", "〜くする / 〜にする", "make (something) ...", "い-adj (く) / な-adj (に) + する",
  """With する, adjectives describe making a change: 部屋を暖かくする (warm up the room),
  静かにする (be quiet). With なる they describe things changing by themselves.""",
  r"(?:する|し|して)", "音を小さくしてください。", pre="a", tail=True, check=first_lemma("為る"),
  neg=r"なくして|無くして")
P("ga_suru", "〜がする", "(I) sense, there's a smell/sound/taste", "Noun + がする",
  """がする describes what you perceive: いい匂いがする (it smells good), 変な音がする
  (there's a strange sound).""",
  r"(?:匂い|におい|臭い|音|声|味|感じ)が" + SURU, "台所からいい匂いがします。", tail=True)

# ---------------------------------------------------------------- reason / purpose / contrast
_PURPOSE_TAIL = r"、[^。]*?(?:かか(?!わら)|要る|要り|いくら|十分|遅すぎ|必要|便利)"


def _purpose_after_comma(t, k):
    """直すのに、どのくらい時間がかかりますか: のに + comma, then what it takes → purpose, not "although"."""
    return bool(re.match(_PURPOSE_TAIL, "".join(x.s for x in t[k:])))


P("noni", "〜のに (although)", "even though, despite", "Plain form + のに",
  """のに expresses surprise or frustration at an unexpected result: 薬を飲んだのに治らない
  (I took the medicine, but I'm not better).""",
  r"のに(?!便利|必要|使|役|十分|時間|かか|お金)", "薬を飲んだのに、まだ熱があります。", after="nva",
  check=lambda t, i, k: (t[i].p2 == "接続助詞" or (t[i].p2 == "準体助詞" and k < len(t) and t[k].s == "、"))
  and not _purpose_after_comma(t, k))
P("noni_purpose", "〜のに (for)", "for, in order to", "Verb (dictionary) + のに",
  """のに after a dictionary form means "for (the purpose of)": この箱は本を入れるのに便利だ
  (this box is handy for putting books in). It's usually followed by 便利, 必要, 使う, かかる.""",
  r"のに(?=便利|必要|使|役|いい|十分|時間|かか(?!わら)|お金|" + _PURPOSE_TAIL + ")",
  "この箱は本を入れるのに便利です。", after="v")
P("tame_ni", "〜ために", "for, in order to; because of", "Verb (dictionary) / Noun + の + ために",
  """ために gives a purpose you control (日本へ行くために貯金する, save money to go to Japan) or a
  cause (事故のために遅れた, late because of an accident).""",
  r"ため(?:に|の)?", "日本へ行くためにお金を貯めています。", after="nv", check=first_lemma("為"))
P("shi", "〜し", "and also (listing reasons)", "Plain form + し",
  """し lists reasons, implying there are more: 安いし、おいしいし、よく行く (it's cheap and tasty, so I
  go often).""",
  r"し(?=、)", "この店は安いし、おいしいです。", after="nva", check=first_pos("助詞", "接続助詞"))
P("ni_tsuite", "〜について", "about, concerning", "Noun + について",
  """について means "about": 日本の歴史について話す (talk about Japanese history). Before a noun it
  becomes についての.""",
  r"について(?:の|は|も)?", "日本の歴史について話しましょう。", after="n")
P("hou_ga_comp", "〜より〜のほうが", "A is more ... than B", "B + より + A + のほうが",
  """In comparisons, ほうが marks the side that "wins": バスより電車のほうが速い (the train is faster than
  the bus). ほう (方) means "side, direction".""",
  r"(?:の)?(?:ほう|方)が", "バスより電車のほうが速いです。", after="nva", req=r"より",
  neg=r"ほうがいい|方がいい|ほうが良い|方が良い")
P("hodo_nai", "〜ほど〜ない", "not as ... as", "A は B ほど + negative",
  """ほど + negative means "not as ... as": 今年は去年ほど寒くない (this year isn't as cold as last
  year).""",
  r"ほど", "今年は去年ほど寒くないです。", after="nv", req=r"ほど.*(?:ない|ません)")
P("to_onaji", "〜と同じ", "the same as", "Noun + と同じ",
  """と同じ means "the same as": 私のと同じかばん (the same bag as mine). Before a noun it stays 同じ
  (no な).""",
  r"と(?:同じ|おなじ)", "私のと同じかばんですね。", after="any")
P("to_omou", "〜と思う", "I think", "Plain form + と思う",
  """と思う gives your opinion: 明日は雨が降ると思う (I think it'll rain tomorrow). と思っている
  describes a lasting opinion, often someone else's.""",
  r"と(?:思|おも)(?:う|い|っ|わ)", "明日は雨が降ると思います。", after="nva", tail=True)
P("to_iu_quote", "〜と言う", "say that", "Quote + と言う",
  """と marks quoted speech: 彼は行かないと言った (he said he wouldn't go). Direct quotes use 「」.""",
  r"と(?:言|い)(?:う|い|っ|わ)", "彼は行かないと言いました。", after="nva", tail=True,
  check=lambda t, i, k: t[i].p2 == "格助詞")
P("ka_dou_ka", "〜かどうか", "whether or not", "Plain form + かどうか",
  """かどうか embeds a yes/no question: 行けるかどうか分からない (I don't know whether I can go).""",
  r"かどうか", "明日行けるかどうか分かりません。", after="nva")

# ---------------------------------------------------------------- degree / ease
P("sugiru", "〜すぎる", "too (much)", "Verb stem / adj stem + すぎる",
  """すぎる means "too much": 食べすぎた (I ate too much), 高すぎる (too expensive). いい becomes
  よすぎる, ない becomes なさすぎる.""",
  r"(?:過|す)ぎ(?:る|た|て|ます|ない)?", "昨日は食べすぎました。", pre="va", tail=True,
  check=first_lemma("過ぎる"))
P("yasui", "〜やすい", "easy to", "Verb stem + やすい",
  """やすい after a verb stem means "easy to do": この本は読みやすい (this book is easy to read).""",
  r"やす(?:い|く|かっ)", "この本は読みやすいです。", pre="v", check=first_lemma("易い", "やすい"))
P("nikui", "〜にくい", "hard to", "Verb stem + にくい",
  """にくい after a verb stem means "hard to do": この字は読みにくい (this handwriting is hard to read).""",
  r"にく(?:い|く|かっ)", "この字は読みにくいです。", pre="v", check=first_lemma("難い", "にくい"))
P("hajimeru", "〜始める", "start to", "Verb stem + 始める",
  """始める (はじめる) after a verb stem means "start doing": 雨が降り始めた (it started to rain).""",
  r"(?:始|はじ)め", "雨が降り始めました。", pre="v", tail=True, check=first_lemma("始める"))
P("owaru", "〜終わる", "finish doing", "Verb stem + 終わる",
  """終わる (おわる) after a verb stem means "finish doing": 本を読み終わった (I finished reading the book).""",
  r"(?:終|お)わ(?:る|り|っ|ら)", "その本はもう読み終わりました。", pre="v", tail=True, check=first_lemma("終わる"))
P("tsuzukeru", "〜続ける", "keep doing", "Verb stem + 続ける",
  """続ける (つづける) after a verb stem means "continue doing": 一時間歩き続けた (I kept walking for an
  hour).""",
  r"(?:続|つづ)け", "一時間歩き続けました。", pre="v", tail=True, check=first_lemma("続ける"))
P("sa", "〜さ", "-ness (noun from adjective)", "Adj stem + さ",
  """さ turns an adjective into a measurable noun: 高さ (height), 大切さ (importance).""",
  r"さ", "この山の高さは何メートルですか。", pre="a", check=first_pos("接尾辞"))

# ---------------------------------------------------------------- time
P("aida", "〜間 / 間に", "while, during", "Verb (ている) / Noun + の + 間(に)",
  """間 (あいだ) means "throughout the time": 夏休みの間、ずっと家にいた. 間に means "at some point during":
  留守の間に泥棒が入った (a burglar came in while I was out).""",
  r"(?:間|あいだ)(?:に|は|中)?", "私が寝ている間に、雪が降りました。", after="nv",
  check=lambda t, i, k: t[i].kana == "あいだ")
P("uchi_ni", "〜うちに", "while (still); before it changes", "Verb / adj / Noun + の + うちに",
  """うちに means doing something while a state lasts: 若いうちに旅行したい (I want to travel while I'm
  young). ないうちに = before something happens.""",
  r"うちに", "若いうちにたくさん旅行したいです。", after="nva", check=first_lemma("内"))
P("made_ni", "〜までに", "by (deadline)", "Noun / Verb + までに",
  """までに sets a deadline: 五時までに帰る (be back by five). Compare まで, "until".""",
  r"までに", "五時までに帰ってください。", after="nv")
P("tokoro_da", "〜ところだ", "about to / in the middle of / just did", "Verb + ところだ",
  """ところ shows the stage of an action: 出かけるところだ (about to leave), 食べているところだ (in the middle
  of eating), 着いたところだ (just arrived).""",
  r"ところ(?:だ|です|だった|でした)", "今、出かけるところです。", after="v")
P("tabakari", "〜たばかり", "just did", "Verb (た-form) + ばかり",
  """たばかり means something happened very recently: 日本に来たばかりだ (I've only just come to Japan).
  It feels more subjective than たところ.""",
  r"ばかり(?:だ|です|なのに|の|で)?", "日本に来たばかりです。", pre="v", check=prev_is("た", "だ"))
P("mama", "〜まま", "as it is, unchanged", "Verb (た) / Noun + の / adj + まま",
  """まま means leaving something in a state: 靴のまま入る (go in with your shoes on), 窓を開けたまま寝た
  (I slept with the window open).""",
  r"まま(?:に|で|だ|です)?", "窓を開けたまま寝てしまいました。", after="nva")
P("naide", "〜ないで (without)", "without doing", "Verb (ない-form) + で",
  """ないで connects "without doing": 朝ご飯を食べないで学校に行った (I went to school without eating
  breakfast).""",
  r"ないで(?!くだ|下さ|ほし|もら|いただ|いる|い|ください)", "朝ご飯を食べないで学校に行きました。", pre="v")
P("zu_ni", "〜ずに", "without doing (written)", "Verb (ない-stem) + ずに",
  """ずに is the more written equivalent of ないで: 何も言わずに帰った (left without saying anything).
  する becomes せずに.""",
  r"ずに", "彼は何も言わずに帰りました。", pre="v")
P("nakute", "〜なくて", "because not", "Verb/adj (ない-form minus い) + くて",
  """なくて gives a negative reason: 友達が来なくて寂しかった (I was lonely because my friend didn't
  come).""",
  r"なくて(?!は|も)", "バスが来なくて困りました。", pre="va")

# ---------------------------------------------------------------- particles & small words
P("zutsu", "〜ずつ", "each, at a time", "Amount + ずつ",
  """ずつ means "each" or "at a time": 一人に二つずつ (two for each person), 少しずつ (little by little).""",
  r"ずつ", "毎日少しずつ勉強しています。", after="any")
P("oki_ni", "〜おきに", "every other, at intervals of", "Amount + おきに",
  """おきに means "skipping": 一日おきに (every other day), 五メートルおきに (every five meters).""",
  r"おきに", "一日おきにジョギングをしています。", after="n")
P("toka", "〜とか", "things like, or", "Noun / Verb + とか",
  """とか lists examples casually: 本とか雑誌とか (books, magazines and such). It's the spoken
  counterpart of や...など.""",
  r"とか(?![^。]*とか)", "週末は映画とか買い物とかに行きます。", after="nv", check=first_pos("助詞"))  # blank the last one
P("nado", "〜など / なんか", "and so on, things like", "Noun + など",
  """など means "and so on / such as": 果物などを買った. なんか is a casual version that can also be
  dismissive: 宿題なんかしたくない.""",
  r"など|なんか", "りんごやバナナなどを買いました。", after="n", check=first_pos("助詞"))
P("demo_suggest", "〜でも (or something)", "or something, even", "Noun + でも",
  """でも after a noun softens a suggestion: お茶でも飲みませんか (would you like some tea or something?).
  It can also mean "even": 子供でも分かる.""",
  r"でも", "お茶でも飲みませんか。", after="n",
  check=lambda t, i, k: t[i].p1 == "助詞",
  req=r"でも.{0,8}(?:ませんか|ましょう|どう|いかが|しよう|行こう|飲もう|食べよう)")
P("q_ka", "Question word + か", "some- (something, someone)", "何か, 誰か, どこか, いつか",
  """Question word + か makes an indefinite word: 何か (something), 誰か (someone), どこか (somewhere),
  いつか (someday).""",
  r"(?:何|なに|誰|だれ|どこ|いつ|どれ)か", "何か飲みたいです。", check=lambda t, i, k: t[k - 1].p2 == "副助詞")
P("q_mo", "Question word + も", "no- / every- (with negative / positive)", "何も, 誰も, どこも, いつも",
  """Question word + も with a negative means "no-": 何も食べない (eat nothing), 誰も来ない (no one comes).
  いつも and どこも are also used positively: always, everywhere.""",
  r"(?:何|なに|誰|だれ|どこ|どれ)も", "昨日は何も食べませんでした。")
P("q_demo", "Question word + でも", "any- (whatever, anyone)", "何でも, 誰でも, どこでも, いつでも",
  """Question word + でも means "any-": 何でも食べる (I'll eat anything), いつでもいい (any time is fine).""",
  r"(?:何|なん|なに|誰|だれ|どこ|いつ|どれ)でも", "私は何でも食べます。")
