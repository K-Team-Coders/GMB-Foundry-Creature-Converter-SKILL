# Русский / English → dnd5e keys

Russian statblocks come from different translations (Phantom Lancer / dnd.su,
official 2024 «Студия 101», Hobby World, fan translations), so several words map
to the same key. When a word is not here, translate by meaning.

## Abilities
| key | RU | short | EN |
|---|---|---|---|
| str | Сила | СИЛ | Strength |
| dex | Ловкость | ЛОВ | Dexterity |
| con | Телосложение, Выносливость | ТЕЛ, ВЫН | Constitution |
| int | Интеллект | ИНТ | Intelligence |
| wis | Мудрость | МДР, МУД | Wisdom |
| cha | Харизма | ХАР | Charisma |

## Skills
| key | RU variants | EN |
|---|---|---|
| acr | Акробатика | Acrobatics |
| ani | Уход за животными, Обращение с животными | Animal Handling |
| arc | Магия, Тайные знания | Arcana |
| ath | Атлетика | Athletics |
| dec | Обман | Deception |
| his | История | History |
| ins | Проницательность | Insight |
| itm | Запугивание | Intimidation |
| inv | Анализ, Расследование | Investigation |
| med | Медицина | Medicine |
| nat | Природа | Nature |
| prc | Внимательность, Восприятие | Perception |
| prf | Выступление | Performance |
| per | Убеждение | Persuasion |
| rel | Религия | Religion |
| slt | Ловкость рук | Sleight of Hand |
| ste | Скрытность | Stealth |
| sur | Выживание | Survival |

## Sizes
tiny — Крошечный · sm — Маленький · med — Средний · lg — Большой · huge — Огромный · grg — Громадный, Колоссальный

## Creature types
aberration — Аберрация · beast — Зверь · celestial — Небожитель, Небесный · construct — Конструкт ·
dragon — Дракон · elemental — Элементаль, Стихийный · fey — Фея, Фейское существо ·
fiend — Исчадие, Изверг · giant — Великан · humanoid — Гуманоид · monstrosity — Монстр, Чудовище ·
ooze — Слизь · plant — Растение · undead — Нежить

## Damage types
| key | RU |
|---|---|
| acid | кислота, кислотный |
| bludgeoning | дробящий |
| cold | холод |
| fire | огонь |
| force | силовое поле, силовой, энергия силы |
| lightning | электричество, молния |
| necrotic | некротическая энергия, некротический |
| piercing | колющий |
| poison | яд |
| psychic | психическая энергия, психический |
| radiant | излучение, свет, сияющий |
| slashing | рубящий, режущий |
| thunder | звук, гром |

«от немагических атак» → put bludgeoning/piercing/slashing in the list and `"<key>_bypasses": ["mgc"]`.
«…не посеребрённых» → `sil`, «…не адамантиновых» → `ada`.

## Conditions
blinded ослеплённый · charmed очарованный, обворожённый · deafened оглохший ·
exhaustion истощение · frightened испуганный · grappled схваченный ·
incapacitated недееспособный · invisible невидимый · paralyzed парализованный ·
petrified окаменевший · poisoned отравленный · prone сбитый с ног, лежащий ничком ·
restrained опутанный, обездвиженный · stunned ошеломлённый · unconscious бессознательный

## Senses
darkvision тёмное зрение · blindsight слепое зрение · tremorsense чувство вибрации, сейсмочувствие ·
truesight истинное зрение. «пассивная Внимательность N» — computed by Foundry, ignore.

## Languages (keys)
common Общий, Всеобщий · dwarvish Дварфийский · elvish Эльфийский · giant Великанский ·
gnomish Гномий · goblin Гоблинский · halfling Полуросликов · orc Орочий ·
abyssal Бездны · celestial Небесный · deep Глубинная речь · draconic Драконий ·
infernal Инфернальный · primordial Первичный (aquan Акван, auran Ауран, ignan Игнан, terran Терран) ·
sylvan Сильван, Лесной · undercommon Подземный · druidic Друидический · cant Воровской жаргон.
Anything else («любые два языка», «понимает, но не говорит») → `languages_custom`.

## Activation
action — действие · bonus — бонусное действие · reaction — реакция ·
legendary — легендарное действие · lair — действие логова · special — особое ·
minute/hour — время сотворения в минутах/часах.

## Uses / recovery
«перезарядка 5–6» → `{"recharge":5}` · «перезарядка 6» → `{"recharge":6}` ·
«N/день», «N раз в день» → `{"max":N,"per":"day"}` ·
«после короткого или продолжительного отдыха» → `per: "sr"` ·
«после продолжительного отдыха» → `per: "lr"` · «на рассвете» → `per: "dawn"`.

## Areas
cone конус · cube куб · cylinder цилиндр · line линия · sphere сфера · radius радиус ·
square квадрат · wall стена. «Эманация» (2024) → `radius` centred on self.

## Spell schools
abj ограждение · con вызов, призыв · div прорицание · enc очарование ·
evo воплощение, эвокация · ill иллюзия · nec некромантия · trs преобразование, трансмутация

## Spell components
vocal В/Вербальный · somatic С/Соматический · material М/Материальный

## Weapon properties
fin фехтовальное · lgt лёгкое · hvy тяжёлое · two двуручное · ver универсальное ·
thr метательное · amm боеприпас · lod перезарядка · rch досягаемость ·
spc особое · mgc магическое · sil посеребрённое · ada адамантиновое
