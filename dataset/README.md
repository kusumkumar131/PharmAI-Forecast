# Pharmaceutical Sales Dataset & Catalog Documentation

## 1. Dataset Origin & Attribution
- **Dataset Title**: Pharma Sales Data
- **Authors**: Milan Zdravkovic / M. Callara
- **Kaggle Source**: [https://www.kaggle.com/datasets/milanzdravkovic/pharma-sales-data](https://www.kaggle.com/datasets/milanzdravkovic/pharma-sales-data)
- **GitHub Repository**: [https://github.com/mcallara/pharma-sales-data](https://github.com/mcallara/pharma-sales-data)
- **Timeframe**: January 2, 2014 to October 8, 2019 (2,106 continuous daily records)

## 2. Anatomical Therapeutic Chemical (ATC) Classification
The real-world sales records are classified using the World Health Organization (WHO) Anatomical Therapeutic Chemical (ATC) classification system:

| ATC Code | Therapeutic Category | Representative Real Medicines | Clinical Purpose |
|:---|:---|:---|:---|
| **M01AB** | Anti-inflammatory & antirheumatic products, non-steroids (Acetic acid derivatives) | Diclofenac, Aceclofenac | Joint pain, rheumatoid arthritis, osteoarthritis |
| **M01AE** | Anti-inflammatory & antirheumatic products, non-steroids (Propionic acid derivatives) | Ibuprofen, Naproxen, Ketoprofen | Pain relief, inflammation, fever reduction |
| **N02BA** | Other analgesics and antipyretics (Salicylic acid and derivatives) | Aspirin (Acetylsalicylic acid) | Mild-to-moderate pain, cardioprotective antiplatelet |
| **N02BE** | Other analgesics and antipyretics (Anilides) | Paracetamol (Acetaminophen) | First-line antipyretic and analgesic |
| **N05B** | Psycholeptics, Anxiolytics | Diazepam, Alprazolam, Lorazepam | Anxiety disorders, muscle spasm, premedication |
| **N05C** | Psycholeptics, Hypnotics and Sedatives | Zolpidem, Zopiclone | Short-term management of insomnia |
| **R03** | Drugs for obstructive airway diseases | Salbutamol, Budesonide, Montelukast | Asthma, COPD, bronchospasm |
| **R06** | Antihistamines for systemic use | Cetirizine, Levocetirizine, Loratadine | Allergic rhinitis, urticaria, allergy relief |

## 3. Important Real-World Data Distinctions & Limitations
1. **Category-Level Aggregation**: The public dataset contains real daily sales totals aggregated at the ATC category level, not individual pill or SKU barcodes.
2. **Absence of Historical Batch Expiry in Public Data**: Real pharmacy sales logs in public archives do not disclose manufacturer batch serial numbers or historical discard dates for confidentiality and data minimization reasons.
3. **Transparent Methodology**: 
   - Authentic demand forecasting models are trained on the genuine historical sales volumes of these 8 therapeutic classes.
   - Batch inventory, expiry tracking, and First-Expiry-First-Out (FEFO) dispensing run against active batch records in the MongoDB inventory store.
   - Expiry risk is computed via a transparent, mathematical velocity engine (Remaining Days × Average Daily Demand) alongside a classification architecture, strictly avoiding fabricated ML metrics.
