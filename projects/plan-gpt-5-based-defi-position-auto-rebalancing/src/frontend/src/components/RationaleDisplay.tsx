import React, { useState, useEffect } from 'react';

interface RationaleDisplayProps {
  rationaleText?: string;
  timestamp?: string;
  isLoading?: boolean;
  error?: string;
}

const RationaleDisplay: React.FC<RationaleDisplayProps> = ({
  rationaleText,
  timestamp,
  isLoading = false,
  error,
}) => {
  const [displayText, setDisplayText] = useState<string>('');
  const [errorState, setErrorState] = useState<string>('');

  useEffect(() => {
    if (rationaleText) {
      setDisplayText(rationaleText);
      setErrorState('');
    } else {
      setDisplayText('');
      setErrorState('');
    }
  }, [rationaleText]);

  useEffect(() => {
    if (error) {
      setErrorState(error);
    } else {
      setErrorState('');
    }
  }, [error]);

  return (
    <div
      className="bg-white rounded-lg shadow-md p-6 flex flex-col items-center w-full max-w-lg"
      aria-label="ChatGPT Rationale Display"
      role="alert"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
        }
      }}
    >
      {isLoading && (
        <div className="text-center mt-4">
          <p>Loading rationale...</p>
        </div>
      )}

      {error && (
        <div className="mt-4 text-red-500">
          {error}
        </div>
      )}

      <div className="mt-4 text-lg font-medium">Rationale</div>
      {displayText && (
        <div className="mt-2 text-gray-700">{displayText}</div>
      )}

      {timestamp && (
        <div className="mt-4 font-small text-gray-600">
          Generated at: {timestamp}
        </div>
      )}
    </div>
  );
};

export default RationaleDisplay;