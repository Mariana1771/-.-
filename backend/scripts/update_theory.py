import os
import sys


def main() -> None:
    from pathlib import Path

    # Ensure project root is on sys.path when running from /scripts
    project_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(project_root))

    sys.stdout.reconfigure(encoding="utf-8")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lingua.settings")

    import django  # noqa: WPS433

    django.setup()

    from learning.models import Lesson  # noqa: WPS433

    theories: dict[int, str] = {
        # -------- A1 --------
        1: """
<div class="theory-block prose">
  <h3>Привітання та знайомство (A1)</h3>
  <p><b>Коли що казати</b>:</p>
  <ul>
    <li><b>Dobrý deň</b> — універсально і ввічливо (майже завжди ок).</li>
    <li><b>Ahoj / Čau</b> — неформально (друзі, знайомі).</li>
    <li><b>Dovidenia</b> — до побачення (ввічливо).</li>
  </ul>
  <p><b>Знайомство</b> — 3 базові фрази:</p>
  <ul>
    <li><b>Volám sa …</b> — Мене звати …</li>
    <li><b>Som z …</b> — Я з …</li>
    <li><b>Teší ma.</b> — Приємно.</li>
  </ul>
  <p><b>Міні-діалог</b>:</p>
  <p>
    A: <i>Dobrý deň. Volám sa Oľha. A vy?</i><br/>
    B: <i>Dobrý deň. Ja som Martin. Teší ma.</i><br/>
    A: <i>Teší ma. Som z Ukrajiny.</i>
  </p>
  <p><b>Типові помилки</b>: <i>Som …</i> = “я є/я (професія/стан)”, а <i>Som z …</i> = “я з (країни/міста)”.</p>
</div>
""".strip(),
        2: """
<div class="theory-block prose">
  <h3>Дієслово <i>byť</i> (бути) — A1</h3>
  <p><b>byť</b> — головне дієслово для “я є/ти є/він є”. Його використовуємо для: професії, стану, національності, місця (з прикметником).</p>
  <table>
    <tr><th>Особа</th><th>Форма</th><th>Приклад</th></tr>
    <tr><td>ja</td><td><b>som</b></td><td>Ja <b>som</b> študent/študentka.</td></tr>
    <tr><td>ty</td><td><b>si</b></td><td>Ty <b>si</b> doma?</td></tr>
    <tr><td>on/ona/ono</td><td><b>je</b></td><td>Ona <b>je</b> unavená.</td></tr>
    <tr><td>my</td><td><b>sme</b></td><td>My <b>sme</b> z Kyjeva.</td></tr>
    <tr><td>vy</td><td><b>ste</b></td><td>Vy <b>ste</b> učitelia?</td></tr>
    <tr><td>oni/ony</td><td><b>sú</b></td><td>Oni <b>sú</b> v práci.</td></tr>
  </table>
  <p><b>Заперечення</b>: пишемо <b>nie</b> окремо: <b>nie som</b>, <b>nie je</b>, <b>nie sme</b>.</p>
  <p><b>Шаблон</b>: (хто) + forma byť + (хто/який/де).<br/>
     <i>Ja som z Ukrajiny.</i> / <i>Ona je lekárka.</i> / <i>My sme doma.</i>
  </p>
</div>
""".strip(),
        3: """
<div class="theory-block prose">
  <h3>Числівники 1–20 (A1)</h3>
  <p>Вчи числа як “блок”: 1–10, потім 11–19, далі 20.</p>
  <p><b>1–10</b>: jeden/jedna, dva/dve, tri, štyri, päť, šesť, sedem, osem, deväť, desať.</p>
  <p><b>11–19</b> зазвичай мають -násť: <i>jedenásť, dvanásť, trinásť, …, devätnásť</i>.</p>
  <p><b>20</b>: <b>dvadsať</b>.</p>
  <p><b>Приклади</b>:</p>
  <ul>
    <li><i>Mám <b>päť</b> otázok.</i> — У мене 5 питань.</li>
    <li><i>Je <b>desať</b> hodín.</i> — 10 година.</li>
    <li><i>Potrebujem <b>dvanásť</b> minút.</i> — Мені потрібно 12 хв.</li>
  </ul>
  <p><b>Важливі нюанси</b>:</p>
  <ul>
    <li><b>jeden / jedna / jedno</b> — залежить від роду: <i>jeden muž</i>, <i>jedna žena</i>, <i>jedno auto</i>.</li>
    <li><b>dva / dve</b> — “два” теж має варіант: <i>dva muži</i>, але <i>dve ženy</i>.</li>
  </ul>
  <p><b>Міні-практика</b> (прочитай вголос):</p>
  <ul>
    <li><i>Mám 11 rokov.</i></li>
    <li><i>O 15 minút odchádzam.</i></li>
    <li><i>Je 20:10.</i></li>
  </ul>
  <p><b>Порада</b>: у словацькій часто кажуть <i>koľko máš rokov?</i> (скільки маєш років), а не “я є 20”.</p>
</div>
""".strip(),
        14: """
<div class="theory-block prose">
  <h3>Дієслово <i>mať</i> (мати) + вік (A1)</h3>
  <p><b>mať</b> використовуємо для “мати/володіти” і для віку.</p>
  <table>
    <tr><th>Особа</th><th>Форма</th><th>Приклад</th></tr>
    <tr><td>ja</td><td><b>mám</b></td><td><i><b>Mám</b> čas.</i></td></tr>
    <tr><td>ty</td><td><b>máš</b></td><td><i><b>Máš</b> auto?</i></td></tr>
    <tr><td>on/ona</td><td><b>má</b></td><td><i>Ona <b>má</b> problém.</i></td></tr>
    <tr><td>my</td><td><b>máme</b></td><td><i><b>Máme</b> dve mačky.</i></td></tr>
    <tr><td>vy</td><td><b>máte</b></td><td><i><b>Máte</b> otázku?</i></td></tr>
    <tr><td>oni</td><td><b>majú</b></td><td><i><b>Majú</b> čas.</i></td></tr>
  </table>
  <p><b>Вік</b>: <b>Mám 20 rokov.</b> — дослівно “маю 20 років”.</p>
  <p><b>Заперечення</b>: <b>ne</b> + разом: <b>nemám</b>, <b>nemáš</b>, <b>nemá</b>…</p>
</div>
""".strip(),
        15: """
<div class="theory-block prose">
  <h3>Питальні слова + базові питання (A1)</h3>
  <p><b>Питальні слова</b> допомагають будувати короткі питання без складної граматики.</p>
  <table>
    <tr><th>Словацькою</th><th>Українською</th><th>Приклад</th></tr>
    <tr><td><b>Kto?</b></td><td>хто?</td><td><i><b>Kto</b> je to?</i></td></tr>
    <tr><td><b>Čo?</b></td><td>що?</td><td><i><b>Čo</b> robíš?</i></td></tr>
    <tr><td><b>Kde?</b></td><td>де?</td><td><i><b>Kde</b> bývaš?</i></td></tr>
    <tr><td><b>Kedy?</b></td><td>коли?</td><td><i><b>Kedy</b> ideš?</i></td></tr>
    <tr><td><b>Ako?</b></td><td>як?</td><td><i><b>Ako</b> sa máš?</i></td></tr>
    <tr><td><b>Prečo?</b></td><td>чому?</td><td><i><b>Prečo</b> si doma?</i></td></tr>
    <tr><td><b>Koľko?</b></td><td>скільки?</td><td><i><b>Koľko</b> to stojí?</i></td></tr>
    <tr><td><b>Odkiaľ?</b></td><td>звідки?</td><td><i><b>Odkiaľ</b> si?</i></td></tr>
  </table>
  <p><b>Шаблон</b>: питальне слово + дієслово + решта. <br/>Напр.: <i>Kde je stanica?</i> / <i>Koľko máš rokov?</i></p>
</div>
""".strip(),
        24: """
<div class="theory-block prose">
  <h3>Займенники + <i>byť/mať</i> (теп., мин., майб.) — A1</h3>
  <p>Це “ядро” рівня A1: якщо ти це розумієш і вмієш застосувати — ти вже можеш будувати десятки базових речень.</p>

  <h3>1) Присвійні займенники (môj/tvoj/…)</h3>
  <p><b>Хто?</b> → “чий/чия/чиє?”</p>
  <table>
    <tr><th>Особа</th><th>чий?</th><th>чия?</th><th>чиє?</th></tr>
    <tr><td>ja</td><td><b>môj</b></td><td><b>moja</b></td><td><b>moje</b></td></tr>
    <tr><td>ty</td><td><b>tvoj</b></td><td><b>tvoja</b></td><td><b>tvoje</b></td></tr>
    <tr><td>my</td><td><b>náš</b></td><td><b>naša</b></td><td><b>naše</b></td></tr>
    <tr><td>vy</td><td><b>váš</b></td><td><b>vaša</b></td><td><b>vaše</b></td></tr>
  </table>
  <p><b>Його/її/їх</b> (часто без зміни форми): <b>jeho</b> (його), <b>jej</b> (її), <b>ich</b> (їхній).</p>
  <p><b>Приклади</b>:</p>
  <ul>
    <li><i>Toto je <b>môj</b> dom.</i></li>
    <li><i>Kde je <b>tvoja</b> mama?</i></li>
    <li><i>Moja sestra má mačku. <b>Jej</b> mačka sa volá Lia.</i></li>
    <li><i>Sú už <b>ich</b> rodičia doma?</i></li>
  </ul>

  <h3>2) Питальні слова</h3>
  <table>
    <tr><th>Словацькою</th><th>Українською</th><th>Приклад</th></tr>
    <tr><td><b>Kto?</b></td><td>хто?</td><td><i><b>Kto</b> je to?</i></td></tr>
    <tr><td><b>Čo?</b></td><td>що?</td><td><i><b>Čo</b> je to?</i></td></tr>
    <tr><td><b>Čí / čia / čie?</b></td><td>чий/чия/чиє?</td><td><i><b>Čí</b> je to dom?</i></td></tr>
  </table>
  <p><b>Шаблон</b>: <i>To je mama.</i> → питання: <i><b>Kto</b> je to?</i><br/>
     <i>To je lampa.</i> → питання: <i><b>Čo</b> je to?</i></p>

  <h3>3) Важлива різниця: <i>oni</i> vs <i>ony</i></h3>
  <p>У базовому рівні запам’ятай просто:</p>
  <ul>
    <li><b>oni</b> — зазвичай група з чоловіками / або змішана група (є хоча б один чоловік).</li>
    <li><b>ony</b> — жіночий рід (дівчата/жінки) та багато неістот.</li>
  </ul>
  <p><b>Приклади</b>:</p>
  <ul>
    <li><i>Futbalisti hrajú futbal. <b>Oni</b> hrajú futbal.</i></li>
    <li><i>Dievčatá sa hrajú vo dvore. <b>Ony</b> sa hrajú vo dvore.</i></li>
    <li><i>Zošity ležia na stole. <b>Ony</b> ležia na stole.</i></li>
    <li><i>Päť dievčat a jeden chlap sa smiali. <b>Oni</b> sa smiali.</i></li>
  </ul>

  <h3>4) <i>byť</i> (бути) — теперішній час</h3>
  <table>
    <tr><th>Особа</th><th>Форма</th><th>Приклад</th></tr>
    <tr><td>ja</td><td><b>som</b></td><td><i>Som hladný/hladná.</i></td></tr>
    <tr><td>ty</td><td><b>si</b></td><td><i>Odkiaľ <b>si</b>?</i></td></tr>
    <tr><td>on/ona/ono</td><td><b>je</b></td><td><i>Ona <b>je</b> unavená.</i></td></tr>
    <tr><td>my</td><td><b>sme</b></td><td><i>Sme žiaci.</i></td></tr>
    <tr><td>vy</td><td><b>ste</b></td><td><i>Ste učiteľ?</i></td></tr>
    <tr><td>oni/ony</td><td><b>sú</b></td><td><i>Oni/ony <b>sú</b> doma.</i></td></tr>
  </table>
  <p><b>Заперечення (теп. час)</b>: частка <b>nie</b> пишеться <b>окремо</b>: <i>nie som, nie je, nie sme…</i></p>
  <p><b>Приклад</b>: <i>Nie som študentka, som učiteľka.</i></p>

  <h3>5) <i>byť</i> — майбутній і минулий час</h3>
  <p><b>Майбутній</b>:</p>
  <p><i>budem, budeš, bude, budeme, budete, budú</i></p>
  <p><b>Приклад</b>: <i>Budem zajtra doma.</i></p>
  <p><b>Минулий</b> (узгодження за родом):</p>
  <ul>
    <li><i>bol som</i> (чол.), <i>bola som</i> (жін.), <i>bolo</i> (сер.), <i>boli sme</i> (множ.)</li>
  </ul>
  <p><b>Приклади</b>:</p>
  <ul>
    <li><i>Bol si dnes v škole?</i></li>
    <li><i>Boli sme na dedine.</i></li>
  </ul>
  <p><b>Заперечення (мин./майб.)</b>: <b>ne-</b> пишеться <b>разом</b>: <i>nebol, nebola, nebudeš…</i></p>
  <p><i>Nebudeš zajtra v škole.</i> / <i>Včera som nebola v kine.</i></p>

  <h3>6) <i>mať</i> (мати) — теперішній час</h3>
  <table>
    <tr><th>Особа</th><th>Форма</th><th>Приклад</th></tr>
    <tr><td>ja</td><td><b>mám</b></td><td><i>Mám pekné šaty.</i></td></tr>
    <tr><td>ty</td><td><b>máš</b></td><td><i>Máš pravdu.</i></td></tr>
    <tr><td>on/ona/ono</td><td><b>má</b></td><td><i>Má nový zošit.</i></td></tr>
    <tr><td>my</td><td><b>máme</b></td><td><i>Máme veľa zošitov.</i></td></tr>
    <tr><td>vy</td><td><b>máte</b></td><td><i>Máte dnes voľno?</i></td></tr>
    <tr><td>oni/ony</td><td><b>majú</b></td><td><i>Majú peknú dcéru.</i></td></tr>
  </table>
  <p><b>Заперечення</b>: <b>ne-</b> разом: <i>nemám, nemáš, nemá…</i></p>

  <h3>7) Не плутай: <i>byť</i> / <i>byt</i> / <i>biť</i></h3>
  <ul>
    <li><b>byť</b> — бути</li>
    <li><b>byt</b> — квартира</li>
    <li><b>biť</b> — бити</li>
  </ul>

  <h3>Міні-практика (як у конспекті)</h3>
  <p><b>Заповни пропуски</b> (приклад):</p>
  <ul>
    <li><i>Toto je (my) ___ nové auto.</i></li>
    <li><i>(vy) ___ dom? Nie, to nie je (my) ___ dom.</i></li>
    <li><i>Moja sestra má mačku. (ona) ___ mačka sa volá Lia.</i></li>
  </ul>
  <p><b>Постав питання</b>:</p>
  <p><i>To je mesto.</i> → <i>Čo je to?</i> / <i>To je mama.</i> → <i>Kto je to?</i></p>
</div>
""".strip(),
        13: """
<div class="theory-block prose">
  <h3>Родина + присвійні займенники (A1)</h3>
  <p><b>1) Лексика “родина”</b> — мінімум, який потрібен щодня:</p>
  <ul>
    <li><b>mama</b> — мама, <b>otec</b> — тато</li>
    <li><b>brat</b> — брат, <b>sestra</b> — сестра</li>
    <li><b>syn</b> — син, <b>dcéra</b> — донька</li>
    <li><b>starý otec</b> — дідусь, <b>stará mama</b> — бабуся</li>
  </ul>
  <p><b>2) Присвійні займенники</b> відповідають на питання “чий/чия/чиє?” і змінюються за родом:</p>
  <table>
    <tr><th>Хто</th><th>Чий?</th><th>Чия?</th><th>Чиє?</th></tr>
    <tr><td>я</td><td><b>môj</b></td><td><b>moja</b></td><td><b>moje</b></td></tr>
    <tr><td>ти</td><td><b>tvoj</b></td><td><b>tvoja</b></td><td><b>tvoje</b></td></tr>
    <tr><td>ми</td><td><b>náš</b></td><td><b>naša</b></td><td><b>naše</b></td></tr>
    <tr><td>ви</td><td><b>váš</b></td><td><b>vaša</b></td><td><b>vaše</b></td></tr>
  </table>
  <p><b>Його/її/їх</b> в базовому рівні часто без зміни форми:</p>
  <ul>
    <li><b>jeho</b> — його, <b>jej</b> — її, <b>ich</b> — їхній</li>
  </ul>
  <p><b>Приклади</b>:</p>
  <ul>
    <li><i>To je <b>môj</b> brat.</i></li>
    <li><i>Kde je <b>tvoja</b> sestra?</i></li>
    <li><i>To sú <b>ich</b> rodičia.</i></li>
  </ul>
  <p><b>Типова помилка</b>: не плутай <i>jej</i> (її) з <i>ja</i> (я). <i>jej</i> — присвійний займенник.</p>
</div>
""".strip(),

        # -------- A2 --------
        4: """
<div class="theory-block prose">
  <h3>Теперішній час (A2): як утворюється</h3>
  <p>У теперішньому часі форма змінюється за особами. Важливо вчити дієслово одразу як “табличку”.</p>
  <p><b>robiť</b> (робити): robím, robíš, robí, robíme, robíte, robia.</p>
  <p><b>pracovať</b> (працювати): pracujem, pracuješ, pracuje, pracujeme, pracujete, pracujú.</p>
  <p><b>Позиція підмета</b> часто не обовʼязкова: <i>Robím úlohu.</i> = <i>Ja robím úlohu.</i></p>
  <p><b>Приклади</b>:</p>
  <ul>
    <li><i>Čo <b>robíš</b> dnes?</i></li>
    <li><i>My <b>pracujeme</b> každý deň.</i></li>
  </ul>
  <p><b>Як вчитись швидко</b>:</p>
  <ul>
    <li>Випиши 6 форм (ja/ty/on/my/vy/oni) і проговори 2–3 рази.</li>
    <li>Зроби 3 речення з кожною формою: <i>robím, robíš, robí…</i></li>
  </ul>
  <p><b>Типові помилки</b>:</p>
  <ul>
    <li>Не плутай закінчення <i>-ujem</i> / <i>-uješ</i>: <i>pracujem</i> (я) vs <i>pracuješ</i> (ти).</li>
    <li>У питанні інтонація часто важливіша за порядок слів: <i>Robíš dnes?</i></li>
  </ul>
</div>
""".strip(),
        5: """
<div class="theory-block prose">
  <h3>Відмінки (A2): навіщо вони і як не плутатись</h3>
  <p>У словацькій 7 відмінків. На практиці починай з: <b>Genitív</b> після <i>do</i>, <b>Datív</b> після <i>k</i>, <b>Lokál</b> після <i>v/o</i>, <b>Inštrumentál</b> після <i>s/so</i>.</p>
  <p><b>Приклад “žena”</b> (жінка):</p>
  <p>žena → ženy → žene → ženu → žena → (o) žene → (so) ženou</p>
  <p><b>Міні-правило</b>: не вчи “всі 7 одразу”, вчи разом із прийменником і прикладом: <i>do školy</i>, <i>v škole</i>, <i>so sestrou</i>.</p>
  <p><b>Шпаргалка (найчастіше)</b>:</p>
  <ul>
    <li><b>do + Gen.</b>: <i>Idem do mesta.</i></li>
    <li><b>v + Lok.</b>: <i>Som v meste.</i></li>
    <li><b>k + Dat.</b>: <i>Idem k lekárovi.</i></li>
    <li><b>s/so + Inštr.</b>: <i>Som s kamarátom.</i></li>
  </ul>
  <p><b>Типова плутанина</b>: “де?” ≠ “куди?”. <i>Som v škole</i> (де), але <i>Idem do školy</i> (куди).</p>
</div>
""".strip(),
        18: """
<div class="theory-block prose">
  <h3>Прислівники частоти (A2)</h3>
  <p>Ці слова відповідають на “як часто?” і роблять мову природнішою.</p>
  <ul>
    <li><b>vždy</b> — завжди</li>
    <li><b>často</b> — часто</li>
    <li><b>niekedy</b> — інколи</li>
    <li><b>zriedka</b> — рідко</li>
    <li><b>nikdy</b> — ніколи</li>
  </ul>
  <p><b>Позиція</b>: зазвичай перед дієсловом: <i>Ja <b>často</b> pracujem doma.</i></p>
  <p><b>Заперечення</b>: <i>nikdy</i> часто йде з дієсловом із <b>ne-</b>: <i>Nikdy <b>nefajčím</b>.</i></p>
  <p><b>Де ставити у реченні</b> (швидка логіка):</p>
  <ul>
    <li>перед дієсловом: <i>Ona <b>niekedy</b> chodí pešo.</i></li>
    <li>після <i>byť</i> можна теж природно: <i>Je <b>často</b> unavená.</i> (але найчастіше — перед основним дієсловом)</li>
  </ul>
  <p><b>Міні-практика (готові речення)</b> — спробуй заміняти прислівник:</p>
  <ul>
    <li><i>Ja ___ varím večeru.</i> (vždy/často/niekedy/zriedka/nikdy)</li>
    <li><i>My ___ cestujeme vlakom.</i></li>
  </ul>
  <p><b>Типові помилки</b>:</p>
  <ul>
    <li><i>nikdy</i> + дієслово без <b>ne-</b> звучить неприродно: краще <i>Nikdy <b>nepijem</b> kávu.</i></li>
    <li>не плутай <i>niekedy</i> (інколи) з <i>niekde</i> (десь).</li>
  </ul>
</div>
""".strip(),
        19: """
<div class="theory-block prose">
  <h3>Reflexívні дієслова (A2): <i>sa/si</i></h3>
  <p>Reflexívне дієслово має частку <b>sa</b> або <b>si</b>. Вона не перекладається дослівно, але є частиною конструкції.</p>
  <ul>
    <li><b>učiť sa</b> — вчитись</li>
    <li><b>volať sa</b> — називатись</li>
    <li><b>cítiť sa</b> — почуватись</li>
  </ul>
  <p><b>Правило 2-ї позиції</b> (простими словами): <b>sa/si</b> часто стоїть після першого “сильного” слова:</p>
  <p><i>Dnes <b>sa</b> učím.</i> / <i>Ako <b>sa</b> cítiš?</i></p>
  <p><b>Коли sa, а коли si?</b></p>
  <ul>
    <li><b>sa</b> — найчастіше “себе” як об’єкт дії або частина дієслова: <i>učiť <b>sa</b></i>, <i>cítiť <b>sa</b></i>.</li>
    <li><b>si</b> — часто має значення “собі”: <i>dať <b>si</b> kávu</i> (випити кави), <i>kúpiť <b>si</b> lístok</i>.</li>
  </ul>
  <p><b>Більше прикладів</b>:</p>
  <ul>
    <li><i>Volám <b>sa</b> Katka.</i></li>
    <li><i>My <b>sa</b> stretávame každý týždeň.</i></li>
    <li><i>Dám <b>si</b> čaj.</i></li>
  </ul>
  <p><b>Типові помилки</b>:</p>
  <ul>
    <li>не став <i>sa</i> на початок: *<i>Sa učím dnes</i>* → <i>Dnes <b>sa</b> učím.</i></li>
    <li>не перекладай дослівно українське “себе” — вчи як готову конструкцію: <i>volať sa</i>, <i>cítiť sa</i>.</li>
  </ul>
</div>
""".strip(),
        7: """
<div class="theory-block prose">
  <h3>Модальні дієслова (A2): <i>musieť / môcť / chcieť</i></h3>
  <p>Модальні дієслова показують <b>не дію</b>, а <b>ставлення</b> до дії: хочу / можу / мушу.</p>
  <p><b>Головне правило</b>: модальне дієслово + <b>інфінітив</b> (форма “робити/піти/купити”).</p>
  <p><b>Приклади</b>:</p>
  <ul>
    <li><i>Musím <b>ísť</b>.</i> — Мушу піти.</li>
    <li><i>Môžem <b>pomôcť</b>?</i> — Можу допомогти?</li>
    <li><i>Chcem <b>kúpiť</b> chlieb.</i> — Хочу купити хліб.</li>
  </ul>
  <p><b>Швидкі форми (теперішній час)</b> — достатньо найчастіших:</p>
  <table>
    <tr><th></th><th>musieť</th><th>môcť</th><th>chcieť</th></tr>
    <tr><td>ja</td><td><b>musím</b></td><td><b>môžem</b></td><td><b>chcem</b></td></tr>
    <tr><td>ty</td><td>musíš</td><td>môžeš</td><td>chceš</td></tr>
    <tr><td>on/ona</td><td>musí</td><td>môže</td><td>chce</td></tr>
    <tr><td>my</td><td>musíme</td><td>môžeme</td><td>chceme</td></tr>
    <tr><td>vy</td><td>musíte</td><td>môžete</td><td>chcete</td></tr>
    <tr><td>oni</td><td>musia</td><td>môžu</td><td>chcú</td></tr>
  </table>
  <p><b>Типові помилки</b>: не кажи *<i>musím idem</i>* — після модального має бути інфінітив: <i>musím ísť</i>.</p>
</div>
""".strip(),
        8: """
<div class="theory-block prose">
  <h3>Прийменники + відмінки (A2): “де?” vs “куди?”</h3>
  <p>Найчастіша плутанина — різниця між <b>місцем</b> і <b>напрямком</b>.</p>
  <table>
    <tr><th>Питання</th><th>Словацькою</th><th>Відмінок</th><th>Приклад</th></tr>
    <tr><td>Де?</td><td><b>v</b> (у/в)</td><td>Lokál</td><td><i>Som <b>v</b> škole.</i></td></tr>
    <tr><td>Куди?</td><td><b>do</b> (до всередину)</td><td>Genitív</td><td><i>Idem <b>do</b> školy.</i></td></tr>
    <tr><td>Куди (на поверхню/подію)?</td><td><b>na</b></td><td>Akuzatív</td><td><i>Idem <b>na</b> stanicu.</i></td></tr>
    <tr><td>До кого/чого?</td><td><b>k</b></td><td>Datív</td><td><i>Idem <b>k</b> lekárovi.</i></td></tr>
    <tr><td>З ким/чим?</td><td><b>s/so</b></td><td>Inštrumentál</td><td><i>Som <b>so</b> sestrou.</i></td></tr>
  </table>
  <p><b>Порада</b>: вчи фразами парами: <i>Som v práci</i> ↔ <i>Idem do práce</i>.</p>
</div>
""".strip(),
        9: """
<div class="theory-block prose">
  <h3>Майбутній час (A2): <i>budem + інфінітив</i></h3>
  <p>Для <b>недоконаних</b> дієслів (процес, регулярність) майбутній час часто будуємо через <b>byť</b> у майбутньому.</p>
  <p><b>Формула</b>: <b>budem/budeš/bude/budeme/budete/budú</b> + інфінітив.</p>
  <p><b>Приклади</b>:</p>
  <ul>
    <li><i>Zajtra <b>budem pracovať</b>.</i></li>
    <li><i>Večer <b>budeme variť</b>.</i></li>
    <li><i>Kedy <b>budeš mať</b> čas?</i></li>
  </ul>
  <p><b>Негатив</b>: <b>ne-</b> пишемо разом із формою <i>budem</i>:</p>
  <ul>
    <li><i><b>Nebudem</b> pracovať.</i> — Я не буду працювати.</li>
    <li><i><b>Nebudeme</b> doma.</i> — Ми не будемо вдома.</li>
  </ul>
  <p><b>Питання</b> (інтонація): <i>Budeš zajtra doma?</i></p>
  <p><b>Важливо</b>: багато доконаних дієслів мають “коротке майбутнє” без <i>budem</i>: <i>urobím, napíšem</i> (це вже ближче до B1).</p>
</div>
""".strip(),
        16: """
<div class="theory-block prose">
  <h3>Порівняння прикметників (A2)</h3>
  <p>Є 3 ступені: <b>позитив</b> (який?), <b>компаратив</b> (якіший?), <b>суперлатив</b> (най-).</p>
  <table>
    <tr><th>Ступінь</th><th>Приклад</th><th>Значення</th></tr>
    <tr><td>позитив</td><td><b>pekný</b></td><td>гарний</td></tr>
    <tr><td>компаратив</td><td><b>krajší</b></td><td>гарніший</td></tr>
    <tr><td>суперлатив</td><td><b>najkrajší</b></td><td>найгарніший</td></tr>
  </table>
  <p><b>Часті нерегулярні</b>:</p>
  <ul>
    <li><b>dobrý → lepší → najlepší</b></li>
    <li><b>veľký → väčší → najväčší</b></li>
  </ul>
  <p><b>Приклад у реченні</b>: <i>Tento film je <b>lepší</b>.</i> / <i>To je <b>najlepší</b> deň.</i></p>
</div>
""".strip(),
        17: """
<div class="theory-block prose">
  <h3>Imperatív (A2): прохання і наказ</h3>
  <p>Imperatív — це форма “зроби/зробіть”. У словацькій важливо розрізняти <b>ти</b> і <b>ви</b> (ввічливо або до групи).</p>
  <p><b>Найуживаніші</b>:</p>
  <ul>
    <li><b>Poď!</b> — Ходімо! (до “ти”)</li>
    <li><b>Poďte!</b> — Ходімо/ходіть! (ввічливо/до групи)</li>
    <li><b>Povedz!</b> — Скажи! / <b>Povedzte!</b> — Скажіть!</li>
    <li><b>Pozri!</b> — Подивись! / <b>Pozrite!</b> — Подивіться!</li>
  </ul>
  <p><b>Ввічлива форма</b> майже завжди звучить краще з <i>prosím</i>: <i>Povedzte, prosím, pomaly.</i></p>
</div>
""".strip(),
        44: """
<div class="theory-block prose">
  <h3>Погода (A2): як говорити природно</h3>
  <p>Найчастіше вживається конструкція <b>Je + прикметник</b> або просто дієслово.</p>
  <table>
    <tr><th>Словацькою</th><th>Українською</th><th>Коментар</th></tr>
    <tr><td><b>Je slnečno.</b></td><td>Сонячно.</td><td>Je + прикметник</td></tr>
    <tr><td><b>Je zamračené.</b></td><td>Хмарно.</td><td>нейтрально</td></tr>
    <tr><td><b>Prší.</b></td><td>Дощить.</td><td>дієслово без “je”</td></tr>
    <tr><td><b>Sneží.</b></td><td>Сніжить.</td><td>дієслово без “je”</td></tr>
  </table>
  <p><b>Приклади</b>:</p>
  <ul>
    <li><i>Dnes je slnečno, ale večer prší.</i></li>
    <li><i>Zajtra bude zamračené.</i></li>
  </ul>
</div>
""".strip(),

        # -------- B1 --------
        22: """
<div class="theory-block prose">
  <h3>Непряма мова (B1): <i>povedal, že…</i></h3>
  <p>Непряма мова потрібна, коли переказуємо слова/думку іншої людини.</p>
  <p><b>Шаблон</b>: X + (povedal/povedala) + <b>že</b> + речення.</p>
  <ul>
    <li><i>On povedal, <b>že</b> príde.</i> — Він сказав, що прийде.</li>
    <li><i>Ona povedala, <b>že</b> nemá čas.</i> — Вона сказала, що не має часу.</li>
  </ul>
  <p><b>Як звучати природніше</b> (часті дієслова “сказати/пояснити/думати”):</p>
  <ul>
    <li><i>Tvrdí, že…</i> — стверджує, що…</li>
    <li><i>Myslí si, že…</i> — думає, що…</li>
    <li><i>Vysvetlil, že…</i> — пояснив, що…</li>
  </ul>
  <p><b>Міні-практика</b> (перетвори пряму мову на непряму):</p>
  <ul>
    <li>Пряма: <i>„Nemám čas.“</i> → Непряма: <i>Ona povedala, že nemá čas.</i></li>
    <li>Пряма: <i>„Prídem zajtra.“</i> → <i>On povedal, že príde zajtra.</i></li>
  </ul>
  <p><b>Типові помилки</b>:</p>
  <ul>
    <li>не плутай <i>že</i> (що) з <i>aby</i> (щоб).</li>
    <li>не “рви” речення: краще коротко і ясно, ніж складно і з помилками.</li>
  </ul>
  <p><b>Порада</b>: не ускладнюй. На B1 достатньо стабільно будувати “že + речення” з правильним часом у контексті.</p>
</div>
""".strip(),
        23: """
<div class="theory-block prose">
  <h3>Заперечення в минулому (B1)</h3>
  <p>У минулому часі заперечення робимо через <b>ne-</b> перед формою:</p>
  <ul>
    <li><b>byť</b>: <i>bol</i> → <b>nebol</b>, <i>bola</i> → <b>nebola</b>, <i>boli</i> → <b>neboli</b></li>
    <li>інші дієслова: <i>urobil</i> → <b>neurobil</b>, <i>povedala</i> → <b>nepovedala</b></li>
  </ul>
  <p><b>Приклади</b>:</p>
  <p><i>Včera som <b>nebol</b> doma.</i><br/><i>Ona <b>nešla</b> do práce.</i></p>
  <p><b>Що важливо памʼятати</b>:</p>
  <ul>
    <li>заперечення пишеться <b>разом</b>: <i>ne+bol</i>, <i>ne+urobil</i>, <i>ne+šiel</i>.</li>
    <li>форма дієприкметника лишається “родова”: <i>nebol</i> (чол.), <i>nebola</i> (жін.), <i>nebolo</i> (сер.), <i>neboli</i> (множ.).</li>
  </ul>
  <p><b>Міні-практика</b> (запереч):</p>
  <ul>
    <li><i>Včera som bol v škole.</i> → <i>Včera som <b>nebol</b> v škole.</i></li>
    <li><i>Ona povedala pravdu.</i> → <i>Ona <b>nepovedala</b> pravdu.</i></li>
    <li><i>My sme išli domov.</i> → <i>My sme <b>nešli</b> domov.</i></li>
  </ul>
</div>
""".strip(),
        6: """
<div class="theory-block prose">
  <h3>Минулий час (B1): як утворюється і коли що вибрати</h3>
  <p>Минулий час утворюємо через “бути” + дієприкметник на <b>-l</b>. Дієприкметник узгоджується за родом/числом.</p>
  <p><b>Формула</b>: <b>som/si/sme/ste</b> + <b>robil/robila/robili</b>.</p>
  <table>
    <tr><th></th><th>чол.</th><th>жін.</th><th>множина</th></tr>
    <tr><td>ja</td><td>som robil</td><td>som robila</td><td>—</td></tr>
    <tr><td>ty</td><td>si robil</td><td>si robila</td><td>—</td></tr>
    <tr><td>on/ona</td><td>robil</td><td>robila</td><td>—</td></tr>
    <tr><td>my</td><td colspan="3">sme robili</td></tr>
    <tr><td>vy</td><td colspan="3">ste robili</td></tr>
    <tr><td>oni</td><td colspan="3">robili</td></tr>
  </table>
  <p><b>Приклади</b>: <i>Včera som pracoval/pracovala.</i> / <i>My sme boli doma.</i></p>
  <p><b>Типова помилка</b>: не забувай про рід: <i>ja som bola</i> (жін.), <i>ja som bol</i> (чол.).</p>
</div>
""".strip(),
        10: """
<div class="theory-block prose">
  <h3>Вид дієслів (B1): процес vs результат</h3>
  <p>Словацька (як і українська) має <b>недоконаний</b> (процес/повторення) і <b>доконаний</b> (результат/одна дія) вид.</p>
  <table>
    <tr><th>Недоконаний</th><th>Доконаний</th><th>Приклад</th></tr>
    <tr><td>robiť</td><td>urobiť</td><td><i>Dnes <b>robím</b> úlohu.</i> vs <i>Dnes <b>urobím</b> úlohu.</i></td></tr>
    <tr><td>písať</td><td>napísať</td><td><i>Píšem e-mail.</i> vs <i>Napíšem e-mail.</i></td></tr>
  </table>
  <p><b>Майбутнє</b>:</p>
  <ul>
    <li>недоконаний: <i>budem robiť</i></li>
    <li>доконаний: <i>urobím</i></li>
  </ul>
  <p><b>Як вибрати?</b> Якщо важливий результат/завершення — доконаний. Якщо процес/тривалість — недоконаний.</p>
</div>
""".strip(),
        11: """
<div class="theory-block prose">
  <h3>Умовний спосіб (B1): “я б…”</h3>
  <p>Умовний спосіб потрібен для ввічливості, побажань, гіпотез: “я б зробив”, “ти б міг”.</p>
  <p><b>Формула</b>: <b>by</b> + (som/si/sme/ste) + дієприкметник (-l/-la/-li).</p>
  <p><b>Приклади</b>:</p>
  <ul>
    <li><i><b>By som si dal</b> kávu.</i> — Я б випив кави.</li>
    <li><i><b>By si mi pomohol</b>?</i> — Ти б мені допоміг?</li>
    <li><i><b>Boli by ste</b> takí láskaví…?</i> — Ввічливий формат.</li>
  </ul>
  <p><b>Порада</b>: умовний дуже “піднімає рівень” мовлення, бо звучить мʼяко і доречно.</p>
</div>
""".strip(),
        12: """
<div class="theory-block prose">
  <h3>Підрядні речення (B1): <i>že / aby / keď</i></h3>
  <p>Ці сполучники допомагають з’єднувати думки в “дорослі” речення.</p>
  <ul>
    <li><b>že</b> — “що” (думка/повідомлення): <i>Myslím, <b>že</b> je to dobré.</i></li>
    <li><b>aby</b> — “щоб” (мета): <i>Učím sa, <b>aby</b> som rozumel.</i></li>
    <li><b>keď</b> — “коли/якщо” (час/умова): <i><b>Keď</b> prší, ostávam doma.</i></li>
  </ul>
  <p><b>Типові помилки</b>:</p>
  <ul>
    <li>після <i>aby</i> часто потрібне <i>som/si/sme…</i>: <i>aby som…</i></li>
    <li>не плутай <i>že</i> і <i>aby</i>: <i>že</i> = факт/думка, <i>aby</i> = мета.</li>
  </ul>
</div>
""".strip(),
        20: """
<div class="theory-block prose">
  <h3>Порядок слів + enklitiky <i>sa/si</i> (B1)</h3>
  <p>У словацькій порядок слів гнучкий, але є правило: короткі слова (enklitiky) часто йдуть <b>на 2-й позиції</b>.</p>
  <p><b>Найчастіші</b>: <b>sa, si, mi, ti, mu, jej, ho, ju</b>.</p>
  <p><b>Приклади</b>:</p>
  <ul>
    <li><i>Dnes <b>sa</b> učím.</i> (після першого слова)</li>
    <li><i>Ja <b>si</b> myslím, že…</i></li>
    <li><i>Prečo <b>si</b> to myslíš?</i></li>
  </ul>
  <p><b>Практичний лайфхак</b>: спочатку став “перший шматок” речення, потім одразу <i>sa/si</i>, а далі — решту.</p>
</div>
""".strip(),
        21: """
<div class="theory-block prose">
  <h3>Зворотні займенники (B1): <i>seba</i> і <i>svoj</i></h3>
  <p>Це тема, яка сильно впливає на “нативність”.</p>
  <p><b>seba</b> = “себе” (обʼєкт):</p>
  <ul>
    <li><i>Vidím <b>seba</b> v zrkadle.</i></li>
  </ul>
  <p><b>svoj</b> = “свій” (коли власник = підмет):</p>
  <ul>
    <li><i>Beriem <b>svoj</b> telefón.</i> (я беру свій телефон)</li>
    <li><i>Ona berie <b>svoj</b> telefón.</i> (вона бере свій телефон)</li>
  </ul>
  <p><b>Чому не môj?</b> Бо <i>môj</i> = “мій” (я власник), а <i>svoj</i> працює з будь-яким підметом: я/ти/вона/ми.</p>
</div>
""".strip(),

        # -------- B2 (переписуємо “дипломно”, структурно) --------
        52: """
<div class="theory-block prose">
  <h3>B2: Стиль (нейтральний vs формальний)</h3>
  <p>На B2 важливо не тільки “правильно”, а й <b>доречно</b>. В одній ситуації підходить нейтрально, в іншій — формально.</p>
  <table>
    <tr><th>Нейтрально</th><th>Формально</th><th>Коли</th></tr>
    <tr><td>Chcem sa opýtať…</td><td>Dovoľte mi opýtať sa…</td><td>питання до незнайомої людини / у листі</td></tr>
    <tr><td>Môžete mi povedať…?</td><td>Mohli by ste mi, prosím, povedať…?</td><td>ввічливо, без тиску</td></tr>
    <tr><td>Pošlem vám to dnes.</td><td>Zašlem vám to dnes.</td><td>листування/робота</td></tr>
  </table>
  <p><b>Ключ</b>: у формальному стилі частіше використовують <b>podmieňovací spôsob</b> (by ste/by som) та “м’які” конструкції.</p>
  <p><b>Приклад</b>:<br/>
     <i>Mohli by ste mi prosím poslať zhrnutie zo stretnutia?</i></p>
</div>
""".strip(),
        53: """
<div class="theory-block prose">
  <h3>B2: Väzby (керування) — говорити як носій</h3>
  <p>Часто помилка на B2 — не закінчення, а <b>прийменник</b> після дієслова. Тому вчи “дієслово + прийменник + приклад”.</p>
  <table>
    <tr><th>Вираз</th><th>Модель</th><th>Приклад</th></tr>
    <tr><td><b>Záleží to od…</b></td><td>od + Gen.</td><td><i>Záleží to <b>od</b> času.</i></td></tr>
    <tr><td><b>Prispieť k…</b></td><td>k + Dat.</td><td><i>To prispelo <b>k</b> úspechu.</i></td></tr>
    <tr><td><b>Veriť v…</b></td><td>v + Akuz.</td><td><i>Verím <b>v</b> zmenu.</i></td></tr>
    <tr><td><b>Spoliehať sa na…</b></td><td>na + Akuz.</td><td><i>Spolieham sa <b>na</b> teba.</i></td></tr>
  </table>
  <p><b>Порада</b>: запиши 1 приклад і повторюй як “готову фразу”. Це швидше, ніж зубрити правила.</p>
</div>
""".strip(),
        54: """
<div class="theory-block prose">
  <h3>B2: Пасив і participiá — коли це справді потрібно</h3>
  <p>Пасив корисний, коли важливий <b>результат</b> або коли виконавець неважливий/невідомий (офіційний стиль, новини).</p>
  <p><b>1) Стан / результат</b> (часто “je/sú + príčastie”):<br/>
     <i>Dvere sú otvorené.</i> / <i>Projekt je pripravený.</i>
  </p>
  <p><b>2) Подія в минулому</b> (“bol/bola/bolo/boli + príčastie”):<br/>
     <i>Dom <b>bol postavený</b> v roku 2010.</i>
  </p>
  <p><b>3) Майбутнє</b> (“bude/budú + príčastie”):<br/>
     <i>Zmluva <b>bude podpísaná</b> zajtra.</i>
  </p>
  <p><b>Типова помилка</b>: не плутай “я роблю” з “зроблено”.<br/>
     <i>Robím správu.</i> (я роблю) vs <i>Správa je urobená.</i> (зроблено)
  </p>
</div>
""".strip(),
        55: """
<div class="theory-block prose">
  <h3>B2: Small talk + м’які уточнення</h3>
  <p>Small talk — це не “порожні слова”, а спосіб звучати природно: додати уточнення, змінити тему, показати ввічливість.</p>
  <p><b>Слова-переходи</b>: <i>mimochodom</i> (між іншим), <i>vlastne</i> (власне), <i>v podstate</i> (по суті), <i>úprimne</i> (чесно).</p>
  <p><b>М’яке уточнення</b>:</p>
  <ul>
    <li><i>Ak tomu dobre rozumiem, myslíš…?</i> — Якщо правильно розумію, ти маєш на увазі…?</li>
    <li><i>Mohol by si to trochu spresniť?</i> — Можеш трохи уточнити?</li>
  </ul>
  <p><b>Фрази, щоб підтримати розмову</b>:</p>
  <ul>
    <li><i>To znie zaujímavo.</i> — Це звучить цікаво.</li>
    <li><i>A ako si sa k tomu dostal/a?</i> — А як ти до цього прийшов/прийшла?</li>
    <li><i>Čo ťa na tom baví najviac?</i> — Що тобі в цьому подобається найбільше?</li>
  </ul>
  <p><b>Як “мʼяко не погодитись”</b> (без конфлікту):</p>
  <ul>
    <li><i>Chápem, ale ja to vnímam trochu inak.</i> — Розумію, але я сприймаю трохи інакше.</li>
    <li><i>Je možné, že máš pravdu, napriek tomu…</i> — Можливо, ти правий/права, попри це…</li>
  </ul>
  <p><b>Міні-діалог</b>:<br/>
     A: <i>Mimochodom, ako to dopadlo?</i><br/>
     B: <i>Úprimne? Celkom dobre, ale trvalo to dlhšie.</i>
  </p>
  <p><b>Міні-практика</b>: перефразуй нейтрально → ввічливо:</p>
  <ul>
    <li><i>Čo chceš?</i> → <i>Môžem sa spýtať, čo potrebuješ?</i></li>
    <li><i>Nerozumiem.</i> → <i>Prepáč, mohol by si to vysvetliť trochu inak?</i></li>
  </ul>
</div>
""".strip(),
        56: """
<div class="theory-block prose">
  <h3>B2: Робота — зустрічі, дедлайни, пріоритети</h3>
  <p><b>Ціль</b>: говорити чітко, але ввічливо. На роботі часто важливі: терміни, пріоритет, домовленості.</p>
  <p><b>Базові фрази</b>:</p>
  <ul>
    <li><i>Máme termín do piatku.</i> — дедлайн до п’ятниці</li>
    <li><i>Je to vysoká priorita.</i> — високий пріоритет</li>
    <li><i>Posuňme to na pondelok.</i> — перенесімо на понеділок</li>
    <li><i>Pošlem vám zhrnutie.</i> — надішлю підсумок</li>
  </ul>
  <p><b>Ввічлива пропозиція</b>: <i>Navrhujem, aby sme…</i> / <i>Bolo by lepšie, keby…</i></p>
  <p><b>Зустріч (meeting) — міні-структура</b>:</p>
  <ul>
    <li><b>ціль</b>: <i>Cieľom stretnutia je…</i></li>
    <li><b>план</b>: <i>Navrhujem tento postup…</i></li>
    <li><b>домовленість</b>: <i>Dohodnime sa, že…</i></li>
    <li><b>підсумок</b>: <i>Pošlem krátke zhrnutie.</i></li>
  </ul>
  <p><b>Ввічливі формули</b> (піднімають рівень):</p>
  <ul>
    <li><i>Mohli by sme to posunúť na…?</i> — Чи могли б перенести на…?</li>
    <li><i>Bolo by možné dostať spätnú väzbu do…?</i> — Чи можна отримати фідбек до…?</li>
  </ul>
  <p><b>Типові помилки</b>:</p>
  <ul>
    <li>не плутай <i>termín</i> (дедлайн/термін) і <i>stretnutie</i> (зустріч).</li>
    <li>краще сказати конкретно: <i>do piatku</i>, <i>do 17:00</i>, ніж “швидко”.</li>
  </ul>
</div>
""".strip(),
        57: """
<div class="theory-block prose">
  <h3>B2: Подорожі — проблеми та рішення</h3>
  <p>Коли виникає проблема, важливо: <b>описати факт</b> → <b>попросити перевірити</b> → <b>запропонувати рішення</b>.</p>
  <p><b>Корисні шаблони</b>:</p>
  <ul>
    <li><i>Zdá sa, že došlo k chybe…</i> — здається, сталася помилка…</li>
    <li><i>Mohli by ste to prosím overiť?</i> — можете перевірити?</li>
    <li><i>Je možné to zmeniť / vymeniť?</i> — можна змінити/обміняти?</li>
  </ul>
  <p><b>Приклад</b>: <i>Zdá sa, že moja rezervácia nie je v systéme. Mohli by ste to prosím overiť?</i></p>
  <p><b>Лексика “проблеми”</b>:</p>
  <ul>
    <li><b>rezervácia</b> — резервація, <b>letenka</b> — авіаквиток</li>
    <li><b>meškanie</b> — затримка, <b>zrušenie</b> — скасування</li>
    <li><b>reklamácia</b> — скарга/претензія</li>
  </ul>
  <p><b>Як звучати професійно</b>:</p>
  <ul>
    <li><i>Mohli by ste mi prosím povedať, čo sa stalo?</i></li>
    <li><i>Potreboval/a by som potvrdenie e-mailom.</i> — потрібне підтвердження листом</li>
    <li><i>Aké sú možnosti riešenia?</i> — які варіанти рішення?</li>
  </ul>
  <p><b>Міні-практика</b>: зроби 2 речення про проблему + 1 речення з рішенням (шаблон):<br/>
     <i>Zdá sa, že… / Potreboval/a by som… / Je možné…?</i>
  </p>
</div>
""".strip(),
        58: """
<div class="theory-block prose">
  <h3>B2: Думка й аргументи (структуровано)</h3>
  <p><b>Структура</b>: теза → причина → приклад → висновок. Це “дипломно” виглядає в будь-якому тексті.</p>
  <p><b>Зв’язки</b>:</p>
  <ul>
    <li><i>Na jednej strane… na druhej strane…</i></li>
    <li><i>Okrem toho</i> (крім того), <i>napriek tomu</i> (попри це), <i>z tohto dôvodu</i> (з цієї причини)</li>
  </ul>
  <p><b>Приклад</b>: <i>Na jednej strane je to pohodlné, na druhej strane to môže byť drahé. Napriek tomu sa to často oplatí.</i></p>
  <p><b>Готові шаблони для аргументації</b>:</p>
  <ul>
    <li><i>Podľa môjho názoru…</i> — на мою думку…</li>
    <li><i>Domnievam sa, že…</i> — я вважаю, що… (більш формально)</li>
    <li><i>Je to dôležité, pretože…</i> — це важливо, тому що…</li>
    <li><i>Napríklad…</i> — наприклад…</li>
  </ul>
  <p><b>Міні-практика</b>: напиши 4 речення за схемою:</p>
  <ul>
    <li>1) <i>Podľa môjho názoru …</i></li>
    <li>2) <i>Je to dôležité, pretože …</i></li>
    <li>3) <i>Napríklad …</i></li>
    <li>4) <i>Z tohto dôvodu …</i></li>
  </ul>
  <p><b>Типові помилки</b>: не став 5 причин одразу — краще 1–2 сильні аргументи + приклад.</p>
</div>
""".strip(),
        59: """
<div class="theory-block prose">
  <h3>B2: Скарга / reklamácia (ввічливо)</h3>
  <p>Сильна скарга на B2 — це <b>тон</b> + <b>факт</b> + <b>очікування</b>.</p>
  <p><b>Шаблон</b>:</p>
  <ul>
    <li><i>Chcel by som sa sťažovať na…</i></li>
    <li><i>Nie som spokojný/á s…</i></li>
    <li><i>Bol by som rád, keby sme našli riešenie.</i></li>
    <li><i>Očakávam vrátenie peňazí / výmenu.</i></li>
  </ul>
  <p><b>Приклад</b>: <i>Nie som spokojný s kvalitou. Bol by som rád, keby sme našli riešenie.</i></p>
  <p><b>Як написати/сказати скаргу “правильно”</b>:</p>
  <ul>
    <li><b>факт</b>: що саме сталося (без емоцій)</li>
    <li><b>дата/деталі</b>: коли, номер замовлення, чек</li>
    <li><b>очікування</b>: що ти хочеш (обмін/повернення/знижка)</li>
  </ul>
  <p><b>Корисні фрази</b>:</p>
  <ul>
    <li><i>Objednávka číslo…</i> — замовлення №…</li>
    <li><i>Tovar prišiel poškodený.</i> — товар прийшов пошкоджений</li>
    <li><i>Prosím o výmenu / vrátenie peňazí.</i></li>
    <li><i>Bol by som vďačný, keby ste mi odpovedali do…</i> — буду вдячний за відповідь до…</li>
  </ul>
  <p><b>Міні-шаблон (копіюй і міняй деталі)</b>:</p>
  <p>
    <i>Dobrý deň, chcel by som sa sťažovať na …</i><br/>
    <i>Objednávka číslo … z dňa …</i><br/>
    <i>Prosím o výmenu / vrátenie peňazí.</i><br/>
    <i>Ďakujem.</i>
  </p>
</div>
""".strip(),
    }

    updated = 0
    missing: list[int] = []
    for lesson_id, html in theories.items():
        try:
            l = Lesson.objects.get(id=lesson_id)
        except Lesson.DoesNotExist:
            missing.append(lesson_id)
            continue
        l.theory = html
        l.save(update_fields=["theory"])
        updated += 1

    print(f"Updated theory for {updated} lesson(s).")
    if missing:
        print("Missing lesson ids:", missing)


if __name__ == "__main__":
    main()

