# Financial Contract Drift Monitor - Architecture

## System Architecture Diagram

```mermaid
flowchart TD
    subgraph Sources[Document Sources]
        D1[Contracts / LPAs / Side Letters (PDF/Scan)]
        D2[Amendments & Riders]
        D3[Operational Data (CSV/DB): Fees, Reports, Allocations]
    end

    subgraph Pathway[Pathway Runtime]
        I[Live Ingestion + Connectors]
        H[Hybrid Index (BM25 + Vectors)]
        S[Streaming Join / Validator]
    end

    subgraph LandingAI[LandingAI ADE (DPT-2)]
        E[Structured Extraction<br/>(tables, clauses, fields)]
        Ev[Evidence Spans<br/>(page#, table cell, text)]
    end

    subgraph O2A[O2A Service (Your code)]
        N[Obligation Ontology<br/>(normalize terms)]
        C[Policy Compiler<br/>(YAML/JSON rules)]
        R[Conflict & Drift Detector]
        P[Policy Store]
    end

    subgraph UX[Review & Actions]
        UI[Analyst Dashboard]
        A1[Exports (CSV/Excel/Memo)]
        A2[Webhooks: CRM/Portfolio/Slack]
    end

    D1 --> I --> H
    D2 --> I
    H --> E
    E --> N --> C --> P
    E --> Ev
    R <---> P
    D3 --> S
    P --> S
    S --> UI
    S --> A1
    S --> A2
    Ev -. evidence links .-> UI

    click Pathway "https://pathway.com" _blank
    click LandingAI "https://docs.landing.ai/ade/ade-overview" _blank
```

## Component Details

### 1. Document Sources
- **Contracts/LPAs/Side Letters**: PDF documents containing financial terms
- **Amendments & Riders**: Updates to existing contracts
- **Operational Data**: Real-time data from portfolio, CRM, and fund admin systems

### 2. Pathway Runtime
- **Live Ingestion**: Monitors file systems, emails, and data streams
- **Hybrid Index**: Combines BM25 and vector search for document retrieval
- **Streaming Validator**: Continuously validates data against policies

### 3. LandingAI ADE (DPT-2)
- **Structured Extraction**: Converts unstructured documents to structured data
- **Evidence Spans**: Links extracted data back to source locations
- **Table Processing**: Handles complex financial tables and matrices

### 4. O2A Service (Core Logic)
- **Obligation Ontology**: Normalizes contract terms into standard format
- **Policy Compiler**: Converts extracted data into enforceable rules
- **Drift Detector**: Identifies changes between contract versions
- **Policy Store**: Manages compiled policies and rules

### 5. Review & Actions
- **Analyst Dashboard**: Web interface for reviewing alerts and changes
- **Exports**: Generate reports for auditors and compliance
- **Webhooks**: Integrate with external systems (CRM, portfolio, Slack)

## Data Flow

1. **Document Ingestion**: New or updated documents are detected by Pathway
2. **Extraction**: LandingAI ADE extracts structured fields and evidence
3. **Normalization**: O2A service converts extracted data to standard ontology
4. **Policy Compilation**: Rules are generated from normalized data
5. **Validation**: Streaming validator checks operational data against policies
6. **Alerting**: Violations and changes trigger alerts and notifications
7. **Review**: Analysts review alerts through dashboard
8. **Action**: Alerts are resolved or escalated through webhooks

## Key Features

### Drift Detection
- Compares contract versions to identify changes
- Assesses risk impact of each change
- Provides evidence linking changes to source documents

### Policy Enforcement
- Converts contract terms into machine-readable rules
- Validates operational data against contract requirements
- Blocks or alerts on violations

### Evidence Tracking
- Links all extracted data back to source documents
- Provides page numbers, table cells, and text snippets
- Enables audit trails and compliance reporting

### Real-time Monitoring
- Continuous validation of operational data
- Immediate alerts for policy violations
- Integration with existing business systems

## Technology Stack

- **Pathway**: Real-time data processing and streaming
- **LandingAI ADE DPT-2**: Document extraction and parsing
- **FastAPI**: REST API and web services
- **PostgreSQL**: Data persistence
- **Redis**: Caching and job queues
- **Pydantic**: Data validation and serialization

## Security Considerations

- Webhook signature verification
- Encrypted data transmission
- Access control and authentication
- Audit logging and compliance reporting
