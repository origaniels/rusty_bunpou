"""French texts for the N2 grammar points (written for this app, not translated word for word)."""

FR = {
    "ue_de": dict(
        meaning="après ; pour, dans le cadre de",
        structure="Verbe (forme en た) / Nom + の + 上で",
        explanation="""上で (うえで) signifie « après avoir fait » (よく考えた上で決める, décider après
        mûre réflexion) ou « pour, dans le cadre de » : 生活する上で大切なこと (ce qui est important
        pour vivre).""",
    ),
    "ue_wa": dict(
        meaning="maintenant que, puisque",
        structure="Verbe (forme du dictionnaire / en た) + 上は",
        explanation="""上は (うえは) signifie « maintenant que (il faut donc) » : 約束した上は、守らなければならない
        (puisque j'ai promis, je dois tenir parole).""",
    ),
    "ijou_wa": dict(
        meaning="puisque, du moment que",
        structure="Forme neutre + 以上(は)",
        explanation="""以上は (いじょうは) signifie « du moment que » : 引き受けた以上、最後までやる (du
        moment que j'ai accepté, j'irai jusqu'au bout).""",
    ),
    "kara_ni_wa": dict(
        meaning="puisque, maintenant que",
        structure="Forme neutre + からには",
        explanation="""からには signifie « puisque (j'ai fait ceci), je dois… » :
        日本に来たからには、日本語を覚えたい (puisque je suis venu au Japon, je veux apprendre le
        japonais).""",
    ),
    "sai": dict(
        meaning="lors de, au moment de",
        structure="Verbe / Nom + の + 際(に)",
        explanation="""際 (さい) est un « quand » soutenu : お降りの際は足元にご注意ください (en
        descendant, veuillez faire attention à la marche).""",
    ),
    "ni_saishite": dict(
        meaning="à l'occasion de",
        structure="Nom / Verbe + に際して",
        explanation="""に際して signifie « au moment de (un événement important) » :
        出発に際して挨拶をした (j'ai dit quelques mots au moment du départ).""",
    ),
    "ni_atatte": dict(
        meaning="au moment de (entreprendre)",
        structure="Nom / Verbe + にあたって",
        explanation="""にあたって signifie « au moment d'entreprendre (quelque chose d'important) » :
        開店にあたって準備をする (faire les préparatifs pour l'ouverture du magasin).""",
    ),
    "to_sureba": dict(
        meaning="si (on suppose que)",
        structure="Forme neutre + とすれば",
        explanation="""とすれば / とすると / としたら signifient « à supposer que » :
        明日行くとしたら、何時がいい? (si on y va demain, quelle heure te convient ?).""",
    ),
    "to_naru_to": dict(
        meaning="quand il s'agit de ; si cela devient",
        structure="Nom / forme neutre + となると",
        explanation="""となると signifie « quand il s'agit de / s'il faut » : 留学となると、お金がかかる
        (partir étudier à l'étranger, ça coûte de l'argent).""",
    ),
    "to_ieba": dict(
        meaning="à propos de, en parlant de",
        structure="Nom + といえば",
        explanation="""といえば reprend un sujet qui vient d'être évoqué : 京都といえば、お寺が有名だ (en
        parlant de Kyoto, la ville est célèbre pour ses temples).""",
    ),
    "kara_to_itte": dict(
        meaning="ce n'est pas parce que",
        structure="Forme neutre + からといって",
        explanation="""からといって rejette une conclusion hâtive : 高いからといって、いいものとは限らない
        (ce n'est pas parce que c'est cher que c'est bien).""",
    ),
    "kara_koso": dict(
        meaning="c'est justement parce que",
        structure="Forme neutre + からこそ",
        explanation="""からこそ insiste sur la raison : 好きだからこそ厳しくする (c'est justement parce
        que je tiens à toi que je suis sévère).""",
    ),
    "kara_suru_to": dict(
        meaning="du point de vue de, à en juger par",
        structure="Nom + からすると / からすれば",
        explanation="""からすると signifie « à en juger par / du point de vue de » :
        親からすると、子供はいつまでも子供だ (pour des parents, un enfant reste toujours un
        enfant).""",
    ),
    "kara_shite": dict(
        meaning="à commencer par ; à en juger par",
        structure="Nom + からして",
        explanation="""からして signifie « rien que, à commencer par » : 名前からして怪しい (rien que le
        nom est suspect).""",
    ),
    "ni_shitara": dict(
        meaning="du point de vue de (quelqu'un)",
        structure="Nom (personne) + にしたら / にすれば",
        explanation="""にしたら / にすれば adoptent le point de vue d'une autre personne :
        子供にしたら、つまらない話だろう (pour un enfant, c'est sans doute une histoire
        ennuyeuse).""",
    ),
    "nai_kagiri": dict(
        meaning="à moins que",
        structure="Verbe (forme en ない) + 限り",
        explanation="""ない限り (かぎり) signifie « à moins que » : 謝らない限り許さない (je ne te
        pardonnerai pas à moins que tu ne t'excuses).""",
    ),
    "kagiri": dict(
        meaning="tant que ; autant que",
        structure="Forme neutre + 限り(は)",
        explanation="""限り signifie « tant que » (生きている限り, tant que je vivrai) ou « pour autant
        que » (私の知る限り, pour autant que je sache).""",
    ),
    "ippou": dict(
        meaning="tandis que, d'un autre côté",
        structure="Forme neutre + 一方(で)",
        explanation="""一方で oppose deux aspects : 都会は便利な一方で、物価が高い (la ville est
        pratique, mais la vie y est chère).""",
    ),
    "hanmen": dict(
        meaning="en revanche, mais d'un autre côté",
        structure="Forme neutre + 反面",
        explanation="""反面 (はんめん) montre le revers d'une même chose : この仕事は楽しい反面、責任も重い
        (ce travail est agréable, mais les responsabilités sont lourdes).""",
    ),
    "mono_no": dict(
        meaning="bien que, certes … mais",
        structure="Forme neutre + ものの",
        explanation="""ものの signifie « bien que (en réalité…) » : 買ったものの、一度も使っていない
        (je l'ai acheté, mais je ne m'en suis jamais servi).""",
    ),
    "ni_mo_kakawarazu": dict(
        meaning="malgré, en dépit de",
        structure="Nom / forme neutre + にもかかわらず",
        explanation="""にもかかわらず signifie « malgré » : 雨にもかかわらず、たくさんの人が来た (malgré
        la pluie, beaucoup de gens sont venus).""",
    ),
    "nagara_mo": dict(
        meaning="bien que, tout en",
        structure="Radical du verbe / adjectif + ながらも",
        explanation="""ながらも signifie « bien que » : 狭いながらも楽しい我が家 (notre maison, petite
        mais joyeuse).""",
    ),
    "tsutsu_mo": dict(
        meaning="tout en (sachant que)",
        structure="Radical du verbe + つつも",
        explanation="""つつも est un « bien que (tout en faisant) » écrit : 体に悪いと知りつつも、タバコがやめられない
        (je sais que c'est mauvais pour la santé, et pourtant je n'arrive pas à arrêter de fumer).
        Il oppose souvent ce qu'on sait ou pense à ce qu'on fait.""",
    ),
    "tsutsu": dict(
        meaning="tout en (faisant)",
        structure="Radical du verbe + つつ",
        explanation="""つつ est un ながら écrit : 景色を楽しみつつ歩く (marcher en profitant du
        paysage).""",
    ),
    "tsutsu_aru": dict(
        meaning="être en train de (changement)",
        structure="Radical du verbe + つつある",
        explanation="""つつある décrit un changement en cours : 地球の気温は上がりつつある (la
        température de la Terre est en train d'augmenter).""",
    ),
    "wari_ni": dict(
        meaning="compte tenu de, pour",
        structure="Forme neutre / Nom + の + わりに",
        explanation="""わりに signifie « compte tenu de » : 値段のわりにおいしい (c'est bon, pour le
        prix).""",
    ),
    "ni_shiro": dict(
        meaning="même si ; que … ou que",
        structure="Forme neutre / Nom + にしろ",
        explanation="""にしろ / にせよ signifient « même si » ou, répétés, « que A ou que B » :
        行くにしろ行かないにしろ連絡して (que tu y ailles ou non, préviens-moi).""",
    ),
    "ta_tokoro_de": dict(
        meaning="même si (ça ne sert à rien)",
        structure="Verbe (forme en た) + ところで",
        explanation="""たところで signifie « même si l'on fait… (ça ne servira à rien) » :
        今から急いだところで間に合わない (même si on se dépêche maintenant, on n'arrivera pas à
        temps).""",
    ),
    "dokoro_ka": dict(
        meaning="loin de ; sans parler de",
        structure="Nom / forme neutre + どころか",
        explanation="""どころか signifie « loin de (c'est même le contraire) » : 休むどころか、ますます忙しくなった
        (loin de me reposer, je suis de plus en plus occupé).""",
    ),
    "dokoro_dewa_nai": dict(
        meaning="ce n'est pas le moment de",
        structure="Nom / Verbe + どころではない",
        explanation="""どころではない indique qu'il n'y a pas de place pour quelque chose :
        忙しくて旅行どころではない (je suis trop occupé pour penser à voyager).""",
    ),
    "bakari_ka": dict(
        meaning="non seulement … mais même",
        structure="Nom / forme neutre + ばかりか",
        explanation="""ばかりか signifie « non seulement… mais (encore plus) » :
        彼は英語ばかりか、中国語も話せる (il parle non seulement anglais, mais même chinois).""",
    ),
    "bakari_ni": dict(
        meaning="rien que parce que (mauvais résultat)",
        structure="Forme neutre + ばかりに",
        explanation="""ばかりに donne une cause qui a mené à un mauvais résultat :
        嘘をついたばかりに、信用を失った (pour un simple mensonge, j'ai perdu leur confiance).""",
    ),
    "bakari_da": dict(
        meaning="ne faire que (empirer), de plus en plus",
        structure="Verbe (forme du dictionnaire) + 一方だ",
        explanation="""一方だ / ばかりだ décrivent un changement qui continue dans un seul sens :
        物価は上がる一方だ (les prix ne cessent d'augmenter).""",
    ),
    "mo_kamawazu": dict(
        meaning="sans se soucier de",
        structure="Nom + もかまわず",
        explanation="""もかまわず signifie « sans se soucier de » : 人目もかまわず泣いた (elle a pleuré
        sans se soucier des regards).""",
    ),
    "wa_tomokaku": dict(
        meaning="mis à part",
        structure="Nom + はともかく",
        explanation="""はともかく met un point de côté : 味はともかく、量が多い (le goût, passe encore,
        mais les portions sont copieuses).""",
    ),
    "wa_motoyori": dict(
        meaning="sans parler de, à plus forte raison",
        structure="Nom + はもとより",
        explanation="""はもとより signifie « sans parler de » ; c'est un はもちろん plus soutenu :
        子供はもとより大人も楽しめる (les adultes aussi peuvent s'amuser, sans parler des enfants).
        La seconde partie contient généralement も.""",
    ),
    "ni_kakawarazu": dict(
        meaning="indépendamment de, quel que soit",
        structure="Nom + にかかわらず",
        explanation="""にかかわらず signifie « quel que soit » : 年齢にかかわらず参加できる (tout le monde
        peut participer, quel que soit son âge).""",
    ),
    "wo_towazu": dict(
        meaning="sans distinction de",
        structure="Nom + を問わず",
        explanation="""を問わず (とわず) signifie « sans distinction de » : 男女を問わず (hommes et
        femmes sans distinction).""",
    ),
    "ni_kagirazu": dict(
        meaning="pas seulement",
        structure="Nom + に限らず",
        explanation="""に限らず (かぎらず) signifie « pas seulement » :
        若者に限らず、お年寄りにも人気がある (c'est populaire non seulement chez les jeunes, mais
        aussi chez les personnes âgées). La seconde partie élargit le champ, souvent avec も.""",
    ),
    "ni_kagiru": dict(
        meaning="rien de tel que ; réservé à",
        structure="Nom / Verbe + に限る",
        explanation="""に限る signifie « X, il n'y a rien de mieux » : 夏はビールに限る (en été, rien ne
        vaut une bière). Il signifie aussi simplement « réservé à » : 参加者は学生に限る (participation
        réservée aux étudiants).""",
    ),
    "ni_kagitte": dict(
        meaning="justement quand ; seulement",
        structure="Nom + に限って",
        explanation="""に限って signifie « justement (au mauvais moment / chez la mauvaise
        personne) » : 急いでいる時に限って、バスが来ない (c'est justement quand on est pressé que le
        bus ne vient pas).""",
    ),
    "ni_sugi_nai": dict(
        meaning="ne … que, n'être que",
        structure="Nom / forme neutre + に過ぎない",
        explanation="""に過ぎない (すぎない) signifie « ce n'est rien de plus que » : それは噂に過ぎない
        (ce n'est qu'une rumeur).""",
    ),
    "ni_kuwaete": dict(
        meaning="en plus de",
        structure="Nom + に加えて",
        explanation="""に加えて (くわえて) signifie « en plus de » : 雨に加えて風も強くなった (en plus de la
        pluie, le vent s'est levé). C'est écrit ou soutenu ; à l'oral, on dirait plutôt それに ou
        だけじゃなく.""",
    ),
    "ni_tomonatte": dict(
        meaning="en même temps que, avec",
        structure="Nom / Verbe + に伴って",
        explanation="""に伴って (ともなって) décrit des choses qui changent ensemble :
        人口の増加に伴って、問題も増えた (avec la hausse de la population, les problèmes ont aussi
        augmenté).""",
    ),
    "ni_oujite": dict(
        meaning="selon, en fonction de",
        structure="Nom + に応じて",
        explanation="""に応じて (おうじて) signifie « en fonction de / en réponse à » :
        能力に応じて給料を払う (payer selon les compétences).""",
    ),
    "ni_sotte": dict(
        meaning="le long de ; conformément à",
        structure="Nom + に沿って",
        explanation="""に沿って (そって) signifie « le long de » (川に沿って歩く, marcher le long de la
        rivière) ou « conformément à » (計画に沿って進める, avancer selon le plan).""",
    ),
    "ni_motozuite": dict(
        meaning="fondé sur",
        structure="Nom + に基づいて",
        explanation="""に基づいて (もとづいて) signifie « fondé sur » : 事実に基づいた映画 (un film
        tiré de faits réels).""",
    ),
    "wo_moto_ni": dict(
        meaning="à partir de, en s'inspirant de",
        structure="Nom + をもとに",
        explanation="""をもとに signifie « à partir de (en se servant de X comme matière) » :
        経験をもとに小説を書いた (j'ai écrit un roman à partir de mon expérience). Comparez avec
        に基づいて, qui signifie « conformément à » des règles ou des faits.""",
    ),
    "wo_tooshite": dict(
        meaning="par l'intermédiaire de ; tout au long de",
        structure="Nom + を通して",
        explanation="""を通して (とおして) / を通じて (つうじて) signifient « par l'intermédiaire de »
        ou « tout au long de (une période) ».""",
    ),
    "wo_megutte": dict(
        meaning="au sujet de (une dispute)",
        structure="Nom + をめぐって",
        explanation="""をめぐって signifie « autour de (une question qui fait débat) » :
        遺産をめぐって争う (se disputer à propos d'un héritage).""",
    ),
    "wo_hajime": dict(
        meaning="à commencer par",
        structure="Nom + をはじめ",
        explanation="""をはじめ signifie « à commencer par (l'exemple principal) » :
        社長をはじめ、社員全員が集まった (tous les employés, à commencer par le président, se sont
        réunis).""",
    ),
    "ni_hanshite": dict(
        meaning="contrairement à",
        structure="Nom + に反して",
        explanation="""に反して (はんして) signifie « contrairement à, à l'encontre de » :
        予想に反して、試合に負けた (contrairement aux prévisions, nous avons perdu le match). Il
        s'emploie avec des attentes, des souhaits ou des règles ; devant un nom, il devient
        に反する.""",
    ),
    "ni_sakidatte": dict(
        meaning="avant, en prélude à",
        structure="Nom + に先立って",
        explanation="""に先立って (さきだって) signifie « avant (en guise de préparation) » :
        試合に先立って開会式が行われた (la cérémonie d'ouverture a eu lieu avant le match).""",
    ),
    "ni_watatte": dict(
        meaning="sur toute la durée de, sur toute l'étendue de",
        structure="Nom + にわたって",
        explanation="""にわたって signifie « s'étendant sur (une longue durée / une vaste zone) » :
        三日間にわたって会議が開かれた (la conférence s'est tenue sur trois jours).""",
    ),
    "ni_kakete": dict(
        meaning="de … à (période ou zone)",
        structure="Nom + にかけて",
        explanation="""から〜にかけて signifie « de … jusqu'à » pour une période ou une zone aux limites
        floues : 夜から朝にかけて雨が降る (il pleuvra de la nuit jusqu'au matin). Comparez avec
        から〜まで, aux limites précises.""",
    ),
    "ni_oite": dict(
        meaning="dans, à (soutenu)",
        structure="Nom + において",
        explanation="""において est un で soutenu : 会議は大阪において行われる (la conférence se tiendra
        à Osaka).""",
    ),
    "ni_mukete": dict(
        meaning="en vue de, à l'intention de",
        structure="Nom + に向けて",
        explanation="""に向けて (むけて) signifie « en vue de (un objectif) » : 試験に向けて勉強している
        (j'étudie en vue de l'examen). Il peut aussi signifier « à l'intention de » :
        若者に向けたメッセージ (un message destiné aux jeunes).""",
    ),
    "wo_kikkake_ni": dict(
        meaning="à l'occasion de, suite à",
        structure="Nom + をきっかけに",
        explanation="""をきっかけに signifie « suite à, à l'occasion de » : 留学をきっかけに料理を始めた
        (c'est en partant étudier à l'étranger que je me suis mis à cuisiner). を契機に et を機に en
        sont des variantes plus soutenues.""",
    ),
    "wo_nozoite": dict(
        meaning="à l'exception de",
        structure="Nom + を除いて",
        explanation="""を除いて (のぞいて) signifie « à l'exception de » : 日曜日を除いて毎日営業している
        (nous sommes ouverts tous les jours sauf le dimanche). C'est un 以外 soutenu ; を除き en est
        la variante écrite.""",
    ),
    "nuki": dict(
        meaning="sans, en laissant de côté",
        structure="Nom + 抜きで",
        explanation="""抜き (ぬき) signifie « sans » : 朝ご飯抜きで出かけた (je suis sorti sans
        petit-déjeuner).""",
    ),
    "irai": dict(
        meaning="depuis",
        structure="Verbe (forme en て) / Nom + 以来",
        explanation="""以来 (いらい) signifie « depuis » : 卒業して以来、彼に会っていない (je ne l'ai pas
        revu depuis la fin de nos études). Après un verbe, il prend la forme en て ; après un nom, il
        se met directement : 先月以来 (depuis le mois dernier).""",
    ),
    "sue_ni": dict(
        meaning="au terme de, finalement",
        structure="Verbe (forme en た) / Nom + の + 末に",
        explanation="""末に (すえに) signifie « au terme de (un long processus) » :
        よく考えた末に、会社を辞めた (après mûre réflexion, j'ai quitté mon entreprise). Il se met
        après un verbe au passé ou un nom + の, et le résultat peut être bon ou mauvais.""",
    ),
    "ageku": dict(
        meaning="au bout du compte (après bien des difficultés)",
        structure="Verbe (forme en た) / Nom + の + あげく",
        explanation="""あげく signifie « après tout ça (et malheureusement) » :
        さんざん迷ったあげく、何も買わなかった (après avoir longuement hésité, je n'ai finalement rien
        acheté).""",
    ),
    "shidai": dict(
        meaning="dès que ; selon",
        structure="Radical du verbe / Nom + 次第",
        explanation="""次第 (しだい) signifie « dès que » (着き次第連絡する, je te contacte dès que
        j'arrive) ou « selon » (天気次第だ, ça dépend du temps).""",
    ),
    "ue_ni": dict(
        meaning="en plus de, de surcroît",
        structure="Forme neutre + 上に",
        explanation="""上に (うえに) ajoute quelque chose dans le même sens : この店は安い上においしい
        (ce restaurant est bon marché, et en plus il est bon).""",
    ),
    "kanenai": dict(
        meaning="risquer de (résultat fâcheux)",
        structure="Radical du verbe + かねない",
        explanation="""かねない avertit qu'une chose fâcheuse pourrait arriver :
        そんな運転では事故を起こしかねない (en conduisant comme ça, tu risques d'avoir un
        accident).""",
    ),
    "kaneru": dict(
        meaning="ne pas pouvoir (poliment)",
        structure="Radical du verbe + かねる",
        explanation="""かねる est un refus poli : そのご質問にはお答えしかねます (je crains de ne pas
        pouvoir répondre à cette question).""",
    ),
    "gatai": dict(
        meaning="difficile à (accepter)",
        structure="Radical du verbe + がたい",
        explanation="""がたい signifie qu'une chose est difficile à accepter ou à faire :
        信じがたい話 (une histoire difficile à croire).""",
    ),
    "zurai": dict(
        meaning="pénible à, malcommode à",
        structure="Radical du verbe + づらい",
        explanation="""づらい signifie « difficile, pénible à faire » : この靴は歩きづらい (on marche
        mal avec ces chaussures).""",
    ),
    "kkonai": dict(
        meaning="impossible que, pas moyen",
        structure="Radical du verbe + っこない",
        explanation="""っこない est un « pas moyen » familier : そんなの、できっこない (ça, c'est
        impossible).""",
    ),
    "eru": dict(
        meaning="pouvoir, possible",
        structure="Radical du verbe + 得る (うる / える)",
        explanation="""得る (うる / える) après un radical de verbe signifie « possible » : ありうる
        (possible), 考えうる (concevable). Le négatif est えない : ありえない (impossible).""",
    ),
    "nuku": dict(
        meaning="faire jusqu'au bout",
        structure="Radical du verbe + 抜く",
        explanation="""抜く (ぬく) après un radical de verbe signifie « jusqu'au bout » :
        最後まで走り抜いた (il a couru jusqu'au bout).""",
    ),
    "ge": dict(
        meaning="qui a l'air",
        structure="Radical de l'adjectif + げ",
        explanation="""げ après un radical d'adjectif signifie « qui a l'air » : 寂しげな顔 (un air
        triste).""",
    ),
    "zaru_wo_enai": dict(
        meaning="ne pas pouvoir faire autrement que",
        structure="Verbe (radical de la forme en ない) + ざるを得ない",
        explanation="""ざるを得ない (えない) signifie « ne pas avoir d'autre choix que » :
        中止せざるを得ない (nous sommes obligés d'annuler). する devient せざる.""",
    ),
    "zuni_wa_irarenai": dict(
        meaning="ne pas pouvoir s'empêcher de",
        structure="Verbe (radical de la forme en ない) + ずにはいられない",
        explanation="""ずにはいられない / ないではいられない signifient « ne pas pouvoir s'empêcher de » :
        笑わずにはいられなかった (je n'ai pas pu m'empêcher de rire). Ils décrivent une envie
        irrépressible ; する devient せずにはいられない.""",
    ),
    "hoka_nai": dict(
        meaning="ne rien pouvoir faire d'autre que",
        structure="Verbe (forme du dictionnaire) + ほかない",
        explanation="""ほかない / よりほかない signifient « il n'y a rien d'autre à faire que » :
        待つほかない (on ne peut qu'attendre).""",
    ),
    "made_mo_nai": dict(
        meaning="pas besoin de",
        structure="Verbe (forme du dictionnaire) + までもない",
        explanation="""までもない signifie « il n'est même pas nécessaire de » : 言うまでもない (inutile
        de le dire).""",
    ),
    "nai_koto_ni_wa": dict(
        meaning="à moins de, tant qu'on ne … pas",
        structure="Verbe (forme en ない) + ことには",
        explanation="""ないことには signifie « tant qu'on ne fait pas (ceci), rien n'est possible » :
        食べてみないことには、分からない (tant qu'on n'a pas goûté, on ne peut pas savoir).""",
    ),
    "mai": dict(
        meaning="ne … pas (volonté ou supposition négative)",
        structure="Verbe (forme du dictionnaire) + まい",
        explanation="""まい est une négation écrite de la volonté ou de la supposition :
        二度と行くまい (je n'y retournerai jamais), 雨は降るまい (il ne pleuvra sans doute pas).""",
    ),
    "you_dewa_nai_ka": dict(
        meaning="… -ons ! (appel au groupe)",
        structure="Verbe (forme volitive) + ではないか",
        explanation="""ようではないか est un appel vibrant adressé à un groupe :
        みんなで頑張ろうではないか (donnons tous le meilleur de nous-mêmes !).""",
    ),
    "mono_nara": dict(
        meaning="si jamais (c'était possible)",
        structure="Verbe (forme potentielle / volitive) + ものなら",
        explanation="""ものなら signifie « si jamais (c'est peu probable) » :
        できるものなら、もう一度やり直したい (si seulement je pouvais, je recommencerais tout).""",
    ),
    "mono_ka": dict(
        meaning="jamais de la vie !",
        structure="Forme neutre + ものか",
        explanation="""ものか (もんか) est un « jamais ! » catégorique : 二度と行くものか (jamais je n'y
        retournerai !).""",
    ),
    "mono_dakara": dict(
        meaning="c'est que (excuse)",
        structure="Forme neutre + ものだから",
        explanation="""ものだから donne une raison, souvent comme excuse :
        道が混んでいたものだから、遅れてしまった (c'est que la route était bouchée, alors je suis en
        retard). À l'oral familier, il devient もんだから ou もので.""",
    ),
    "mono_ga_aru": dict(
        meaning="il y a quelque chose de (impression)",
        structure="Forme neutre + ものがある",
        explanation="""ものがある exprime une impression : 彼の歌には人を感動させるものがある (il y a
        dans ses chansons quelque chose qui touche les gens).""",
    ),
    "mono_dewa_nai": dict(
        meaning="il ne faut pas, ça ne se fait pas",
        structure="Verbe (forme du dictionnaire) + ものではない",
        explanation="""ものではない donne un conseil de bienséance : 人の悪口を言うものではない (on ne
        dit pas du mal des autres). Il nie aussi une idée générale : 努力は必ずしも報われるものではない
        (l'effort n'est pas toujours récompensé).""",
    ),
    "koto_ka": dict(
        meaning="combien … !",
        structure="Mot interrogatif … + ことか",
        explanation="""ことか exprime une émotion forte : どんなに心配したことか (si tu savais combien
        je me suis inquiété !).""",
    ),
    "koto_dakara": dict(
        meaning="le connaissant, comme c'est",
        structure="Nom + の + ことだから",
        explanation="""ことだから donne une raison fondée sur le caractère de quelqu'un :
        彼のことだから、また遅れるだろう (le connaissant, il va encore être en retard).""",
    ),
    "koto_naku": dict(
        meaning="sans (jamais)",
        structure="Verbe (forme du dictionnaire) + ことなく",
        explanation="""ことなく signifie « sans » : 休むことなく働き続けた (il a travaillé sans
        relâche).""",
    ),
    "koto_ni": dict(
        meaning="(je trouve que) … chose, … -ment",
        structure="Adjectif / Verbe (forme en た) + ことに",
        explanation="""ことに exprime le sentiment de celui qui parle face à un fait :
        残念なことに、雨が降ってきた (malheureusement, il s'est mis à pleuvoir).""",
    ),
    "koto_kara": dict(
        meaning="du fait que",
        structure="Forme neutre + ことから",
        explanation="""ことから donne la base d'un jugement ou d'un nom : 富士山が見えることから、この町は富士見と呼ばれる
        (comme on y voit le mont Fuji, cette ville s'appelle Fujimi).""",
    ),
    "to_iu_mono_da": dict(
        meaning="c'est ça, … (vérité générale)",
        structure="Forme neutre + というものだ",
        explanation="""というものだ donne un verdict général sur la nature des choses :
        それが人生というものだ (c'est la vie). Il sonne souvent comme une conclusion ou une petite
        leçon ; というものではない rejette une telle généralisation.""",
    ),
    "to_iu_koto_da": dict(
        title="〜ということだ (ouï-dire)",
        meaning="il paraît que ; cela veut dire que",
        structure="Forme neutre + ということだ",
        explanation="""ということだ / とのことだ rapportent une information : 会議は中止だということだ
        (il paraît que la réunion est annulée). Il sert aussi à résumer ou reformuler :
        要は時間が足りないということだ (bref, ça veut dire qu'on manque de temps).""",
    ),
    "to_itta": dict(
        meaning="tel que, comme",
        structure="Nom + といった + Nom",
        explanation="""といった énumère des exemples : 寿司や天ぷらといった日本料理 (des plats japonais
        comme les sushis ou les tempuras).""",
    ),
    "ka_no_you": dict(
        meaning="comme si",
        structure="Forme neutre + かのように",
        explanation="""かのように signifie « comme si (alors que non) » : 何もなかったかのように笑った (il a
        ri comme si de rien n'était).""",
    ),
    "dake_atte": dict(
        meaning="comme on peut s'y attendre de",
        structure="Forme neutre / Nom + だけあって",
        explanation="""だけあって signifie « comme on pouvait s'y attendre de » : プロだけあって、上手だ
        (c'est un pro, ça se voit : il est doué).""",
    ),
    "dake_ni": dict(
        meaning="d'autant plus que",
        structure="Forme neutre / Nom + だけに",
        explanation="""だけに signifie « justement parce que (d'autant plus) » :
        期待していただけに、がっかりした (j'étais d'autant plus déçu que j'avais de grands
        espoirs).""",
    ),
    "amari_excess": dict(
        meaning="tellement que, sous l'effet de",
        structure="Nom + の / Verbe + あまり",
        explanation="""あまり (dans cet emploi) signifie « sous l'effet d'un excès de… » :
        緊張のあまり、何も言えなかった (j'étais tellement nerveux que je n'ai rien pu dire).""",
    ),
    "sasuga": dict(
        meaning="comme on pouvait s'y attendre",
        structure="さすが(に / は)",
        explanation="""さすが indique que quelque chose est à la hauteur de sa réputation :
        さすがプロだ (c'est bien un pro).""",
    ),
    "semete": dict(
        meaning="au moins",
        structure="せめて …",
        explanation="""せめて signifie « au moins (c'est le minimum que je voudrais) » :
        せめて一日休みたい (j'aimerais au moins un jour de repos).""",
    ),
    "mushiro": dict(
        meaning="plutôt",
        structure="むしろ …",
        explanation="""むしろ signifie « plutôt, à vrai dire » : 涼しいというより、むしろ寒い (il ne fait
        pas frais, il fait plutôt froid). Il choisit la plus juste de deux options, souvent après
        より ou というより.""",
    ),
    "kanarazushimo": dict(
        meaning="pas forcément",
        structure="必ずしも + forme négative",
        explanation="""必ずしも〜ない signifie « pas toujours / pas forcément » :
        高いものが必ずしもいいとは限らない (ce qui est cher n'est pas forcément bien).""",
    ),
    "douse": dict(
        meaning="de toute façon (résigné)",
        structure="どうせ …",
        explanation="""どうせ exprime la résignation : どうせ間に合わない (de toute façon, on n'arrivera
        pas à temps).""",
    ),
    "douyara": dict(
        meaning="on dirait que, apparemment",
        structure="どうやら …",
        explanation="""どうやら signifie « apparemment (à en juger par la situation) » :
        どうやら雨が降りそうだ (on dirait bien qu'il va pleuvoir). Il est généralement suivi de
        らしい, ようだ ou そうだ.""",
    ),
    "yohodo": dict(
        meaning="vraiment (sans doute), drôlement",
        structure="よほど …",
        explanation="""よほど signifie « vraiment (à en juger par les indices) » :
        よほど疲れていたのだろう (il devait être vraiment fatigué).""",
    ),
    "toutei": dict(
        meaning="absolument pas, en aucun cas",
        structure="到底 + forme négative",
        explanation="""到底 (とうてい) + forme négative signifie « absolument pas » : 到底間に合わない
        (il est absolument impossible d'arriver à temps). Il souligne l'impossibilité, souvent avec
        できない ou 無理.""",
    ),
}
