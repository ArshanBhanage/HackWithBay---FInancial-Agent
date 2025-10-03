export type Severity = "HIGH" | "MEDIUM" | "LOW";

export type Status = "OPEN" | "ACK" | "RESOLVED";

export interface Violation {
  id: string;
  detectedAt: string; // ISO
  investor: string;
  contract: string;
  ruleId: string;
  ruleType: string;
  expected: string;
  actual: string;
  severity: Severity;
  status: Status;
  evidence: {
    doc: string;
    page: number;
    text: string;
  };
  diff?: { 
    before?: string; 
    after?: string; 
  };
}

export interface Contract {
  id: string;
  name: string;
  type: string;
  investor: string;
  uploadedAt: string;
  status: "PROCESSING" | "COMPLETED" | "ERROR";
  extractedFields?: ContractField[];
}

export interface ContractField {
  fieldName: string;
  value: string;
  confidence: number;
  pageNumber: number;
  boundingBox?: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
}

export interface Alert {
  id: string;
  contractId: string;
  violationId: string;
  severity: Severity;
  message: string;
  detectedAt: string;
  status: Status;
  evidence: {
    document: string;
    page: number;
    text: string;
  };
}

export interface Policy {
  id: string;
  name: string;
  version: string;
  rules: PolicyRule[];
  createdAt: string;
  updatedAt: string;
}

export interface PolicyRule {
  id: string;
  type: string;
  field: string;
  operator: string;
  value: string;
  severity: Severity;
  description: string;
}

export interface DashboardStats {
  totalViolations: number;
  openViolations: number;
  resolvedViolations: number;
  highSeverityViolations: number;
  contractsProcessed: number;
  lastUpdated: string;
}

export interface TimeSeriesData {
  day: string;
  count: number;
}
