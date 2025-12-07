// File: src/App.js (Phiên bản Ultimate: FULL TÍNH NĂNG + LOGIN + PDF + HIGHLIGHT + VIDEO)
import ChatBox from './ChatBox';
import React, { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
// Gộp import từ antd để code gọn gàng hơn
import { 
  Layout, Menu, Table, Tag, Button, Card, Row, Col, Statistic, 
  message, Modal, Input, Space, Typography, Tabs, Upload, Empty, Spin, Popconfirm,
  ConfigProvider, theme, Switch
} from 'antd';
// Gộp import icon
import {
  DashboardOutlined, ScanOutlined, 
  BugOutlined, EyeOutlined,
  FileTextOutlined, LinkOutlined, InboxOutlined, DownloadOutlined, LogoutOutlined, ReloadOutlined ,DeleteOutlined, MessageOutlined
} from '@ant-design/icons';
// Import thư viện biểu đồ
import { 
  PieChart, Pie, Cell, Tooltip as RechartsTooltip, ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Legend 
} from 'recharts';
import moment from 'moment';
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';
import Highlighter from "react-highlight-words";

import Login from './Login'; // Đảm bảo file Login.js đã có

const { Header, Content, Footer, Sider } = Layout;
const { Title, Text } = Typography;
const { Search } = Input;
const { Dragger } = Upload;

const API_URL = "http://localhost:8000/api/v1";
const COLORS = ['#52c41a', '#faad14', '#f5222d']; 

const App = () => {
  // --- STATE GIAO DIỆN (DARK MODE) ---
  const [isDarkMode, setIsDarkMode] = useState(false);
  const { defaultAlgorithm, darkAlgorithm } = theme;

  // --- STATE DỮ LIỆU & LOGIN ---
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [data, setData] = useState([]); 
  const [loading, setLoading] = useState(false);
  const [searchText, setSearchText] = useState("");

  // --- STATE MODAL ---
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [activeTab, setActiveTab] = useState('1'); 
  const [urlInput, setUrlInput] = useState(""); 
  const [fileList, setFileList] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [detailModalOpen, setDetailModalOpen] = useState(false);
  const [selectedRecord, setSelectedRecord] = useState(null);

  // --- 1. CHECK LOGIN KHI MỞ APP ---
  useEffect(() => {
    const token = localStorage.getItem('riskguard_token');
    if (token) {
      setIsLoggedIn(true);
      fetchData(token); 
    }
  }, []);

  const getAuthHeader = () => {
    const token = localStorage.getItem('riskguard_token');
    return { headers: { Authorization: `Bearer ${token}` } };
  };

  // --- 2. LẤY DỮ LIỆU TỪ API ---
  const fetchData = async (tokenParam = null) => {
    const token = tokenParam || localStorage.getItem('riskguard_token');
    if (!token) return;

    setLoading(true);
    try {
      const response = await axios.get(`${API_URL}/results`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setData(response.data);
    } catch (error) {
      if (error.response && error.response.status === 401) {
        message.error("Hết phiên đăng nhập!");
        handleLogout();
      } else {
        message.error("Lỗi kết nối Server!");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('riskguard_token');
    setIsLoggedIn(false);
    setData([]);
    message.info("Đã đăng xuất.");
  };

  const handleLoginSuccess = () => {
    setIsLoggedIn(true);
    fetchData();
  };

  // --- 3. XỬ lý QUÉT ---
  const handleScanSubmit = async () => {
    const config = getAuthHeader(); 
    if (activeTab === '1') {
      // Logic URL
      if (!urlInput) return message.warning("Vui lòng nhập URL!");
      try {
        await axios.post(`${API_URL}/scan/url`, { url: urlInput }, config);
        message.success("Đã gửi URL!");
        resetAndCloseModal();
      } catch (error) {
        message.error("Lỗi: " + error.message);
      }
    } else {
      // Logic File
      if (fileList.length === 0) return message.warning("Chưa chọn file!");
      const formData = new FormData();
      formData.append('file', fileList[0]);
      setUploading(true);
      try {
        await axios.post(`${API_URL}/scan/file`, formData, {
          headers: { 'Content-Type': 'multipart/form-data', 'Authorization': `Bearer ${localStorage.getItem('riskguard_token')}` }
        });
        message.success("Upload thành công!");
        resetAndCloseModal();
      } catch (error) {
        message.error("Lỗi upload!");
      } finally {
        setUploading(false);
      }
    }
  };

  const resetAndCloseModal = () => {
    setIsModalOpen(false);
    setUrlInput("");
    setFileList([]);
    // Bật Mèo Loading
    setLoading(true); 
    setTimeout(() => { fetchData(); }, 4000); 
  };
  // --- HÀM XÓA BẢN GHI ---
  const handleDelete = async (id) => {
    try {
      // Gọi API xóa (Gửi kèm Token)
      await axios.delete(`${API_URL}/results/${id}`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('riskguard_token')}` }
      });
      message.success("Đã xóa bản ghi!");
      fetchData(); // Tải lại danh sách ngay lập tức
    } catch (error) {
      message.error("Lỗi khi xóa!");
    }
  };

  // --- 4. XUẤT PDF ---
  const exportPDF = () => {
    const doc = new jsPDF();
    doc.text("BAO CAO RUI RO (RISKGUARD AI)", 14, 20);
    const tableColumn = ["Loai", "Tieu de", "Muc do", "Diem", "Thoi gian"];
    const tableRows = [];
    data.forEach(item => {
      const type = item.url.startsWith('http') ? "WEB" : "FILE";
      const title = (item.page_title || item.url).substring(0, 40); 
      tableRows.push([type, title, item.analysis?.label, item.analysis?.risk_score, moment(item.scanned_at).format("DD/MM HH:mm")]);
    });
    autoTable(doc, { head: [tableColumn], body: tableRows, startY: 35 });
    doc.save("BaoCao_RiskGuard.pdf");
  };

  // --- 5. UI HELPERS ---
  const chartData = useMemo(() => {
    const safe = data.filter(d => d.analysis?.label === 'SAFE').length;
    const warning = data.filter(d => d.analysis?.label === 'WARNING').length;
    const dangerous = data.filter(d => d.analysis?.label === 'DANGEROUS').length;
    return [{ name: 'An toàn', value: safe }, { name: 'Cảnh báo', value: warning }, { name: 'Nguy hiểm', value: dangerous }];
  }, [data]);

  const filteredData = data.filter(item => 
    item.url.toLowerCase().includes(searchText.toLowerCase()) || 
    (item.page_title && item.page_title.toLowerCase().includes(searchText.toLowerCase()))
  );

  // --- 4. CẤU HÌNH CỘT BẢNG (CHUẨN: 1 NÚT XEM + 1 NÚT XÓA) ---
  const columns = [
    { 
      title: '', key: 'icon', width: 60, align: 'center', 
      render: (_, r) => r.url.startsWith('http') ? <LinkOutlined style={{color:'#1890ff', fontSize: 18}}/> : <FileTextOutlined style={{color:'#fa8c16', fontSize: 18}}/> 
    },
    { 
      title: 'Trạng thái', dataIndex: ['analysis', 'label'], key: 'label', width: 130, 
      render: (l) => <Tag color={l==='DANGEROUS'?'red':l==='SAFE'?'success':'warning'}>{l}</Tag> 
    },
    { 
      title: 'Thông tin', dataIndex: 'url', key: 'url', 
      render: (t, r) => <div><Text strong style={{display:'block', maxWidth: 350}} ellipsis>{r.page_title}</Text><Text type="secondary" style={{fontSize:11}}>{t}</Text></div> 
    },
    { 
      title: 'Điểm', dataIndex: ['analysis', 'risk_score'], key: 'risk_score', width: 80, 
      render: (s) => <b style={{color: s>50?'red':'green'}}>{s}/100</b> 
    },
    { 
      title: 'Thời gian', dataIndex: 'scanned_at', width: 150, 
      render: (t) => moment(t).format("HH:mm DD/MM") 
    },
    { 
      title: 'Hành động', key: 'action', width: 120, 
      render: (_, r) => (
        <Space>
           {/* Chỉ có 1 nút Xem ở đây */}
           <Button size="small" icon={<EyeOutlined />} onClick={() => { setSelectedRecord(r); setDetailModalOpen(true); }}>Xem</Button>
           
           {/* Nút Xóa */}
           <Popconfirm title="Xóa bản ghi này?" onConfirm={() => handleDelete(r.request_id)} okText="Xóa" cancelText="Hủy">
              <Button size="small" danger icon={<DeleteOutlined />} />
           </Popconfirm>
        </Space>
      ),
    },
  ];

  const catLoadingIcon = (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
      <video width="150" autoPlay loop muted playsInline><source src="/loading_cat.mp4" type="video/mp4" /></video>
      <div style={{ marginTop: 10, fontWeight: 'bold', color: '#1890ff' }}>Đang xử lý...</div>
    </div>
  );

  // --- RENDER ---
  if (!isLoggedIn) return <Login onLoginSuccess={handleLoginSuccess} />;

  return (
    <ConfigProvider theme={{ algorithm: isDarkMode ? darkAlgorithm : defaultAlgorithm }}>
      <Layout style={{ minHeight: '100vh' }}>
        
        {/* SIDEBAR */}
        <Sider width={240} theme="dark" collapsible>
          <div style={{ padding: '20px', textAlign: 'center', color: 'white', fontSize: 18, fontWeight: 'bold' }}>🛡️ RiskGuard AI</div>
          <Menu theme="dark" defaultSelectedKeys={['1']} mode="inline" items={[{ key: '1', icon: <DashboardOutlined />, label: 'Dashboard Giám sát' }]} />
          
          <div style={{ padding: '20px', textAlign: 'center', marginTop: '20px' }}>
              <div style={{ background: 'white', borderRadius: '15px', padding: '10px', boxShadow: '0 4px 8px rgba(0,0,0,0.2)' }}>
                 <video width="100%" autoPlay loop muted controls playsInline style={{ borderRadius: '10px' }}><source src="/mascot.mp4" type="video/mp4" /></video>
                 <div style={{ color: '#333', marginTop: 5, fontWeight: 'bold', fontSize: 13 }}>Trợ lý AI đang chạy... 🎵</div>
              </div>
          </div>
        </Sider>

        <Layout>
          {/* HEADER */}
          <Header style={{ padding: '0 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: isDarkMode ? '#001529' : '#fff' }}>
            <Title level={4} style={{margin: 0, color: isDarkMode ? 'white' : 'black'}}>Trung tâm Kiểm soát Rủi ro</Title>
            <Space>
               <Switch checkedChildren="🌙" unCheckedChildren="☀️" checked={isDarkMode} onChange={setIsDarkMode} />
               <Button icon={<DownloadOutlined />} onClick={exportPDF}>Xuất PDF</Button>
               <Button icon={<ReloadOutlined />} onClick={() => fetchData()}>Làm mới</Button>
               <Button type="primary" icon={<ScanOutlined />} onClick={() => setIsModalOpen(true)}>QUÉT MỚI</Button>
               <Popconfirm title="Đăng xuất?" onConfirm={handleLogout}><Button danger icon={<LogoutOutlined />}>Thoát</Button></Popconfirm>
            </Space>
          </Header>

          {/* CONTENT */}
          <Content style={{ margin: '24px' }}>
            <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
               <Col span={6}><Card hoverable><Statistic title="Tổng lượt quét" value={data.length} prefix={<ScanOutlined />} /></Card></Col>
               <Col span={6}><Card hoverable><Statistic title="Nội dung Nguy hiểm" value={chartData[2].value} valueStyle={{ color: '#cf1322' }} prefix={<BugOutlined />} /></Card></Col>
               <Col span={12}>
                  <Card title="Tỷ lệ Rủi ro" bodyStyle={{padding: 0, height: 120}}>
                     <div style={{display: 'flex', height: '100%'}}>
                        <div style={{flex: 1}}>
                          <ResponsiveContainer><PieChart><Pie data={chartData} cx="50%" cy="50%" innerRadius={35} outerRadius={50} dataKey="value">{chartData.map((e, i) => <Cell key={i} fill={COLORS[i]} />)}</Pie><RechartsTooltip /></PieChart></ResponsiveContainer>
                        </div>
                        <div style={{flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center', fontSize: 12}}>
                           <Tag color="#52c41a">An toàn: {chartData[0].value}</Tag>
                           <Tag color="#faad14">Cảnh báo: {chartData[1].value}</Tag>
                           <Tag color="#f5222d">Nguy hiểm: {chartData[2].value}</Tag>
                        </div>
                     </div>
                  </Card>
               </Col>
            </Row>

            <Card title="Phân tích Xu hướng (Real-time)" style={{ marginBottom: 24 }}>
               <div style={{ width: '100%', height: 250 }}>
                  <ResponsiveContainer>
                     <BarChart data={data.slice(0, 10).reverse()}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="scanned_at" tickFormatter={(t) => moment(t).format("HH:mm")} />
                        <YAxis domain={[0, 100]} />
                        <RechartsTooltip labelFormatter={(t) => moment(t).format("DD/MM HH:mm")} formatter={(v) => [`${v} điểm`, 'Rủi ro']} />
                        <Legend />
                        <Bar name="Điểm Rủi ro" dataKey="analysis.risk_score" fill="#1890ff">{data.slice(0, 10).reverse().map((e, i) => <Cell key={i} fill={e.analysis?.risk_score > 50 ? '#f5222d' : '#52c41a'} />)}</Bar>
                     </BarChart>
                  </ResponsiveContainer>
               </div>
            </Card>

            <Card title="Danh sách Web/File đã quét" extra={<Search placeholder="Tìm kiếm..." onSearch={v=>setSearchText(v)} onChange={e=>setSearchText(e.target.value)} style={{ width: 250 }} />}>
               <Spin spinning={loading} indicator={catLoadingIcon}>
                  <Table columns={columns} dataSource={filteredData} rowKey="request_id" pagination={{ pageSize: 6 }} />
               </Spin>
            </Card>
          </Content>
          <Footer style={{ textAlign: 'center' }}>RiskGuard AI System ©2025</Footer>

          {/* --- MODAL 2: CHI TIẾT (NÂNG CẤP CÓ CHAT) --- */}
        <Modal 
            title={<span><BugOutlined /> Phân tích chi tiết & Trợ lý ảo</span>} 
            open={detailModalOpen} 
            onCancel={() => setDetailModalOpen(false)} 
            footer={null} 
            width={900} // Tăng chiều rộng lên chút cho thoải mái
        >
           {selectedRecord && (
             <Tabs defaultActiveKey="1" items={[
               {
                 key: '1',
                 label: '📊 Báo cáo Rủi ro',
                 children: (
                   <div>
                      <Row gutter={16} style={{marginBottom: 20}}>
                         <Col span={12}><Card size="small" title="Kết quả AI"><Title level={3} style={{color: selectedRecord.analysis?.label === 'DANGEROUS' ? 'red' : 'green', margin: 0}}>{selectedRecord.analysis?.label}</Title><Text>Điểm số: {selectedRecord.analysis?.risk_score}/100</Text></Card></Col>
                         <Col span={12}><Card size="small" title="Từ khóa phát hiện">{selectedRecord.analysis?.detected_keywords?.length > 0 ? selectedRecord.analysis.detected_keywords.map(k => <Tag color="volcano" key={k}>{k}</Tag>) : <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="Sạch" />}</Card></Col>
                      </Row>
                      <div style={{marginTop: 10, padding: 15, background: isDarkMode ? '#141414' : '#fff', borderRadius: 5, maxHeight: 400, overflowY: 'auto', border: '1px solid #d9d9d9', lineHeight: '1.8'}}>
                          <Highlighter highlightClassName="YourHighlightClass" searchWords={selectedRecord.analysis?.detected_keywords || []} autoEscape={true} textToHighlight={selectedRecord.content_preview || ""} highlightStyle={{ backgroundColor: '#ffccc7', padding: '0 2px', borderRadius: 2, fontWeight: 'bold', color: 'red' }} />
                      </div>
                   </div>
                 )
               },
               {
                  key: '2',
                  label: '💬 Chat với AI (Qwen3)', 
                  children: (
                   <div>
                      <div style={{marginBottom: 10, fontStyle: 'italic', color: '#888'}}>
                         💡 Bạn có thể hỏi: "Tóm tắt bài này", "Tại sao lại bị đánh dấu nguy hiểm?", "Trích xuất tên người/địa điểm"...
                      </div>
                      {/* Truyền nội dung bài viết vào để AI học */}
                      <ChatBox contextContent={selectedRecord.content_preview} />
                   </div>
                 )
               }
             ]} />
           )}
        </Modal>
        </Layout>
        <Modal 
           title="Quét nội dung mới" 
           open={isModalOpen} 
           onCancel={() => setIsModalOpen(false)} 
           footer={null}
        >
           <Tabs defaultActiveKey="1" items={[
             { 
               key: '1', 
               label: <span><LinkOutlined /> URL Website</span>, 
               children: (
                 <div style={{padding: 20}}>
                    <Input size="large" prefix={<LinkOutlined />} placeholder="Nhập link (VD: https://vnexpress.net)" value={urlInput} onChange={e => setUrlInput(e.target.value)} />
                    <Button type="primary" block size="large" style={{marginTop: 15}} loading={loading} onClick={handleScanSubmit}>BẮT ĐẦU QUÉT</Button>
                 </div>
               ) 
             },
             { 
               key: '2', 
               label: <span><FileTextOutlined /> Tệp tin</span>, 
               children: (
                 <div style={{padding: 10}}>
                    <Dragger fileList={fileList} beforeUpload={(f)=>{setFileList([f]); return false;}} onRemove={()=>setFileList([])} maxCount={1}>
                       <p className="ant-upload-drag-icon"><InboxOutlined /></p>
                       <p>Kéo thả file vào đây</p>
                    </Dragger>
                    <Button type="primary" block size="large" style={{marginTop: 15}} loading={uploading} onClick={handleScanSubmit}>UPLOAD & QUÉT</Button>
                 </div>
               ) 
             }
           ]} onChange={k => setActiveTab(k)} />
        </Modal>
      </Layout>
    </ConfigProvider>
  );
};

export default App;