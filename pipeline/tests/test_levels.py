"""N4–N1 grammar points: each pattern must match its own example sentence, and known false
positives (found while reviewing selected sentences) must stay rejected."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import grammar_n1  # noqa: E402,F401
import grammar_n2  # noqa: E402,F401
import grammar_n3  # noqa: E402,F401
import grammar_n4  # noqa: E402,F401
import grammar_n5  # noqa: E402
from extra_examples import EXTRA  # noqa: E402
from jp import tokenize  # noqa: E402
from patterns import POINTS  # noqa: E402

BY_ID = {p["id"]: p for p in POINTS}


def blanks(pid, sentence):
    toks = tokenize(sentence)
    return ["".join(t.s for t in toks[a:b]) for a, b, _ in BY_ID[pid]["match"](toks)]


@pytest.mark.parametrize("p", POINTS, ids=[p["id"] for p in POINTS])
def test_example_matches_exactly_once(p):
    assert len(p["match"](tokenize(p["ex"]))) == 1, p["ex"]


def test_ids_unique_across_levels():
    ids = [p["id"] for p in POINTS] + [p["id"] for p in grammar_n5.POINTS]
    assert len(ids) == len(set(ids))


def test_metadata_complete():
    for p in POINTS:
        assert p["level"] in ("N4", "N3", "N2", "N1")
        assert p["title"] and p["meaning"] and p["structure"], p["id"]
        assert len(p["explanation"]) > 60, p["id"]


def test_level_sizes():
    from collections import Counter
    n = Counter(p["level"] for p in POINTS)
    assert all(n[lv] >= 80 for lv in ("N4", "N3", "N2", "N1")), n


def test_extra_examples_refer_to_known_points():
    assert set(EXTRA) <= set(BY_ID) | {p["id"] for p in grammar_n5.POINTS}
    for pid, items in EXTRA.items():
        for ja, en in items:
            assert ja.endswith(("。", "！", "？")) and en, (pid, ja)


# (point, sentence, expected blank)
POSITIVE = [
    ("noni_purpose", "直すのに、どのくらい時間がかかりますか。", "のに"),
    ("koto_ga_aru_some", "一人になると、時々泣きたくなることがあります。", "ことがあります"),
    ("tara", "家に帰ったら電話します。", "帰ったら"),
    ("sou_look", "このケーキはおいしそうですね。", "おいしそう"),
    ("sou_hear", "明日は雨が降るそうです。", "そうです"),
    ("potential", "私は漢字が読めます。", "読めます"),
    ("passive", "私は先生に褒められました。", "褒められました"),
    ("volitional", "一緒に行こう。", "行こう"),
    ("te_shimau", "財布をなくしてしまいました。", "なくしてしまいました"),
    ("wake_ni_wa_ikanai", "明日は試験なので、遊んでいるわけにはいかない。", "わけにはいかない"),
    ("you_ni_naru", "日本語が話せるようになりました。", "ようになりました"),
    ("zaru_wo_enai", "雨のため、試合を中止せざるを得ない。", "せざるを得ない"),
    ("to_ii_to_ii", "味といい値段といい、申し分ない。", "といい"),
]

# (point, sentence) — false positives seen in real Tatoeba sentences
NEGATIVE = [
    ("ni_itaru", "もし彼がそこにいたら、あなたのメッセージを伝えることができたのにね。"),
    ("katawara", "メアリーは読書をしており、１匹の猫がかたわらで眠っていた。"),
    ("dani", "誰かが君の腕時計を盗んだにちがいない。"),
    ("de_are", "マジであれが着たいの？"),
    ("taru", "渇した者に水を、飢えたる者には糧を与えよ。"),
    ("koto_ni", "台所の床を掃除することに、もうこれ以上の時間を費やしたくなかった。"),
    ("koto_kara", "できることから始めよう！"),
    ("to_itta", "彼女は昨日病気だといったが、それは本当のことではなかった。"),
    ("dake_ni", "トムはメアリーとほんの数分会うためだけに、何時間も待った。"),
    ("mono_dakara", "結果は望ましいものではなかった。"),
    ("mono_ga_aru", "何か必要なものがあったら、遠慮なく言ってください。"),
    ("koto_ka", "なるほど、そういうことか。"),
    ("koto_dakara", "よくあることだから、気にしてないわ。"),
    ("mono_nara", "選んでいただいたものなら何でも結構です。"),
    ("wo_tooshite", "道を開けて子どもを通してください。"),
    ("wo_hajime", "それから、彼は、ケンブリッジで研究を始め、宇宙の本質について考えた。"),
    ("ni_kakete", "彼は礼儀にかけている。"),
    ("ni_kakete", "数学にかけては彼はクラスの誰にも引けを取らない。"),
    ("sue_ni", "今月の末で１０年間ここに住んでいることになります。"),
    ("sue_ni", "彼は末永く記憶に残るだろう。"),
    ("wo_moto_ni", "椅子を元に戻したいのですが。"),
    ("wo_tooshite", "この報告書にざっと目を通していただけませんか。"),
    ("wo_megutte", "お城を巡るのが趣味です。"),
    ("wo_hajime", "彼女は夕食後すぐ宿題を始めた。"),
    ("ni_kakete", "気にかけてくれてありがとう。"),
    ("ni_mukete", "男は銃を警官に向けた。"),
    ("ni_kuwaete", "まず卵を強くかき混ぜそれをスープに加えます。"),
    ("ni_sotte", "本当にそう思います。"),
    ("ni_kuwaete", "僕もゲームに加えて下さい。"),
    ("ni_oujite", "我々は彼らの要求に応じなければならなかった。"),
    ("ni_kakawarazu", "私が来るなと言ったのにかかわらず、彼はやってきた。"),
    ("bakari_da", "あの少年たちは若さがあふれんばかりだ。"),
    ("bakari_ni", "絶好の機会とばかりに飛びついた。"),
    ("bakari_ni", "骨と皮ばかりにやせこけたねこでした。"),
    ("bakari_ni", "彼は同意すると言わんばかりにうなずいた。"),  # N1 んばかり
    ("mono_no", "彼は甘いものの量を減らした。"),
    ("mono_no", "トムは食べたものの何かでアレルギー反応を起こしている。"),
    ("ni_shiro", "お前なぁ、わがままも大概にしろよ。"),
    ("ta_tokoro_de", "次の信号を渡ったところで、止めてください。"),
    ("wari_ni", "この仕事は割に合わないな。"),
    ("ni_atatte", "トムは流れ弾に当たって死んだ。"),
    ("ni_atatte", "お金のことはジェーンにあたってみるよ。"),
    ("kara_suru_to", "飛行機から見ると、その島は巨大なクモのように見える。"),
    ("ni_atatte", "私は火に当たって体を暖めた。"),
    ("ni_atatte", "父の母は、私の祖母にあたります。"),
    ("to_sureba", "１匹の猫を別とすれば家は空っぽだった。"),
    ("to_sureba", "忘れようとすればするほど元彼のこと思い出しちゃう。"),
    ("to_ieba", "どちらかと言えば、私は家にいたいな。"),
    ("kara_suru_to", "空から見ると川は巨大な蛇のように見えた。"),
    ("kara_shite", "他人からしてもらいたいように他人にしなさい。"),
    ("ni_shitara", "甘いものを口にしたら、気分がよくなったわ。"),
    ("ni_shitara", "しゃべるのもいい加減にしたら。"),
    ("gimi", "とても不気味だと思った。"),
    ("gimi", "いい気味。"),
    ("tate", "彼女は気立てがいい。"),
    ("kakeru", "２人が知り合ったきっかけは何だったの？"),
    ("tokoro_datta", "彼女はそのとき、夕食を作っているところだった。"),
    ("to_itte_mo", "彼女は２０歳といっても通用する。"),
    ("ni_shite_mo", "薬だけを頼りにしても治らないよ。"),
    ("kakeru", "彼は見かけよりずっと年をとっている。"),  # appearance
    ("kakeru", "彼女は僕に微笑みかけながら一曲歌った。"),
    ("dasu", "彼の家を見つけだせなかった。"),
    ("to_itte_mo", "彼は天才だと言っても過言ではない。"),
    ("to_itte_mo", "何といっても私がまちがっておりました。"),
    ("ni_shite_wa", "今日はこれでおしまいにしてはどうでしょう。"),
    ("ni_shite_mo", "約束を午前１０時３０分にしてもよろしいですか。"),
    ("koso", "私たちの家へようこそ。"),
    ("wa_mochiron", "彼女はもちろん英語が話せます。"),
    ("ikura_temo", "魚は海にはいくらでもいる。"),
    ("kiri", "３ヶ月に一回、新商品が発表されるのできりがない。"),
    ("mono_da", "僕たちは彼が死んだものだとあきらめた。"),  # ものと思う = assume
    ("kuse_ni", "彼はポケットに手を入れるのが癖になっている。"),  # habit
    ("ni_yotte", "壁により掛かるな。"),  # lean against
    ("ni_tsurete", "母は彼を私の部屋につれてきた。"),  # bring along
    ("ni_shite_wa", "自分の誤りを人のせいにしてはいけない。"),  # must not
    ("koto_ni_natte_iru", "あなた、困ったことになっているんでしょう？"),  # be in trouble
    ("koto_wa_nai", "私はこんなに早く目覚めたことはない。"),  # have never
    ("koto_da", "盗むのはいけないことだ。"),  # not advice
    ("koto_da", "問題は誰が決定を下すかということだ。"),
    ("shika_nai", "この世界に存在するものはすべて、夢でしかない。"),  # でしかない
    ("ni_shitagatte", "父は私を医者にしたがっている。"),  # したがる, not 従う
    ("uchi_ni", "私はたいてい７時頃うちに帰ります。"),  # うち = home
    ("toka", "僕はなんとか時間までにそこに着いた。"),  # なんとか = somehow
    ("toka", "なんで出発前に買っとかなかったの？"),  # っとく = ておく
    ("demo_suggest", "彼は何でも自分の思い通りにしようとする。"),  # 何でも = anything
    ("owaru", "あのドラマ、最後にいつも意味深な言葉を言って終わるよね。"),
    ("zu_ni", "私は彼のことを考えずにはいられない。"),  # N2 ずにはいられない
    ("o_ni_naru", "いろいろお世話になりました。"),  # set phrase
    ("noni", "あなたの家を見つけるのに、何の苦労もありませんでしたよ。"),  # purpose のに
    ("koto_ga_aru_some", "明日は特に何もすることがありません。"),  # こと = thing to do
    ("koto_ga_aru_some", "実はお願いしたいことがありまして。"),
    ("koto_ga_aru_some", "なにか私にできることがありましたらお知らせ下さい。"),
    ("koto_ga_aru_some", "1つ分からないことがあります。"),
    ("koto_ga_aru_some", "やることがあるんだ。"),
    ("koto_ga_aru_some", "変なことがあったんだ。"),
    ("koto_ga_aru_some", "分からないことがあったら、いつでも私に聞きなさい。"),
    ("noni", "直すのに、どのくらい時間がかかりますか。"),  # purpose のに
    ("noni_purpose", "私が来るなと言ったのにかかわらず、彼はやってきた。"),
    ("tara_dou", "明日雨が降ったらどうしようか。"),  # what shall we do if
    ("tara_dou", "失敗したらどうなるんですか。"),  # what happens if
    ("tara_dou", "それ自分がされたらどう思う？"),  # how would you feel if
    ("te_aru", "オーストラリアの学校にも運動会ってあるんですか？"),  # 運動会って, not てある
    ("cha_ikenai", "なんで僕がやらなくちゃいけないの。"),  # なくちゃ = must
    ("deshita", "私のことでしたらご心配なく。"),
    ("de_are", "必要であれば、明日来ますよ。"),             # conditional であれば
    ("ni_shiro", "捕まらないようにしろよ。"),                # imperative of する
    ("ta_tokoro_de", "私の聞いたところでは、彼は来ないそうだ。"),  # "from what I heard"
    ("ijou_wa", "予想した以上に悪い天気だ。"),              # "more than"
    ("ue_de", "犬が芝生の上で寝ている。"),                  # literal "on top of"
    ("naku_shite", "なくしていた財布を見つけた。"),         # the verb なくす
    ("o_suru", "彼はお金を返した。"),                       # お金 is a noun, not お〜する
    ("ku_suru", "努力なくしては何もできない。"),
    ("tsutsu_mo", "明日東京へ立つつもりだ。"),              # つもり, not つつも
    ("sou_look", "彼女はもうすぐ結婚するそうだ。"),         # hearsay, not appearance
    ("tokoro_wo", "彼がカンニングをしているところを見た。"),
    ("noni", "この箱は本を入れるのに便利です。"),           # purpose のに, not "although"
    ("bakari_only", "日本に来たばかりです。"),              # たばかり (just did)
]


@pytest.mark.parametrize("pid,sentence,expected", POSITIVE)
def test_blank(pid, sentence, expected):
    assert expected in blanks(pid, sentence), blanks(pid, sentence)


@pytest.mark.parametrize("pid,sentence", NEGATIVE)
def test_false_positive_rejected(pid, sentence):
    if pid in BY_ID:
        assert blanks(pid, sentence) == []
    else:  # N5 point
        p = next(p for p in grammar_n5.POINTS if p["id"] == pid)
        assert p["match"](tokenize(sentence)) == []
