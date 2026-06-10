# LIS Database Schema — Design

---

## 🔧 Lookup / Reference Tables

```
Titles:
  Id
  Name
  IsDeleted
  CreatedAt
  UpdatedAt

Units:
  Id
  Name
  IsDeleted
  CreatedAt
  UpdatedAt

PatientContexts:
  -- Examples: fasting, pregnant, pediatric, post-dialysis
  Id
  Name
  IsDeleted
  CreatedAt
  UpdatedAt

PaymentMethods:
  Id
  Name
  IsDeleted
  CreatedAt
  UpdatedAt

RejectionReasons:
  Id
  Name
  IsDeleted
  CreatedAt
  UpdatedAt
```

---

## 👥 Users & Auth

```
Users:
  Id
  FirstName
  LastName
  Email
  PasswordHash
  IsActive
  CreatedAt
  UpdatedAt
```

---

## 🧑‍⚕️ Patients

```
Patients:
  Id
  Identifier
  FirstName
  LastName
  DateOfBirth
  Gender: male | female
  Phone
  Address
  IsDeleted
  CreatedAt
  UpdatedAt

PatientInsurance:
  Id
  PatientId --> Patients
  InsuranceProviderId --> InsuranceProviders
  PolicyNumber
  IsPrimary                                       
  IsDeleted
  CreatedAt
  UpdatedAt
```

---

## 🩺 Doctors

```
Doctors:
  Id
  FirstName
  LastName
  Provenance
  Phone
  TitleId --> Titles
  IsDeleted
  CreatedAt
  UpdatedAt
```

---

## 🧪 Specimen Types

```
SpecimenTypes:
  Id
  Name
  Description
  Color
  IsDeleted
  CreatedAt
  UpdatedAt
```

---

## 📋 Catalog

```
Categories:
  Id
  Name
  SortOrder
  IsDeleted
  CreatedAt
  UpdatedAt

Catalog:
  Id
  Type: item | panel
  Name
  Code                                            -- ✅ UNIQUE constraint required
  Price
  IsOrderable
  CategoryId --> Categories
  IsDeleted
  CreatedAt
  UpdatedAt

CatalogSpecimenRequirements:
  CatalogId --> Catalog
  SpecimenTypeId --> SpecimenTypes
  VolumeMl
  Instructions

CatalogPanelItems:
  Id
  PanelId --> Catalog  (Type must = 'panel')      -- ✅ DB constraint required
  TestId --> Catalog   (Type must = 'item')        -- ✅ DB constraint required
  SortOrder                                       
  CreatedAt
  UpdatedAt
```

---

## 🔬 Analytes

```
Analytes:
  Id
  Code                                            -- ✅ UNIQUE constraint required
  Name
  UnitId --> Units
  DataType: numeric | text | options | image
  OptionsData
  ReferenceText
  IsCalculated
  CalculationFormula
  IsDeleted
  CreatedAt
  UpdatedAt

CatalogItemAnalytes:
  Id
  CatalogItemId --> Catalog
  AnalyteId --> Analytes
  SortOrder
  CreatedAt
  UpdatedAt
```

---

## ✅ Validation & Rules

```
ValidationRules:
  Id
  AnalyteId --> Analytes
  TargetGender: male | female | all
  MinAgeYears                                     -- nullable
  MaxAgeYears                                     -- nullable
  RequiredContextId --> PatientContexts           -- nullable (null = all contexts)
  Priority                                        -- (higher = more specific, wins over lower)
  AbsurdMin
  AbsurdMax
  PanicMin
  PanicMax
  NormalMin
  NormalMax
  ExpectedValue
  MaxDeltaPercent
  CreatedAt
  UpdatedAt

ConsistencyRules:
  Id
  Name
  Formula                                         -- e.g. "{A001} / {A002} > 0.85" using Analytes.Code
  FormulaDescription                              -- plain English explanation
  ErrorMessage
  Severity: warning | error
  IsDeleted
  CreatedAt
  UpdatedAt

ConsistencyRuleAnalytes:
  Id
  RuleId --> ConsistencyRules
  AnalyteId --> Analytes
  CreatedAt
  UpdatedAt

ReflexRules:
  Id
  TriggerAnalyteId --> Analytes
  TriggerOperator: gt | lt | eq | gte | lte | in  
  TriggerValue
  ActionCatalogId --> Catalog
  IsDeleted
  CreatedAt
  UpdatedAt
```

---

## 📦 Orders

```
Orders:
  Id
  PatientId --> Patients
  DoctorId --> Doctors
  PatientInsuranceId --> PatientInsurance         
  Status: registered | collected | in_progress | partial_results | completed | cancelled
  PatientContextId --> PatientContexts
  Notes
  CreatedBy --> Users                             
  CreatedAt
  UpdatedAt

OrderItems:
  Id
  OrderId --> Orders
  CatalogId --> Catalog
  OrderSpecimenId --> OrderSpecimens              -- (links item to required specimen early)
  CatalogPrice
  PriceCharged
  PriceOverrideReason
  IsCoveredByInsurance
  SortOrder
  IsReflexAdded
  CreatedAt
  UpdatedAt

OrderCatalogItemAnalytes:
  Id
  OrderItemId --> OrderItems
  CatalogItemAnalyteId --> CatalogItemAnalytes
  SortOrder
  CreatedAt
  UpdatedAt

OrderSpecimens:
  Id
  OrderId --> Orders
  SpecimenTypeId --> SpecimenTypes
  CollectionTime
  CollectedBy
  Status: collected | rejected | processed
  RejectionReasonId --> RejectionReasons
  Notes
  CreatedAt
  UpdatedAt
```

---

## 🤖 Instruments

```
Instruments:                                      
  Id
  Name
  Model
  SerialNumber
  IsActive
  CreatedAt
  UpdatedAt
```

---

## 📊 Results

```
AnalyteResults:
  Id
  OrderItemId --> OrderItems
  AnalyteId --> Analytes
  SpecimenId --> OrderSpecimens
  InstrumentId --> Instruments                    -- (nullable = manual entry)
  ResultValue
  ValidationRuleId --> ValidationRules            
  IsAbnormal
  IsCritical
  DeltaFlag
  IsRejected
  RejectionReason
  Status: pending | resulted | verified | rejected
  ResultedById --> Users
  ResultedAt
  VerifiedById --> Users
  VerifiedAt
  CreatedAt
  UpdatedAt

AnalyteResultComments:
  Id
  AnalyteResultId --> AnalyteResults
  UserId --> Users
  Comment
  CreatedAt
  UpdatedAt

CriticalNotifications:
  Id
  AnalyteResultId --> AnalyteResults
  NotifiedById --> Users
  NotifiedToId --> Users
  NotifiedAt
  Method: call | sms | in_app | email             
  Acknowledged                                    
  AcknowledgedAt                                  
  Notes
  CreatedAt
  UpdatedAt
```

---

## 📄 Reports

```
ReportTemplates:                                  
  Id
  Name
  Description
  TemplateStorageUrl
  IsDefault
  IsDeleted
  CreatedAt
  UpdatedAt

Reports:
  Id                                              
  OrderId --> Orders
  Version                                         -- (1, 2, 3 for re-releases)
  ReportTemplateId --> ReportTemplates            -- (nullable)
  ReleasedById --> Users
  ReleasedAt
  Channel: print | email | whatsapp | portal
  DeliveryStatus: pending | sent | failed         -- 
  RecipientNote
  ReportStorageUrl
  IsVoided                                        -- (marks superseded versions)
  CreatedAt
  UpdatedAt
```

---

## 🔔 Notifications

```
Notifications:                                    (routine notification log)
  Id
  OrderId --> Orders                              -- nullable
  PatientId --> Patients                          -- nullable
  UserId --> Users
  Type: result_ready | order_update | report_released | general
  Channel: sms | email | whatsapp | in_app
  Message
  Status: pending | sent | failed
  SentAt
  CreatedAt
  UpdatedAt
```

---

## 💳 Insurance

```
InsuranceProviders:
  Id
  Name
  IsDeleted
  CreatedAt
  UpdatedAt

InsurancePricing:
  Id
  InsuranceProviderId --> InsuranceProviders
  CatalogId --> Catalog
  InsurancePrice
  CreatedAt
  UpdatedAt
```

---

## 🧾 Invoices

```
Invoices:
  Id
  OrderId --> Orders
  Version                                         -- (supports reissues)
  IsVoided                                        -- (marks superseded invoices)
  TotalAmount
  Discount
  NetAmount
  AmountPaid
  PaymentStatus: unpaid | paid | partial | refunded
  PaymentMethodId --> PaymentMethods
  CreatedById --> Users
  CreatedAt
  UpdatedAt
```

---

## 💰 Doctor Commissions

```
DoctorCommissionConfigs:
  Id
  DoctorId --> Doctors
  CommissionRate
  InsuranceCommissionRate
  EffectiveFrom
  EffectiveUntil
  -- ✅ NOTE: Enforce non-overlapping date ranges per DoctorId
  --          via PostgreSQL EXCLUDE USING GIST with tsrange
  CreatedAt
  UpdatedAt

DoctorCommissionEntries:
  Id
  OrderId --> Orders
  DoctorId --> Doctors
  OrderNetAmount
  RateApplied
  CommissionAmount
  PayoutStatus: pending | paid
  PaidAt
  CreatedAt
  UpdatedAt

DoctorCommissionPayments:
  Id
  DoctorId --> Doctors
  TotalCommissionAmount
  CreatedBy --> Users
  CreatedAt
  UpdatedAt

DoctorCommissionPaymentEntries:
  Id
  DoctorCommissionPaymentId --> DoctorCommissionPayments
  DoctorCommissionEntryId --> DoctorCommissionEntries
  CreatedAt
  UpdatedAt
```

---

## 📝 Audit

```
AuditLogs:
  Id
  TableName
  RecordId
  Action: insert | update | delete
  OldValues
  NewValues
  PerformedById --> Users
  PerformedAt
  CreatedAt
```

---

## 📐 Constraints & Index Notes

```
-- Unique constraints
UNIQUE: Catalog.Code
UNIQUE: Analytes.Code

-- CatalogPanelItems type enforcement
CHECK: PanelId references Catalog where Type = 'panel'
CHECK: TestId references Catalog where Type = 'item'

-- DoctorCommissionConfigs: no overlapping date ranges per doctor
ALTER TABLE DoctorCommissionConfigs
  ADD CONSTRAINT no_overlapping_commission_configs
  EXCLUDE USING GIST (
    DoctorId WITH =,
    tsrange(EffectiveFrom, EffectiveUntil) WITH &&
  );

-- PatientInsurance: only one primary per patient
CREATE UNIQUE INDEX one_primary_insurance_per_patient
  ON PatientInsurance (PatientId)
  WHERE IsPrimary = true AND IsDeleted = false;
```


---

# 🔄 Production Workflow Model

> Every step below maps directly to tables and field state changes in the schema above.
> Actor roles: **Receptionist**, **Phlebotomist**, **Supervisor**, **Technician**, **Pathologist**, **System (automated)**.

---

## PHASE 1 — Patient & Order Registration

### Step 1.1 — Look up or create Patient
**Actor:** Receptionist

```
ACTION: Search Patients by Identifier, Name, or DateOfBirth
IF not found:
  INSERT Patients (Identifier, FirstName, LastName, DateOfBirth, Gender, Phone, Address)

IF patient has insurance:
  INSERT PatientInsurance (PatientId, InsuranceProviderId, PolicyNumber, IsPrimary=true)
```

---

### Step 1.2 — Create Order
**Actor:** Receptionist

```
INSERT Orders (
  PatientId,
  DoctorId,
  PatientInsuranceId,   -- nullable if cash
  PatientContextId,     -- e.g. fasting, pregnant
  Status = 'registered',
  Notes,
  CreatedBy
)
```

---

### Step 1.3 — Add Tests / Panels to Order
**Actor:** Receptionist

```
FOR each selected Catalog item (item or panel):

  INSERT OrderItems (
    OrderId,
    CatalogId,
    CatalogPrice,
    PriceCharged,         -- may differ if override
    IsCoveredByInsurance,
    SortOrder,
    IsReflexAdded = false
  )

  IF Catalog.Type = 'panel':
    -- Expand panel into constituent tests via CatalogPanelItems
    -- Each panel item also becomes an OrderItem row

  -- Copy analytes for this test into order
  FOR each CatalogItemAnalyte of this CatalogId:
    INSERT OrderCatalogItemAnalytes (OrderItemId, CatalogItemAnalyteId, SortOrder)
```

---

### Step 1.4 — Determine Required Specimens
**Actor:** System (automated on order save)

```
-- For each OrderItem, look up CatalogSpecimenRequirements
-- Deduplicate specimen types across all items in the order
-- (e.g. two tests needing EDTA blood = one tube, not two)

FOR each distinct SpecimenType required:
  INSERT OrderSpecimens (
    OrderId,
    SpecimenTypeId,
    Status = 'collected'  -- will be updated at collection time
  )

-- Link each OrderItem to its required OrderSpecimen
UPDATE OrderItems SET OrderSpecimenId = <matched OrderSpecimen Id>
```

---

### Step 1.5 — Generate Invoice
**Actor:** System (automated on order save)

```
INSERT Invoices (
  OrderId,
  Version = 1,
  IsVoided = false,
  TotalAmount,    -- sum of OrderItems.PriceCharged
  Discount,
  NetAmount,
  AmountPaid = 0,
  PaymentStatus = 'unpaid',
  PaymentMethodId,
  CreatedById
)
```

---

### Step 1.6 — Calculate Doctor Commission Entry
**Actor:** System (automated on order save)

```
-- Find active DoctorCommissionConfig for DoctorId at current date
SELECT * FROM DoctorCommissionConfigs
WHERE DoctorId = :doctorId
AND EffectiveFrom <= NOW()
AND (EffectiveUntil IS NULL OR EffectiveUntil >= NOW())

INSERT DoctorCommissionEntries (
  OrderId,
  DoctorId,
  OrderNetAmount,    -- Invoices.NetAmount
  RateApplied,       -- CommissionRate or InsuranceCommissionRate
  CommissionAmount,
  PayoutStatus = 'pending'
)
```

---

## PHASE 2 — Specimen Collection

### Step 2.1 — Print or Display Collection Instructions
**Actor:** Phlebotomist

```
-- Query all OrderSpecimens for this Order
SELECT
  os.Id,
  st.Name         AS SpecimenType,
  st.Color        AS TubeColor,
  csr.VolumeMl,
  csr.Instructions
FROM OrderSpecimens os
JOIN SpecimenTypes st ON st.Id = os.SpecimenTypeId
JOIN CatalogSpecimenRequirements csr ON csr.SpecimenTypeId = os.SpecimenTypeId
WHERE os.OrderId = :orderId
```

---

### Step 2.2 — Record Collection
**Actor:** Phlebotomist

```
UPDATE OrderSpecimens SET
  CollectionTime = NOW(),
  CollectedBy    = :userId,
  Status         = 'collected'
WHERE Id = :specimenId

UPDATE Orders SET
  Status = 'collected'
WHERE Id = :orderId
```

---

### Step 2.3 — Specimen Rejection (if applicable)
**Actor:** Phlebotomist / Lab Receptionist

```
-- If specimen is haemolysed, insufficient, wrong tube, etc.
UPDATE OrderSpecimens SET
  Status            = 'rejected',
  RejectionReasonId = :reasonId,
  Notes             = :notes
WHERE Id = :specimenId

-- Mark affected AnalyteResults as rejected
UPDATE AnalyteResults SET
  IsRejected     = true,
  RejectionReason = :reason,
  Status          = 'rejected'
WHERE SpecimenId = :specimenId
```

---

## PHASE 3 — Result Entry & Validation

### Step 3.1 — Technician Picks Up Work
**Actor:** Technician

```
-- Technician queries all pending OrderItems (collected specimens, not yet resulted)
-- Filtered by category/discipline at app layer

SELECT
  o.Id            AS OrderId,
  p.FirstName,
  p.LastName,
  p.DateOfBirth,
  p.Gender,
  o.PatientContextId,
  oi.Id           AS OrderItemId,
  c.Name          AS TestName,
  c.CategoryId,
  st.Name         AS SpecimenType,
  st.Color        AS TubeColor,
  os.Status       AS SpecimenStatus
FROM OrderItems oi
JOIN Orders o          ON o.Id  = oi.OrderId
JOIN Patients p        ON p.Id  = o.PatientId
JOIN Catalog c         ON c.Id  = oi.CatalogId
JOIN OrderSpecimens os ON os.Id = oi.OrderSpecimenId
JOIN SpecimenTypes st  ON st.Id = os.SpecimenTypeId
WHERE os.Status  = 'collected'
AND o.Status     IN ('collected', 'in_progress', 'partial_results')
ORDER BY o.CreatedAt, oi.SortOrder

UPDATE Orders SET Status = 'in_progress'
WHERE Id = :orderId AND Status = 'collected'
```

---

### Step 3.2 — Enter Analyte Results
**Actor:** Technician (manual) or System (instrument feed)

```
FOR each analyte in OrderCatalogItemAnalytes for this OrderItem:

  INSERT AnalyteResults (
    OrderItemId,
    AnalyteId,
    SpecimenId,
    InstrumentId,    -- null if manual
    ResultValue,
    Status = 'resulted',
    ResultedById = :userId,
    ResultedAt = NOW()
  )
```

---

### Step 3.3 — Automatic Validation
**Actor:** System (triggered on result insert)

```
-- 1. Find best matching ValidationRule
SELECT * FROM ValidationRules
WHERE AnalyteId = :analyteId
AND (TargetGender = :patientGender OR TargetGender = 'all')
AND (MinAgeYears IS NULL OR MinAgeYears <= :patientAge)
AND (MaxAgeYears IS NULL OR MaxAgeYears >= :patientAge)
AND (RequiredContextId IS NULL OR RequiredContextId = :patientContextId)
ORDER BY Priority DESC
LIMIT 1

-- 2. Apply rule
IF ResultValue < AbsurdMin OR ResultValue > AbsurdMax:
  → Block result, force technician review

IF ResultValue < PanicMin OR ResultValue > PanicMax:
  → Set IsCritical = true
  → Trigger CriticalNotification workflow (Phase 4.5)

IF ResultValue < NormalMin OR ResultValue > NormalMax:
  → Set IsAbnormal = true

-- 3. Delta check (compare to previous result for same patient+analyte)
SELECT ResultValue FROM AnalyteResults
JOIN OrderItems ON OrderItems.Id = AnalyteResults.OrderItemId
JOIN Orders ON Orders.Id = OrderItems.OrderId
WHERE AnalyteResults.AnalyteId = :analyteId
AND Orders.PatientId = :patientId
AND AnalyteResults.Status = 'verified'
ORDER BY AnalyteResults.ResultedAt DESC
LIMIT 1

IF ABS(new - previous) / previous * 100 > MaxDeltaPercent:
  → Set DeltaFlag = true

-- 4. Update result record
UPDATE AnalyteResults SET
  ValidationRuleId = :ruleId,
  IsAbnormal       = :isAbnormal,
  IsCritical       = :isCritical,
  DeltaFlag        = :deltaFlag
WHERE Id = :resultId
```

---

### Step 3.4 — Consistency Rule Check
**Actor:** System (triggered after all analytes of an OrderItem are resulted)

```
-- For each ConsistencyRule linked to analytes in this OrderItem:
SELECT cr.* FROM ConsistencyRules cr
JOIN ConsistencyRuleAnalytes cra ON cra.RuleId = cr.Id
WHERE cra.AnalyteId IN (:analyteIdsForThisOrderItem)
AND cr.IsDeleted = false

-- Evaluate Formula (e.g. "{A001} / {A002} > 0.85")
-- Substitute analyte codes with their ResultValues
-- If formula evaluates to false:
  IF Severity = 'error':
    → Block verification, show error to technician
  IF Severity = 'warning':
    → Show warning, allow technician to proceed with acknowledgement
```

---

### Step 3.5 — Critical Value Notification
**Actor:** System (triggered when IsCritical = true)

```
INSERT CriticalNotifications (
  AnalyteResultId,
  NotifiedById,   -- technician or system
  NotifiedToId,   -- ordering doctor or supervisor
  NotifiedAt = NOW(),
  Method,         -- call | sms | in_app | email
  Acknowledged = false
)

-- Notification must be acknowledged before result can be verified
-- Pathologist/supervisor acknowledges:
UPDATE CriticalNotifications SET
  Acknowledged   = true,
  AcknowledgedAt = NOW()
WHERE Id = :notificationId
```

---

### Step 3.6 — Reflex Rule Evaluation
**Actor:** System (triggered on result insert)

```
-- Check if any ReflexRule is triggered by this result
SELECT * FROM ReflexRules
WHERE TriggerAnalyteId = :analyteId
AND IsDeleted = false

-- Evaluate TriggerOperator + TriggerValue against ResultValue
-- e.g. if Glucose > 11.1 → auto-add HbA1c test

IF triggered:
  INSERT OrderItems (
    OrderId,
    CatalogId   = ActionCatalogId,
    IsReflexAdded = true,
    CatalogPrice,
    PriceCharged
  )
  -- Then re-run Step 1.3 for this new item
  -- Update Invoice to reflect added test (new Invoice Version)
```

---

### Step 3.7 — Calculated Analytes
**Actor:** System (triggered after all source analytes are resulted)

```
-- For analytes where IsCalculated = true
-- Evaluate CalculationFormula substituting referenced analyte results
-- e.g. LDL = TotalCholesterol - HDL - (Triglycerides / 5)

INSERT AnalyteResults (
  OrderItemId,
  AnalyteId,
  ResultValue    = <calculated>,
  InstrumentId   = null,
  Status         = 'resulted',
  ResultedById   = null   -- system-generated
)
```

---

## PHASE 4 — Result Verification

### Step 4.1 — Pathologist Reviews & Verifies
**Actor:** Pathologist

```
-- Pathologist reviews all AnalyteResults for an OrderItem
-- Checks flagged results: IsAbnormal, IsCritical, DeltaFlag
-- May add comments:

INSERT AnalyteResultComments (
  AnalyteResultId,
  UserId,
  Comment,
  CreatedAt = NOW()
)

-- Verify each result:
UPDATE AnalyteResults SET
  Status       = 'verified',
  VerifiedById = :pathologistId,
  VerifiedAt   = NOW()
WHERE Id = :resultId
```

---

### Step 4.2 — Update Order Status
**Actor:** System (triggered after verification)

```
-- Check if all OrderItems for this Order are fully verified
IF all AnalyteResults for all OrderItems = 'verified':
  UPDATE Orders SET Status = 'completed'
ELSE IF some verified, some pending:
  UPDATE Orders SET Status = 'partial_results'
```

---

## PHASE 5 — Report Generation & Release

### Step 5.1 — Generate Report
**Actor:** Pathologist / System

```
-- Compile all verified AnalyteResults for this Order
-- Apply ReportTemplate (default or selected)
-- Generate PDF → upload to storage → get URL

INSERT Reports (
  OrderId,
  Version        = 1,
  ReportTemplateId,
  ReleasedById   = :userId,
  ReleasedAt     = NOW(),
  Channel,       -- print | email | whatsapp | portal
  DeliveryStatus = 'pending',
  ReportStorageUrl,
  IsVoided       = false
)
```

---

### Step 5.2 — Deliver Report
**Actor:** System

```
-- Attempt delivery via chosen Channel
-- On success:
UPDATE Reports SET DeliveryStatus = 'sent'

-- On failure:
UPDATE Reports SET DeliveryStatus = 'failed'
-- Retry logic or manual re-send

-- Log notification:
INSERT Notifications (
  OrderId,
  PatientId,
  UserId,
  Type    = 'report_released',
  Channel,
  Message,
  Status  = 'sent',
  SentAt  = NOW()
)
```

---

### Step 5.3 — Report Correction (Re-release)
**Actor:** Pathologist

```
-- If a result needs correction after release:

-- 1. Void current report
UPDATE Reports SET IsVoided = true
WHERE OrderId = :orderId AND IsVoided = false

-- 2. Correct the result
UPDATE AnalyteResults SET
  ResultValue  = :correctedValue,
  Status       = 'resulted'   -- back to resulted for re-verification
WHERE Id = :resultId

-- 3. Re-verify
UPDATE AnalyteResults SET
  Status       = 'verified',
  VerifiedById = :pathologistId,
  VerifiedAt   = NOW()

-- 4. Issue new report version
INSERT Reports (
  OrderId,
  Version          = <previous Version + 1>,
  ReportTemplateId,
  ReleasedById,
  ReleasedAt       = NOW(),
  Channel,
  DeliveryStatus   = 'pending',
  ReportStorageUrl = <new URL>,
  IsVoided         = false
)
```

---

## PHASE 6 — Billing & Payment

### Step 6.1 — Payment Collection
**Actor:** Receptionist / Cashier

```
UPDATE Invoices SET
  AmountPaid    = :amount,
  PaymentStatus = CASE
    WHEN :amount >= NetAmount THEN 'paid'
    WHEN :amount > 0          THEN 'partial'
    ELSE 'unpaid'
  END,
  PaymentMethodId = :methodId
WHERE Id = :invoiceId
AND IsVoided = false
```

---

### Step 6.2 — Invoice Correction / Reissue
**Actor:** Supervisor / Admin

```
-- Void current invoice
UPDATE Invoices SET IsVoided = true
WHERE OrderId = :orderId AND IsVoided = false

-- Create corrected version
INSERT Invoices (
  OrderId,
  Version       = <previous Version + 1>,
  IsVoided      = false,
  TotalAmount,
  Discount,
  NetAmount,
  AmountPaid    = 0,
  PaymentStatus = 'unpaid',
  CreatedById
)
```

---

### Step 6.3 — Insurance Billing
**Actor:** System / Admin

```
-- Determine insurance price for each covered OrderItem
SELECT ip.InsurancePrice
FROM InsurancePricing ip
JOIN PatientInsurance pi ON pi.InsuranceProviderId = ip.InsuranceProviderId
JOIN Orders o            ON o.PatientInsuranceId   = pi.Id
WHERE ip.CatalogId = :catalogId
AND   o.Id         = :orderId

-- Apply IsCoveredByInsurance flag on OrderItems
UPDATE OrderItems SET
  IsCoveredByInsurance = true,
  PriceCharged         = :insurancePrice
WHERE Id = :orderItemId
```

---

## PHASE 7 — Doctor Commission Payout

### Step 7.1 — Supervisor Reviews Pending Commissions
**Actor:** Admin / Finance

```
SELECT
  dce.Id,
  d.FirstName,
  d.LastName,
  o.Id          AS OrderId,
  dce.OrderNetAmount,
  dce.RateApplied,
  dce.CommissionAmount,
  dce.PayoutStatus
FROM DoctorCommissionEntries dce
JOIN Doctors d ON d.Id = dce.DoctorId
JOIN Orders  o ON o.Id = dce.OrderId
WHERE dce.PayoutStatus = 'pending'
AND   dce.DoctorId     = :doctorId
```

---

### Step 7.2 — Record Commission Payment
**Actor:** Admin / Finance

```
-- Create payment batch
INSERT DoctorCommissionPayments (
  DoctorId,
  TotalCommissionAmount,  -- sum of selected entries
  CreatedBy,
  CreatedAt = NOW()
)

-- Link entries to payment
FOR each selected DoctorCommissionEntry:
  INSERT DoctorCommissionPaymentEntries (
    DoctorCommissionPaymentId,
    DoctorCommissionEntryId,
    CreatedAt = NOW()
  )

  -- Mark entry as paid
  UPDATE DoctorCommissionEntries SET
    PayoutStatus = 'paid',
    PaidAt       = NOW()
  WHERE Id = :entryId
```

---

## PHASE 8 — Audit Trail

### Every write operation across all phases:
**Actor:** System (DB trigger or application layer)

```
INSERT AuditLogs (
  TableName,
  RecordId,
  Action,       -- insert | update | delete
  OldValues,    -- JSON snapshot of previous state
  NewValues,    -- JSON snapshot of new state
  PerformedById,
  PerformedAt = NOW()
)
```

---

## 📊 Complete Order Status State Machine

```
registered
    │
    ▼
collected          ← OrderSpecimens all collected
    │
    ▼
in_progress        ← first AnalyteResult entered
    │
    ├──────────────────────┐
    ▼                      ▼
partial_results        completed    ← all AnalyteResults verified
    │                      │
    └──────────────────────┘
                           │
                           ▼
                      [Report Released]
                           │
                           ▼
                      [Invoice Paid]

    cancelled  ← can occur from registered or collected only
```

---

## 📊 AnalyteResult Status State Machine

```
pending
    │
    ▼
resulted           ← technician enters value
    │
    ├── [validation fails absurd check] → back to pending (technician must fix)
    │
    ▼
verified           ← pathologist confirms
    │
    ├── [correction needed] → back to resulted
    │
    ▼
rejected           ← specimen rejected or result invalidated
```

---

## 📊 Specimen Status State Machine

```
collected
    │
    ├──────────────┐
    ▼              ▼
processed       rejected    ← RejectionReasonId set
```

---

## 📊 Key Cross-Phase Data Flow

```
Catalog ──────────────────────────────────────────────────────────┐
  └─ CatalogItemAnalytes                                           │
  └─ CatalogSpecimenRequirements                                   │
  └─ CatalogPanelItems                                             │
         │                                                         │
         ▼                                                         │
Orders → OrderItems → OrderCatalogItemAnalytes                     │
              │                                                    │
              ▼                                                    │
         OrderSpecimens                                            │
              │                                                    │
              ▼                                                    │
         WorklistAssignments                                       │
              │                                                    │
              ▼                                                    │
         AnalyteResults ──── ValidationRules ◄── Analytes ◄────────┘
              │
              ├── AnalyteResultComments
              ├── CriticalNotifications
              └── [triggers] ReflexRules → new OrderItems
                             ConsistencyRules → warnings/blocks

Orders → Invoices → PaymentMethods
Orders → DoctorCommissionEntries → DoctorCommissionPayments
Orders → Reports → Notifications
```

---

---

# 🔐 RBAC — Role-Based Access Control

---

## Schema

```
Permissions:
  Id
  Resource        -- e.g. 'orders', 'results', 'reports', 'worklist'
  Action          -- e.g. 'create', 'view', 'verify', 'release', 'assign'
  Description
  CreatedAt

Roles:
  Id
  Name            -- e.g. 'pathologist', 'technician', 'receptionist'
  Description
  IsDefault       -- if true, auto-assigned to new users
  IsDeleted
  CreatedAt
  UpdatedAt

RolePermissions:
  Id
  RoleId       --> Roles
  PermissionId --> Permissions
  CreatedAt

UserRoles:
  Id
  UserId       --> Users
  RoleId       --> Roles
  AssignedById --> Users      -- who granted this role
  AssignedAt
  ExpiresAt                   -- nullable: for temporary role grants
  CreatedAt
  UpdatedAt
```

---

## Full Permission Registry

```
-- Patients
patients:create          -- register new patient
patients:view            -- search and view patient records
patients:edit            -- update demographics, contact info

-- Patient Insurance
patient_insurance:create -- add insurance policy to patient
patient_insurance:view
patient_insurance:edit   -- correct policy number, switch primary

-- Orders
orders:create            -- create new order
orders:view              -- view order details and status
orders:edit              -- edit order before specimen collection (doctor, context, notes)
orders:cancel            -- cancel an order

-- Order Items
order_items:create       -- add tests to an order
order_items:view
order_items:edit         -- adjust price override, sort order
order_items:delete       -- remove a test before processing

-- Specimens
specimens:view
specimens:collect        -- record specimen collection
specimens:reject         -- mark specimen as rejected with reason

-- Results
results:enter            -- technician enters result values
results:edit             -- correct a result before verification
results:verify           -- pathologist verifies results
results:view             -- any authorized viewer

-- Critical Notifications
critical_notifications:view
critical_notifications:acknowledge

-- Reports
reports:release          -- pathologist releases a report
reports:void             -- void a superseded report version
reports:view             -- doctor, patient portal, lab staff

-- Invoices
invoices:create
invoices:view
invoices:edit            -- adjust discount, correct amounts
invoices:void            -- void and reissue an invoice

-- Payments
payments:view
payments:collect         -- record a payment
payments:refund          -- issue a refund

-- Commissions
commissions:view
commissions:pay          -- record a commission payout

-- Catalog & Rules (admin / setup)
catalog:manage           -- full CRUD on catalog items and panels
rules:manage             -- full CRUD on validation, consistency, reflex rules

-- Users & Roles (admin only)
users:manage             -- create, edit, deactivate users
roles:manage             -- create roles, assign permissions

-- Audit
audit:view               -- read-only access to audit logs
```

---

## Default Role → Permission Mapping

```
super_admin:
  ALL permissions

lab_manager:
  patients:view
  patients:edit
  patient_insurance:view
  orders:view
  orders:edit
  orders:cancel
  order_items:view
  order_items:edit
  order_items:delete
  specimens:view
  catalog:manage
  rules:manage
  results:view
  critical_notifications:view
  critical_notifications:acknowledge
  reports:view
  reports:void
  invoices:view
  invoices:edit
  invoices:void
  payments:view
  payments:refund
  commissions:view
  users:manage
  roles:manage
  audit:view

receptionist:
  patients:create
  patients:view
  patients:edit
  patient_insurance:create
  patient_insurance:view
  patient_insurance:edit
  orders:create
  orders:view
  orders:edit
  orders:cancel
  order_items:create
  order_items:view
  order_items:edit
  order_items:delete
  specimens:view
  invoices:create
  invoices:view
  payments:view
  payments:collect
  reports:view

phlebotomist:
  patients:view
  orders:view
  order_items:view
  specimens:view
  specimens:collect
  specimens:reject

supervisor:
  patients:view
  orders:view
  order_items:view
  specimens:view
  results:view
  results:edit
  critical_notifications:view
  critical_notifications:acknowledge

technician:
  patients:view
  orders:view
  order_items:view
  specimens:view
  results:enter
  results:edit
  results:view

pathologist:
  patients:view
  orders:view
  order_items:view
  specimens:view
  results:view
  results:edit
  results:verify
  critical_notifications:view
  critical_notifications:acknowledge
  reports:release
  reports:void
  reports:view

finance:
  orders:view
  invoices:create
  invoices:view
  invoices:edit
  invoices:void
  payments:view
  payments:collect
  payments:refund
  commissions:view
  commissions:pay

doctor:
  patients:view             -- own patients only (enforced at app layer)
  orders:view               -- own orders only
  order_items:view          -- own orders only
  results:view              -- own patients only
  reports:view              -- own patients only

patient:
  reports:view              -- own reports only (portal access)
```

---

## Resolving Effective Permissions at Runtime

```sql
-- Get all permissions for a given user (across all their roles)
SELECT DISTINCT
  p.Resource,
  p.Action
FROM UserRoles ur
JOIN RolePermissions rp ON rp.RoleId       = ur.RoleId
JOIN Permissions p      ON p.Id            = rp.PermissionId
JOIN Roles r            ON r.Id            = ur.RoleId
WHERE ur.UserId    = :userId
AND   r.IsDeleted  = false
AND   (ur.ExpiresAt IS NULL OR ur.ExpiresAt > NOW())
```

---

## RBAC Enforcement Points in Workflow

```
PHASE 1 — Registration
  patients:create              → Receptionist
  patients:edit                → Receptionist, Lab Manager
  patient_insurance:create     → Receptionist
  patient_insurance:edit       → Receptionist, Lab Manager
  orders:create                → Receptionist
  orders:edit                  → Receptionist, Lab Manager
  orders:cancel                → Receptionist, Lab Manager
  order_items:create           → Receptionist
  order_items:edit             → Receptionist, Lab Manager
  order_items:delete           → Receptionist, Lab Manager
  invoices:create              → Receptionist, Finance
  payments:collect             → Receptionist, Finance

PHASE 2 — Specimen Collection
  specimens:collect            → Phlebotomist
  specimens:reject             → Phlebotomist

PHASE 3 — Result Entry & Validation
  results:enter                → Technician
  results:edit                 → Technician, Supervisor (before verification)
  critical_notifications:view  → Supervisor, Pathologist
  critical_notifications:acknowledge → Supervisor, Pathologist

PHASE 4 — Verification
  results:verify               → Pathologist
  results:edit                 → Pathologist (correction before verify)

PHASE 5 — Report Release
  reports:release              → Pathologist
  reports:void                 → Pathologist, Lab Manager
  reports:view                 → Doctor (own), Patient (own), Lab Staff

PHASE 6 — Billing
  invoices:edit                → Finance, Lab Manager
  invoices:void                → Finance, Lab Manager
  payments:collect             → Receptionist, Finance
  payments:refund              → Finance, Lab Manager

PHASE 7 — Commissions
  commissions:view             → Finance, Lab Manager
  commissions:pay              → Finance

PHASE 8 — Audit
  audit:view                   → Lab Manager, Super Admin only
```

---

## RBAC Workflow — PHASE 0 (runs before every operation)

### Step 0.1 — Permission Guard
**Actor:** System (application middleware)

```
FUNCTION can(userId, resource, action):

  SELECT COUNT(*) FROM UserRoles ur
  JOIN RolePermissions rp ON rp.RoleId       = ur.RoleId
  JOIN Permissions p      ON p.Id            = rp.PermissionId
  JOIN Roles r            ON r.Id            = ur.RoleId
  WHERE ur.UserId    = :userId
  AND   p.Resource   = :resource
  AND   p.Action     = :action
  AND   r.IsDeleted  = false
  AND   (ur.ExpiresAt IS NULL OR ur.ExpiresAt > NOW())

  IF count = 0 → DENY (403)
  IF count > 0 → ALLOW → proceed to requested phase
```

---

### Step 0.2 — Row-Level Scoping (for restricted roles)

```
-- Doctor: can only see their own patients' data
IF user has role 'doctor':
  ALL queries on Orders, AnalyteResults, Reports
  must include: WHERE Orders.DoctorId = :userId

-- Patient: can only see their own reports
IF user has role 'patient':
  ALL queries on Reports
  must include: WHERE Orders.PatientId = :patientId

-- Technician: can only see pending orders with collected specimens
IF user has role 'technician':
  Queries on OrderItems filtered by:
  WHERE os.Status = 'collected'
  AND o.Status IN ('collected', 'in_progress', 'partial_results')
```

---

### Step 0.3 — Role Assignment (admin operation)

```
-- Assign a role to a user
INSERT UserRoles (
  UserId,
  RoleId,
  AssignedById = :adminUserId,
  AssignedAt   = NOW(),
  ExpiresAt    = null     -- or a date for temporary grants
)

-- Revoke a role
DELETE FROM UserRoles
WHERE UserId = :userId
AND   RoleId = :roleId

-- All role changes are captured by AuditLogs automatically
```

---

## Constraints & Index Notes (RBAC)

```sql
-- A user cannot have the same role assigned twice (active)
CREATE UNIQUE INDEX unique_active_user_role
  ON UserRoles (UserId, RoleId)
  WHERE ExpiresAt IS NULL OR ExpiresAt > NOW();

-- A role cannot have the same permission twice
CREATE UNIQUE INDEX unique_role_permission
  ON RolePermissions (RoleId, PermissionId);

-- Permissions must be unique per resource+action pair
CREATE UNIQUE INDEX unique_permission
  ON Permissions (Resource, Action);
```
