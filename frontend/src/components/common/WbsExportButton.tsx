import React, { useState } from 'react';
import { Button, message } from 'antd';
import { FileExcelOutlined } from '@ant-design/icons';
import { downloadProjectWbs } from '@/api/cards';

interface WbsExportButtonProps {
  projectId: string;
  projectName: string;
}

// Epic별 시트로 구성된 WBS Excel 파일을 다운로드하는 버튼
const WbsExportButton: React.FC<WbsExportButtonProps> = ({ projectId, projectName }) => {
  const [downloading, setDownloading] = useState(false);

  const handleDownload = async () => {
    setDownloading(true);
    try {
      await downloadProjectWbs(projectId, projectName);
    } catch {
      message.error('WBS 다운로드에 실패했습니다');
    } finally {
      setDownloading(false);
    }
  };

  return (
    <Button icon={<FileExcelOutlined />} loading={downloading} onClick={handleDownload}>
      WBS 다운로드
    </Button>
  );
};

export default WbsExportButton;
