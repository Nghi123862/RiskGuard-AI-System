// File: src/App.js (Phiên bản Ultimate: Hỗ trợ URL + File Upload)
import React, { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import { 
  Layout, Menu, Table, Tag, Button, Card, Row, Col, Statistic, 
  message, Modal, Input, Space, Typography, List, Tabs, Upload, Empty
} from 'antd';
import {
  DashboardOutlined, ScanOutlined, SafetyCertificateOutlined, 
  WarningOutlined, ReloadOutlined, BugOutlined, EyeOutlined,
  FileTextOutlined, LinkOutlined, InboxOutlined
} from '@ant-design/icons';
import { 
  PieChart, Pie, Cell, Tooltip as RechartsTooltip, Legend, ResponsiveContainer 
} from 'recharts';
import moment from 'moment';

const { Header, Content, Footer, Sider } = Layout;
const { Title, Text, Paragraph } = Typography;
const { Search } = Input;
const { Dragger } = Upload;

// --- CẤU HÌNH ---
const API_URL = "http://localhost:8000/api/v1";
const COLORS = ['#52c41a', '#faad14', '#f5222d']; // Xanh (Safe), Vàng (Warning), Đỏ (Dangerous)

const App = () => {
  // --- STATE DỮ LIỆU ---
  const [data, setData] = useState([]); 
  const [loading, setLoading] = useState(false);
  const [searchText, setSearchText] = useState("");

  // --- STATE MODAL QUÉT MỚI ---
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [activeTab, setActiveTab] = useState('1'); // 1: URL, 2: File
  const [urlInput, setUrlInput] = useState(""); 
  const [fileList, setFileList] = useState([]);
  const [uploading, setUploading] = useState(false);

  // --- STATE MODAL CHI TIẾT ---
  const [detailModalOpen, setDetailModalOpen] = useState(false);
  const [selectedRecord, setSelectedRecord] = useState(null);

  // --- 1. HÀM LẤY DỮ LIỆU TỪ MONGODB ---
  const fetchData = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_URL}/results`);
      setData(response.data);
    } catch (error) {
      message.error("Không thể kết nối tới Server Backend!");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  // --- 2. HÀM XỬ LÝ QUÉT (URL HOẶC FILE) ---
  const handleScanSubmit = async () => {
    // TRƯỜNG HỢP 1: QUÉT URL
    if (activeTab === '1') {
      if (!urlInput) return message.warning("Vui lòng nhập URL!");
      try {
        await axios.post(`${API_URL}/scan/url`, { url: urlInput });
        message.success("Đã gửi URL đi quét!");
        resetAndCloseModal();
      } catch (error) {
        message.error("Gửi URL thất bại: " + error.message);
      }
    } 
    // TRƯỜNG HỢP 2: UPLOAD FILE
    else {
      if (fileList.length === 0) return message.warning("Vui lòng chọn file!");
      
      const formData = new FormData();
      formData.append('file', fileList[0]); // Lấy file đầu tiên

      setUploading(true);
      try {
        await axios.post(`${API_URL}/scan/file`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
        message.success("Upload file thành công! Hệ thống đang phân tích...");
        resetAndCloseModal();
      } catch (error) {
        message.error("Lỗi upload file!");
      } finally {
        setUploading(false);
      }
    }
  };

  const resetAndCloseModal = () => {
    setIsModalOpen(false);
    setUrlInput("");
    setFileList([]);
    setTimeout(fetchData, 3000); // Tự động load lại sau 3s
  };

  // --- 3. CHUẨN BỊ DỮ LIỆU BIỂU ĐỒ ---
  const chartData = useMemo(() => {
    const safe = data.filter(d => d.analysis?.label === 'SAFE').length;
    const warning = data.filter(d => d.analysis?.label === 'WARNING').length;
    const dangerous = data.filter(d => d.analysis?.label === 'DANGEROUS').length;
    return [
      { name: 'An toàn', value: safe },
      { name: 'Cảnh báo', value: warning },
      { name: 'Nguy hiểm', value: dangerous },
    ];
  }, [data]);

  // Lọc dữ liệu tìm kiếm
  const filteredData = data.filter(item => 
    item.url.toLowerCase().includes(searchText.toLowerCase()) || 
    (item.page_title && item.page_title.toLowerCase().includes(searchText.toLowerCase()))
  );

  // --- 4. CẤU HÌNH CỘT BẢNG ---
  const columns = [
    {
      title: 'Loại', key: 'type', width: 80, align: 'center',
      render: (_, record) => record.url.startsWith('http') ? <LinkOutlined style={{color: '#1890ff'}} /> : <FileTextOutlined style={{color: '#fa8c16'}} />
    },
    {
      title: 'Trạng thái', dataIndex: ['analysis', 'label'], key: 'label', width: 130,
      render: (label) => {
        let color = label === 'DANGEROUS' ? 'red' : label === 'SAFE' ? 'success' : 'warning';
        let icon = label === 'DANGEROUS' ? <BugOutlined /> : <SafetyCertificateOutlined />;
        return <Tag icon={icon} color={color}>{label || "PENDING"}</Tag>;
      },
    },
    {
      title: 'Đối tượng quét (Web/File)', dataIndex: 'url', key: 'url',
      render: (text, record) => (
        <div>
          <Text strong style={{display: 'block', maxWidth: 400}} ellipsis={true}>
             {record.page_title || "Đang xử lý..."}
          </Text>
          <Text type="secondary" style={{fontSize: 12}}>{text}</Text>
        </div>
      ),
    },
    {
      title: 'Rủi ro', dataIndex: ['analysis', 'risk_score'], key: 'risk_score', 
      sorter: (a, b) => (a.analysis?.risk_score || 0) - (b.analysis?.risk_score || 0),
      render: (score) => <b style={{color: score > 50 ? 'red' : 'green'}}>{score}/100</b>
    },
    {
      title: 'Thời gian', dataIndex: 'scanned_at', key: 'scanned_at', width: 160,
      render: (t) => moment(t).format("HH:mm DD/MM")
    },
    {
      title: 'Hành động', key: 'action', width: 100,
      render: (_, record) => (
        <Button size="small" icon={<EyeOutlined />} onClick={() => { setSelectedRecord(record); setDetailModalOpen(true); }}>
          Xem
        </Button>
      ),
    },
  ];

  // Cấu hình Tabs trong Modal
  const tabItems = [
    {
      key: '1', label: <span><LinkOutlined /> Quét URL Website</span>,
      children: (
        <div style={{padding: '20px 0'}}>
          <Input size="large" prefix={<LinkOutlined />} placeholder="Nhập địa chỉ (VD: https://dantri.com.vn)" value={urlInput} onChange={e => setUrlInput(e.target.value)} />
          <div style={{marginTop: 10, color: '#888'}}>Hệ thống sẽ tự động Crawl và phân tích nội dung trang web.</div>
        </div>
      )
    },
    {
      key: '2', label: <span><FileTextOutlined /> Quét Tệp tin</span>,
      children: (
        <div style={{padding: '10px 0'}}>
          <Dragger 
            fileList={fileList}
            beforeUpload={(file) => { setFileList([file]); return false; }} 
            onRemove={() => setFileList([])}
            maxCount={1}
          >
            <p className="ant-upload-drag-icon"><InboxOutlined /></p>
            <p className="ant-upload-text">Nhấp hoặc kéo thả file vào đây</p>
            <p className="ant-upload-hint">Hỗ trợ: .PDF, .DOCX, .TXT (Tối đa 10MB)</p>
          </Dragger>
        </div>
      )
    }
  ];

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider width={240} theme="dark" collapsible>
        <div style={{ padding: '20px', textAlign: 'center', color: 'white', fontSize: 18, fontWeight: 'bold' }}>
          🛡️ RiskGuard AI
        </div>
        <Menu theme="dark" defaultSelectedKeys={['1']} mode="inline" items={[
            { key: '1', icon: <DashboardOutlined />, label: 'Dashboard Giám sát' },
        ]} />
      </Sider>

      <Layout className="site-layout" style={{background: '#f0f2f5'}}>
        <Header style={{ background: '#fff', padding: '0 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Title level={4} style={{margin: 0}}>Trung tâm Kiểm soát Rủi ro Nội dung</Title>
          <Space>
             <Button icon={<ReloadOutlined />} onClick={fetchData}>Làm mới</Button>
             <Button type="primary" size="large" icon={<ScanOutlined />} onClick={() => setIsModalOpen(true)}>QUÉT MỚI</Button>
          </Space>
        </Header>

        <Content style={{ margin: '24px' }}>
          {/* 1. THỐNG KÊ */}
          <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
             <Col span={6}>
               <Card hoverable><Statistic title="Tổng lượt quét" value={data.length} prefix={<ScanOutlined />} /></Card>
             </Col>
             <Col span={6}>
               <Card hoverable><Statistic title="Nội dung Nguy hiểm" value={chartData[2].value} valueStyle={{ color: '#cf1322' }} prefix={<BugOutlined />} /></Card>
             </Col>
             <Col span={12}>
                <Card title="Tỷ lệ Rủi ro" bodyStyle={{padding: 0, height: 120}}>
                   <div style={{display: 'flex', height: '100%'}}>
                      <div style={{flex: 1}}>
                        <ResponsiveContainer>
                          <PieChart>
                            <Pie data={chartData} cx="50%" cy="50%" innerRadius={35} outerRadius={50} paddingAngle={2} dataKey="value">
                              {chartData.map((entry, index) => <Cell key={`cell-${index}`} fill={COLORS[index]} />)}
                            </Pie>
                            <RechartsTooltip />
                          </PieChart>
                        </ResponsiveContainer>
                      </div>
                      <div style={{flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center', fontSize: 12}}>
                         <div><Tag color="#52c41a">●</Tag> An toàn: {chartData[0].value}</div>
                         <div style={{marginTop: 5}}><Tag color="#faad14">●</Tag> Cảnh báo: {chartData[1].value}</div>
                         <div style={{marginTop: 5}}><Tag color="#f5222d">●</Tag> Nguy hiểm: {chartData[2].value}</div>
                      </div>
                   </div>
                </Card>
             </Col>
          </Row>

          {/* 2. BẢNG DỮ LIỆU */}
          <Card title="Dữ liệu giám sát thời gian thực" extra={<Search placeholder="Tìm kiếm..." onSearch={v => setSearchText(v)} onChange={e => setSearchText(e.target.value)} style={{ width: 250 }} />}>
             <Table loading={loading} columns={columns} dataSource={filteredData} rowKey="request_id" pagination={{ pageSize: 6 }} />
          </Card>
        </Content>
        <Footer style={{ textAlign: 'center' }}>RiskGuard System ©2025 - Powered by PhoBERT AI & Kafka</Footer>

        {/* --- MODAL 1: QUÉT MỚI (TAB URL / FILE) --- */}
        <Modal title="Tạo yêu cầu quét mới" open={isModalOpen} onCancel={() => setIsModalOpen(false)} 
           footer={[
             <Button key="back" onClick={() => setIsModalOpen(false)}>Hủy</Button>,
             <Button key="submit" type="primary" loading={uploading} onClick={handleScanSubmit}>BẮT ĐẦU QUÉT</Button>
           ]}
        >
           <Tabs defaultActiveKey="1" items={tabItems} onChange={key => setActiveTab(key)} />
        </Modal>

        {/* --- MODAL 2: CHI TIẾT --- */}
        <Modal title="Chi tiết Phân tích Rủi ro" open={detailModalOpen} onCancel={() => setDetailModalOpen(false)} footer={null} width={800}>
           {selectedRecord ? (
             <div>
                <Row gutter={16}>
                  <Col span={12}>
                     <Card size="small" title="Kết quả AI">
                        <div style={{textAlign: 'center', padding: 10}}>
                           <Title level={2} style={{color: selectedRecord.analysis?.label === 'DANGEROUS' ? '#f5222d' : '#52c41a', margin: 0}}>
                              {selectedRecord.analysis?.label}
                           </Title>
                           <Text>Điểm rủi ro: {selectedRecord.analysis?.risk_score}/100</Text>
                           <div style={{marginTop: 10}}>Model: <Tag>{selectedRecord.analysis?.model_used || "PhoBERT"}</Tag></div>
                        </div>
                     </Card>
                  </Col>
                  <Col span={12}>
                     <Card size="small" title="Từ khóa phát hiện">
                        {selectedRecord.analysis?.detected_keywords?.length > 0 ? (
                           selectedRecord.analysis.detected_keywords.map(k => <Tag color="volcano" key={k} style={{marginBottom: 5, fontSize: 14}}>{k.toUpperCase()}</Tag>)
                        ) : <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="Không tìm thấy từ khóa xấu" />}
                     </Card>
                  </Col>
                </Row>
                <div style={{marginTop: 20}}>
                   <Text strong>Trích xuất nội dung (500 ký tự đầu):</Text>
                   <div style={{marginTop: 5, padding: 15, background: '#f5f5f5', borderRadius: 5, maxHeight: 200, overflowY: 'auto', border: '1px solid #d9d9d9'}}>
                      {selectedRecord.content_preview}
                   </div>
                </div>
             </div>
           ) : <div />}
        </Modal>

      </Layout>
    </Layout>
  );
};

export default App;