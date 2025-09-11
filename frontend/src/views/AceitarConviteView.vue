<template>
  <v-container fluid class="fill-height bg-grey-lighten-4">
    <v-row class="d-flex align-center justify-center">
      <v-col cols="12" sm="8" md="5" lg="4">
        <v-card elevation="8">
          <v-toolbar color="blue-darken-3">
            <v-toolbar-title>Aceitar Convite</v-toolbar-title>
          </v-toolbar>

          <v-card-text class="pt-6 text-center">
            <v-skeleton-loader
              v-if="loading"
              type="article"
            ></v-skeleton-loader>

            <div v-else-if="error">
              <v-alert type="error" variant="tonal">{{ error }}</v-alert>
              <v-btn to="/login" class="mt-4">Ir para o Login</v-btn>
            </div>

            <div v-else-if="conviteInfo">
              <p class="text-h6 mb-2">{{ conviteInfo.remetente_nome }}</p>
              <p class="mb-4">
                convidou você para o casal
                <strong>"{{ conviteInfo.casal_nome }}"</strong>.
              </p>

              <!-- Caso 1: Usuário já está logado -->
              <div v-if="isLoggedIn">
                <v-btn color="success" @click="aceitar" :loading="saving"
                  >Entrar no Casal</v-btn
                >
              </div>

              <!-- Caso 2: Usuário não está logado -->
              <div v-else>
                <p class="text-caption mb-4">
                  Para aceitar, crie uma conta ou faça login.
                </p>
                <v-btn to="/login" color="primary" class="me-2"
                  >Fazer Login</v-btn
                >
                <v-btn to="/register" variant="outlined">Criar Conta</v-btn>
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, onMounted, computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import axios from "@/api/axios";

const route = useRoute();
const router = useRouter();

const loading = ref(true);
const saving = ref(false);
const error = ref("");
const conviteInfo = ref(null);
const token = ref(route.query.token || null);

const isLoggedIn = computed(() => !!localStorage.getItem("accessToken"));

onMounted(async () => {
  if (!token.value) {
    error.value = "Token de convite não encontrado.";
    loading.value = false;
    return;
  }

  // Armazena o token para ser usado após o login/registro
  localStorage.setItem("pendingInvitationToken", token.value);

  try {
    const { data } = await axios.get(`/convites/info/${token.value}/`);
    conviteInfo.value = data;
  } catch (e) {
    error.value =
      e.response?.data?.detail ||
      "Não foi possível carregar as informações do convite.";
    localStorage.removeItem("pendingInvitationToken"); // Limpa se o token for inválido
  } finally {
    loading.value = false;
  }
});

async function aceitar() {
  saving.value = true;
  try {
    await axios.post("/convites/aceitar/", { token: token.value });
    localStorage.removeItem("pendingInvitationToken");
    // Forçar logout de sessão antiga se houver (opcional, mas bom)
    // E redirecionar para o dashboard. O token JWT será o novo.
    router.push("/?convite_aceito=1");
  } catch (e) {
    error.value =
      e.response?.data?.detail || "Ocorreu um erro ao aceitar o convite.";
  } finally {
    saving.value = false;
  }
}
</script>
