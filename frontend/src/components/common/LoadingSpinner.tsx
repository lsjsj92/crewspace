import React from 'react';
import { Spin } from 'antd';

const LoadingSpinner: React.FC = () => {
  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%', minHeight: '200px' }}>
      <Spin size="large" />
    </div>
  );
};

export default LoadingSpinner;
