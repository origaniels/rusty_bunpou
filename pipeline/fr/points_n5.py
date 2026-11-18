"""French texts for the N5 grammar points (written for this app, not translated word for word)."""

FR = {
    "da": dict(
        meaning="être (familier)",
        structure="Nom / adj. en な + だ",
        explanation="""だ est la copule familière : elle relie un sujet à un nom ou à un adjectif en な,
        comme « être » en français. C'est l'équivalent neutre de です. À l'oral familier on la laisse
        souvent tomber, et on ne la met jamais après un adjectif en い (暑いだ est faux).""",
    ),
    "desu": dict(
        meaning="être (poli)",
        structure="Nom / adjectif + です",
        explanation="""です est la copule polie. Après un nom ou un adjectif en な, elle signifie « être ».
        Après un adjectif en い, elle n'a pas de sens propre : elle rend simplement la phrase polie.""",
    ),
    "deshita": dict(
        meaning="était (poli)",
        structure="Nom / adj. en な + でした",
        explanation="""でした est le passé de です : « X est Y » devient « X était Y », en restant poli.
        Pour les adjectifs en い, c'est l'adjectif lui-même qui porte le passé (暑かったです), pas
        でした.""",
    ),
    "datta": dict(
        meaning="était (familier)",
        structure="Nom / adj. en な + だった",
        explanation="""だった est le passé de だ, la copule familière : « était ». Comme だ, elle se met
        après les noms et les adjectifs en な, jamais après les adjectifs en い.""",
    ),
    "janai": dict(
        meaning="ne pas être",
        structure="Nom / adj. en な + じゃない / ではない (+ です) / ではありません",
        explanation="""Pour dire que quelque chose « n'est pas » un nom ou un adjectif en な, on remplace
        だ par じゃない (à l'oral) ou ではない (plus soutenu, à l'écrit). Les formes polies sont
        じゃないです / じゃありません et ではありません. じゃ n'est qu'une contraction de では.""",
    ),
    "na_adj": dict(
        title="Adjectif en な + な",
        meaning="(relie un adjectif en な à un nom)",
        structure="Adj. en な + な + Nom",
        explanation="""Les adjectifs en な prennent な quand ils sont placés juste devant un nom :
        静かな部屋 (une pièce calme), きれいな花 (une jolie fleur). En fin de phrase, ils prennent
        だ ou です à la place.""",
    ),
    "wa": dict(
        meaning="marqueur de thème",
        structure="Thème + は + commentaire",
        explanation="""は (prononcé « wa ») marque le thème : ce dont parle la phrase. On peut le
        comprendre comme « quant à X, … ». Tout ce qui suit est un commentaire sur ce thème. Il
        oppose souvent le thème à autre chose, et c'est la grande différence avec が.""",
    ),
    "mo": dict(
        meaning="aussi",
        structure="Nom + も",
        explanation="""も signifie « aussi » et remplace は, が ou を : 私も行きます (j'y vais aussi).
        Il peut se placer après d'autres particules : 東京にも (à Tokyo aussi). Avec un verbe à la
        forme négative, il signifie « non plus ».""",
    ),
    "ga": dict(
        meaning="marqueur du sujet",
        structure="Sujet + が + verbe / adjectif",
        explanation="""が marque le sujet grammatical, celui qui fait l'action ou qui est dans un
        état. On l'emploie pour présenter une information nouvelle, pour répondre à « qui ? /
        quoi ? », et avec des mots comme ある, いる, 好き ou 分かる, dont l'objet prend が.""",
    ),
    "no": dict(
        meaning="possession / lien entre deux noms",
        structure="Nom + の + Nom",
        explanation="""の relie deux noms, le premier précisant le second : 私の本 (mon livre),
        日本の車 (une voiture japonaise), 先生の友達 (l'ami du professeur). Il couvre « de » et
        bien d'autres relations. Attention à l'ordre, inverse du français : on dit « professeur の
        ami ».""",
    ),
    "wo": dict(
        meaning="marqueur du complément d'objet direct",
        structure="Objet + を + verbe",
        explanation="""を (prononcé « o ») marque le complément d'objet direct, ce qui subit
        l'action : パンを食べる (manger du pain). Avec un verbe de déplacement, il peut aussi marquer
        le lieu que l'on traverse ou parcourt : 公園を歩く (se promener dans le parc).""",
    ),
    "ni": dict(
        meaning="à, vers, dans (destination, moment, lieu où l'on se trouve)",
        structure="Nom + に",
        explanation="""に désigne une cible : la destination (学校に行く, aller à l'école), la personne
        qui reçoit (友達にあげる, donner à un ami), un moment précis (七時に起きる, se lever à sept
        heures) ou le lieu où quelque chose se trouve (部屋にいる, être dans la chambre).""",
    ),
    "e": dict(
        meaning="vers, en direction de",
        structure="Lieu + へ + verbe de déplacement",
        explanation="""へ (prononcé « e ») indique la direction d'un déplacement : 日本へ行く (aller
        au Japon). Il est très proche de に ; へ insiste sur la direction, に sur le point
        d'arrivée.""",
    ),
    "de": dict(
        meaning="à, dans (lieu d'une action) ; en, avec (moyen)",
        structure="Lieu / outil + で + verbe",
        explanation="""で marque le lieu où se déroule une action (図書館で勉強する, étudier à la
        bibliothèque) ou le moyen utilisé (バスで行く, y aller en bus ; 箸で食べる, manger avec des
        baguettes). Comparez avec に, qui marque simplement l'endroit où quelque chose se
        trouve.""",
    ),
    "to": dict(
        meaning="et ; avec",
        structure="Nom + と + Nom / Personne + と + verbe",
        explanation="""と relie des noms dans une liste complète : パンと牛乳 (du pain et du lait).
        Après une personne, il signifie « avec » : 友達と行く (y aller avec un ami). Il ne relie que
        des noms, jamais des verbes ou des phrases.""",
    ),
    "ya": dict(
        meaning="et (entre autres)",
        structure="Nom + や + Nom",
        explanation="""や énumère des noms à titre d'exemples, en sous-entendant qu'il y en a
        d'autres : 本やペン (des livres, des stylos, etc.). と donne au contraire une liste complète.
        On l'associe souvent à など.""",
    ),
    "kara_from": dict(
        title="から (depuis)",
        meaning="de, depuis (point de départ)",
        structure="Nom + から",
        explanation="""から après un nom marque un point de départ, dans l'espace ou dans le temps :
        駅から歩く (marcher depuis la gare), 九時から (à partir de neuf heures). Il va naturellement
        de pair avec まで.""",
    ),
    "made": dict(
        meaning="jusqu'à",
        structure="Nom + まで",
        explanation="""まで marque un point d'arrivée dans l'espace ou dans le temps : 駅まで (jusqu'à
        la gare), 五時まで (jusqu'à cinq heures). On le combine souvent avec から : 九時から五時まで
        (de neuf heures à cinq heures).""",
    ),
    "ka": dict(
        title="か (question)",
        meaning="marqueur de question",
        structure="Phrase + か",
        explanation="""か à la fin d'une phrase la transforme en question : 学生ですか (vous êtes
        étudiant ?). En langage poli, pas besoin de point d'interrogation. En langage familier,
        か peut sembler brusque : on utilise plutôt une intonation montante.""",
    ),
    "ne": dict(
        meaning="n'est-ce pas ? (recherche d'accord)",
        structure="Phrase + ね",
        explanation="""ね en fin de phrase invite l'interlocuteur à être d'accord, comme « n'est-ce
        pas ? » ou « hein ? » : いい天気ですね (il fait beau, n'est-ce pas ?). Il rend la phrase plus
        douce et plus amicale.""",
    ),
    "yo": dict(
        meaning="(insistance ; apporte une information)",
        structure="Phrase + よ",
        explanation="""よ en fin de phrase annonce à l'interlocuteur quelque chose qu'il ne sait
        peut-être pas, ou insiste : おいしいですよ (c'est délicieux, tu sais). Trop l'utiliser peut
        paraître insistant.""",
    ),
    "yori": dict(
        meaning="que (comparaison)",
        structure="A + は + B + より + adjectif",
        explanation="""より marque l'élément auquel on compare : 犬は猫より大きい (les chiens sont plus
        grands que les chats). Le mot suivi de より correspond au « que » français. Il va souvent
        avec のほうが de l'autre côté de la comparaison.""",
    ),
    "dake": dict(
        meaning="seulement, juste",
        structure="Nom / verbe + だけ",
        explanation="""だけ signifie « seulement / juste » et limite le mot qui précède : 一つだけ (un
        seul), 見るだけ (je regarde seulement). Contrairement à しか, il s'emploie avec un verbe à la
        forme affirmative.""",
    ),
    "shika": dict(
        meaning="ne … que (avec un verbe négatif)",
        structure="Nom + しか + verbe à la forme négative",
        explanation="""しか signifie « seulement », mais le verbe qui suit est toujours à la forme
        négative, exactement comme « ne … que » en français : 百円しかない (je n'ai que 100 yens).
        Il souligne que la quantité est petite ou insuffisante.""",
    ),
    "gurai": dict(
        meaning="environ, à peu près",
        structure="Quantité + ぐらい / くらい",
        explanation="""ぐらい (ou くらい) après une quantité signifie « environ » : 一時間ぐらい (environ
        une heure), 百人くらい (une centaine de personnes). Pour un moment précis, on utilise ごろ.""",
    ),
    "goro": dict(
        meaning="vers (un moment)",
        structure="Moment + ごろ",
        explanation="""ごろ après un moment précis signifie « vers » : 三時ごろ (vers trois heures),
        十月ごろ (vers octobre). Pour les quantités et les durées, on utilise ぐらい.""",
    ),
    "tachi": dict(
        meaning="(pluriel pour les personnes)",
        structure="Personne + たち",
        explanation="""Les noms japonais n'ont normalement pas de pluriel, mais on peut ajouter たち
        aux personnes (et aux pronoms) pour former un groupe : 私たち (nous), 子供たち (les enfants).
        On ne l'emploie pas pour les objets.""",
    ),
    "kore": dict(
        meaning="ceci / cela / cela là-bas / lequel",
        structure="これ / それ / あれ / どれ (seuls)",
        explanation="""Ces pronoms remplacent une chose. これ : près de celui qui parle. それ : près de
        celui qui écoute. あれ : loin des deux. どれ : lequel (parmi trois ou plus). Ils s'emploient
        seuls, jamais directement devant un nom ; pour cela, on utilise この/その/あの/どの.""",
    ),
    "kono": dict(
        meaning="ce … -ci / ce … -là / ce … là-bas / quel (+ nom)",
        structure="この / その / あの / どの + Nom",
        explanation="""Ces mots se placent toujours juste devant un nom : この本 (ce livre-ci), その人
        (cette personne-là), あの店 (ce magasin là-bas), どの車 (quelle voiture). Même logique de
        distance que これ/それ/あれ/どれ.""",
    ),
    "koko": dict(
        meaning="ici / là / là-bas / où",
        structure="ここ / そこ / あそこ / どこ",
        explanation="""Les mots de lieu suivent le même schéma : ここ (ici, près de moi), そこ (là,
        près de toi), あそこ (là-bas, loin des deux), どこ (où ?).""",
    ),
    "masu": dict(
        meaning="(verbe poli, non passé)",
        structure="Radical du verbe + ます",
        explanation="""ます rend un verbe poli au présent ou au futur : 食べる → 食べます, 行く →
        行きます. Le verbe se met à son radical (連用形). On l'utilise avec des inconnus, des
        professeurs, des collègues.""",
    ),
    "masen": dict(
        meaning="(verbe poli, négatif)",
        structure="Radical du verbe + ません",
        explanation="""ません est la forme négative polie : 食べません (je ne mange pas / je ne
        mangerai pas), 行きません. C'est la forme « ne … pas » de ます.""",
    ),
    "mashita": dict(
        meaning="(verbe poli, passé)",
        structure="Radical du verbe + ました",
        explanation="""ました est le passé poli : 食べました (j'ai mangé), 行きました (je suis allé).
        Comme ます, il se met après le radical : le radical utilisé pour ます fonctionne aussi ici :
        見ます → 見ました, します → しました.""",
    ),
    "masendeshita": dict(
        meaning="(verbe poli, passé négatif)",
        structure="Radical du verbe + ませんでした",
        explanation="""ませんでした est le passé négatif poli : 食べませんでした (je n'ai pas mangé).
        C'est littéralement ません + でした.""",
    ),
    "mashou": dict(
        meaning="… -ons ! (proposition)",
        structure="Radical du verbe + ましょう",
        explanation="""ましょう correspond à notre impératif « allons-y ! » : 行きましょう (allons-y).
        C'est la forme volitive polie ; elle sert aussi à proposer de faire quelque chose soi-même
        (« je vais … »).""",
    ),
    "mashouka": dict(
        meaning="et si on … ? / voulez-vous que je … ?",
        structure="Radical du verbe + ましょうか",
        explanation="""ましょうか transforme « allons-y » en suggestion ou en offre : 行きましょうか (on
        y va ?), 手伝いましょうか (voulez-vous que je vous aide ?).""",
    ),
    "masenka": dict(
        meaning="ça vous dirait de … ? (invitation)",
        structure="Radical du verbe + ませんか",
        explanation="""ませんか demande littéralement « ne voulez-vous pas … ? » ; c'est une façon
        polie et douce d'inviter quelqu'un : 一緒に行きませんか (ça vous dirait d'y aller
        ensemble ?).""",
    ),
    "nai": dict(
        title="ない (négation)",
        meaning="ne … pas (négatif familier)",
        structure="Verbe (forme en ない)",
        explanation="""La forme négative neutre : 食べる → 食べない, 行く → 行かない (le son en « u »
        devient un son en « a » + ない), する → しない, 来る → こない. Exception : ある → ない. Au
        passé : 食べなかった.""",
    ),
    "ta": dict(
        title="た (passé)",
        meaning="(passé familier)",
        structure="Verbe (forme en た)",
        explanation="""Le passé neutre. Il se forme exactement comme la forme en て, avec た au lieu
        de て : 食べた, 行った, 読んだ, した, 来た.""",
    ),
    "tai": dict(
        meaning="vouloir (faire)",
        structure="Radical du verbe + たい",
        explanation="""たい se met après le radical du verbe et signifie « vouloir faire » : 食べたい
        (je veux manger), 行きたい. Il se conjugue comme un adjectif en い : 行きたくない, 行きたかった.
        On l'utilise pour ses propres envies ; pour les autres, cela sonne présomptueux.""",
    ),
    "te_iru": dict(
        meaning="être en train de … ; être dans un état",
        structure="Verbe (forme en て) + いる",
        explanation="""Forme en て + いる décrit une action en cours (読んでいる, être en train de lire)
        ou l'état qui résulte d'une action (結婚している, être marié ; 知っている, savoir). Forme
        polie : ています. À l'oral familier, le い disparaît souvent : 読んでる.""",
    ),
    "te_kudasai": dict(
        meaning="… s'il vous plaît (demande)",
        structure="Verbe (forme en て) + ください",
        explanation="""Forme en て + ください est une demande polie : 見てください (regardez, s'il
        vous plaît), 待ってください (attendez, s'il vous plaît). Dans cet emploi, ください s'écrit
        souvent en kana.""",
    ),
    "naide_kudasai": dict(
        meaning="ne … pas, s'il vous plaît",
        structure="Verbe (forme en ない) + でください",
        explanation="""Pour demander à quelqu'un de ne pas faire quelque chose, on utilise la forme
        en ない + でください : 触らないでください (ne touchez pas, s'il vous plaît).""",
    ),
    "o_kudasai": dict(
        meaning="donnez-moi …, s'il vous plaît",
        structure="Nom + を + ください",
        explanation="""Nom + をください sert à demander quelque chose : 水をください (de l'eau, s'il
        vous plaît). C'est la façon de commander ou de demander un objet.""",
    ),
    "temo_ii": dict(
        meaning="pouvoir, avoir le droit de",
        structure="Verbe (forme en て) + もいい",
        explanation="""Forme en て + もいい donne ou demande une permission : 入ってもいいですか (je
        peux entrer ?), 食べてもいい (tu peux le manger). Littéralement « même si tu fais …, c'est
        bien ».""",
    ),
    "tewa_ikenai": dict(
        meaning="il ne faut pas, interdit de",
        structure="Verbe (forme en て) + はいけない",
        explanation="""Forme en て + はいけない interdit quelque chose : ここで泳いではいけない (il est
        interdit de nager ici). Littéralement « si tu fais …, ça ne va pas ». Forme polie :
        てはいけません.""",
    ),
    "tekara": dict(
        meaning="après avoir …",
        structure="Verbe (forme en て) + から",
        explanation="""Forme en て + から signifie « après avoir fait X, (on fait) Y », en insistant sur
        l'ordre : 手を洗ってから食べる (manger après s'être lavé les mains).""",
    ),
    "ta_koto_ga_aru": dict(
        meaning="avoir déjà … (expérience)",
        structure="Verbe (forme en た) + ことがある",
        explanation="""Forme en た + ことがある parle d'une expérience vécue : 富士山に登ったことがある
        (j'ai déjà gravi le mont Fuji). Au négatif, ことがない signifie « n'avoir jamais … ».""",
    ),
    "tari": dict(
        meaning="faire des choses comme A et B",
        structure="Verbe (forme en た) + り, Verbe (forme en た) + り + する",
        explanation="""たり énumère des actions à titre d'exemples, sans ordre ni liste complète :
        本を読んだり、映画を見たりする (je fais des choses comme lire des livres ou regarder des
        films). Le dernier たり est suivi de する.""",
    ),
    "hou_ga_ii": dict(
        meaning="il vaudrait mieux …",
        structure="Verbe (forme en た / en ない) + ほうがいい",
        explanation="""ほうがいい donne un conseil : 早く寝たほうがいい (tu ferais mieux de te coucher
        tôt). Un conseil positif utilise en général le passé (た) ; un conseil négatif utilise
        ない : 行かないほうがいい (il vaudrait mieux ne pas y aller).""",
    ),
    "mae_ni": dict(
        meaning="avant de …",
        structure="Verbe (forme du dictionnaire) + 前に / Nom + の + 前に",
        explanation="""前に signifie « avant ». Après un verbe, on utilise toujours la forme du
        dictionnaire, même si la phrase est au passé : 寝る前に (avant de dormir). Après un nom, on
        met の : 食事の前に (avant le repas).""",
    ),
    "ato_de": dict(
        meaning="après …",
        structure="Verbe (forme en た) + 後で / Nom + の + 後で",
        explanation="""後で (あとで) signifie « après ». Après un verbe, celui-ci est au passé :
        食べた後で (après avoir mangé). Après un nom, on met の : 授業の後で (après le cours).""",
    ),
    "ni_iku": dict(
        title="に行く (but)",
        meaning="aller (pour) faire …",
        structure="Radical du verbe + に + 行く / 来る",
        explanation="""Radical du verbe + に + un verbe de déplacement (行く, 来る, 帰る) exprime le but
        du déplacement : 映画を見に行く (aller voir un film), 遊びに来る (venir passer un moment).""",
    ),
    "nagara": dict(
        meaning="tout en …",
        structure="Radical du verbe + ながら",
        explanation="""ながら relie deux actions faites en même temps par la même personne :
        音楽を聞きながら勉強する (étudier en écoutant de la musique), comme notre gérondif « en … ».
        L'action principale est la seconde.""",
    ),
    "nakereba": dict(
        meaning="devoir, il faut",
        structure="Verbe (forme en ない sans い) + ければならない",
        explanation="""なければならない signifie « devoir » : 勉強しなければならない (je dois étudier).
        Littéralement « si je n'étudie pas, ça ne va pas ». Variantes : なければいけない, forme polie
        なければなりません.""",
    ),
    "nasai": dict(
        meaning="fais … ! (ordre)",
        structure="Radical du verbe + なさい",
        explanation="""なさい est un ordre ferme mais pas impoli, typique des parents et des
        professeurs : 早く寝なさい (va te coucher !), よく聞きなさい (écoute bien).""",
    ),
    "kata": dict(
        title="方 (manière de)",
        meaning="la façon de …, comment …",
        structure="Radical du verbe + 方",
        explanation="""Radical du verbe + 方 (かた) forme un nom qui signifie « la façon de faire » :
        書き方 (la façon d'écrire), 使い方 (le mode d'emploi). Le complément du verbe prend alors の :
        漢字の読み方 (la lecture des kanji).""",
    ),
    "aru": dict(
        title="ある (existence, choses)",
        meaning="il y a (choses)",
        structure="Chose + が + ある",
        explanation="""ある dit qu'une chose non vivante existe ou se trouve quelque part :
        机の上に本がある (il y a un livre sur le bureau). Il signifie aussi « avoir » : 時間がある
        (avoir le temps). Sa forme négative est irrégulière : ない.""",
    ),
    "iru": dict(
        title="いる (existence, êtres vivants)",
        meaning="il y a (personnes, animaux)",
        structure="Personne / animal + が + いる",
        explanation="""いる dit qu'une personne ou un animal existe ou se trouve quelque part :
        公園に子供がいる (il y a des enfants dans le parc). Il signifie aussi « avoir » pour la famille
        ou les animaux : 兄がいる (j'ai un grand frère).""",
    ),
    "i_adj_neg": dict(
        meaning="ne pas être (adjectif en い, négatif)",
        structure="Adj. en い (sans い) + くない",
        explanation="""Pour mettre un adjectif en い à la forme négative, on remplace le い final par
        くない : 高い → 高くない (pas cher). Forme polie : 高くないです / 高くありません. Irrégulier :
        いい → よくない.""",
    ),
    "i_adj_past": dict(
        meaning="était (adjectif en い, passé)",
        structure="Adj. en い (sans い) + かった",
        explanation="""Le passé d'un adjectif en い : on remplace い par かった : 楽しい → 楽しかった
        (c'était amusant). On ajoute です pour être poli : 楽しかったです (jamais 楽しいでした).
        Irrégulier : いい → よかった.""",
    ),
    "kute": dict(
        meaning="et (pour enchaîner des adjectifs en い)",
        structure="Adj. en い (sans い) + くて",
        explanation="""Pour enchaîner un adjectif en い avec autre chose, on utilise sa forme en て :
        on enlève い et on ajoute くて : 安くておいしい (bon marché et bon). Pour les adjectifs en な
        et les noms, on utilise で.""",
    ),
    "naru": dict(
        title="なる (devenir)",
        meaning="devenir",
        structure="Adj. en い → く + なる / Nom, adj. en な + に + なる",
        explanation="""なる signifie « devenir ». Les adjectifs en い changent い en く : 寒くなる (il
        se met à faire froid). Les noms et les adjectifs en な prennent に : 先生になる (devenir
        professeur), 元気になる (se rétablir).""",
    ),
    "hoshii": dict(
        meaning="vouloir (quelque chose)",
        structure="Nom + が + ほしい",
        explanation="""ほしい est un adjectif en い qui signifie « vouloir (une chose) » :
        新しい車がほしい (je veux une nouvelle voiture). La chose voulue prend が. Pour vouloir faire
        une action, on utilise たい.""",
    ),
    "suki": dict(
        meaning="aimer",
        structure="Nom + が + 好き",
        explanation="""好き (すき) est un adjectif en な qui signifie « aimé, apprécié » : 猫が好きです
        (j'aime les chats). Ce qu'on aime prend が. 大好き signifie « adorer » ; le contraire est
        嫌い (きらい).""",
    ),
    "ichiban": dict(
        meaning="le plus, numéro un",
        structure="一番 + adjectif",
        explanation="""一番 (いちばん) devant un adjectif forme un superlatif : 一番高い (le plus cher).
        Le groupe de comparaison est souvent introduit par の中で : 果物の中でりんごが一番好きです
        (de tous les fruits, c'est la pomme que je préfère).""",
    ),
    "amari": dict(
        meaning="pas très, pas beaucoup",
        structure="あまり + forme négative",
        explanation="""あまり avec un verbe ou un adjectif à la forme négative signifie « pas très /
        pas beaucoup » : あまり高くない (pas très cher), あまり食べない (je ne mange pas
        beaucoup).""",
    ),
    "kara_because": dict(
        title="から (parce que)",
        meaning="parce que, donc",
        structure="Phrase + から",
        explanation="""から après une phrase donne la raison : 雨だから、行かない (il pleut, donc je n'y
        vais pas). La raison vient d'abord, la conséquence ensuite. Il est un peu plus subjectif et
        plus familier que ので.""",
    ),
    "node": dict(
        meaning="comme, étant donné que",
        structure="Phrase + ので (な après un nom / adj. en な)",
        explanation="""ので donne aussi une raison, mais paraît plus doux et plus objectif que から,
        d'où son emploi fréquent dans les explications polies : 熱があるので、休みます (j'ai de la
        fièvre, je vais donc me reposer). Après un nom ou un adjectif en な, il devient なので.""",
    ),
    "ga_but": dict(
        title="が (mais)",
        meaning="mais",
        structure="Phrase + が、Phrase",
        explanation="""が après une phrase complète signifie « mais » : 高いですが、おいしいです (c'est
        cher, mais c'est bon). Il est légèrement soutenu ; il peut aussi simplement adoucir une
        introduction (すみませんが…, excusez-moi, mais…).""",
    ),
    "kedo": dict(
        meaning="mais, bien que",
        structure="Phrase + けど / けれど(も)",
        explanation="""けど est le « mais » familier : 行きたいけど、時間がない (je voudrais y aller,
        mais je n'ai pas le temps). けれど et けれども sont des variantes plus longues et un peu plus
        soutenues.""",
    ),
    "deshou": dict(
        meaning="sans doute ; n'est-ce pas ?",
        structure="Phrase + でしょう",
        explanation="""でしょう exprime une supposition, « sans doute » : 明日は雨でしょう (il pleuvra
        sans doute demain). Avec une intonation montante, il demande une confirmation : « n'est-ce
        pas ? ». Forme familière : だろう.""",
    ),
    "toki": dict(
        meaning="quand, au moment où",
        structure="Verbe / adjectif / Nom + の + とき",
        explanation="""とき (時) signifie « quand / au moment où » : 子供のとき (quand j'étais
        enfant), 暇なとき (quand je suis libre), 寝るとき (au moment de me coucher).""",
    ),
    "to_iu": dict(
        meaning="appelé, nommé",
        structure="Nom propre + という + Nom",
        explanation="""X という Y signifie « un Y appelé X » : 田中という人 (une personne qui s'appelle
        Tanaka), 「こころ」という本 (un livre intitulé « Kokoro »). Il relie aussi toute une phrase à
        un nom qui la résume : 結婚したといううわさ (la rumeur selon laquelle elle s'est mariée).""",
    ),
}
