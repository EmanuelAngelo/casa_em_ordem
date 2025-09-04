import axios from "axios";

const instance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api/",
  timeout: 15000,
});

// se já tiver auth por Bearer, descomente:
// instance.interceptors.request.use((config) => {
//   const token = localStorage.getItem('accessToken')
//   if (token) config.headers.Authorization = `Bearer ${token}`
//   return config
// })

export default instance;
