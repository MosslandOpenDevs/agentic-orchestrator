import React, { useState, useEffect } from 'react';

interface ClaudeAssetPreviewProps {
  assetType: string;
  assetData: any;
  isLoading: boolean;
  onError: (error: Error) => void;
}

const ClaudeAssetPreview: React.FC<ClaudeAssetPreviewProps> = ({
  assetType,
  assetData,
  isLoading,
  onError,
}) => {
  const [previewContent, setPreviewContent] = useState('');

  useEffect(() => {
    if (assetData && assetData.content) {
      setPreviewContent(assetData.content);
    } else {
      setPreviewContent('');
    }
  }, [assetData]);

  if (isLoading) {
    return (
      <div className="bg-gray-100 p-4 rounded shadow-md flex items-center justify-center">
        Loading Claude Asset...
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-100 p-4 rounded shadow-md flex items-center justify-center">
        Error loading asset: {error.message}
        <button onClick={() => onError(error)}>Retry</button>
      </div>
    );
  }

  return (
    <div className="bg-gray-100 p-4 rounded shadow-md flex flex-col items-center">
      <div className="text-xl font-bold mb-4">
        {assetType} Preview
      </div>
      <div className="p-4" aria-label={`Preview of ${assetType} asset`}>
        {previewContent ? (
          <div className="text-lg leading-relaxed">{previewContent}</div>
        ) : (
          <p>No asset content available.</p>
        )}
      </div>
    </div>
  );
};

export default ClaudeAssetPreview;