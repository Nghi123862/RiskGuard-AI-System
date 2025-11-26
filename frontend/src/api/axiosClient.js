// src/api/axiosClient.js
import axios from 'axios';

const axiosClient = axios.create({
  baseURL: 'http://localhost:8000/api/v1', // Địa chỉ Python Backend
  headers: {
    'Content-Type': 'application/json',
  },
});

export default axiosClient;