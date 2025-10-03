import React, { useState, useMemo } from 'react';
import * as yaml from 'js-yaml';
import { saveAs } from 'file-saver';
import { Download, Copy, Check } from 'lucide-react';

interface YamlData {
  [key: string]: any;
}

interface YamlToTablesProps {
  className?: string;
}

export const YamlToTables: React.FC<YamlToTablesProps> = ({ className = '' }) => {
  const [yamlInput, setYamlInput] = useState(`policy_id: 0f0fd9a8-a712-43b3-b16f-861cbdef5a75
name: Policy from omnibus_final_policy
version: 1.0.0
description: Compiled policy with 5 rules
ontology_version: "o2a.v0.2"
source_documents:
  - name: Omnibus_Financial_Agreement_v1.pdf
    hash: "demo"

rules:
  # Fund-wide management fee 1.75% (decimal)
  - id: R_2b2d6424b6
    type: fee.rate_percent
    basis: management_fee
    applies_to: ALL_INVESTORS
    expected_value: 0.0175
    effective_period: 
      start: "2025-10-03T14:34:37.950266Z"
      end: null
    evidence:
      doc: Omnibus_Financial_Agreement_v1.pdf
      page: 1
      text_snippet: "Management fee shall be one point seven five percent (1.75%) of Net Asset Value (NAV), billed quarterly in advance."
    severity: HIGH
    enforcement:
      when: on_fee_calculation_post
      action: alert_if_mismatch

  # Reporting: quarterly reports within 5 business days
  - id: R_7165ec1b2e
    type: reporting.deadline_days
    basis: reporting_requirement
    applies_to: ALL_INVESTORS
    expected_value: 5
    effective_period:
      start: "2025-10-03T14:34:37.950266Z"
      end: null
    evidence:
      doc: Omnibus_Financial_Agreement_v1.pdf
      page: 1
      text_snippet: "Quarterly reports shall be delivered within five (5) business days following quarter end."
    severity: MEDIUM
    enforcement:
      when: on_report_generated
      action: alert_if_missed

  # MFN: threshold is 10 bps (separate from notice deadline)
  - id: R_bf5b628ba2
    type: mfn.threshold_bps
    basis: mfn
    applies_to: ALL_INVESTORS
    expected_value: 10
    effective_period:
      start: "2025-10-03T14:34:37.950266Z"
      end: null
    evidence:
      doc: Omnibus_Financial_Agreement_v1.pdf
      page: 1
      text_snippet: "The GP shall notify LPs of any side letter granting economic terms more favorable by ≥10 bps within ten (10) days of execution."
    severity: LOW
    enforcement:
      when: on_sideletter_ingested
      action: alert_if_mismatch

  # MFN: notice due within 10 days (deadline rule)
  - id: R_8b6c7fc8b3
    type: mfn.notice_deadline_days
    basis: mfn
    applies_to: ALL_INVESTORS
    expected_value: 10
    effective_period:
      start: "2025-10-03T14:34:37.950266Z"
      end: null
    evidence:
      doc: Omnibus_Financial_Agreement_v1.pdf
      page: 1
      text_snippet: "The GP shall notify LPs of any side letter granting economic terms more favorable by ≥10 bps within ten (10) days of execution."
    severity: LOW
    enforcement:
      when: on_sideletter_ingested
      action: alert_if_missed

  # Interest rate 7% — include if you validate interest
  - id: R_8c46531c3d
    type: interest.rate_percent
    basis: interest_rate
    applies_to: ALL_INVESTORS
    expected_value: 0.07
    effective_period:
      start: "2025-10-03T14:34:37.950266Z"
      end: null
    evidence:
      doc: Omnibus_Financial_Agreement_v1.pdf
      page: 1
      text_snippet: "Interest Rate: 7.00% fixed until maturity. Interest shall be calculated on a 30/360 basis."
    severity: HIGH
    enforcement:
      when: on_interest_post
      action: alert_if_mismatch`);
  const [parsedData, setParsedData] = useState<YamlData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const handleYamlChange = (value: string) => {
    setYamlInput(value);
    setError(null);
    
    if (!value.trim()) {
      setParsedData(null);
      return;
    }

    try {
      const data = yaml.load(value, { schema: yaml.FAILSAFE_SCHEMA }) as YamlData;
      setParsedData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Invalid YAML');
      setParsedData(null);
    }
  };

  const metadata = useMemo(() => {
    if (!parsedData) return null;
    
    const { rules, ...meta } = parsedData;
    return meta;
  }, [parsedData]);

  const rules = useMemo(() => {
    if (!parsedData?.rules || !Array.isArray(parsedData.rules)) return [];
    return parsedData.rules;
  }, [parsedData]);

  const ruleColumns = useMemo(() => {
    if (rules.length === 0) return [];
    
    const allKeys = new Set<string>();
    rules.forEach(rule => {
      if (typeof rule === 'object' && rule !== null) {
        Object.keys(rule).forEach(key => allKeys.add(key));
      }
    });
    
    return Array.from(allKeys);
  }, [rules]);

  const exportToHtml = () => {
    if (!parsedData) return;
    
    const html = `
<!DOCTYPE html>
<html>
<head>
    <title>Policy Export</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        table { border-collapse: collapse; width: 100%; margin-bottom: 20px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        .metadata { margin-bottom: 30px; }
        h2 { color: #333; }
    </style>
</head>
<body>
    <h1>Policy Export</h1>
    
    <div class="metadata">
        <h2>Metadata</h2>
        <table>
            ${metadata ? Object.entries(metadata).map(([key, value]) => `
                <tr>
                    <td><strong>${key}</strong></td>
                    <td>${typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value)}</td>
                </tr>
            `).join('') : '<tr><td colspan="2">No metadata</td></tr>'}
        </table>
    </div>
    
    <h2>Rules (${rules.length})</h2>
    <table>
        <thead>
            <tr>
                ${ruleColumns.map(col => `<th>${col}</th>`).join('')}
            </tr>
        </thead>
        <tbody>
            ${rules.map(rule => `
                <tr>
                    ${ruleColumns.map(col => `
                        <td>${typeof rule[col] === 'object' ? JSON.stringify(rule[col], null, 2) : String(rule[col] || '')}</td>
                    `).join('')}
                </tr>
            `).join('')}
        </tbody>
    </table>
</body>
</html>`;
    
    const blob = new Blob([html], { type: 'text/html;charset=utf-8' });
    saveAs(blob, 'policy-export.html');
  };

  const exportToCsv = () => {
    if (rules.length === 0) return;
    
    const csvContent = [
      ruleColumns.join(','),
      ...rules.map(rule => 
        ruleColumns.map(col => {
          const value = rule[col];
          if (typeof value === 'object') {
            return `"${JSON.stringify(value).replace(/"/g, '""')}"`;
          }
          return `"${String(value || '').replace(/"/g, '""')}"`;
        }).join(',')
      )
    ].join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8' });
    saveAs(blob, 'rules.csv');
  };

  const copyToClipboard = async () => {
    if (!yamlInput) return;
    
    try {
      await navigator.clipboard.writeText(yamlInput);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  return (
    <div className={`max-w-7xl mx-auto p-6 space-y-6 ${className}`}>
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-4">YAML Policy Viewer</h1>
        
        {/* YAML Input and Tables Side by Side */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          {/* Left: YAML Input */}
          <div>
            <label htmlFor="yaml-input" className="block text-sm font-medium text-gray-700 mb-2">
              YAML Policy:
            </label>
            <textarea
              id="yaml-input"
              value={yamlInput}
              onChange={(e) => handleYamlChange(e.target.value)}
              placeholder="Paste your YAML policy here..."
              className="w-full h-96 p-4 border border-gray-300 rounded-md font-mono text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
            {error && (
              <div className="mt-2 text-red-600 text-sm">
                Error: {error}
              </div>
            )}
          </div>

          {/* Right: Parsed Tables */}
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-4">Parsed Tables:</h3>
            {!parsedData ? (
              <div className="h-96 flex items-center justify-center border-2 border-dashed border-gray-300 rounded-md">
                <div className="text-center">
                  <div className="text-gray-400 mb-2">
                    <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <p className="text-sm text-gray-500">Enter valid YAML to see tables</p>
                </div>
              </div>
            ) : (
              <div className="h-96 overflow-y-auto space-y-4">
                {/* Metadata Table */}
                {metadata && Object.keys(metadata).length > 0 && (
                  <div>
                    <h4 className="text-sm font-semibold text-gray-800 mb-2">Metadata</h4>
                    <div className="overflow-x-auto">
                      <table className="min-w-full bg-white border border-gray-200 rounded-lg text-xs">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="px-2 py-1 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-b">
                              Key
                            </th>
                            <th className="px-2 py-1 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-b">
                              Value
                            </th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200">
                          {Object.entries(metadata).map(([key, value]) => (
                            <tr key={key} className="hover:bg-gray-50">
                              <td className="px-2 py-1 text-xs font-medium text-gray-900 border-r">
                                {key}
                              </td>
                              <td className="px-2 py-1 text-xs text-gray-700">
                                {typeof value === 'object' ? (
                                  <pre className="whitespace-pre-wrap text-xs bg-gray-100 p-1 rounded">
                                    {JSON.stringify(value, null, 2)}
                                  </pre>
                                ) : (
                                  String(value)
                                )}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* Rules Table */}
                {rules.length > 0 && (
                  <div>
                    <h4 className="text-sm font-semibold text-gray-800 mb-2">
                      Rules ({rules.length})
                    </h4>
                    <div className="overflow-x-auto">
                      <table className="min-w-full bg-white border border-gray-200 rounded-lg text-xs">
                        <thead className="bg-gray-50">
                          <tr>
                            {ruleColumns.map((col) => (
                              <th
                                key={col}
                                className="px-2 py-1 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-b"
                              >
                                {col}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200">
                          {rules.map((rule, index) => (
                            <tr key={index} className="hover:bg-gray-50">
                              {ruleColumns.map((col) => (
                                <td key={col} className="px-2 py-1 text-xs text-gray-700 border-r last:border-r-0">
                                  {typeof rule[col] === 'object' ? (
                                    <pre className="whitespace-pre-wrap text-xs bg-gray-100 p-1 rounded">
                                      {JSON.stringify(rule[col], null, 2)}
                                    </pre>
                                  ) : (
                                    String(rule[col] || '')
                                  )}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-3 mb-6">
          <button
            onClick={copyToClipboard}
            disabled={!yamlInput}
            className="flex items-center gap-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-md disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
            {copied ? 'Copied!' : 'Copy YAML'}
          </button>
          
          <button
            onClick={exportToHtml}
            disabled={!parsedData}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Download className="w-4 h-4" />
            Export HTML
          </button>
          
          <button
            onClick={exportToCsv}
            disabled={rules.length === 0}
            className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-md disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Download className="w-4 h-4" />
            Rules CSV
          </button>
        </div>

      </div>
    </div>
  );
};

export default YamlToTables;
