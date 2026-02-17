import React from 'react';
import { ThemeCustomizer } from './ThemeCustomizer';
import { BlockchainToolbox } from './BlockchainToolbox';

const Dashboard: React.FC = () => {
  const [isDarkMode, setIsDarkMode] = React.useState(true);

  return (
    <div className={`min-h-screen flex flex-col ${isDarkMode ? 'bg-gray-900 text-white' : 'bg-white text-black'} transition-colors duration-300`}>
      {/* Header */}
      <header className="flex items-center justify-between px-4 py-2">
        <h1 className="text-xl font-bold">Dark Islands Enhanced</h1>
        <button
          onClick={() => setIsDarkMode(!isDarkMode)}
          className={`px-3 py-1 rounded ${isDarkMode ? 'bg-gray-800' : 'bg-blue-500'} text-white`}
        >
          {isDarkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
        </button>
      </header>

      {/* Main Content Area */}
      <main className="flex flex-grow">
        {/* Sidebar */}
        <aside className={`w-64 bg-gray-800 text-white p-4 ${isDarkMode ? '' : 'hidden md:block'}`}>
          <nav className="space-y-2">
            <a href="#theme-customizer" className="block py-2 px-3 rounded hover:bg-gray-700">Theme Customizer</a>
            <a href="#blockchain-toolbox" className="block py-2 px-3 rounded hover:bg-gray-700">Blockchain Toolbox</a>
          </nav>
        </aside>

        {/* Content Area */}
        <div className={`flex-grow p-4`}>
          <section id="theme-customizer">
            <h2 className="text-xl font-semibold mb-4">Theme Customizer</h2>
            <ThemeCustomizer />
          </section>
          
          <section id="blockchain-toolbox" className="mt-8">
            <h2 className="text-xl font-semibold mb-4">Blockchain Toolbox</h2>
            <BlockchainToolbox />
          </section>
        </div>
      </main>

      {/* Footer */}
      <footer className={`flex items-center justify-between px-4 py-2 ${isDarkMode ? 'bg-gray-800 text-white' : 'bg-gray-100'} mt-auto`}>
        <p>&copy; 2023 Dark Islands Enhanced</p>
        <nav className="space-x-2">
          <a href="#" className={`hover:underline ${isDarkMode ? '' : 'text-black'}`}>Privacy Policy</a>
          <a href="#" className={`hover:underline ${isDarkMode ? '' : 'text-black'}`}>Terms of Service</a>
        </nav>
      </footer>
    </div>
  );
};

export default Dashboard;