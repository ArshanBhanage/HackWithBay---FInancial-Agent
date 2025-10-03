import React from 'react';
import YamlToTables from '../components/YamlToTables';

const YamlViewer: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      <YamlToTables />
    </div>
  );
};

export default YamlViewer;
