import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'next/searchparams';

interface ReportTemplate {
  id: number;
  name: string;
  fields: string[];
}

interface ReportGeneratorProps {
  templates: ReportTemplate[];
}

const ReportGenerator: React.FC<ReportGeneratorProps> = ({ templates }) => {
  const [selectedTemplate, setSelectedTemplate] = useState<ReportTemplate | null>(null);
  const [filters, setFilters] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [reportData, setReportData] = useState<any>(null);

  const [searchParams, setSearchParams] = useSearchParams();

  useEffect(() => {
    const params = searchParams;
    if (params) {
      setFilters({
        startDate: params.get('startDate'),
        endDate: params.get('endDate'),
        // Add other filter parameters as needed
      });
    }
  }, [searchParams]);

  const handleTemplateSelect = (template: ReportTemplate) => {
    setSelectedTemplate(template);
  };

  const generateReport = async () => {
    setLoading(true);
    setError(null);

    try {
      // Simulate data fetching - replace with your actual API call
      const data = await fetchData(filters, selectedTemplate?.id);
      setReportData(data);
    } catch (err: any) {
      setError(err.message || 'An error occurred while generating the report.');
    } finally {
      setLoading(false);
    }
  };

  const fetchData = async (filters: Record<string, any>, templateId: number) => {
    // Replace this with your actual data fetching logic
    await new Promise(resolve => setTimeout(resolve, 1000)); // Simulate network delay
    const data = {
      "data": [
        { "id": 1, "name": "Item A", "value": 10 },
        { "id": 2, "name": "Item B", "value": 20 },
        { "id": 3, "name": "Item C", "value": 30 }
      ]
    };
    return data;
  };

  return (
    <div className="report-generator w-full max-w-4xl mx-auto p-4">
      <h2 className="text-2xl font-bold mb-4">Report Generator</h2>

      {loading && <p className="text-center text-gray-300">Loading...</p>}

      {error && <p className="text-center text-red-500">{error}</p>}

      {!loading && !error && (
        <>
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">Select Template:</label>
            <select
              id="templateSelect"
              className="bg-gray-100 border border-gray-300 rounded-md text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 p-2"
              onChange={(e) => handleTemplateSelect(templates.find(t => t.id === parseInt(e.target.value))}
            >
              <option value="" disabled selected>Choose a template</option>
              {templates.map((template) => (
                <option key={template.id} value={template.id}>
                  {template.name}
                </option>
              ))}
            </select>
          </div>

          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">Filters:</label>
            <div className="flex">
              <input
                type="date"
                id="startDate"
                className="bg-gray-100 border border-gray-300 rounded-md text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 p-2 w-full"
                onChange={(e) => setFilters({...filters, startDate: e.target.value})}
              />
              <input
                type="date"
                id="endDate"
                className="bg-gray-100 border border-gray-300 rounded-md text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 p-2 w-full"
                onChange={(e) => setFilters({...filters, endDate: e.target.value})}
              />
            </div>
          </div>

          {reportData && (
            <pre className="bg-white p-4 rounded-md shadow-md">
              {JSON.stringify(reportData, null, 2)}
            </pre>
          )}
        </>
      )}
    </div>
  );
};

export default ReportGenerator;