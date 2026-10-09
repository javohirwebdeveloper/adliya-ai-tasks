# RAG: 1-topshiriq bazasi + qalqon + Gemma 4

Savollar: 1-topshiriqning ko'r to'plami, bazada bor 120 ta va bazada yo'q 60 ta. Har savolga to'qima ism, pasport, telefon qo'shilgan; Gemma faqat qalqondan o'tgan matnni ko'rgan.

**Qidirish** (to'g'ri javob 1-o'rinda / 3 talikda):

| So'rov | 1-o'rin | 3 talik |
|---|---|---|
| Toza savol (1-topshiriqdagi o'lchov) | 87.5% | 91.7% |
| Shaxsiy ma'lumotli savol, yashirilgan matnning o'zi (Gemma'ga shu manbalar berildi) | 75.8% | 81.7% |
| Shaxsiy ma'lumot berilgan gaplar oddiy qoida bilan olib tashlangan (rad etildi) | 74.2% | 79.2% |
| Gemma qayta yozgan qidiruv savoli | 81.7% | 87.5% |

| | RAG'siz Gemma | RAG bilan |
|---|---|---|
| Bazada bor savolga javob berdi | 99.2% | 81.7% |
| Hakam: to'g'ri | 27.5% | 75.0% |
| Hakam: qisman | 64.2% | 6.7% |
| Hakam: noto'g'ri | 7.5% | 0.0% |
| Bazada yo'q savolga "javob yo'q" dedi | 41.7% | 100.0% |
| Javob fuqaro tilida | 95.8% | 89.8% |
| O'zidan belgi ([ISM_2] kabi) to'qidi | 0 | 0 |

RAG javoblarining 96.9% i to'g'ri manbaga havola qilgan (to'g'ri javob manbalar orasida bo'lgan holatlarning 97.9% i).
RAG bazada bor 22 ta savolga "javob yo'q" dedi: ulardan 1 tasida to'g'ri javob topilgan 3 manba orasida bor edi (ortiqcha ehtiyotkorlik), qolganlarida qidiruv uni topmagan.
Javobdagi summa, muddat kabi raqam manbada yo'q holatlar: RAG'siz 0, RAG bilan 0. RAG'siz Gemma raqam aytishdan qochgan, lekin idora va tartibni to'qigan (hakam bahosi shuni ushlaydi).
Hakam bahosi va "to'g'ri" ulushlari bazada bor hamma savolga nisbatan (rad etilganlar ham maxrajda).
