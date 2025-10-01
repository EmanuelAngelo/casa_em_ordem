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

            <div v-else>
              <!-- Informação principal (fluxo por token descontinuado) -->
              <p class="text-h6 mb-2">Convite para entrar em um grupo</p>
              <p class="mb-4">
                Nosso fluxo de convite por link/token foi descontinuado. Agora,
                o responsável do <strong>grupo</strong> deve adicionar você
                informando seu <strong>usuário</strong> ou
                <strong>e-mail</strong> dentro do próprio sistema.
              </p>

              <!-- Caso 1: Usuário já está logado -->
              <div v-if="isLoggedIn">
                <v-alert type="info" variant="tonal" class="mb-4">
                  Compartilhe seu usuário com quem vai te convidar:
                  <br />
                  <strong>{{ currentUserLabel }}</strong>
                </v-alert>
                <v-btn color="primary" @click="copiarUsuario" :loading="saving">
                  Copiar meu usuário
                </v-btn>
                <div class="mt-4">
                  <v-btn to="/" class="mt-2">Ir para o Dashboard</v-btn>
                </div>
              </div>

              <!-- Caso 2: Usuário não está logado -->
              <div v-else>
                <p class="text-caption mb-4">
                  Para entrar em um grupo, faça login ou crie sua conta e
                  informe seu usuário para o responsável te adicionar.
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
import { useRoute } from "vue-router";

const route = useRoute();

const loading = ref(true);
const saving = ref(false);
const error = ref("");
const token = ref(route.query.token || null);

// Está logado quando há accessToken
const isLoggedIn = computed(() => !!localStorage.getItem("accessToken"));
// Mostra um rótulo amigável pro usuário logado
const currentUserLabel = computed(() => {
  return (
    localStorage.getItem("userName") ||
    localStorage.getItem("lastLoginUsername") ||
    "meu-usuario"
  );
});

onMounted(async () => {
  // Fluxo antigo por token foi descontinuado: apenas mantemos a UX
  // Armazenamos o token (se existir) para referência futura e explicamos o novo fluxo.
  if (token.value) {
    localStorage.setItem("pendingInvitationToken", token.value);
  }

  // Como não existe mais /convites/info/:token/, não consultamos API aqui.
  // Apenas sinalizamos ao usuário o novo procedimento.
  loading.value = false;
});

async function copiarUsuario() {
  try {
    saving.value = true;
    await navigator.clipboard.writeText(currentUserLabel.value);
  } catch (_) {
    // silencioso; manter layout
  } finally {
    saving.value = false;
  }
}
</script>
