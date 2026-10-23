import pandas as pd
import numpy as np
import uuid
import random

print("Loading Synthea CSV files...")
encounters = pd.read_csv("../encounters.csv")
observations = pd.read_csv("../observations.csv")

# 1. Map Encounters to HL7 ADT Messages (ADT^A01: Admission, ADT^A08: Update)
print("Transforming Encounters to HL7 ADT messages...")
adt_records = []
for idx, row in encounters.iterrows():
    # Inpatient/Emergency -> ADT^A01, Ambulatory/Wellness -> ADT^A08
    msg_type = "ADT^A01" if str(row.get("ENCOUNTERCLASS", "")).lower() in ["inpatient", "emergency"] else "ADT^A08"
    sending_app = "Epic_Prelude_ADT" if msg_type == "ADT^A01" else "Ambulatory_Kiosk"
    dept = row.get("DESCRIPTION", "General Medicine")
    
    adt_records.append({
        "Transaction_ID": f"TXN-{uuid.uuid4().hex[:8].upper()}",
        "Timestamp": row["START"],
        "Message_Control_ID": f"MSG-ADT-{100000 + idx}",
        "Trigger_Event": msg_type,
        "Sending_Application": sending_app,
        "Receiving_EMR": "Epic_Inpatient_Prod",
        "Hospital_Department": dept[:35] if pd.notna(dept) else "General Medicine",
        "Patient_ID": row["PATIENT"],
        "Base_Source": "Encounters"
    })

df_adt = pd.DataFrame(adt_records)

# 2. Map Observations to HL7 ORU Lab Messages (ORU^R01)
print("Transforming Observations to HL7 ORU messages...")
sample_obs = observations.sample(n=min(len(observations), 40000), random_state=42)
oru_records = []
for idx, row in sample_obs.iterrows():
    sending_app = random.choice(["Sunquest_LIS", "Roche_Cobas_Analyzer", "Cerner_Millennium_Lab"])
    oru_records.append({
        "Transaction_ID": f"TXN-{uuid.uuid4().hex[:8].upper()}",
        "Timestamp": row["DATE"],
        "Message_Control_ID": f"MSG-ORU-{200000 + idx}",
        "Trigger_Event": "ORU^R01",
        "Sending_Application": sending_app,
        "Receiving_EMR": "Epic_Inpatient_Prod",
        "Hospital_Department": "Central Laboratory",
        "Patient_ID": row["PATIENT"],
        "Base_Source": "Observations"
    })

df_oru = pd.DataFrame(oru_records)

# Combine into master HL7 transaction stream
df_hl7 = pd.concat([df_adt, df_oru], ignore_index=True)
df_hl7["Timestamp"] = pd.to_datetime(df_hl7["Timestamp"], errors="coerce")
df_hl7 = df_hl7.dropna(subset=["Timestamp"]).sort_values("Timestamp").reset_index(drop=True)

# 3. Simulate Interface Engine Metrics (Latency, ACK/NACK, and Error Segments)
print("Simulating Interface Engine telemetry (latency, NACKs, and error segments)...")
np.random.seed(42)
random.seed(42)

latencies = []
ack_status = []
hl7_error_code = []
error_segments = []

for idx, row in df_hl7.iterrows():
    hour = row["Timestamp"].hour
    
    # Base engine latency (30 - 250 ms)
    lat = int(np.random.exponential(scale=95) + 35)
    # Inject latency spikes during morning and evening shift handoffs (7-8 AM, 7 PM)
    if hour in [7, 8, 19] and random.random() < 0.20:
        lat += random.randint(950, 3200)
    latencies.append(lat)
    
    # 5.5% overall failure (NACK) rate
    is_nack = random.random() < 0.055
    if is_nack:
        ack_status.append("NACK")
        err_code = np.random.choice(["AE", "AR", "CE"], p=[0.74, 0.18, 0.08])
        hl7_error_code.append(err_code)
        
        if row["Trigger_Event"].startswith("ADT"):
            # Missing MRN in PID-3 is the leading hospital admission error
            seg = np.random.choice(
                ["PID-3 (Missing Primary MRN)", "PV1-2 (Invalid Patient Class)", "PV1-44 (Admit Datetime Null)"],
                p=[0.76, 0.16, 0.08]
            )
        else: # ORU lab results
            seg = np.random.choice(
                ["OBX-3 (Unmapped LOINC Code)", "OBR-4 (Invalid Universal Service ID)", "PID-3 (Patient Not Found)"],
                p=[0.58, 0.26, 0.16]
            )
        error_segments.append(seg)
    else:
        ack_status.append("ACK")
        hl7_error_code.append("AA") # Application Accept
        error_segments.append("None")

df_hl7["Processing_Time_ms"] = latencies
df_hl7["ACK_NACK_Status"] = ack_status
df_hl7["HL7_Error_Code"] = hl7_error_code
df_hl7["Error_Segment"] = error_segments

# Export clean fact table
output_filename = "Fact_HL7_Transactions.csv"
df_hl7.to_csv(output_filename, index=False)
print(f"Successfully generated {len(df_hl7)} HL7 interface transactions into '{output_filename}'!")