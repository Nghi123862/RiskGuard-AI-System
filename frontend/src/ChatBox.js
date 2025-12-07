import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { Input, Button, List, Avatar, Spin, message } from 'antd';
import { SendOutlined, RobotOutlined, UserOutlined } from '@ant-design/icons';

const API_URL = "http://localhost:8000/api/v1";

const ChatBox = ({ contextContent }) => {
  const [messages, setMessages] = useState([
    { role: 'ai', content: 'Xin chào! Tôi đã đọc xong nội dung này. Bạn cần tôi giúp gì không? (Tóm tắt, giải thích rủi ro...)' }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  // Tự động cuộn xuống cuối khi có tin nhắn mới
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMsg = { role: 'user', content: input };
    setMessages(prev => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const token = localStorage.getItem('riskguard_token');
      const response = await axios.post(`${API_URL}/chat`, {
        message: userMsg.content,
        context: contextContent || ""
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      const aiMsg = { role: 'ai', content: response.data.reply };
      setMessages(prev => [...prev, aiMsg]);

    } catch (error) {
      message.error("AI đang bận, vui lòng thử lại sau.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '400px', border: '1px solid #d9d9d9', borderRadius: '8px', background: '#fff' }}>
      {/* KHUNG HIỂN THỊ TIN NHẮN */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '15px' }}>
        <List
          itemLayout="horizontal"
          dataSource={messages}
          renderItem={item => (
            <List.Item style={{ border: 'none', padding: '5px 0' }}>
              <div style={{ 
                  display: 'flex', 
                  width: '100%', 
                  justifyContent: item.role === 'user' ? 'flex-end' : 'flex-start' 
              }}>
                {item.role === 'ai' && <Avatar icon={<RobotOutlined />} style={{ backgroundColor: '#1890ff', marginRight: 10 }} />}
                
                <div style={{
                    background: item.role === 'user' ? '#1890ff' : '#f0f2f5',
                    color: item.role === 'user' ? '#fff' : '#000',
                    padding: '8px 12px',
                    borderRadius: '12px',
                    maxWidth: '70%',
                    wordWrap: 'break-word'
                }}>
                    {item.content}
                </div>

                {item.role === 'user' && <Avatar icon={<UserOutlined />} style={{ backgroundColor: '#87d068', marginLeft: 10 }} />}
              </div>
            </List.Item>
          )}
        />
        {loading && <div style={{ textAlign: 'left', marginLeft: 40, color: '#999' }}>AI đang suy nghĩ... <Spin size="small" /></div>}
        <div ref={messagesEndRef} />
      </div>

      {/* KHUNG NHẬP LIỆU */}
      <div style={{ padding: '10px', borderTop: '1px solid #eee', display: 'flex' }}>
        <Input 
            placeholder="Hỏi AI về nội dung này..." 
            value={input} 
            onChange={e => setInput(e.target.value)}
            onPressEnter={handleSend}
            disabled={loading}
        />
        <Button type="primary" icon={<SendOutlined />} onClick={handleSend} loading={loading} style={{ marginLeft: 10 }}>
            Gửi
        </Button>
      </div>
    </div>
  );
};

export default ChatBox;