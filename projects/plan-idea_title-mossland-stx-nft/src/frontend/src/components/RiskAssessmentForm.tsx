import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hookform';
import { useToast } from 'react-toastify';

interface RiskAssessmentFormProps {
  initialData?: any; // Allow passing initial data for pre-filled values
}

interface RiskProfile {
  riskTolerance: number;
  investmentHorizon: number;
  financialGoals: string;
}

const RiskAssessmentForm: React.FC<RiskAssessmentFormProps> = ({ initialData }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const toast = useToast();

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm({
    defaultValues: initialData,
    resolver: (data) => data,
  });

  const onSubmit = async (data: RiskProfile) => {
    setLoading(true);
    setError(null);

    try {
      // Simulate a risk assessment calculation
      await new Promise((resolve) => setTimeout(resolve, 1000));

      // Simulate success
      toast.success('Risk assessment complete!', {
        position: 'top-right',
        autoClose: 5000,
        style: {
          backgroundColor: '#e9ecef',
          color: '#333',
        },
      });

      reset();
    } catch (err: any) {
      setError(err.message || 'An error occurred');
      toast.error(err.message, {
        position: 'top-right',
        autoClose: 5000,
        style: {
          backgroundColor: '#e9ecef',
          color: '#333',
        },
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (error) {
      // Handle error state - potentially show a more detailed error message
      toast.error(error, {
        position: 'top-right',
        autoClose: 5000,
        style: {
          backgroundColor: '#e9ecef',
          color: '#333',
        },
      });
    }
  }, [error]);

  return (
    <div className="max-w-md mx-auto p-6 bg-white rounded-lg shadow-md overflow-hidden">
      <h2 className="text-xl font-semibold mb-4">Risk Assessment</h2>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        {/* Risk Tolerance Levels */}
        <div className="mb-4">
          <label className="text-base font-medium text-gray-700 mb-1">Risk Tolerance Level:</label>
          <div className="flex items-center">
            <label className="mr-2">
              <input
                type="radio"
                name="riskTolerance"
                value="low"
                checked={initialData?.riskTolerance === 'low'}
                className="mr-2"
                ref={register({ required: true })}
              />
              Low
            </label>
            <label>
              <input
                type="radio"
                name="riskTolerance"
                value="medium"
                checked={initialData?.riskTolerance === 'medium'}
                className="mr-2"
                ref={register({ required: true })}
              />
              Medium
            </label>
            <label>
              <input
                type="radio"
                name="riskTolerance"
                value="high"
                checked={initialData?.riskTolerance === 'high'}
                className="mr-2"
                ref={register({ required: true })}
              />
              High
            </label>
          </div>
        </div>

        {/* Investment Horizon */}
        <div className="mb-4">
          <label className="text-base font-medium text-gray-700 mb-1">Investment Horizon (Years):</label>
          <input
            type="number"
            name="investmentHorizon"
            min="1"
            max="20"
            placeholder="Enter investment horizon"
            className="input input-bordered rounded-md"
            ref={register({ required: true })}
          />
        </div>

        {/* Financial Goals */}
        <div className="mb-4">
          <label className="text-base font-medium text-gray-700 mb-1">Financial Goals:</label>
          <input
            type="text"
            name="financialGoals"
            placeholder="Enter your financial goals"
            className="input input-bordered rounded-md"
            ref={register({ required: true })}
          />
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-md"
          disabled={loading}
        >
          {loading ? 'Calculating...' : 'Submit'}
        </button>
      </form>
    </div>
  );
};

export default RiskAssessmentForm;