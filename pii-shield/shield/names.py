"""Ko'p uchraydigan ismlar: yolg'iz yozilgan ismni ("men Dilshod", "Aziza opa") topish uchun.
Familiyasiz ism faqat yonida ishora bo'lsa yashiriladi: oldida "men", "ismim", "fuqaro"; ortida "aka", "opa", "xonim".
"""
MALE = """Abbos Abdulaziz Abdulla Abdurahmon Abdusamad Abduaziz Abror Adham Akbar Akmal Akrom Alibek Alisher Anvar Asilbek
Asror Aziz Azizbek Bahodir Bahrom Baxtiyor Bahtiyor Behruz Bekzod Bobur Botir Davron Dilmurod Dilshod Diyor Doniyor
Dostonbek Elbek Eldor Elyor Ergash Erkin Farhod Farrux Fazliddin Feruz G'ayrat G'ofur Hamid Hasan Hayot Husan Ibrohim
Ikrom Ilhom Islom Islombek Ismoil Jahongir Jaloliddin Jamshid Jasur Javlon Javohir Kamol Kamoliddin Komil Laziz Lochin
Mahmud Mansur Mirjalol Muhammad Muhammadali Murod Muzaffar Nodir Nurbek Nuriddin Odil Olim Otabek Oybek Ozod Po'lat
Qahramon Qodir Rahim Rahmon Rasul Ravshan Ruslan Rustam Sanjar Sardor Sardorbek Sarvar Shavkat Sherzod Shohruh Shoxrux
Shuhrat Sirojiddin Sobir Sulton Sunnat Temur Timur Tohir Tolib Ulug'bek Umar Umid Usmon Xurshid Yusuf Zafar Ziyodulla
Zokir Bekmurod Jo'rabek Mirzo Nosir Obid Rauf Sodiq Toir Valijon Yorqin Zuhriddin Abdulloh Asadbek Bunyod Hojiakbar
Ivan Viktor Sergey Aleksandr Dmitriy Nikolay Andrey Pavel Vladimir Oleg Igor"""
FEMALE = """Aziza Barno Charos Dildora Dilfuza Dilnoza Dilorom Dinara Durdona Feruza Gulbahor Gulchehra Gulnora Gulshan
Hilola Iroda Kamola Kumush Laylo Lola Madina Maftuna Malika Marjona Mohinur Mohira Muazzam Munisa Nargiza Nigora
Nilufar Nodira Oydin Ozoda Rayhon Robiya Sabina Sevara Shahnoza Shahzoda Shoira Sitora Umida Yulduz Zarina Zebo Zilola
Zuhra Mavluda Muhabbat Nasiba Saodat Xurshida Yorqinoy Farangiz Gulnoza Dilbar Mastura Ra'no Anna Elena Olga Tatyana
Natalya Irina Mariya Yekaterina Svetlana"""
FIRST_NAMES = sorted(set((MALE + " " + FEMALE).split()), key=len, reverse=True)
