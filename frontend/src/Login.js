import React, { useState } from 'react';
import axios from 'axios';
import { Form, Input, Button, Card, Typography, message } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';

const { Title, Text } = Typography;

const Login = ({ onLoginSuccess }) => {
  const [loading, setLoading] = useState(false);

  const handleLogin = async (values) => {
    setLoading(true);
    try {
      // Gửi request lấy Token (Dùng Form Data theo chuẩn OAuth2)
      const formData = new URLSearchParams();
      formData.append('username', values.username);
      formData.append('password', values.password);

      const response = await axios.post('http://localhost:8000/api/v1/token', formData, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      });

      const token = response.data.access_token;
      
      // Lưu token vào bộ nhớ trình duyệt
      localStorage.setItem('riskguard_token', token);
      message.success("Đăng nhập thành công! Chào mừng Admin.");
      
      // Chuyển hướng vào Dashboard
      onLoginSuccess();

    } catch (error) {
      message.error("Đăng nhập thất bại! Vui lòng kiểm tra lại tài khoản.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ 
      height: '100vh', 
      display: 'flex', 
      justifyContent: 'center', 
      alignItems: 'center', 
      background: 'linear-gradient(135deg, #1f4037 0%, #99f2c8 100%)' // Màu nền xanh ngầu
    }}>
      <Card style={{ width: 400, borderRadius: 15, boxShadow: '0 10px 25px rgba(0,0,0,0.3)' }}>
        <div style={{ textAlign: 'center', marginBottom: 20 }}>
          <div style={{ fontSize: 40 }}>🛡️</div>
          <Title level={2} style={{ color: '#1f4037' }}>RiskGuard AI</Title>
          <Text type="secondary">Hệ thống Giám sát An ninh Nội dung</Text>
        </div>

        <Form name="login" onFinish={handleLogin} layout="vertical">
          <Form.Item name="username" rules={[{ required: true, message: 'Vui lòng nhập tên đăng nhập!' }]}>
            <Input size="large" prefix={<UserOutlined />} placeholder="Tên đăng nhập" />
          </Form.Item>

          <Form.Item name="password" rules={[{ required: true, message: 'Vui lòng nhập mật khẩu!' }]}>
            <Input.Password size="large" prefix={<LockOutlined />} placeholder="Mật khẩu" />
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" block size="large" loading={loading} 
              style={{ background: '#1f4037', borderColor: '#1f4037', fontWeight: 'bold' }}>
              ĐĂNG NHẬP
            </Button>
          </Form.Item>
        </Form>
        <div style={{ textAlign: 'center', color: '#888' }}>
           Tài khoản Demo: <b>admin / admin123</b>
        </div>
      </Card>
    </div>
  );
};

export default Login;