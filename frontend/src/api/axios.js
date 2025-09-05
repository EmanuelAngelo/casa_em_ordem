import axios from "axios";

const instance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api/",
  timeout: 15000,
});

// Bearer em toda request
instance.interceptors.request.use((config) => {
  const token = localStorage.getItem("accessToken");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Refresh automático ao pegar 401
let isRefreshing = false;
let queue = [];

function processQueue(error, token = null) {
  queue.forEach(({ resolve, reject }) => {
    if (token) {
      resolve(token);
    } else {
      reject(error);
    }
  });
  queue = [];
}

instance.interceptors.response.use(
  (r) => r,
  async (error) => {
    const original = error.config;
    const status = error.response?.status;

    // Se não for 401 ou já tentamos refresh nessa request, repassa erro
    if (status !== 401 || original._retry) {
      return Promise.reject(error);
    }

    // Se não tem refresh, manda pro login
    const refresh = localStorage.getItem("refreshToken");
    if (!refresh) {
      localStorage.removeItem("accessToken");
      if (!window.location.pathname.includes("/login")) {
        const red = encodeURIComponent(
          window.location.pathname + window.location.search
        );
        window.location.href = `/login?redirect=${red}`;
      }
      return Promise.reject(error);
    }

    // Evitar corrida: fila as requests enquanto refresh está em andamento
    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        queue.push({
          resolve: (token) => {
            original.headers.Authorization = `Bearer ${token}`;
            resolve(instance(original));
          },
          reject,
        });
      });
    }

    // Tenta refresh
    original._retry = true;
    isRefreshing = true;
    try {
      const { data } = await axios.post(
        (import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api/") +
          "token/refresh/",
        { refresh },
        { timeout: 15000 }
      );

      const newAccess = data.access;
      localStorage.setItem("accessToken", newAccess);
      instance.defaults.headers.common.Authorization = `Bearer ${newAccess}`;

      processQueue(null, newAccess);
      original.headers.Authorization = `Bearer ${newAccess}`;
      return instance(original);
    } catch (err) {
      processQueue(err, null);
      localStorage.removeItem("accessToken");
      localStorage.removeItem("refreshToken");
      if (!window.location.pathname.includes("/login")) {
        const red = encodeURIComponent(
          window.location.pathname + window.location.search
        );
        window.location.href = `/login?redirect=${red}`;
      }
      return Promise.reject(err);
    } finally {
      isRefreshing = false;
    }
  }
);

export default instance;
