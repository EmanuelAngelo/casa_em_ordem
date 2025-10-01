<template>
  <v-container fluid class="fill-height">
    <v-row class="d-flex align-center justify-center">
      <v-col cols="12" sm="8" md="5" lg="4">
        <v-card elevation="8">
          <v-toolbar color="blue-darken-3">
            <v-toolbar-title>Criar conta</v-toolbar-title>
          </v-toolbar>

          <v-card-text class="pt-6">
            <v-form @submit.prevent="onSubmit" :disabled="loading">
              <v-text-field
                v-model="first_name"
                label="Nome"
                prepend-inner-icon="mdi-account"
                class="mb-3"
              />
              <v-text-field
                v-model="username"
                label="Usuário"
                prepend-inner-icon="mdi-account-circle"
                required
                class="mb-3"
              />
              <v-text-field
                v-model="email"
                label="E-mail"
                prepend-inner-icon="mdi-email"
                type="email"
                class="mb-3"
              />
              <v-text-field
                v-model="password"
                label="Senha"
                type="password"
                prepend-inner-icon="mdi-lock"
                required
                class="mb-3"
              />
              <v-text-field
                v-model="nome_grupo"
                label="Nome do grupo (opcional)"
                prepend-inner-icon="mdi-home-group"
              />
              <span>
                Se alguém da casa já
                <b>criou conta com o nome do grupo,</b> deixe em branco
              </span>
              <v-btn
                class="mt-4"
                color="blue-darken-3"
                block
                :loading="loading"
                type="submit"
              >
                Criar e entrar
              </v-btn>
            </v-form>

            <v-alert v-if="error" type="error" variant="tonal" class="mt-4">
              {{ error }}
            </v-alert>
          </v-card-text>

          <v-card-actions class="justify-center">
            <RouterLink to="/login">Já tem conta? Entrar</RouterLink>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref } from "vue";
import { useRouter, useRoute } from "vue-router";
import axios from "@/api/axios";

const router = useRouter();
const route = useRoute();

const first_name = ref("");
const username = ref("");
const email = ref("");
const password = ref("");
const nome_grupo = ref(""); // <-- antes era nome_casal
const loading = ref(false);
const error = ref("");

async function onSubmit() {
  loading.value = true;
  error.value = "";
  try {
    const { data } = await axios.post("/auth/register/", {
      first_name: first_name.value,
      username: username.value,
      email: email.value,
      password: password.value,
      nome_grupo: nome_grupo.value, // <-- chave esperada pelo backend
    });

    localStorage.setItem("accessToken", data.access);
    localStorage.setItem("refreshToken", data.refresh);
    localStorage.setItem(
      "userName",
      data.user?.first_name || data.user?.username || username.value
    );

    axios.defaults.headers.common["Authorization"] = `Bearer ${data.access}`;

    const pendingToken = localStorage.getItem("pendingInvitationToken");
    if (pendingToken) {
      try {
        // Mantido como está no seu fluxo; ajuste a rota se necessário no backend
        await axios.post("/convites/aceitar/", { token: pendingToken });
        localStorage.removeItem("pendingInvitationToken");
      } catch (acceptError) {
        console.error(
          "Falha ao aceitar convite pendente após registro:",
          acceptError
        );
      }
    }

    const redirect = route.query.redirect || "/";
    router.replace(redirect);
  } catch (e) {
    const errors = e.response?.data;
    let errorMessage =
      "Não foi possível criar a conta. Verifique os dados e tente novamente.";

    if (errors && typeof errors === "object") {
      const firstErrorKey = Object.keys(errors)[0];
      const errorMessages = errors[firstErrorKey];
      if (Array.isArray(errorMessages) && errorMessages.length > 0) {
        errorMessage = errorMessages[0];
      } else if (typeof errorMessages === "string") {
        errorMessage = errorMessages;
      }
    }

    error.value = errorMessage;
  } finally {
    loading.value = false;
  }
}
</script>
