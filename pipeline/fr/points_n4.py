"""French texts for the N4 grammar points (written for this app, not translated word for word)."""

FR = {
    "ba": dict(
        meaning="si (condition)",
        structure="Verbe / adjectif (forme en ば)",
        explanation="""La forme en ば pose une condition : 安ければ買う (si c'est bon marché, je
        l'achète). Les verbes changent leur dernier son en « u » en « e » + ば (行く → 行けば) ; les
        adjectifs en い prennent ければ. Elle insiste souvent sur ce qu'il faut pour obtenir le
        résultat.""",
    ),
    "tara": dict(
        meaning="si / quand (une fois que)",
        structure="Verbe / adjectif (forme en た) + ら",
        explanation="""たら est le « si / quand » le plus souple : une fois la première chose
        arrivée, la seconde suit. 帰ったら電話する (je t'appelle quand je rentre). Il se forme sur la
        forme en た : 食べたら, 高かったら.""",
    ),
    "nara": dict(
        meaning="si (c'est le cas que) ; quant à",
        structure="Nom / forme neutre + なら",
        explanation="""なら reprend un sujet ou une situation pour donner un conseil ou une
        réaction : 日本に行くなら、京都がいい (si tu vas au Japon, Kyoto, c'est bien). Il exprime
        moins un ordre dans le temps que たら.""",
    ),
    "to_cond": dict(
        title="〜と (chaque fois que)",
        meaning="quand / chaque fois que (conséquence naturelle)",
        structure="Verbe (forme du dictionnaire) + と",
        explanation="""と après la forme du dictionnaire décrit une conséquence naturelle ou
        automatique : このボタンを押すと、ドアが開く (quand on appuie sur ce bouton, la porte
        s'ouvre). La seconde partie ne peut pas être une demande ou un souhait.""",
    ),
    "temo": dict(
        meaning="même si",
        structure="Verbe / adjectif (forme en て) + も",
        explanation="""ても signifie « même si / bien que » : 雨が降っても行く (j'y vais même s'il
        pleut). Après un nom ou un adjectif en な, il devient でも : 子供でも分かる (même un enfant
        comprend).""",
    ),
    "ba_yokatta": dict(
        meaning="j'aurais dû, si seulement j'avais …",
        structure="Verbe (forme en ば) + よかった",
        explanation="""ばよかった exprime le regret de ne pas avoir fait quelque chose :
        もっと勉強すればよかった (j'aurais dû étudier davantage). たらよかった en est une variante
        familière.""",
    ),
    "tara_dou": dict(
        meaning="et si tu … ?",
        structure="Verbe (forme en た) + らどう(ですか)",
        explanation="""たらどう(ですか) est une suggestion amicale : 医者に行ったらどうですか (et si
        vous alliez voir un médecin ?).""",
    ),
    "sou_look": dict(
        title="〜そう (avoir l'air)",
        meaning="avoir l'air, être sur le point de",
        structure="Radical du verbe / de l'adjectif + そう",
        explanation="""そう après un radical de verbe ou d'adjectif décrit l'apparence : おいしそう
        (ça a l'air bon), 雨が降りそうだ (on dirait qu'il va pleuvoir). いい devient よさそう, ない
        devient なさそう.""",
    ),
    "sou_hear": dict(
        title="〜そうだ (on dit que)",
        meaning="j'ai entendu dire que, il paraît que",
        structure="Forme neutre + そうだ",
        explanation="""そうだ après une phrase complète à la forme neutre rapporte un ouï-dire :
        明日は雨が降るそうだ (il paraît qu'il pleuvra demain). Contrairement au そう « avoir l'air »,
        il se met après la forme du dictionnaire ou la forme neutre.""",
    ),
    "rashii": dict(
        title="〜らしい (apparemment)",
        meaning="apparemment, il semble que",
        structure="Forme neutre + らしい",
        explanation="""らしい rapporte ce qu'on déduit de ce qu'on a entendu ou vu : 彼は病気らしい
        (apparemment, il est malade). Il paraît plus objectif et plus « de seconde main » que
        ようだ.""",
    ),
    "you_da": dict(
        meaning="il semble que, on dirait",
        structure="Forme neutre / Nom + の + ようだ",
        explanation="""ようだ donne une supposition fondée sur sa propre observation :
        誰もいないようだ (on dirait qu'il n'y a personne). Équivalent familier : みたいだ.""",
    ),
    "mitai": dict(
        meaning="on dirait, comme",
        structure="Forme neutre / Nom + みたい",
        explanation="""みたい est la version familière de ようだ : 雨みたい (on dirait qu'il pleut),
        子供みたいに (comme un enfant). Il se met directement après un nom, sans の.""",
    ),
    "kamoshirenai": dict(
        meaning="peut-être, il se peut que",
        structure="Forme neutre / Nom + かもしれない",
        explanation="""かもしれない signifie « il se peut que » : 明日は雪かもしれない (il va
        peut-être neiger demain). Forme polie : かもしれません. À l'oral familier, on l'abrège en
        かも.""",
    ),
    "hazu": dict(
        meaning="devrait, normalement",
        structure="Forme neutre / Nom + の + はず",
        explanation="""はず exprime une attente solide fondée sur des faits : 彼はもう着いたはずだ (il
        devrait déjà être arrivé). はずがない signifie « il est impossible que … ».""",
    ),
    "darou": dict(
        meaning="sans doute (familier)",
        structure="Forme neutre / Nom + だろう",
        explanation="""だろう est la forme neutre de でしょう : 明日は晴れるだろう (il fera sans doute
        beau demain). Avec une intonation montante, il demande l'approbation : « hein ? ».""",
    ),
    "n_desu": dict(
        meaning="(c'est que … : explication)",
        structure="Forme neutre + んです / のです",
        explanation="""んです (のです) présente une phrase comme une explication ou un contexte :
        頭が痛いんです (c'est que j'ai mal à la tête). Dans une question, il demande une
        explication : どうしたんですか (qu'est-ce qui se passe ?).""",
    ),
    "kana": dict(
        meaning="je me demande si",
        structure="Forme neutre + かな",
        explanation="""かな en fin de phrase signifie « je me demande » : 明日晴れるかな (je me
        demande s'il fera beau demain). C'est familier ; かしら en est une variante plus douce
        (traditionnellement féminine).""",
    ),
    "tsumori": dict(
        meaning="avoir l'intention de",
        structure="Verbe (forme du dictionnaire / en ない) + つもり",
        explanation="""つもり exprime une intention : 来年日本へ行くつもりだ (j'ai l'intention d'aller
        au Japon l'an prochain). ないつもり signifie « ne pas avoir l'intention de » ; つもりはない
        est un refus plus net : « je n'ai aucune intention de ».""",
    ),
    "yotei": dict(
        meaning="il est prévu que",
        structure="Verbe (forme du dictionnaire) / Nom + の + 予定",
        explanation="""予定 (よてい) désigne un programme arrêté : 三時に着く予定だ (je dois arriver à
        trois heures). Il sonne plus officiel que つもり.""",
    ),
    "you_to_omou": dict(
        meaning="je pense (faire)",
        structure="Verbe (forme volitive) + と思う",
        explanation="""La forme volitive + と思う annonce une décision ou un projet :
        日本語を勉強しようと思う (je pense me mettre au japonais). ようと思っている indique que l'idée
        vous trotte dans la tête depuis un moment.""",
    ),
    "volitional": dict(
        title="〜よう (volitif)",
        meaning="… -ons ! ; je vais … (familier)",
        structure="Verbe (forme volitive)",
        explanation="""La forme volitive est le « allons-y » familier : 行こう (allons-y), 食べよう
        (mangeons). Les verbes du groupe 1 changent « u » en « ō » (行く → 行こう), ceux du groupe 2
        ajoutent よう. C'est la version neutre de ましょう.""",
    ),
    "te_miru": dict(
        meaning="essayer de (pour voir)",
        structure="Verbe (forme en て) + みる",
        explanation="""てみる signifie « faire pour voir » : 着てみる (l'essayer, pour un vêtement),
        食べてみたい (j'aimerais goûter). Dans cet emploi, みる s'écrit en kana.""",
    ),
    "te_shimau": dict(
        meaning="finir par ; faire complètement",
        structure="Verbe (forme en て) + しまう",
        explanation="""てしまう indique qu'une action est complètement achevée, souvent avec un
        regret : 財布をなくしてしまった (j'ai perdu mon portefeuille, zut). Forme familière :
        ちゃう / じゃう (なくしちゃった).""",
    ),
    "te_oku": dict(
        meaning="faire à l'avance",
        structure="Verbe (forme en て) + おく",
        explanation="""ておく signifie faire quelque chose en prévision, ou le laisser dans cet
        état : ホテルを予約しておく (réserver l'hôtel à l'avance). Forme familière : とく
        (予約しとく).""",
    ),
    "te_aru": dict(
        meaning="avoir été fait (état)",
        structure="Verbe transitif (forme en て) + ある",
        explanation="""てある décrit l'état laissé par l'action volontaire de quelqu'un :
        窓が開けてある (la fenêtre a été ouverte, et elle l'est restée). L'objet prend
        généralement が.""",
    ),
    "te_iku": dict(
        meaning="continuer à ; évoluer à partir de maintenant",
        structure="Verbe (forme en て) + いく",
        explanation="""ていく montre un mouvement ou un changement qui se poursuit à partir de
        maintenant : これから寒くなっていく (il va faire de plus en plus froid). Aussi au sens
        propre : 持っていく (emporter).""",
    ),
    "te_kuru": dict(
        meaning="commencer à ; aller (faire) et revenir",
        structure="Verbe (forme en て) + くる",
        explanation="""てくる montre un changement jusqu'à maintenant, ou un mouvement vers celui qui
        parle : 日本語が分かってきた (je commence à comprendre le japonais), ちょっと買ってくる (je
        vais l'acheter et je reviens).""",
    ),
    "te_ageru": dict(
        meaning="faire pour quelqu'un",
        structure="Verbe (forme en て) + あげる",
        explanation="""てあげる signifie rendre service à quelqu'un d'autre : 妹に本を読んであげた
        (j'ai lu un livre à ma petite sœur). Employé envers un supérieur, il peut sembler
        condescendant.""",
    ),
    "te_kureru": dict(
        meaning="quelqu'un fait (pour moi)",
        structure="Verbe (forme en て) + くれる",
        explanation="""てくれる signifie que quelqu'un fait quelque chose pour vous (ou votre
        groupe) : 友達が手伝ってくれた (un ami m'a aidé). てくれませんか est une demande polie.""",
    ),
    "te_morau": dict(
        meaning="se faire faire (par quelqu'un)",
        structure="Verbe (forme en て) + もらう",
        explanation="""てもらう signifie obtenir que quelqu'un fasse quelque chose pour vous :
        先生に作文を直してもらった (mon professeur a corrigé ma rédaction pour moi). Celui qui fait
        l'action prend に.""",
    ),
    "te_itadaku": dict(
        meaning="pourriez-vous … ?",
        structure="Verbe (forme en て) + いただけませんか",
        explanation="""ていただけませんか est une demande très polie : 窓を開けていただけませんか
        (pourriez-vous ouvrir la fenêtre ?). C'est la forme de modestie de てもらえませんか.""",
    ),
    "te_hoshii": dict(
        meaning="vouloir que quelqu'un fasse",
        structure="Verbe (forme en て) + ほしい",
        explanation="""てほしい exprime le souhait qu'une autre personne fasse quelque chose :
        早く帰ってきてほしい (je veux que tu rentres tôt). La personne prend に.""",
    ),
    "te_yokatta": dict(
        meaning="je suis content que",
        structure="Verbe (forme en て) + よかった",
        explanation="""てよかった signifie « je suis content (d'avoir fait) » : 日本に来てよかった (je
        suis content d'être venu au Japon).""",
    ),
    "tagaru": dict(
        meaning="(quelqu'un d'autre) veut",
        structure="Radical du verbe + たがる",
        explanation="""たがる décrit l'envie visible d'une autre personne :
        子供が外で遊びたがっている (les enfants veulent jouer dehors). Pour ses propres envies, on
        utilise たい.""",
    ),
    "garu": dict(
        meaning="(quelqu'un) montre, ressent",
        structure="Radical de l'adjectif + がる",
        explanation="""がる transforme un adjectif de sentiment en verbe qui décrit le sentiment
        visible de quelqu'un d'autre : 寒がる (être frileux), 怖がる (avoir peur), ほしがる
        (convoiter).""",
    ),
    "naito": dict(
        meaning="devoir, il faut",
        structure="Verbe (forme en ない) + といけない",
        explanation="""ないといけない est un « il faut » très courant à l'oral :
        もう帰らないといけない (je dois rentrer maintenant). À l'oral familier, on laisse souvent
        tomber la fin : 帰らないと.""",
    ),
    "nakute_wa": dict(
        meaning="devoir, il faut",
        structure="Verbe (forme en ない sans い) + くてはいけない / ならない",
        explanation="""なくてはいけない / なくてはならない signifient « devoir » :
        薬を飲まなくてはいけない (je dois prendre mon médicament). Contraction familière :
        なくちゃ.""",
    ),
    "nakute_mo_ii": dict(
        meaning="ne pas être obligé de",
        structure="Verbe (forme en ない sans い) + くてもいい",
        explanation="""なくてもいい signifie « pas besoin de » : 明日は来なくてもいい (tu n'es pas
        obligé de venir demain).""",
    ),
    "temo_kamawanai": dict(
        meaning="ça ne dérange pas que",
        structure="Verbe (forme en て) + もかまわない",
        explanation="""てもかまわない donne une permission comme てもいい, mais sonne un peu plus
        soutenu ou indifférent : ここに座ってもかまいませんか (ça vous dérange si je
        m'assieds ici ?).""",
    ),
    "cha_ikenai": dict(
        meaning="il ne faut pas (familier)",
        structure="Verbe (forme en て → ちゃ / じゃ) + いけない",
        explanation="""ちゃいけない / じゃいけない sont la contraction familière de てはいけない :
        触っちゃだめ (pas touche !).""",
    ),
    "potential": dict(
        title="Forme potentielle",
        meaning="pouvoir, être capable de",
        structure="Verbe (forme potentielle)",
        explanation="""La forme potentielle signifie « pouvoir » : 食べられる (pouvoir manger), 読める
        (savoir lire), 来られる, できる. Les verbes du groupe 1 changent « u » en « eru » (書く →
        書ける) ; ceux du groupe 2 ajoutent られる. L'objet prend souvent が.""",
    ),
    "koto_ga_dekiru": dict(
        meaning="pouvoir, être capable de",
        structure="Verbe (forme du dictionnaire) + ことができる",
        explanation="""ことができる est un « pouvoir » plus soutenu : ピアノを弾くことができる (je
        sais jouer du piano).""",
    ),
    "passive": dict(
        title="Forme passive",
        meaning="être fait (par)",
        structure="Verbe (forme passive)",
        explanation="""La forme passive (られる / れる) indique que le sujet subit l'action :
        先生に褒められた (j'ai été félicité par le professeur). Celui qui agit prend に. Elle exprime
        aussi un désagrément subi : 雨に降られた (je me suis fait surprendre par la pluie).""",
    ),
    "causative": dict(
        title="Forme causative",
        meaning="faire faire / laisser faire",
        structure="Verbe (causatif : させる / せる)",
        explanation="""Le causatif signifie « faire faire » ou « laisser faire » :
        子供に野菜を食べさせる (faire manger des légumes à l'enfant). 休ませてください = laissez-moi
        me reposer.""",
    ),
    "causative_passive": dict(
        title="Causatif passif",
        meaning="être obligé de faire",
        structure="Verbe (させられる / される)",
        explanation="""Le causatif passif signifie être obligé de faire quelque chose (contre son
        gré) : 毎日漢字を書かせられた (on m'obligeait à écrire des kanji tous les jours).""",
    ),
    "sasete_kudasai": dict(
        meaning="permettez-moi de",
        structure="Verbe (forme en て du causatif) + ください",
        explanation="""させてください demande poliment une permission : ちょっと考えさせてください
        (laissez-moi réfléchir un peu).""",
    ),
    "sonkeigo_verbs": dict(
        title="Verbes honorifiques (尊敬語)",
        meaning="(verbes de respect)",
        structure="いらっしゃる, おっしゃる, 召し上がる …",
        explanation="""Des verbes honorifiques spéciaux élèvent l'autre personne : いらっしゃる
        (être / aller / venir), おっしゃる (dire), 召し上がる (manger / boire), ご覧になる (voir),
        なさる (faire), くださる (me donner).""",
    ),
    "kenjougo_verbs": dict(
        title="Verbes de modestie (謙譲語)",
        meaning="(verbes de modestie)",
        structure="参る, 申す, いたす, 伺う, いただく …",
        explanation="""Les verbes de modestie abaissent celui qui parle : 参る (aller / venir), 申す
        (dire), いたす (faire), 伺う (rendre visite / demander), いただく (recevoir / manger),
        拝見する (voir), おる (être).""",
    ),
    "o_ni_naru": dict(
        meaning="(action honorifique)",
        structure="お + radical du verbe + になる",
        explanation="""お + radical du verbe + になる rend honorifique la plupart des verbes :
        お帰りになる (rentrer), お待ちになる (attendre).""",
    ),
    "o_suru": dict(
        meaning="(action de modestie)",
        structure="お + radical du verbe + する",
        explanation="""お + radical du verbe + する décrit avec modestie ce que l'on fait pour
        quelqu'un : お持ちします (je vais le porter pour vous), ご案内します (je vais vous guider ;
        ご pour les mots d'origine chinoise).""",
    ),
    "o_kudasai_keigo": dict(
        meaning="veuillez … (demande honorifique)",
        structure="お + radical du verbe + ください",
        explanation="""お + radical du verbe + ください est une demande polie : お待ちください
        (veuillez patienter), ご注意ください (attention, s'il vous plaît).""",
    ),
    "you_ni_suru": dict(
        meaning="faire en sorte de, veiller à",
        structure="Verbe (forme du dictionnaire / en ない) + ようにする",
        explanation="""ようにする signifie faire un effort pour faire quelque chose
        régulièrement : 毎日運動するようにしている (je veille à faire du sport tous les jours).""",
    ),
    "you_ni_naru": dict(
        meaning="en venir à (pouvoir)",
        structure="Verbe (forme du dictionnaire / en ない) + ようになる",
        explanation="""ようになる décrit un changement de capacité ou d'habitude :
        日本語が話せるようになった (je suis maintenant capable de parler japonais).""",
    ),
    "you_ni": dict(
        title="〜ように (pour que)",
        meaning="pour que, afin de",
        structure="Verbe (forme du dictionnaire / en ない) + ように",
        explanation="""ように donne un but qui ne dépend pas directement de votre volonté :
        忘れないようにメモする (je le note pour ne pas oublier). Comparez avec ために, utilisé pour
        une intention directe.""",
    ),
    "you_ni_iu": dict(
        meaning="dire (à quelqu'un) de",
        structure="Verbe (forme du dictionnaire / en ない) + ように言う",
        explanation="""ように言う rapporte une demande ou un ordre : 先生に静かにするように言われた
        (le professeur nous a dit de nous taire).""",
    ),
    "koto_ni_suru": dict(
        meaning="décider de",
        structure="Verbe (forme du dictionnaire / en ない) + ことにする",
        explanation="""ことにする signifie décider de faire quelque chose : 来年留学することにした (j'ai
        décidé de partir étudier à l'étranger l'an prochain). ことにしている = je me suis fixé
        comme règle de …""",
    ),
    "koto_ni_naru": dict(
        meaning="il a été décidé que",
        structure="Verbe (forme du dictionnaire / en ない) + ことになる",
        explanation="""ことになる indique qu'une décision a été prise (par d'autres ou par les
        circonstances) : 来月転勤することになった (il a été décidé que je serai muté le mois
        prochain).""",
    ),
    "koto_ga_aru_some": dict(
        title="〜ことがある (parfois)",
        meaning="il arrive que",
        structure="Verbe (forme du dictionnaire / en ない) + ことがある",
        explanation="""Forme du dictionnaire + ことがある signifie « parfois » :
        朝ご飯を食べないことがある (il m'arrive de ne pas prendre de petit-déjeuner). Avec la forme
        en た, il exprime au contraire une expérience passée.""",
    ),
    "ku_suru": dict(
        meaning="rendre (quelque chose) …",
        structure="Adj. en い (く) / adj. en な (に) + する",
        explanation="""Avec する, les adjectifs décrivent un changement que l'on provoque :
        部屋を暖かくする (réchauffer la pièce), 静かにする (faire silence). Avec なる, ils décrivent
        un changement qui se produit tout seul.""",
    ),
    "ga_suru": dict(
        meaning="(on) sent, il y a une odeur / un bruit / un goût",
        structure="Nom + がする",
        explanation="""がする décrit ce que l'on perçoit : いい匂いがする (ça sent bon), 変な音がする
        (il y a un bruit bizarre).""",
    ),
    "noni": dict(
        title="〜のに (bien que)",
        meaning="alors que, pourtant",
        structure="Forme neutre + のに",
        explanation="""のに exprime la surprise ou l'agacement face à un résultat inattendu :
        薬を飲んだのに治らない (j'ai pris le médicament, et pourtant je ne guéris pas).""",
    ),
    "noni_purpose": dict(
        title="〜のに (pour)",
        meaning="pour, afin de",
        structure="Verbe (forme du dictionnaire) + のに",
        explanation="""のに après la forme du dictionnaire signifie « pour (faire) » :
        この箱は本を入れるのに便利だ (cette boîte est pratique pour ranger des livres). Il est
        généralement suivi de 便利, 必要, 使う ou かかる.""",
    ),
    "tame_ni": dict(
        meaning="pour, afin de ; à cause de",
        structure="Verbe (forme du dictionnaire) / Nom + の + ために",
        explanation="""ために donne un but que l'on maîtrise (日本へ行くために貯金する, économiser
        pour aller au Japon) ou une cause (事故のために遅れた, en retard à cause d'un
        accident).""",
    ),
    "shi": dict(
        meaning="et en plus (énumération de raisons)",
        structure="Forme neutre + し",
        explanation="""し énumère des raisons, en sous-entendant qu'il y en a d'autres :
        安いし、おいしいし、よく行く (c'est bon marché, c'est bon, alors j'y vais souvent).""",
    ),
    "ni_tsuite": dict(
        meaning="au sujet de, concernant",
        structure="Nom + について",
        explanation="""について signifie « au sujet de » : 日本の歴史について話す (parler de l'histoire
        du Japon). Devant un nom, il devient についての.""",
    ),
    "hou_ga_comp": dict(
        meaning="A est plus … que B",
        structure="B + より + A + のほうが",
        explanation="""Dans une comparaison, ほうが marque le côté qui « l'emporte » :
        バスより電車のほうが速い (le train est plus rapide que le bus). ほう (方) signifie « côté,
        direction ».""",
    ),
    "hodo_nai": dict(
        meaning="pas aussi … que",
        structure="A は B ほど + forme négative",
        explanation="""ほど + forme négative signifie « pas aussi … que » : 今年は去年ほど寒くない
        (cette année, il ne fait pas aussi froid que l'an dernier).""",
    ),
    "to_onaji": dict(
        meaning="le même que",
        structure="Nom + と同じ",
        explanation="""と同じ signifie « le même que » : 私のと同じかばん (le même sac que le mien).
        Devant un nom, 同じ reste tel quel (sans な).""",
    ),
    "to_omou": dict(
        meaning="je pense que",
        structure="Forme neutre + と思う",
        explanation="""と思う donne son avis : 明日は雨が降ると思う (je pense qu'il pleuvra demain).
        と思っている décrit une opinion durable, souvent celle de quelqu'un d'autre.""",
    ),
    "to_iu_quote": dict(
        meaning="dire que",
        structure="Citation + と言う",
        explanation="""と marque les paroles rapportées : 彼は行かないと言った (il a dit qu'il n'irait
        pas). Les citations directes se mettent entre 「」.""",
    ),
    "ka_dou_ka": dict(
        meaning="si … ou non",
        structure="Forme neutre + かどうか",
        explanation="""かどうか intègre une question fermée dans une phrase : 行けるかどうか分からない
        (je ne sais pas si je pourrai y aller).""",
    ),
    "sugiru": dict(
        meaning="trop",
        structure="Radical du verbe / de l'adjectif + すぎる",
        explanation="""すぎる signifie « trop » : 食べすぎた (j'ai trop mangé), 高すぎる (trop cher).
        いい devient よすぎる, ない devient なさすぎる.""",
    ),
    "yasui": dict(
        meaning="facile à",
        structure="Radical du verbe + やすい",
        explanation="""やすい après un radical de verbe signifie « facile à faire » :
        この本は読みやすい (ce livre est facile à lire).""",
    ),
    "nikui": dict(
        meaning="difficile à",
        structure="Radical du verbe + にくい",
        explanation="""にくい après un radical de verbe signifie « difficile à faire » :
        この字は読みにくい (cette écriture est difficile à lire).""",
    ),
    "hajimeru": dict(
        meaning="commencer à",
        structure="Radical du verbe + 始める",
        explanation="""始める (はじめる) après un radical de verbe signifie « commencer à » :
        雨が降り始めた (il a commencé à pleuvoir).""",
    ),
    "owaru": dict(
        meaning="finir de",
        structure="Radical du verbe + 終わる",
        explanation="""終わる (おわる) après un radical de verbe signifie « finir de » :
        本を読み終わった (j'ai fini de lire le livre).""",
    ),
    "tsuzukeru": dict(
        meaning="continuer à",
        structure="Radical du verbe + 続ける",
        explanation="""続ける (つづける) après un radical de verbe signifie « continuer à » :
        一時間歩き続けた (j'ai marché pendant une heure sans m'arrêter).""",
    ),
    "sa": dict(
        meaning="(nom tiré d'un adjectif : « -eur », « -ité »)",
        structure="Radical de l'adjectif + さ",
        explanation="""さ transforme un adjectif en nom mesurable : 高さ (la hauteur), 大切さ
        (l'importance).""",
    ),
    "aida": dict(
        meaning="pendant (que)",
        structure="Verbe (ている) / Nom + の + 間(に)",
        explanation="""間 (あいだ) signifie « pendant toute la durée » : 夏休みの間、ずっと家にいた
        (je suis resté à la maison pendant toutes les vacances d'été). 間に signifie « à un moment
        pendant » : 留守の間に泥棒が入った (un cambrioleur est entré pendant mon absence).""",
    ),
    "uchi_ni": dict(
        meaning="tant que ; avant que ça change",
        structure="Verbe / adjectif / Nom + の + うちに",
        explanation="""うちに signifie faire quelque chose tant qu'un état dure : 若いうちに旅行したい
        (je veux voyager tant que je suis jeune). ないうちに = avant que quelque chose
        n'arrive.""",
    ),
    "made_ni": dict(
        meaning="d'ici (échéance)",
        structure="Nom / Verbe + までに",
        explanation="""までに fixe une échéance : 五時までに帰る (rentrer avant cinq heures).
        Comparez avec まで, « jusqu'à ».""",
    ),
    "tokoro_da": dict(
        meaning="être sur le point de / être en train de / venir de",
        structure="Verbe + ところだ",
        explanation="""ところ indique l'étape d'une action : 出かけるところだ (je suis sur le point de
        sortir), 食べているところだ (je suis en train de manger), 着いたところだ (je viens
        d'arriver).""",
    ),
    "tabakari": dict(
        meaning="venir (tout juste) de",
        structure="Verbe (forme en た) + ばかり",
        explanation="""たばかり signifie que quelque chose s'est passé très récemment :
        日本に来たばかりだ (je viens à peine d'arriver au Japon). C'est plus subjectif que
        たところ.""",
    ),
    "mama": dict(
        meaning="tel quel, sans changer",
        structure="Verbe (forme en た) / Nom + の / adjectif + まま",
        explanation="""まま signifie laisser quelque chose dans un état : 靴のまま入る (entrer avec
        ses chaussures), 窓を開けたまま寝た (j'ai dormi la fenêtre ouverte).""",
    ),
    "naide": dict(
        title="〜ないで (sans)",
        meaning="sans (faire)",
        structure="Verbe (forme en ない) + で",
        explanation="""ないで relie deux actions au sens de « sans faire » :
        朝ご飯を食べないで学校に行った (je suis allé à l'école sans prendre de petit-déjeuner).""",
    ),
    "zu_ni": dict(
        meaning="sans (faire), à l'écrit",
        structure="Verbe (radical de la forme en ない) + ずに",
        explanation="""ずに est l'équivalent plus écrit de ないで : 何も言わずに帰った (il est reparti
        sans rien dire). する devient せずに.""",
    ),
    "nakute": dict(
        meaning="parce que … ne … pas",
        structure="Verbe / adjectif (forme en ない sans い) + くて",
        explanation="""なくて donne une raison négative : 友達が来なくて寂しかった (je me sentais seul
        parce que mon ami n'était pas venu).""",
    ),
    "zutsu": dict(
        meaning="chacun, à la fois",
        structure="Quantité + ずつ",
        explanation="""ずつ signifie « chacun » ou « à la fois » : 一人に二つずつ (deux par personne),
        少しずつ (petit à petit).""",
    ),
    "oki_ni": dict(
        meaning="tous les deux …, à intervalles de",
        structure="Quantité + おきに",
        explanation="""おきに indique un intervalle : 一日おきに (un jour sur deux), 五メートルおきに
        (tous les cinq mètres).""",
    ),
    "toka": dict(
        meaning="des choses comme, ou",
        structure="Nom / Verbe + とか",
        explanation="""とか énumère des exemples de façon familière : 本とか雑誌とか (des livres, des
        magazines, ce genre de choses). C'est l'équivalent oral de や…など.""",
    ),
    "nado": dict(
        meaning="etc., des choses comme",
        structure="Nom + など",
        explanation="""など signifie « etc. / par exemple » : 果物などを買った (j'ai acheté des fruits,
        entre autres). なんか en est une version familière, parfois méprisante :
        宿題なんかしたくない (pas envie de faire mes devoirs, moi).""",
    ),
    "demo_suggest": dict(
        title="〜でも (ou quelque chose)",
        meaning="… ou quelque chose ; même",
        structure="Nom + でも",
        explanation="""でも après un nom adoucit une proposition : お茶でも飲みませんか (vous prendrez
        bien un thé ?). Il peut aussi signifier « même » : 子供でも分かる (même un enfant
        comprend).""",
    ),
    "q_ka": dict(
        title="Mot interrogatif + か",
        meaning="quelque (chose, quelqu'un…)",
        structure="何か, 誰か, どこか, いつか",
        explanation="""Mot interrogatif + か donne un mot indéfini : 何か (quelque chose), 誰か
        (quelqu'un), どこか (quelque part), いつか (un jour).""",
    ),
    "q_mo": dict(
        title="Mot interrogatif + も",
        meaning="rien, personne… / tout, toujours",
        structure="何も, 誰も, どこも, いつも",
        explanation="""Mot interrogatif + も avec une forme négative signifie « aucun » :
        何も食べない (ne rien manger), 誰も来ない (personne ne vient). いつも et どこも s'emploient
        aussi à l'affirmatif : toujours, partout.""",
    ),
    "q_demo": dict(
        title="Mot interrogatif + でも",
        meaning="n'importe (quoi, qui…)",
        structure="何でも, 誰でも, どこでも, いつでも",
        explanation="""Mot interrogatif + でも signifie « n'importe … » : 何でも食べる (je mange de
        tout), いつでもいい (n'importe quand, ça va).""",
    ),
}
