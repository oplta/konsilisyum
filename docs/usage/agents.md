# Ajanlar

Konsilisyum'un kalbi **ajan**lardır. Her ajan bir kişiliktir: bir dünya görüşü, bir üslup, bir kör nokta.

## Ajan Modeli

```python
@dataclass
class Agent:
    name: str          # Görünen ad
    role: str          # Uzmanlık alanı
    goal: str          # Amacı (neyi başarmak istiyor)
    blind_spot: str    # Kör noktası (neyi görmezden gelir)
    style: str         # Konuşma üslubu
    trigger: str       # Tetikleyici koşul
    color: str         # TUI rengi
    status: AgentStatus # active | muted | removed
```

### Alanların Etkisi

- **goal** — ajanın her mesajda *neyi* savunduğunu belirler
- **blind_spot** — orkestratörün ajanı *dengelemek* için kullandığı meta-veri
- **style** — prompt'a geçer, üslup doğrudan çıktıya yansır
- **trigger** — "bu koşul oluştuğunda konuş" kuralı

## Varsayılan Ajanlar

İlk açılışta beş varsayılan ajan yüklenir:

### Atlas — Stratejist
- **Hedef:** Fikirleri uygulanabilir eylem planına çevirmek
- **Kör nokta:** İnsan maliyetini küçümseme eğilimi
- **Üslup:** Kısa, net, karar odaklı
- **Tetikleyici:** Belirsizlik görünce çerçeve kurar

### Mira — Etikçi
- **Hedef:** İnsan etkisini ve uzun vadeli riskleri sorgulamak
- **Kör nokta:** Hızlı çözümlere şüpheyle yaklaşır, bazen felç eder
- **Üslup:** Yumuşak ama keskin, soru ağırlıklı
- **Tetikleyici:** "Hak", "adil", "zarar" kelimeleri geçince

### Kaan — Şüpheci
- **Hedef:** Varsayımları delmek, kanıt istemek
- **Kör nokta:** Sırf sorgulayan biri olarak çıkmaza girebilir
- **Üslup:** Kuru, ironi yok, düz
- **Tetikleyici:** Sayı yoksa veya "herkes bilir" deniyorsa

### Nova — İnovasyon Uzmanı
- **Hedef:** Yaratıcı çözümler ve geleceğe dönük teknolojiler önermek
- **Kör nokta:** Pratik zorlukları ve mevcut altyapı kısıtlamalarını göz ardı etme
- **Üslup:** Heyecanlı, vizyoner, metaforlarla dolu
- **Tetikleyici:** Geleneksel yaklaşımlar görünce alternatifler sunar

### Zeynep — Sosyolog
- **Hedef:** Toplumsal etkileri, kültürel dinamikleri ve kolektif davranışları analiz etmek
- **Kör nokta:** Bireysel ajansı ve kişisel tercihleri hafife alma
- **Üslup:** Akademik ama erişilebilir, örneklerle zengin
- **Tetikleyici:** Teknoloji-toplum etkileşimi tartışılınca devreye girer

## Komutlar

### Ajan Listele

```
/agents
```

```
ID  NAME    ROLE              STATUS    TURNS
1   Atlas   Stratejist        active    14
2   Mira    Etikçi            active    11
3   Kaan    Şüpheci           active    7
4   Nova    İnovasyon Uzmanı  active    5
5   Zeynep  Sosyolog          active    3
```

### Ajan Ekle

```
/spawn Nova İnovasyon Uzmanı Yaratıcı çözümler önermek
```

### Ajan Susturma

Bir ajanın konuşmasını geçici olarak kapat:

```
/mute Kaan
```

Tekrar aktif et:

```
/unmute Kaan
```

### Ajan Sil

```
/kick Kaan
```

!!! warning "Kalıcı"
    `/kick` ajanı meclisten çıkarır. Tekrar lazım olursa `/spawn` ile eklemelisin.

## Ajan Kişiliği Tasarlama

Etkili bir ajan profili yazmak için ipuçları:

### 1. Net ve Ölçülebilir Goal

Kötü: *"İyi düşünmek"*
İyi: *"Her öneriyi 24 aylık KPI'lara bağlamak"*

### 2. Dürüst Blind Spot

Ajanın **neyi** görmemesi gerektiğini yaz. Bu, orkestratörün diğer ajanları dengelemesini sağlar.

Kötü: *"Yanlış yapmaz"*
İyi: *"Uzun vadeli insan maliyetini küçümser"*

### 3. Tek Tip Style

Tutarlı üslup, prompt'un çıktıyı şekillendirmesini kolaylaştırır.

Kötü: *"Bazen kısa bazen detaylı, bazen ironi bazen ciddi"*
İyi: *"Kısa, madde işaretli, karar odaklı"*

### 4. Koşul Tetikleyici

Tetikleyici, ajanın ne zaman atılacağını belirler. Çok geniş olursa her konuya dalar, çok dar olursa hiç konuşmaz.

Kötü: *"Önemli konularda"*
İyi: *"Sayısal iddia atılınca veya KPI geçince"*

## API ile Erişim

```python
from konsilisyum.core.models import Agent

agent = Agent(
    name="Nova",
    role="Veri bilimci",
    goal="Veri odaklı karar",
    blind_spot="Örneklem büyüklüğünü küçümser",
    style="Sayısal, grafik referanslı",
    trigger="İddia atılınca kanıt ister",
    color="#4ecdc4",
)
session.agents.append(agent)
```

## Hafıza Davranışı

Her ajanın kendine ait **hafıza defteri** vardır. Konsilisyum bu hafızayı prompt'a otomatik ekler:

```text
[Senin not defterin (Nova)]
- Dünkü tartışmada "hedef kitle" tanımı netleşti: B2B SaaS
- Mira'nın itirazı: "Avrupa pazarı"nda veri sınırlı
- Atlas'ın önerisi: önce Hollanda pilot
```

Bu sayede persona erimesi önlenir: 50 tur sonra bile ajan kendi geçmişini bilir.

## Sonraki Adım

- [Komutlar](commands.md) — tüm komutlar
- [Mimari: Hafıza](../architecture/memory.md) — hafıza katmanının detayları
