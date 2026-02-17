import React, { useState } from 'react';
import { twMerge } from 'tailwind-merge';

interface ThemeCustomizerProps {
  initialColor?: string;
  initialFontSize?: number;
}

const ThemeCustomizer: React.FC<ThemeCustomizerProps> = ({ initialColor = '#000', initialFontSize = 16 }) => {
  const [color, setColor] = useState(initialColor);
  const [fontSize, setFontSize] = useState(initialFontSize);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleColorChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const newColor = event.target.value;
    setColor(newColor);
    localStorage.setItem('customThemeColor', newColor);
  };

  const handleFontSizeChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const newFontSize = parseInt(event.target.value, 10);
    setFontSize(newFontSize);
    localStorage.setItem('customThemeFontSize', newFontSize.toString());
  };

  return (
    <div className="p-4 bg-gray-800 text-white rounded-lg shadow-md w-full max-w-sm">
      {loading && <p>Loading...</p>}
      {error && <p>Error: {error}</p>}
      <label htmlFor="color" className="block mb-2">Custom Color:</label>
      <input
        id="color"
        type="color"
        value={color}
        onChange={handleColorChange}
        aria-label="Select custom color"
        className="w-full p-1 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
      />
      <label htmlFor="fontSize" className="block mt-4 mb-2">Font Size:</label>
      <input
        id="fontSize"
        type="range"
        min={12}
        max={36}
        value={fontSize}
        onChange={handleFontSizeChange}
        aria-label="Adjust font size"
        className="w-full p-1 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
      />
      <div
        style={{ color, fontSize }}
        className={twMerge('mt-4', 'p-2', 'rounded-lg')}
        aria-label="Preview of custom theme settings"
      >
        Preview Text with Custom Theme Settings
      </div>
    </div>
  );
};

export default ThemeCustomizer;