import { createRouter, createWebHistory } from "vue-router";

const routes = [
  {
    path: "/login",
    name: "login",
    component: () => import("@/views/LoginView.vue"),
    meta: { public: true },
  },
  {
    path: "/",
    component: () => import("@/views/TelaPrincipal.vue"),
    meta: { requiresAuth: true },
    children: [
      {
        path: "",
        name: "home",
        component: () => import("@/views/HomeView.vue"),
      },
      {
        path: "lancamentos",
        name: "lancamentos",
        component: () => import("@/views/LancamentosView.vue"),
      },
    ],
  },
  { path: "/:pathMatch(.*)*", redirect: "/" },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

// guard simples (ajuste conforme sua auth real)
router.beforeEach((to) => {
  if (to.meta.public) return true;
  const token = localStorage.getItem("accessToken");
  if (!token) return { name: "login", query: { redirect: to.fullPath } };
  return true;
});

export default router;
