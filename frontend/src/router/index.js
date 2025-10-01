import { createRouter, createWebHistory } from "vue-router";

// lazy imports
const TelaPrincipal = () => import("../views/TelaPrincipal.vue");
const Dashboard = () => import("../views/HomeView.vue");
const Lancamentos = () => import("@/views/LancamentosView.vue");
const Categorias = () => import("@/views/CategoriasView.vue");
const Login = () => import("@/views/LoginView.vue");
const Register = () => import("../views/RegisterView.vue");
const MeuGrupo = () => import("@/views/MeuGrupoView.vue"); // renomeado
const DespesasModelo = () => import("@/views/DespesasModeloView.vue");
const RelatorioFinanceiro = () =>
  import("../views/RelatorioFinanceiroView.vue");
const AceitarConvite = () => import("@/views/AceitarConviteView.vue");

const router = createRouter({
  history: createWebHistory(),
  routes: [
    // PÚBLICAS (sem layout)
    {
      path: "/login",
      name: "login",
      component: Login,
      meta: { public: true, hideChrome: true },
    },
    {
      path: "/register",
      name: "register",
      component: Register,
      meta: { public: true, hideChrome: true },
    },
    // Aceitar convite (rota pública para entrar em grupo)
    {
      path: "/aceitar-convite",
      name: "aceitar-convite",
      component: AceitarConvite,
      meta: { public: true, hideChrome: true },
    },

    // AUTENTICADAS (com layout principal)
    {
      path: "/",
      component: TelaPrincipal, // drawer/topbar aqui
      children: [
        { path: "", name: "dashboard", component: Dashboard },
        { path: "lancamentos", name: "lancamentos", component: Lancamentos },
        {
          path: "relatorio",
          name: "relatorio",
          component: RelatorioFinanceiro,
        },
        { path: "categorias", name: "categorias", component: Categorias },
        { path: "meu-grupo", name: "meu-grupo", component: MeuGrupo },
        { path: "modelos", name: "despesas-modelo", component: DespesasModelo },
      ],
    },

    // fallback
    { path: "/:pathMatch(.*)*", redirect: "/" },
  ],
});

// guard simples
router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem("accessToken");

  // Se rota é privada e não tem token, manda pro login
  if (!to.meta?.public && !token) {
    const redirect = encodeURIComponent(to.fullPath || "/");
    return next(`/login?redirect=${redirect}`);
  }

  // Se já está logado e tentou abrir /login ou /register, vai pro app
  if (to.meta?.public && token) {
    return next("/");
  }

  next();
});

export default router;
