import os
import base64
import datetime
from flask import Flask, render_template, request, redirect, url_for, Response
from fpdf import FPDF
from PIL import Image
from vercel_blob import put, blob # Vercel Blobライブラリをインポート (get -> blob に修正)
from io import BytesIO 

# --- Path Configuration (Vercel Deployment Fix) ---
basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__, template_folder=os.path.join(basedir, 'templates'))

# --- Configuration ---
SECRET_TOKEN = os.environ.get("SECRET_TOKEN", "ajs") 
FONT_FILE = os.path.join(basedir, "NotoSansJP-Regular.ttf")

# --- Data ---
EXPLAINERS = {
    "vi": [ "PHAM VAN THINH", "HOANG ANH NAM" ],
    "id": [ "PETRI SURYANI", "IMELDA SARIHUTAJULU", "FEBRI SAHRULLAH AHDIN", "MARISYA UTARI", "MOHAMMAD FARID HIDAYATULLAH", "VANESSA KOBAYASHI" ],
    "my": [ "PYO EAINDRAY MIN", "PHYOWAI ZAW" ],
    "jp": [ "西野 宏" ],
    "en": [] 
}
TRANSLATIONS = {
    "en": {
        "title": "Confirmation of Preliminary Guidance",
        "items": [
            "1. Matters concerning the content of duties, amount of remuneration, and other working conditions.",
            "2. Content of activities that I can perform in Japan.",
            "3. Matters concerning immigration procedures.",
            "4. Neither I, nor my spouse, lineal relatives, cohabiting relatives, or other persons in a close social relationship with me, will have money or other property managed, nor will any contract stipulating penalties for non-performance of the Specified Skilled Worker employment contract be concluded, in connection with my activities in Japan.",
            "5. If I have paid fees to an organization in my home country for brokerage of the Specified Skilled Worker employment contract application or for preparation for activities, I must fully understand the amount and breakdown and have agreed to it with that organization.",
            "6. The costs required for my support will not be borne by me, either directly or indirectly.",
            "7. The accepting organization must provide transportation from the port of entry or airport where I will arrive in Japan.",
            "8. Support for securing appropriate housing will be provided to me.",
            "9. A system is in place to receive consultations or complaints from me regarding my professional, daily, or social life."
        ],
        "final_confirmation": "Furthermore, regarding item 4, neither I nor my spouse, etc., have currently made any payments for security deposits or entered into contracts related to penalties, and we will not do so in the future.",
        "signature_label": "Signature of the Specified Skilled Worker",
        "agree_checkbox": "I confirm and agree to all the contents above.",
        "submit_button": "Submit Signature and Proceed"
    },
    "id": {
        "title": "Konfirmasi Bimbingan Awal",
        "items": [
            "1. Hal-hal mengenai isi pekerjaan, jumlah upah, dan kondisi kerja lainnya.",
            "2. Isi kegiatan yang dapat saya lakukan di Jepang.",
            "3. Hal-hal mengenai prosedur masuk ke Jepang.",
            "4. Saya, pasangan saya, kerabat langsung, kerabat yang tinggal bersama, atau orang lain yang memiliki hubungan sosial yang erat dengan saya tidak akan menyerahkan pengelolaan uang atau properti lainnya, dan tidak akan menandatangani kontrak yang menetapkan denda atas wanprestasi kontrak kerja Pekerja Berketerampilan Spesifik.",
            "5. Jika saya telah membayar biaya kepada organisasi di negara asal saya untuk perantaraan aplikasi kontrak kerja atau persiapan kegiatan, saya harus sepenuhnya memahami jumlah dan rinciannya dan telah menyetujuinya.",
            "6. Biaya yang diperlukan untuk dukungan saya tidak akan dibebankan kepada saya, baik secara langsung maupun tidak langsung.",
            "7. Organisasi penerima harus menyediakan penjemputan di pelabuhan atau bandara kedatangan saya di Jepang.",
            "8. Dukungan untuk mendapatkan tempat tinggal yang layak akan diberikan kepada saya.",
            "9. Tersedia sistem untuk menerima konsultasi atau keluhan dari saya mengenai kehidupan kerja, sehari-hari, atau sosial."
        ],
        "final_confirmation": "Selanjutnya, mengenai butir 4, saya maupun pasangan saya, dll., saat ini tidak melakukan pembayaran uang jaminan atau terikat kontrak terkait denda, dan tidak akan melakukannya di masa mendatang.",
        "signature_label": "Tanda Tangan Pekerja Berketerampilan Spesifik",
        "agree_checkbox": "Saya mengonfirmasi dan menyetujui semua isi di atas.",
        "submit_button": "Kirim Tanda Tangan dan Lanjutkan"
    },
    "my": {
        "title": "ကြိုတင်လမ်းညွှန်ချက် အတည်ပြုလွှာ",
        "items": [
            "၁။ ကျွန်ုပ်လုပ်ဆောင်ရမည့် လုပ်ငန်းတာဝန်များ၊ လစာပမာဏနှင့် အခြားအလုပ်သမားဆိုင်ရာ အခြေအနေများ။",
            "၂။ ကျွန်ုပ် ဂျပန်နိုင်ငံတွင် လုပ်ဆောင်နိုင်သော လှုပ်ရှားမှုများ၏ အကြောင်းအရာ။",
            "၃။ ကျွန်ုပ်၏ နိုင်ငံတွင်းဝင်ရောက်ခြင်းဆိုင်ရာ လုပ်ထုံးလုပ်နည်းများနှင့် ပတ်သက်သည့်အချက်များ။",
            "၄။ ကျွန်ုပ် သို့မဟုတ် ကျွန်ုပ်၏အိမ်ထောင်ဖက်၊ တိုက်ရိုက်ဆွေမျိုးများ၊ အတူနေဆွေမျိုးများ သို့မဟုတ် ကျွန်ုပ်နှင့် လူမှုရေးအရ ရင်းနှီးသောဆက်ဆံရေးရှိသူများသည် သတ်မှတ်ထားသော ကျွမ်းကျင်လုပ်သား အလုပ်ခန့်ထားမှု စာချုပ်အရ ကျွန်ုပ်၏ ဂျပန်နိုင်ငံでの လှုပ်ရှားမှုများနှင့်ဆက်စပ်၍ အာမခံငွေကောက်ခံခြင်း သို့မဟုတ် အခြားမည်သည့်အကြောင်းပြချက်ဖြင့်မဆို ငွေကြေး သို့မဟုတ် အခြားပိုင်ဆိုင်မှုများကို စီမံခန့်ခွဲခြင်းမပြုရ။ ထို့အပြင် စာချုပ်ပါအချက်များကို မလိုက်နာပါက ဒဏ်ငွေသတ်မှတ်သည့် စာချုပ်များ သို့မဟုတ် ငွေကြေးနှင့် အခြားပိုင်ဆိုင်မှုများကို မတရားလွှဲပြောင်းရန် စီစဉ်သည့် စာချုပ်များ ချုပ်ဆိုထားခြင်းမရှိသလို ချုပ်ဆိုရန် အလားအလာလည်း မရှိပါ။",
            "၅။ ကျွန်ုပ်သည် သတ်မှတ်ထားသော ကျွမ်းကျင်လုပ်သား အလုပ်ခန့်ထားမှုစာချုပ် လျှောက်လွှာကို ကြားခံဆောင်ရွက်ပေးခြင်း သို့မဟုတ် ကျွန်ုပ်၏နိုင်ငံရှိ အဖွဲ့အစည်းတစ်ခုသို့ လုပ်ငန်းဆောင်ရွက်မှုများအတွက် ကြိုတင်ပြင်ဆင်ခြင်းအတွက် အခကြေးငွေပေးချေခဲ့ပါက၊ ပမာဏနှင့် အသေးစိတ်အချက်အလက်များကို အပြည့်အဝနားလည်ပြီး ထိုအဖွဲ့အစည်းနှင့် သဘောတူညီမှု ရရှိထားရပါမည်။",
            "၆။ ကျွန်ုပ်အား ပံ့ပိုးကူညီရန် လိုအပ်သော ကုန်ကျစရိတ်များကို တိုက်ရိုက်ဖြစ်စေ၊ သွယ်ဝိုက်၍ဖြစ်စေ ကျွန်ုပ်က ကျခံမည်မဟုတ်ပါ။",
            "၇။ ကျွန်ုပ်အား လက်ခံသည့်အဖွဲ့အစည်းသည် ကျွန်ုပ် ဂျပန်နိုင်ငံသို့ ဆိုက်ရောက်မည့် ဆိပ်ကမ်း သို့မဟုတ် လေဆိပ်တွင် ကြိုပို့ဝန်ဆောင်မှုပေးရပါမည်။",
            "၈။ ကျွန်ုပ်အတွက် သင့်လျော်သော နေထိုင်စရာနေရာ ရရှိရေးအတွက် အထောက်အပံ့များ ပေးအပ်ပါမည်။",
            "၉။ ကျွန်ုပ်၏ အလုပ်အကိုင်၊ နေ့စဉ်ဘဝ သို့မဟုတ် လူမှုဘဝနှင့်ပတ်သက်၍ တိုင်ပင်ဆွေးနွေးမှုများ သို့မဟုတ် တိုင်ကြားမှုများကို လက်ခံရန် စနစ်တစ်ခု ရှိပါသည်။"
        ],
        "final_confirmation": "ထို့အပြင်၊ အချက် ၄ နှင့်ပတ်သက်၍ ကျွန်ုပ်နှင့် ကျွန်ုပ်၏အိမ်ထောင်ဖက်စသည်တို့သည် အာမခံငွေပေးချေခြင်း သို့မဟုတ် ဒဏ်ငွေများနှင့်သက်ဆိုင်သော စာချုပ်များကို လက်ရှိတွင် ချုပ်ဆိုထားခြင်းမရှိသလို အနာဂတ်တွင်လည်း ချုပ်ဆိုမည်မဟုတ်ပါ။",
        "signature_label": "သတ်မှတ်ထားသော ကျွမ်းကျင်လုပ်သား၏ လက်မှတ်",
        "agree_checkbox": "အထက်ပါ အကြောင်းအရာအားလုံးကို ကျွန်ုပ် အတည်ပြုပြီး သဘောတူပါသည်။",
        "submit_button": "လက်မှတ်ထိုးပြီး ဆက်လက်ဆောင်ရွက်ပါ"
    },
    "vi": {
        "title": "Giấy xác nhận Hướng dẫn Sơ bộ",
        "items": [
            "1. Các vấn đề liên quan đến nội dung công việc, mức lương và các điều kiện lao động khác.",
            "2. Nội dung các hoạt động tôi có thể thực hiện tại Nhật Bản.",
            "3. Các vấn đề liên quan đến thủ tục nhập cảnh vào Nhật Bản.",
            "4. Tôi hoặc vợ/chồng, họ hàng trực hệ hoặc sống cùng, hoặc những người có quan hệ xã hội mật thiết khác với tôi, sẽ không bị quản lý tiền bạc hoặc tài sản khác liên quan đến hoạt động của tôi tại Nhật Bản theo hợp đồng lao động kỹ năng đặc định, và không ký kết bất kỳ hợp đồng nào quy định tiền phạt vi phạm hợp đồng hoặc các hợp đồng dự kiến chuyển giao tài sản bất hợp pháp khác, và dự kiến sẽ không để bị buộc ký kết.",
            "5. Nếu tôi đã trả phí cho một tổ chức ở nước tôi để môi giới đơn xin hợp đồng lao động hoặc để chuẩn bị cho các hoạt động, tôi phải hiểu đầy đủ số tiền và chi tiết và đã đồng ý với tổ chức đó.",
            "6. Các chi phí cần thiết để hỗ trợ tôi sẽ không do tôi chịu, dù trực tiếp hay gián tiếp.",
            "7. Tổ chức tiếp nhận phải bố trí đưa đón tôi tại cảng hoặc sân bay nơi tôi dự định nhập cảnh vào Nhật Bản.",
            "8. Tôi sẽ được hỗ trợ để đảm bảo nhà ở phù hợp.",
            "9. Có một hệ thống để tiếp nhận các cuộc tham vấn hoặc khiếu nại từ tôi liên quan đến cuộc sống nghề nghiệp, sinh hoạt hàng ngày hoặc đời sống xã hội."
        ],
        "final_confirmation": "Ngoài ra, về điều 4, tôi và vợ/chồng của tôi, v.v., hiện không thanh toán tiền đặt cọc hoặc ký kết các hợp đồng liên quan đến tiền phạt, và sẽ không làm như vậy trong tương lai.",
        "signature_label": "Chữ ký của Người lao động Kỹ năng Đặc định",
        "agree_checkbox": "Tôi xác nhận và đồng ý với tất cả các nội dung trên.",
        "submit_button": "Gửi chữ ký và Tiếp tục"
    },
    "th": {
        "title": "เอกสารยืนยันการให้ข้อมูลเบื้องต้น",
        "items": [
            "1. เรื่องที่เกี่ยวกับเนื้อหาของงาน จำนวนค่าตอบแทน และเงื่อนไขการทำงานอื่นๆ",
            "2. เนื้อหาของกิจกรรมที่ฉันสามารถทำได้ในญี่ปุ่น",
            "3. เรื่องที่เกี่ยวกับขั้นตอนการเข้าประเทศของฉัน",
            "4. ข้าพเจ้า คู่สมรส ญาติสายตรงหรือญาติที่อาศัยอยู่ด้วยกัน หรือบุคคลอื่นที่มีความสัมพันธ์ใกล้ชิดทางสังคมกับข้าพเจ้า จะไม่ถูกจัดการเงินหรือทรัพย์สินอื่นใดที่เกี่ยวข้องกับกิจกรรมของข้าพเจ้าในญี่ปุ่นตามสัญญาจ้างงานทักษะเฉพาะ และไม่ได้ทำสัญญาที่กำหนดค่าปรับสำหรับการไม่ปฏิบัติตามสัญญาจ้างงานหรือสัญญาอื่นใดที่คาดว่าจะมีการโอนเงินหรือทรัพย์สินอื่นโดยมิชอบ และคาดว่าจะไม่ถูกบังคับให้ทำสัญญาดังกล่าว",
            "5. ในกรณีที่ฉันได้จ่ายค่าใช้จ่ายให้กับหน่วยงานในประเทศของตนเองเกี่ยวกับการเป็นนายหน้าในการสมัครสัญญาจ้างงานหรือการเตรียมความพร้อมสำหรับกิจกรรมทักษะเฉพาะประเภทที่ 1 ฉันจำเป็นต้องเข้าใจจำนวนเงินและรายละเอียดอย่างถ่องแท้และได้ตกลงกับหน่วยงานนั้นๆ",
            "6. ค่าใช้จ่ายที่จำเป็นสำหรับการสนับสนุนของฉัน จะไม่ถูกเรียกเก็บจากฉันไม่ว่าโดยตรงหรือโดยอ้อม",
            "7. องค์กรต้นสังกัดทักษะเฉพาะจะต้องจัดให้มีการรับส่งฉันที่ท่าเรือหรือสนามบินที่ฉันจะเดินทางเข้าประเทศ",
            "8. จะมีการให้ความช่วยเหลือแก่ฉันในการจัดหาที่อยู่อาศัยที่เหมาะสม",
            "9. มีระบบรองรับการให้คำปรึกษาหรือการร้องทุกข์จากฉันเกี่ยวกับชีวิตการทำงาน ชีวิตประจำวัน หรือชีวิตในสังคม"
        ],
        "final_confirmation": "นอกจากนี้ เกี่ยวกับข้อ 4 ข้าพเจ้าและคู่สมรสของข้าพเจ้า ฯลฯ ไม่ได้จ่ายเงินประกันหรือทำสัญญาเกี่ยวกับค่าปรับใดๆ ในปัจจุบัน และจะไม่ทำในอนาคต",
        "signature_label": "ลายมือชื่อของแรงงานทักษะเฉพาะ",
        "agree_checkbox": "ข้าพเจ้ายืนยันและยอมรับเนื้อหาทั้งหมดข้างต้น",
        "submit_button": "ส่งลายมือชื่อและดำเนินการต่อ"
    }
}
JAPANESE_TEXT = {
    "title": "事前ガイダンスの確認書",
    "items": [
        "１ 私が従事する業務の内容、報酬の額その他の労働条件に関する事項",
        "２ 私が日本において行うことができる活動の内容",
        "３ 私の入国に当たっての手続に関する事項",
        "４ 私又は私の配偶者、直系若しくは同居の親族その他私と社会生活において密接な関係を有する者が、特定技能雇用契約に基づく私の日本における活動に関連して、保証金の徴収その他名目のいかんを問わず、金銭その他の財産を管理されず、かつ特定技能雇用契約の不履行について違約金を定める契約その他の不当に金銭その他の財産の移転を予定する契約の締結をしておらず、かつ、締結させないことが見込まれること",
        "５ 私が特定技能雇用契約の申込みの取次ぎ又は自国等における特定技能１号の活動の準備に関して自国等の機関に費用を支払っている場合は、その額及び内訳を十分理解して、当該機関との間で合意している必要があること",
        "６ 私に対し、私の支援に要する費用について、直接又は間接に負担させないこととしていること",
        "７ 私に対し、特定技能所属機関等が私が入国しようとする港又は飛行場において送迎を行う必要があることとなっていること",
        "８ 私に対し、適切な住居の確保に係る支援がされること",
        "９ 私からの、職業生活、日常生活又は社会生活に関する相談又は苦情の申出を受ける体制があること"
    ],
    "final_confirmation": "また、４について、私及び私の配偶者等は、保証金の支払や違約金等に係る契約を現にしておらず、また、将来にわたりしません。",
}


# --- Routes ---
@app.route('/')
def language_select():
    provided_token = request.args.get('token')
    if provided_token != SECRET_TOKEN:
        return "アクセス権がありません。", 403
    return render_template('language_select.html', token=provided_token)

@app.route('/guidance', methods=['POST'])
def guidance_page():
    provided_token = request.form.get('token')
    lang = request.form.get('lang')
    if provided_token != SECRET_TOKEN:
        return "アクセス権がありません。", 403
    if not lang or lang not in TRANSLATIONS:
        return "言語が選択されていません。", 400
    return render_template('index.html', token=provided_token, lang=lang, translations=TRANSLATIONS[lang], japanese_text=JAPANESE_TEXT)

@app.route('/sign', methods=['POST'])
def sign():
    provided_token = request.form.get('token')
    lang = request.form.get('lang')
    if provided_token != SECRET_TOKEN:
        return "不正なアクセスです。", 403

    signature_data_url = request.form.get('signature_data')
    if signature_data_url:
        timestamp = datetime.datetime.now()
        filename = f"signature_{timestamp.strftime('%Y%m%d_%H%M%S')}.png"
        
        try:
            header, encoded = signature_data_url.split(",", 1)
            image_data = base64.b64decode(encoded)
            put(filename, image_data, options={'access': 'public'})
        except Exception as e:
            print(f"Error uploading signature to Blob: {e}")
            return "署名画像のアップロードに失敗しました。", 500
        
        return redirect(url_for('download_page', signature_file=filename, lang=lang))

    return redirect(url_for('language_select', token=provided_token))

@app.route('/download')
def download_page():
    signature_file = request.args.get('signature_file')
    lang = request.args.get('lang')
    if not signature_file or not lang:
        return "必要な情報が不足しています。", 400
    available_explainers = EXPLAINERS.get(lang, []) + EXPLAINERS.get('jp', [])
    return render_template('download.html', signature_file=signature_file, explainers=list(set(available_explainers)))

@app.route('/generate-pdf', methods=['POST'])
def generate_pdf():
    signature_file = request.form.get('signature_file')
    explainer_name = request.form.get('explainer_name')

    if not signature_file or not explainer_name:
        return "必要な情報が不足しています。", 400

    try:
        # get -> blob.get に修正
        blob_response = blob.get(signature_file)
        signature_image_data = blob_response.read()
        signature_image = Image.open(BytesIO(signature_image_data))
        temp_signature_path = f"/tmp/{signature_file}"
        signature_image.save(temp_signature_path)
    except Exception as e:
        print(f"Error downloading signature from Blob: {e}")
        return "署名画像の取得に失敗しました。", 404
        
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font('NotoSansJP', '', FONT_FILE) 

    # --- PDFレイアウト ---
    pdf.set_font('NotoSansJP', '', 10)
    pdf.set_xy(pdf.l_margin, 10)
    pdf.cell(0, 10, '参考様式第５－９号', align='L')
    pdf.set_xy(0, 25)
    pdf.set_font('NotoSansJP', '', 16)
    pdf.cell(0, 10, '事 前 ガ イ ダ ン ス の 確 認 書', new_x="LMARGIN", new_y="NEXT", align='C')
    pdf.ln(12)
    pdf.set_font('NotoSansJP', '', 10.5)
    list_items = [("１", "私が従事する業務の内容、報酬の額その他の労働条件に関する事項"),("２", "私が日本において行うことができる活動の内容"),("３", "私の入国に当たっての手続に関する事項"),("４", "私又は私の配偶者、直系若しくは同居の親族その他私と社会生活において密接な関係を有する者が、特定技能雇用契約に基づく私の日本における活動に関連して、保証金の徴収その他名目のいかんを問わず、金銭その他の財産を管理されず、かつ特定技能雇用契約の不履行について違約金を定める契約その他の不当に金銭その他の財産の移転を予定する契約の締結をしておらず、かつ、締結させないことが見込まれること"),("５", "私が特定技能雇用契約の申込みの取次ぎ又は自国等における特定技能１号の活動の準備に関して自国等の機関に費用を支払っている場合は、その額及び内訳を十分理解して、当該機関との間で合意している必要があること"),("６", "私に対し、私の支援に要する費用について、直接又は間接に負担させないこととしていること"),("７", "私に対し、特定技能所属機関等が私が入国しようとする港又は飛行場において送迎を行う必要があることとなっていること"),("８", "私に対し、適切な住居の確保に係る支援がされること"),("９", "私からの、職業生活、日常生活又は社会生活に関する相談又は苦情の申出を受ける体制があること")]
    initial_x = pdf.get_x()
    for number, text in list_items:
        pdf.set_x(initial_x)
        pdf.cell(8, 5, number, align='L') 
        pdf.multi_cell(pdf.w - pdf.l_margin - pdf.r_margin - 8, 5, text, new_x="LMARGIN", new_y="NEXT") 
        pdf.ln(1)
    pdf.set_font_size(11)
    pdf.ln(8) 
    pdf.multi_cell(0, 8, 'について、')
    pdf.ln(1) 
    today = datetime.date.today()
    date_time_str = f"{today.year}年{today.month}月{today.day}日  13時00分から16時00分まで"
    text_width = pdf.get_string_width(date_time_str)
    start_x = (pdf.w - text_width) / 2
    pdf.cell(0, 8, date_time_str, new_x="LMARGIN", new_y="NEXT", align='C')
    y_pos = pdf.get_y()
    pdf.line(start_x, y_pos - 1, start_x + text_width, y_pos - 1)
    pdf.ln(4)
    underline_length = 80
    indent = 70
    pdf.cell(0, 8, '特定技能所属機関（又は登録支援機関）の氏名又は名称', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)
    text_to_underline = 'アジア人材サポート協同組合'
    pdf.set_x(pdf.l_margin + indent) 
    pdf.cell(underline_length, 8, text_to_underline, new_x="LMARGIN", new_y="NEXT")
    y_pos = pdf.get_y()
    pdf.line(pdf.l_margin + indent, y_pos - 1, pdf.l_margin + indent + underline_length, y_pos - 1)
    pdf.ln(4)
    pdf.cell(0, 8, '説明者の氏名', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)
    text_to_underline = explainer_name
    pdf.set_x(pdf.l_margin + indent) 
    pdf.cell(underline_length, 8, text_to_underline, new_x="LMARGIN", new_y="NEXT")
    y_pos = pdf.get_y()
    pdf.line(pdf.l_margin + indent, y_pos - 1, pdf.l_margin + indent + underline_length, y_pos - 1)
    pdf.ln(4)
    pdf.multi_cell(0, 8, 'から説明を受け、内容を十分に理解しました。')
    pdf.ln(2)
    pdf.multi_cell(0, 8, 'また、４について、私及び私の配偶者等は、保証金の支払や違約金等に係る契約を現にしておらず、また、将来にわたりしません。')
    date_str = f"{today.year}年{today.month}月{today.day}日"
    sig_y_pos = pdf.h - 35
    pdf.set_y(sig_y_pos)
    pdf.cell(45, 8, '特定技能外国人の署名')
    line_start_x = pdf.get_x()
    line_end_x = line_start_x + 65
    pdf.line(line_start_x, sig_y_pos + 7, line_end_x, sig_y_pos + 7)
    pdf.image(temp_signature_path, x=line_start_x + 5, y=sig_y_pos - 10, w=55, h=15)
    pdf.set_xy(line_end_x + 5, sig_y_pos)
    pdf.cell(0, 8, date_str, align='R')
    
    pdf_output = bytes(pdf.output())
    
    try:
        pdf_filename = os.path.splitext(signature_file)[0] + '.pdf'
        put(pdf_filename, pdf_output, options={'access': 'public'})
        print(f"Successfully uploaded PDF to Blob: {pdf_filename}")
    except Exception as e:
        print(f"Error uploading completed PDF to Blob: {e}")
    
    os.remove(temp_signature_path)

    return Response(
        pdf_output,
        mimetype="application/pdf",
        headers={"Content-Disposition": "attachment;filename=confirmation_signed.pdf"}
    )