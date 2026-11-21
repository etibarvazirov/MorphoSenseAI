import os
import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image,ImageOps
from engine import CONDITIONS,METHODS,P2,P3,get_landmarker,run_analysis

st.set_page_config(page_title='MorphoSense AI | Palm Crease Lab',page_icon='🖐️',layout='wide',initial_sidebar_state='expanded')

CSS='''
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&display=swap');
html,body,[class*="css"],.stApp {font-family:'DM Sans',sans-serif;}
.stApp {background:linear-gradient(140deg,#071521 0%,#0c1d2b 48%,#0b1622 100%);color:#edf7fb;}
section[data-testid="stSidebar"] {
    background: #EAF3F8 !important;
    border-right: 1px solid #B8CDD9 !important;
}

/* Ensure readable typography in the dark sidebar across Streamlit themes. */
/* LIGHT SIDEBAR WITH DARK, READABLE TEXT */
section[data-testid="stSidebar"] *,
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] strong,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] small {
    color: #172B4D !important;
    opacity: 1 !important;
}

section[data-testid="stSidebar"] hr {
    border-color: #B8CDD9 !important;
}

section[data-testid="stSidebar"] [data-baseweb="select"] > div {
    background-color: #FFFFFF !important;
    border-color: #B8CDD9 !important;
}

.block-container {padding-top:1.7rem;max-width:1330px;}
.hero {padding:35px 38px;border:1px solid #245365;border-radius:25px;background:radial-gradient(circle at 88% 20%,#1c5660 0%,transparent 32%),linear-gradient(110deg,#113447,#0d2433);box-shadow:0 16px 55px #03121b55;margin-bottom:20px;}
.eyebrow {font-size:12px;font-weight:800;letter-spacing:2.2px;color:#62e2d2;text-transform:uppercase;}
.hero h1 {font-size:clamp(30px,4vw,54px);line-height:1.1;margin:14px 0 12px;color:#f5fcff;font-weight:800;}
.hero p {font-size:17px;color:#c5dce5;max-width:820px;line-height:1.6;}
.chips {display:flex;flex-wrap:wrap;gap:9px;margin-top:20px;}
.chip {font-size:12px;color:#b9f5ee;background:#164b51;border:1px solid #33777a;padding:8px 12px;border-radius:50px;}
.section-kicker {font-size:12px;letter-spacing:1.8px;text-transform:uppercase;color:#69d9c9;font-weight:800;margin-top:18px;}
.test-card {border:1px solid #2c4755;border-radius:18px;padding:19px 18px;background:linear-gradient(150deg,#142c3b,#0e2332);min-height:166px;margin-bottom:8px;}
.test-num {display:inline-block;color:#70e5d2;font-weight:800;font-size:13px;margin-bottom:11px;}
.test-title {font-weight:800;font-size:17px;color:#f3fbff;margin-bottom:8px;}
.test-desc {font-size:13px;color:#b9cfda;line-height:1.5;}
.small-note {border-left:3px solid #63dac7;background:#12313c;border-radius:8px;padding:14px 18px;color:#c7e2e8;font-size:14px;line-height:1.6;}
.stButton>button[kind="primary"] {background:linear-gradient(90deg,#16b6a6,#1785a4);color:white;border:none;border-radius:13px;font-weight:800;padding:12px 23px;box-shadow:0 8px 25px #13b6a533;}
[data-testid="stMetric"] {border:1px solid #2d4a59;background:#102c3b;border-radius:15px;padding:14px;}
[data-testid="stMetricLabel"], [data-testid="stMetricLabel"] * {color:#c9e1ea !important;opacity:1 !important;}
[data-testid="stMetricValue"], [data-testid="stMetricValue"] * {color:#ffffff !important;opacity:1 !important;font-weight:800 !important;}
[data-testid="stMetricDelta"], [data-testid="stMetricDelta"] * {opacity:1 !important;}
[data-testid="stFileUploader"] {border:1px dashed #448b90;border-radius:16px;padding:10px;background:#102a39;}
hr {border-color:#2b4757!important;}
</style>
'''
st.markdown(CSS,unsafe_allow_html=True)

I18N={
'AZ':{
 'subtitle':'Ovuc xətlərinin izahlı kompüter görməsi analizi','tagline':'Bir şəkil. İki metod. Beş dayanıqlıq sınağı. Aydın elmi izah.','badge1':'Black-hat + Frangi','badge2':'5 görüntü dəyişikliyi','badge3':'Şəffaf nəticələr','badge4':'Klinik diaqnoz deyil',
 'lang':'İnterfeys dili','navigation':'Bölmələr','tab1':'Analiz laboratoriyası','tab2':'Nəticələrin izahı','tab3':'Tədqiqat sübutları','tab4':'Layihə haqqında',
 'pretitle':'ANALİZDƏN ƏVVƏL','preheading':'Hansı dayanıqlıq testləri aparılacaq?','preintro':'Eyni ovuc şəklinə aşağıdakı beş süni dəyişiklik tətbiq olunur. Hər iki metodun dəyişdirilmiş maskası orijinal maskası ilə müqayisə edilir.',
 'tests':[('🌙','Zəif işıq','Şəkil qaraldılır. Zəif işıqlandırmada aşkarlanan xətlərin nə qədər qorunduğu yoxlanılır.'),('☀️','Güclü işıq','Parlaqlıq artırılır. İşıq çox olduqda xətlərin sabitliyi ölçülür.'),('◐','Aşağı kontrast','Xətlərlə dəri arasındakı vizual fərq azaldılır.'),('✳','Gaussian səs-küyü','Kamera səs-küyünü təqlid edən təsadüfi piksel dəyişiklikləri əlavə olunur.'),('◌','Gaussian bulanıqlığı','Fokus itkisini təqlid etmək üçün görüntü bulanıqlaşdırılır.')],
 'upload':'Ovuc şəklini yüklə','uploadhelp':'JPG, PNG və ya WEBP. Ovuc açıq, ön tərəfdən görünən və yaxşı işıqlandırılmış olsun.','start':'▶ Bütün 5 testi işə sal','loading':'Ovuc ROI-si və 10 maska müqayisəsi hesablanır...','privacy':'Şəkil yalnız cari analiz üçün işlənir. Hesabatı endirsəniz, şəkil də ZIP-ə daxil olacaq. Şəxsi şəkilləri yalnız razılıqla yükləyin.',
 'resulttitle':'Canlı analiz nəticələri','roi':'Aşkarlanmış ovuc sahəsi (ROI)','bh':'Black-hat: ilkin maska','fr':'Frangi: ilkin maska','baseline':'İlkin maska ölçmələri','robust':'Beş test üzrə IoU müqayisəsi','download':'⬇ Tam ZIP hesabatını endir','diagnostic':'Səs-küy testi üzrə diaqnostika','empty':'Dəyişdirilmiş maska boşdur — bu, həmin testdə aşkarlamanın dayanması deməkdir. Səbəbi ayrıca yoxlamaq lazımdır.','comparison':'Vizual müqayisə','selecttest':'Test seç','selectmethod':'Metod seç','panels':'Yuxarı: orijinal / dəyişdirilmiş şəkil. Aşağı: orijinal / dəyişdirilmiş maska (qırmızı).','metrics':'Metriklər nə deməkdir?','science':'Elmi məhdudiyyət','sciencebody':'IoU və Dice orijinal və dəyişdirilmiş maskaların uyğunluğunu ölçür, ekspert tərəfindən təsdiqlənmiş qırışların aşkarlanma dəqiqliyini yox. ROI təxminidir. Klinik diaqnoz və tibbi etibarlılıq təsdiqlənməyib.',
 'historical':'Əvvəlki eksperimentlər','p2':'P2 — bir görüntü üzrə tarixi sabitlik testləri','p3':'P3 — 17 müxtəlif iştirakçı üzrə təsviri maska ölçmələri','historynote':'P2, P3 və canlı v3 fərqli protokollardan istifadə edib. Onların nəticələrini birləşdirib eyni eksperiment kimi təqdim etmək olmaz.',
 'about':'Layihənin məqsədi','aboutbody':'MorphoSense AI ovuc xətlərinin mümkün namizədlərini çıxaran və görüntü keyfiyyətinin bu nəticələrə təsirini göstərən təhsil və tədqiqat prototipidir. Gələcəkdə ekspert annotasiyaları, daha çox görüntü və müstəqil validasiya ilə inkişaf etdirilə bilər.','refs':'Elmi mənbələr','need':'Analizə başlamaq üçün əvvəlcə ovuc şəkli yüklə.','wins':'Black-hat üstün olduğu testlər','meanbh':'Black-hat orta IoU','meanfr':'Frangi orta IoU','lowest':'Ən böyük dəyişiklik','winner':'Bu görüntüdə Black-hat {n}/5 testdə daha yüksək uyğunluq göstərdi. Bu, klinik dəqiqlik sübutu deyil.'},
'EN':{
 'subtitle':'Explainable computer vision for palmar crease analysis','tagline':'One image. Two methods. Five robustness tests. Clear scientific explanations.','badge1':'Black-hat + Frangi','badge2':'5 image perturbations','badge3':'Transparent results','badge4':'Not a clinical diagnosis',
 'lang':'Interface language','navigation':'Sections','tab1':'Analysis lab','tab2':'Understand results','tab3':'Research evidence','tab4':'About',
 'pretitle':'BEFORE YOU RUN','preheading':'Which robustness tests will be performed?','preintro':'Five controlled changes are applied to the same palm image. Each method’s perturbed mask is compared with its own original mask.',
 'tests':[('🌙','Low light','Darkens the image to test consistency under reduced illumination.'),('☀️','High light','Increases brightness to test sensitivity to strong lighting.'),('◐','Low contrast','Reduces the visual difference between creases and surrounding skin.'),('✳','Gaussian noise','Adds random pixel noise resembling camera sensor interference.'),('◌','Gaussian blur','Blurs the image to simulate loss of focus.')],
 'upload':'Upload a palm image','uploadhelp':'JPG, PNG or WEBP. Use a clear, front-facing, well-lit palm image.','start':'▶ Run all 5 tests','loading':'Detecting palm ROI and computing 10 mask comparisons...','privacy':'The image is processed for the current analysis. Downloaded ZIP reports include the image. Upload personal images only with permission.',
 'resulttitle':'Live analysis results','roi':'Detected palm ROI','bh':'Black-hat baseline mask','fr':'Frangi baseline mask','baseline':'Baseline mask measurements','robust':'IoU across five perturbations','download':'⬇ Download full ZIP report','diagnostic':'Noise-test diagnostics','empty':'The perturbed mask is empty: detection collapsed in this test. Its technical cause requires investigation.','comparison':'Visual comparison','selecttest':'Select a test','selectmethod':'Select a method','panels':'Top: original / perturbed image. Bottom: baseline / perturbed mask (red).','metrics':'What do the metrics mean?','science':'Scientific limitations','sciencebody':'IoU and Dice measure overlap between original and perturbed masks, not accuracy against expert-labelled true creases. The ROI is approximate. No clinical or diagnostic validation is established.',
 'historical':'Previous experiments','p2':'P2 — historical single-image robustness tests','p3':'P3 — descriptive mask measurements from 17 participants','historynote':'P2, P3 and live v3 use different protocols. Do not pool their numbers as if they were one experiment.',
 'about':'Project purpose','aboutbody':'MorphoSense AI is an educational and research prototype for extracting candidate palm crease structures and showing how image quality affects reproducibility. Future work includes expert annotations, larger datasets and independent validation.','refs':'Scientific references','need':'Upload a palm image to begin.','wins':'Tests led by Black-hat','meanbh':'Black-hat mean IoU','meanfr':'Frangi mean IoU','lowest':'Most disruptive change','winner':'Black-hat had higher consistency in {n}/5 conditions on this image. This is not evidence of clinical accuracy.'},
'RU':{
 'subtitle':'Объяснимый компьютерный анализ ладонных складок','tagline':'Одно изображение. Два метода. Пять тестов устойчивости. Понятные объяснения.','badge1':'Black-hat + Frangi','badge2':'5 изменений изображения','badge3':'Прозрачные результаты','badge4':'Не медицинский диагноз',
 'lang':'Язык интерфейса','navigation':'Разделы','tab1':'Лаборатория анализа','tab2':'Объяснение результатов','tab3':'Научные данные','tab4':'О проекте',
 'pretitle':'ПЕРЕД АНАЛИЗОМ','preheading':'Какие тесты устойчивости будут выполнены?','preintro':'К одному изображению ладони применяются пять контролируемых изменений. Полученные маски сравниваются с исходными масками каждого метода.',
 'tests':[('🌙','Слабое освещение','Изображение затемняется для проверки устойчивости к недостатку света.'),('☀️','Яркое освещение','Яркость увеличивается для оценки влияния сильного света.'),('◐','Низкий контраст','Уменьшается визуальная разница между складками и кожей.'),('✳','Гауссов шум','Добавляются случайные изменения пикселей, имитирующие шум камеры.'),('◌','Гауссово размытие','Имитируется потеря резкости и фокуса.')],
 'upload':'Загрузите изображение ладони','uploadhelp':'JPG, PNG или WEBP. Ладонь должна быть четкой, открытой и снятой спереди.','start':'▶ Запустить все 5 тестов','loading':'Определение области ладони и расчет 10 сравнений масок...','privacy':'Изображение используется для текущего анализа. Скачиваемый ZIP содержит изображение. Загружайте личные фотографии только с разрешения.',
 'resulttitle':'Результаты анализа','roi':'Область ладони (ROI)','bh':'Исходная маска Black-hat','fr':'Исходная маска Frangi','baseline':'Измерения исходных масок','robust':'Сравнение IoU по пяти тестам','download':'⬇ Скачать полный ZIP-отчет','diagnostic':'Диагностика теста шума','empty':'Маска после изменения пуста: в этом тесте обнаружение прекратилось. Техническую причину необходимо проверить.','comparison':'Визуальное сравнение','selecttest':'Выберите тест','selectmethod':'Выберите метод','panels':'Сверху: исходное / измененное изображение. Снизу: исходная / измененная маска (красным).','metrics':'Что означают метрики?','science':'Научные ограничения','sciencebody':'IoU и Dice измеряют совпадение исходных и измененных масок, а не точность по экспертной разметке. ROI приблизительна. Клиническая и диагностическая валидация отсутствует.',
 'historical':'Предыдущие эксперименты','p2':'P2 — исторические тесты устойчивости на одном изображении','p3':'P3 — описательные метрики масок для 17 участников','historynote':'P2, P3 и текущий v3 используют разные протоколы. Их результаты нельзя объединять как один эксперимент.',
 'about':'Цель проекта','aboutbody':'MorphoSense AI — образовательный и исследовательский прототип для выделения предполагаемых складок ладони и оценки влияния качества изображения на воспроизводимость. Дальнейшая работа: экспертная разметка, расширение данных и независимая проверка.','refs':'Научные источники','need':'Для начала загрузите изображение ладони.','wins':'Тесты с преимуществом Black-hat','meanbh':'Средний IoU Black-hat','meanfr':'Средний IoU Frangi','lowest':'Наиболее сильное изменение','winner':'Black-hat показал более высокую устойчивость в {n}/5 тестах для этого изображения. Это не доказывает клиническую точность.'}}

METRIC_EXPLANATIONS={
'AZ':{'Coverage (%)':'ROI daxilində qırış namizədi kimi işarələnmiş piksellərin faizi. Çox olması daha dəqiq olması demək deyil.','Components':'Maskadakı ayrı-ayrı əlaqəli bölgələrin sayı; fraqmentasiyanı təsvir edir.','Mean area (px)':'Bir əlaqəli bölgənin orta piksel sahəsi; təsvir ölçüsündən asılıdır.','IoU':'İlkin və dəyişdirilmiş maskaların kəsişməsinin birləşməsinə nisbəti; 0–1 arası sabitlik göstəricisi.','Dice':'Maska üst-üstə düşməsinin alternativ göstəricisi; IoU-dan müstəqil dəqiqlik sübutu deyil.'},
'EN':{'Coverage (%)':'Percentage of ROI pixels marked as candidate creases; higher does not mean more accurate.','Components':'Number of disconnected mask regions; describes fragmentation.','Mean area (px)':'Average area of a connected region in pixels; depends on resolution.','IoU':'Intersection divided by union of original and perturbed masks; a consistency score from 0 to 1.','Dice':'An alternative overlap score, not an independent accuracy validation.'},
'RU':{'Coverage (%)':'Доля пикселей ROI, отмеченных как предполагаемые складки; больше не значит точнее.','Components':'Число отдельных связанных областей маски; характеризует фрагментацию.','Mean area (px)':'Средняя площадь связанной области в пикселях; зависит от разрешения.','IoU':'Отношение пересечения к объединению исходной и измененной масок; устойчивость от 0 до 1.','Dice':'Альтернативная мера совпадения масок, не независимое доказательство точности.'}}

with st.sidebar:
    st.markdown('## 🖐️ MorphoSense AI')
    lang=st.selectbox('🌐 Language / Dil / Язык',['AZ','EN','RU'],format_func=lambda x:{'AZ':'🇦🇿 Azərbaycan','EN':'🇬🇧 English','RU':'🇷🇺 Русский'}[x])
    t=I18N[lang]
    st.divider()
    st.caption('RESEARCH PROTOTYPE · v1.0')
    st.markdown('**Black-hat**  ·  **Frangi**')
    st.caption('ROI: MediaPipe HandLandmarker')
    st.info(t['sciencebody'],icon='ℹ️')

st.markdown(f'''<div class="hero"><div class="eyebrow">✦ MORPHOSENSE AI · PALM CREASE LAB</div><h1>{t['subtitle']}</h1><p>{t['tagline']}</p><div class="chips"><span class="chip">{t['badge1']}</span><span class="chip">{t['badge2']}</span><span class="chip">{t['badge3']}</span><span class="chip">{t['badge4']}</span></div></div>''',unsafe_allow_html=True)

tabs=st.tabs([t['tab1'],t['tab2'],t['tab3'],t['tab4']])
with tabs[0]:
    st.markdown(f'<div class="section-kicker">{t["pretitle"]}</div>',unsafe_allow_html=True)
    st.subheader(t['preheading'])
    st.write(t['preintro'])
    cols=st.columns(3)
    for i,(emoji,title,desc) in enumerate(t['tests']):
        with cols[i%3]:
            st.markdown(f'<div class="test-card"><div class="test-num">{emoji} &nbsp; TEST {i+1:02}</div><div class="test-title">{title}</div><div class="test-desc">{desc}</div></div>',unsafe_allow_html=True)
    st.markdown('<div class="small-note">'+t['sciencebody']+'</div>',unsafe_allow_html=True)
    st.write('')
    upload=st.file_uploader(t['upload'],type=['png','jpg','jpeg','webp'],help=t['uploadhelp'])
    st.caption(t['privacy'])
    if upload:
        try:
            image=ImageOps.exif_transpose(Image.open(upload)).convert('RGB')
            st.image(image,caption=t['upload'],width=350)
        except Exception:
            st.error('Unsupported or damaged image / Şəkil oxunmur / Ошибка изображения')
            image=None
    else:image=None
    if st.button(t['start'],type='primary',use_container_width=True,disabled=image is None):
        try:
            with st.spinner(t['loading']):
                @st.cache_resource(show_spinner=False)
                def load_model():
                    return get_landmarker(os.path.join(os.path.dirname(__file__),'models','hand_landmarker.task'))
                st.session_state['result']=run_analysis(image,load_model())
        except Exception as exc:
            st.error(f'Analysis error / Analiz xətası: {exc}')
    if 'result' in st.session_state:
        r=st.session_state['result'];df=r['df'];base=r['baseline']
        st.divider();st.subheader(t['resulttitle'])
        cols=st.columns(3)
        for col,title,key in zip(cols,[t['roi'],t['bh'],t['fr']],['roi','Black-hat','Frangi']):
            with col:st.image(r['roi'] if key=='roi' else r['base'][key],caption=title,use_container_width=True)
        pivot=df.pivot(index='Perturbation',columns='Method',values='IoU').reindex(CONDITIONS)
        wins=int((pivot['Black-hat']>pivot['Frangi']).sum())
        a,b,c=st.columns(3)
        a.metric(t['wins'],f'{wins}/5');b.metric(t['meanbh'],f'{pivot["Black-hat"].mean():.4f}');c.metric(t['meanfr'],f'{pivot["Frangi"].mean():.4f}')
        st.markdown(t['winner'].format(n=wins))
        st.subheader(t['robust'])
        plot=df.copy()
        plot['Perturbation']=pd.Categorical(plot['Perturbation'],categories=CONDITIONS,ordered=True)
        fig=px.bar(plot.sort_values('Perturbation'),x='Perturbation',y='IoU',color='Method',barmode='group',color_discrete_map={'Black-hat':'#43d5c0','Frangi':'#f7b56b'},range_y=[0,1],template='plotly_dark',hover_data=['Dice','Changed pixels'])
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',font_color='#d9edf1',legend_title_text='',margin=dict(l=5,r=5,t=15,b=5))
        st.plotly_chart(fig,use_container_width=True)
        st.dataframe(df,use_container_width=True,hide_index=True)
        st.subheader(t['baseline']);st.dataframe(base,use_container_width=True,hide_index=True)
        st.subheader(t['diagnostic'])
        noise=df[df['Perturbation']=='Gaussian noise']
        st.dataframe(noise[['Method','Baseline pixels','Changed pixels','Intersection pixels','IoU']],use_container_width=True,hide_index=True)
        if (noise['Changed pixels']==0).any():st.warning(t['empty'])

        diag_title={'az':'Gaussian noise: mərhələli diaqnostika və sınaq','en':'Gaussian noise: step-by-step diagnostics and trial','ru':'Гауссов шум: диагностика и пробный вариант'}[lang]
        with st.expander(diag_title,expanded=True):
            st.caption({'az':'Əsas IoU/Dice nəticələri dəyişdirilməyib. Median filter yalnız alternativ sınaqdır.','en':'The original IoU/Dice values are unchanged. Median filtering is an experimental alternative only.','ru':'Исходные IoU/Dice не изменены. Медианный фильтр — только экспериментальный вариант.'}[lang])
            diag=r['diagnostic_df']
            st.dataframe(diag,use_container_width=True,hide_index=True)
            for _,row in diag.iterrows():
                method_name=row['Method']
                if row['Before cleanup pixels']>0 and row['After cleanup pixels']==0:
                    msg={'az':f"{method_name}: threshold mərhələsindən sonra piksel var, lakin kiçik obyektlərin təmizlənməsi zamanı hamısı silinir.", 'en':f"{method_name}: pixels survive thresholding, but all are removed during small-object cleanup.", 'ru':f"{method_name}: пиксели проходят порог, но все удаляются при очистке мелких объектов."}[lang]
                    st.warning(msg)
                elif row['Before cleanup pixels']==0:
                    st.warning({'az':f'{method_name}: threshold mərhələsində maska boşalır.','en':f'{method_name}: mask becomes empty at thresholding.','ru':f'{method_name}: маска становится пустой при пороговой обработке.'}[lang])
            trial_method=st.selectbox({'az':'Sınaq vizualı','en':'Trial visualization','ru':'Пробная визуализация'}[lang],METHODS,key='noise_trial_method')
            st.image(r['diagnostic_panels'][trial_method],use_container_width=True)
            st.caption({'az':'Sol: orijinal. Sağ: noise + 3×3 median filter. Aşağıda maskalar. Sınaq IoU yüksək olsa belə, başqa şəkillərdə yoxlanmadan standart metodu dəyişmirik.','en':'Left: original. Right: noise + 3×3 median filter. Masks below. Do not replace the standard pipeline based on one image.','ru':'Слева оригинал, справа шум + медианный фильтр 3×3. Ниже маски. Не заменяйте основной метод по одному изображению.'}[lang])

        st.subheader(t['comparison'])
        cc1,cc2=st.columns(2)
        with cc1:condition=st.selectbox(t['selecttest'],CONDITIONS,format_func=lambda x:t['tests'][CONDITIONS.index(x)][1])
        with cc2:method=st.selectbox(t['selectmethod'],METHODS)
        st.image(r['panels'][(condition,method)],caption=t['panels'],use_container_width=True)
        st.download_button(t['download'],r['zip'],file_name='MorphoSense_Streamlit_Report.zip',mime='application/zip',type='primary',use_container_width=True)
    else:st.caption(t['need'])
with tabs[1]:
    st.subheader(t['metrics'])
    for name,desc in METRIC_EXPLANATIONS[lang].items():
        with st.expander(name,expanded=name=='IoU'):st.write(desc)
    st.divider();st.subheader(t['science']);st.info(t['sciencebody'])
with tabs[2]:
    st.subheader(t['historical'])
    st.markdown('**'+t['p2']+'**');st.dataframe(P2,use_container_width=True,hide_index=True)
    st.markdown('**'+t['p3']+'**');st.dataframe(P3,use_container_width=True,hide_index=True)
    st.warning(t['historynote'])
with tabs[3]:
    st.subheader(t['about']);st.write(t['aboutbody'])
    st.subheader(t['refs'])
    st.markdown('''- [Biesecker et al. (2009), *Elements of Morphology: Standard Terminology for the Hands and Feet*](https://doi.org/10.1002/ajmg.a.32596) — anatomical terminology.
- [NIH MedlinePlus — Single palmar crease](https://medlineplus.gov/ency/article/003290.htm) — clinical background, not software validation.
- [Frangi et al. (1998), *Multiscale Vessel Enhancement Filtering*](https://doi.org/10.1007/BFb0056195) — methodological origin of ridge filtering.
- [Taha & Hanbury (2015), segmentation evaluation metrics](https://doi.org/10.1186/s12880-015-0068-x) — methodological context for overlap measures.

**Evidence levels:** Published references ≠ historical P2/P3 ≠ live single-image analysis. No expert ground-truth segmentation or clinical validation is included.''')
