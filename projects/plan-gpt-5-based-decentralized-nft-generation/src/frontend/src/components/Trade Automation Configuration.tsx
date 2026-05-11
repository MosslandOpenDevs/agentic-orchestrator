import React, { useState, useEffect } from 'react';
import { useToast } from 'react-toastify';

interface Rule {
  id: string;
  name: string;
  condition: string;
  action: string;
  riskLevel: number;
}

interface TradeAutomationConfigProps {
  initialRules?: Rule[];
}

const TradeAutomationConfig: React.FC<TradeAutomationConfigProps> = ({ initialRules = [] }) => {
  const [rules, setRules] = useState<Rule[]>(initialRules);
  const [newRule, setNewRule] = useState<Rule>({} as Rule);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const toast = useToast();

  useEffect(() => {
    // Simulate fetching rules from an API or database
    setTimeout(() => {
      setLoading(false);
    }, 1000);
  }, []);

  const handleRuleChange = (id: string, field: string, value: string) => {
    setRules(
      rules.map((rule) =>
        rule.id === id ? { ...rule, [field]: value } : rule
      )
    );
  };

  const handleAddRule = () => {
    if (!newRule.name || !newRule.condition || !newRule.action) {
      toast(`Please fill in all fields for the new rule`, { type: 'error' });
      return;
    }
    if (newRule.riskLevel < 1 || newRule.riskLevel > 5) {
      toast(`Risk level must be between 1 and 5`, { type: 'error' });
      return;
    }

    setRules([...rules, newRule]);
    setNewRule({} as Rule);
  };

  const handleRemoveRule = (id: string) => {
    setRules(rules.filter((rule) => rule.id !== id));
  };

  const handleUpdateRule = (rule: Rule) => {
    setRules(rules.map((r) => (r.id === rule.id ? rule : r)));
  };

  useEffect(() => {
    if (rules.length > 0) {
      // Simulate updating rules on the server
      setTimeout(() => {
        toast(`Rules updated successfully`, { type: 'success' });
      }, 500);
    }
  }, [rules]);

  if (loading) {
    return (
      <div className="bg-gray-100 p-4 rounded-lg shadow-md">
        <h2 className="text-lg font-semibold mb-4">Trade Automation Configuration</h2>
        <p className="text-gray-600">Loading rules...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-100 p-4 rounded-lg shadow-md">
        <h2 className="text-lg font-semibold mb-4">Error</h2>
        <p className="text-gray-600">Failed to load rules: {error}</p>
      </div>
    );
  }

  return (
    <div className="bg-gray-100 p-4 rounded-lg shadow-md w-full max-w-xl mx-auto">
      <h2 className="text-lg font-semibold mb-4">Trade Automation Rules</h2>
      <div className="mb-4">
        <input
          type="text"
          placeholder="Rule Name"
          value={newRule.name}
          onChange={(e) => setNewRule({...newRule, name: e.target.value})}
          className="w-full px-3 py-2 rounded-md border border-gray-300 focus:outline-none focus:border-blue-500"
          aria-label="Rule Name"
        />
      </div>
      <div className="mb-4">
        <input
          type="text"
          placeholder="Condition"
          value={newRule.condition}
          onChange={(e) => setNewRule({...newRule, condition: e.target.value})}
          className="w-full px-3 py-2 rounded-md border border-gray-300 focus:outline-none focus:border-blue-500"
          aria-label="Condition"
        />
      </div>
      <div className="mb-4">
        <input
          type="text"
          placeholder="Action"
          value={newRule.action}
          onChange={(e) => setNewRule({...newRule, action: e.target.value})}
          className="w-full px-3 py-2 rounded-md border border-gray-300 focus:outline-none focus:border-blue-500"
          aria-label="Action"
        />
      </div>
      <div className="mb-4">
        <input
          type="number"
          placeholder="Risk Level (1-5)"
          value={newRule.riskLevel}
          onChange={(e) => setNewRule({...newRule, riskLevel: parseInt(e.target.value, 10)})}
          className="w-full px-3 py-2 rounded-md border border-gray-300 focus:outline-none focus:border-blue-500"
          aria-label="Risk Level"
        />
      </div>
      <button
        onClick={handleAddRule}
        className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-md w-full max-w-sm"
        aria-label="Add Rule"
      >
        Add Rule
      </button>

      <div className="mt-4">
        {rules.map((rule) => (
          <div
            key={rule.id}
            className="flex items-center justify-between bg-gray-100 p-4 rounded-md mb-2"
            aria-label={`Rule: ${rule.name}`}
          >
            <div className="flex items-center">
              <input
                type="text"
                value={rule.name}
                onChange={(e) => handleRuleChange(rule.id, 'name', e.target.value)}
                className="w-1/2 px-2"
                aria-label={`Rule Name: ${rule.name}`}
              />
              <input
                type="text"
                value={rule.condition}
                onChange={(e) => handleRuleChange(rule.id, 'condition', e.target.value)}
                className="w-1/2 px-2"
                aria-label={`Condition: ${rule.condition}`}
              />
              <input
                type="text"
                value={rule.action}
                onChange={(e) => handleRuleChange(rule.id, 'action', e.target.value)}
                className="w-1/2 px-2"
                aria-label={`Action: ${rule.action}`}
              />
              <input
                type="number"
                value={rule.riskLevel}
                onChange={(e) => handleRuleChange(rule.id, 'riskLevel', e.target.value)}
                className="w-1/2 px-2"
                aria-label={`Risk Level: ${rule.riskLevel}`}
              />
            </div>
            <button onClick={() => handleRemoveRule(rule.id)} className="bg-red-500 hover:bg-red-700 text-white font-bold py-2 px-4 rounded-md">
              Remove
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};

export default TradeAutomationConfig;