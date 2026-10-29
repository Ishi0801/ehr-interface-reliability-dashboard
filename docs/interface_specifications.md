# Interface Specification Document (ISD)
## Enterprise HL7 v2 Inbound Feeds to EHR Core Endpoints

| Specification Detail | Value |
| :--- | :--- |
| Document Version | 1.4 |
| Protocol | HL7 v2.3 / v2.5 over MLLP (Minimal Lower Layer Protocol) |
| Transport Layer | TCP/IP Socket (Standard Port 2575) |
| Receiving System | Enterprise EHR (Epic Core Clinical Ingestion Engine) |
| Target Scope | Inpatient Admissions, Ambulatory Kiosks, and Laboratory Instrumentation |
| Last Reviewed | October 2026 |

---

### 1. Overview & Scope

This specification governs the message formatting, segment requirements, data dictionaries, acknowledgment workflows, and remediation protocols for inbound clinical feeds processed by the hospital interface engine into the central EHR.

---

### 2. Supported Trigger Events

| Message Type | Trigger Event | Description | Sending Application |
| :--- | :--- | :--- | :--- |
| ADT | ADT^A01 | Patient Inpatient Admission | Epic Prelude, Ambulatory Kiosk |
| ADT | ADT^A08 | Patient Demographics / Class Update | Patient Portal, Front-Desk Registration |
| ORU | ORU^R01 | Unsolicited Diagnostic Lab Results | Sunquest LIS, Roche Cobas Analyzer |
| ORM | ORM^O01 | Clinical Order Entry | Inpatient CPOE Workstations |
| MDM | MDM^T02 | Clinical Notes & Transcriptions | Transcription Subsystem |

---

### 3. Segment Mapping & Data Dictionary

#### 3.1 MSH — Message Header Segment (Mandatory)
| Field | Name | Type | Opt | Example Value | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| MSH-1 | Field Separator | ST | R | | | Standard HL7 pipe delimiter |
| MSH-2 | Encoding Characters | ST | R | ^~\& | Component, repetition, escape characters |
| MSH-3 | Sending Application | HD | R | Roche_Cobas_Analyzer | Originating application system |
| MSH-4 | Sending Facility | HD | R | CENTRAL_HOSP | Originating facility identifier |
| MSH-5 | Receiving Application | HD | R | EPIC_INPATIENT | Target EHR endpoint |
| MSH-7 | Date/Time of Message | TS | R | 20261027123000 | ISO format YYYYMMDDHHMMSS |
| MSH-9 | Message Type | CM | R | ORU^R01 | Message code and trigger event |
| MSH-10 | Message Control ID | ST | R | MSG-ORU-216258 | Unique transaction identifier |
| MSH-11 | Processing ID | ID | R | P | P = Production, T = Test |
| MSH-12 | Version ID | VID | R | 2.3 / 2.5 | Standard HL7 release version |

#### 3.2 PID — Patient Identification Segment (Mandatory for ADT & ORU)
| Field | Name | Type | Opt | Example Value | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| PID-3 | Patient Identifier List | CX | R | 98421034^^^MRN | Primary Medical Record Number (MRN) |
| PID-5 | Patient Name | XPN | R | Doe^Jane^M | Legal Family Name ^ Given Name |
| PID-7 | Date/Time of Birth | TS | R | 19850412 | Date of birth (YYYYMMDD) |
| PID-8 | Administrative Sex | IS | R | F | M (Male), F (Female), U (Unknown) |

#### 3.3 OBX — Observation / Result Segment (Mandatory for ORU^R01)
| Field | Name | Type | Opt | Example Value | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| OBX-1 | Set ID — OBX | SI | R | 1 | Sequential line counter |
| OBX-2 | Value Type | ID | R | NM | NM = Numeric, ST = String, TX = Text |
| OBX-3 | Observation Identifier | CE | R | 2345-7^Glucose^LN | Identifier ^ Description ^ Standard (LN = LOINC) |
| OBX-5 | Observation Value | var | R | 105 | Numeric or text clinical result |
| OBX-6 | Units | CE | O | mg/dL^mg/dL^UCUM | Units of measure |
| OBX-11 | Observation Result Status | ID | R | F | F = Final, C = Corrected, P = Preliminary |

---

### 4. Acknowledgment & NACK Resolution Protocol

Every inbound message must receive an acknowledgment (ACK or NACK) within 1,500 ms.

#### 4.1 Acknowledgment Codes (MSA-1)
* AA (Application Accept): Payload validated, parsed, and committed to EHR database.
* AE (Application Error): Syntax valid, but business/schema validation failed (held in triage queue).
* AR (Application Reject): Malformed segment, structural error, or mandatory segment missing.

#### 4.2 Error Classification & Remediation Matrix
| HL7 Error Segment | Failure Mode | Underlying Cause | Analyst Remediation Procedure |
| :--- | :--- | :--- | :--- |
| PID-3 | Missing Primary MRN | Registration kiosk permitted submission with null ID | Re-queue record; route to MPI matching queue; add front-end validation rule. |
| OBX-3 | Unmapped LOINC Code | Analyzer firmware deployed new test code without interface update | Update translation table in interface engine; map instrument code to standard LOINC. |
| OBR-4 | Invalid Service ID | Outdated order catalog reference | Synchronize EHR charge master (CDM) with ancillary order catalog. |
| PV1-2 | Invalid Patient Class | Discharged patient encounter received admission message | Review encounter status; adjust admitting workflow logic. |
| PV1-44 | Admit Datetime Null | Inpatient admission payload missing mandatory timestamp | Verify clinical registration payload; enforce timestamp generator in engine. |

---

### 5. Change Control & SLA Requirements

1. Uptime SLA: Feeds must maintain >= 98.0% clean delivery rate over any rolling 24-hour cycle.
2. Latency SLA: P95 processing latency must remain under 500 ms.
3. Change Management: Any modification to segment parsers or dictionary mappings requires formal validation through the pre-production mirror using automated regression scripts prior to production sign-off.
