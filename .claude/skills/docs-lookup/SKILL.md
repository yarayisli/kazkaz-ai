---
name: docs-lookup
description: Bir kütüphanenin veya API'nin güncel dokümanına başvurmak için resmi kaynağı WebFetch ile çek. Ezber yerine kaynak. Kullan — kod yazarken/incelerken bir kütüphanenin fonksiyon, argüman, sürüm davranışı veya migration notu geçtiğinde; hata mesajı bir framework'e ait olduğunda; "X sürümünde bu var mı" sorusu geldiğinde.
allowed-tools: WebFetch, WebSearch
---

# Kütüphane dokümanı çekme refleksi

Model ağırlıkları donuk, kütüphaneler değil. Aşağıdaki durumlarda **önce dokümanı çek**, sonra kod yaz:

- Bir fonksiyonun imzası / parametre adı / dönüş tipi belirsiz.
- Bir sürümde davranışın değişip değişmediği bilinmiyor (deprecation, rename, breaking change).
- Kullanıcı "X kütüphanesiyle Y nasıl yapılır" diye soruyor.
- Bir hata mesajı bir framework'ün adını içeriyor (Streamlit runtime error, Firebase auth code, Prophet fitting warning, vb.).
- Yeni bir bağımlılık öneriyorsun — önce güncel API'ye bak.

## Bu projede sık geçen kütüphaneler ve resmi kaynak

| Kütüphane | Doküman kökü |
|---|---|
| Streamlit | https://docs.streamlit.io/ |
| Firebase Auth REST | https://firebase.google.com/docs/reference/rest/auth |
| Firestore (Python admin) | https://firebase.google.com/docs/firestore/quickstart |
| Groq Python SDK | https://console.groq.com/docs/api-reference |
| google-generativeai | https://ai.google.dev/gemini-api/docs |
| Prophet | https://facebook.github.io/prophet/docs/quick_start.html |
| statsmodels ExpSmoothing | https://www.statsmodels.org/stable/generated/statsmodels.tsa.holtwinters.ExponentialSmoothing.html |
| Plotly Python | https://plotly.com/python/ |
| ReportLab | https://docs.reportlab.com/ |
| Pandas | https://pandas.pydata.org/docs/reference/index.html |

## İş akışı

1. Kütüphane adını **ezberden değil**, `requirements-2.txt`'den doğrula (sürüm önemli).
2. Yukarıdaki tablodan kökü al, konu segmentini ekle (ör. Streamlit için `/library/api-reference/widgets/st.file_uploader`).
3. `WebFetch(url, "X hakkında güncel API; parametreler, dönüş, minimum sürüm")` çağır.
4. Kök URL'yi bilmiyorsan `WebSearch("kütüphaneadı X resmi doc site:...")` ile önce resmi domain'i bul, sonra `WebFetch`.
5. Cevabı yazarken **sürümü de belirt** ("Streamlit ≥1.32'de `st.dialog` mevcut").
6. Blog/StackOverflow'a düşme; sadece resmi doküman ve resmi repo README'si sayılır.

## Kaçınılacak refleksler

- "Muhtemelen şöyle bir parametresi vardır" diye tahmin yürütmek.
- Eski cevabı hafızadan yeniden söylemek — kütüphane 6 aydır güncellenmiş olabilir.
- Kütüphaneyi hiç doğrulamadan `pip install` önermek — önce güncel sürüme ve alternatiflere bak.
