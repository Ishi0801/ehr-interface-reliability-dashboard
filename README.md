# Enterprise EHR & Interface Engine Reliability Dashboard (HL7 v2 & EHR Integration)

An executive health IT business intelligence solution monitoring hospital interface engine feeds (HL7 v2.x: ADT admissions, ORU lab results) entering an enterprise Electronic Health Record (EHR) system.

---

## 🏥 Clinical & Operational Problem

Hospital interface engines (e.g., Mirth Connect, Corepoint) process millions of HL7 transactions daily between ancillary departmental systems and the central EHR. 

When message queues lag or fail:
* Critical lab observations (`ORU^R01`) do not populate the patient chart, directly delaying physician diagnoses.
* Patient registration feeds (`ADT^A01`, `ADT^A08`) fail, resulting in mismatched patient identity and potential duplicate records.
* Health system leadership lacks visibility into interface throughput velocity, SLA compliance, and root causes of Negative Acknowledgments (NACKs).

This project models and visualizes **50,000+ simulated HL7 transactions** to identify feed bottlenecks, assess latency percentiles, and prioritize interface error remediation.

---

## 🏗️ Architecture & Data Pipeline

```text
[ Synthea Patient Encounters & Lab Observations ]
                        │
                        ▼
       [ Python Transformation & Simulation Engine ]
   (transform_synthea_to_hl7.py maps clinical events to HL7
    v2 message types, simulates latency, & injects NACK codes)
                        │
                        ▼
            [ Fact_HL7_Transactions.csv ]
                        │
                        ▼
     [ Dimensional Star Schema Modeling (BI Layer) ]
          ├── Dim_MessageType (ADT, ORU, MDM, ORM)
          ├── Dim_SystemEndpoint (LIS, PACS, Prelude, Core EHR)
          └── Dim_ErrorCategory (PID-3, PV1-2, OBX-3)
                        │
                        ▼
   [ Executive Visualizations (Tableau / Power BI) ]
```

---

## 📊 Core Visualizations & Key Operational Insights

### 1. Real-Time Interface Health Scorecard
* **Clean Delivery Rate:** Monitored against a 98.0% SLA benchmark.
* **P95 Processing Latency:** Tracks 95th percentile delivery time to detect system queue stalls before outright feed failure occurs.

### 2. Hourly Message Congestion Matrix
* Pinpoints significant latency spikes (>1,500 ms) occurring systematically at **07:00–08:00 AM** and **07:00 PM**.
* **Operational Action:** Demonstrates that morning and evening nurse shift handoffs cause clinical order entry and patient transfer surges that congest engine queues.

### 3. NACK Root-Cause Pareto Analysis
* Isolates error frequency across HL7 segments.
* **Operational Action:** Proves that **PID-3 (Missing Primary MRN)** accounts for >75% of failed ADT registration messages, pinpointing upstream kiosk/registration validation as the primary operational fix rather than interface engine software errors.

### 4. Department Latency & Ingestion Lag Tracker
* Identifies delivery lag distribution across inpatient departments, the Emergency Department (ED), and central laboratories.

---

## 📋 HL7 v2 Message Type Mapping

| Trigger Event | Description | Source Application | Receiving EMR |
| :--- | :--- | :--- | :--- |
| `ADT^A01` | Patient Admission / Inpatient Staging | Epic Prelude | Epic Inpatient Prod |
| `ADT^A08` | Patient Information / Class Update | Ambulatory Kiosk | Epic Inpatient Prod |
| `ORU^R01` | Observational Lab Results | Sunquest LIS / Roche Analyzer | Epic Inpatient Prod |
| `ORM^O01` | Clinical Orders Entry | Epic Orders | Core Engine Node |
| `MDM^T02` | Clinical Notes & Transcriptions | Transcription Feeds | Epic Inpatient Prod |

---

## 🚀 How to Run the Transformation Script

### 1. Prerequisites
* Python 3.10+
* Synthea open-source encounter and observation CSV exports

### 2. Setup
```bash
git clone https://github.com/<your-username>/ehr-interface-reliability-dashboard.git
cd ehr-interface-reliability-dashboard

python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Run Transformation
Place your `encounters.csv` and `observations.csv` in `data/raw/` and execute:
```bash
python scripts/transform_synthea_to_hl7.py
```
This generates the dimensional table in `data/processed/Fact_HL7_Transactions.csv`.