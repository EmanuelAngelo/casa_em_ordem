<template>
  <v-container fluid class="fill-height">
    <v-row class="d-flex align-center justify-center">
      <v-col cols="12" sm="8" md="5" lg="4">
        <v-card elevation="8">
          <v-toolbar color="blue-darken-3">
            <v-toolbar-title>Acessar</v-toolbar-title>
          </v-toolbar>

          <v-card-text class="pt-6">
            <v-form @submit.prevent="onSubmit" :disabled="loading">
              <v-text-field
                v-model="username"
                label="Usuário"
                prepend-inner-icon="mdi-account"
                autocomplete="username"
                required
                class="mb-3"
              />
              <v-text-field
                v-model="password"
                label="Senha"
                type="password"
                prepend-inner-icon="mdi-lock"
                autocomplete="current-password"
                required
              />
              <v-btn
                class="mt-4"
                color="blue-darken-3"
                block
                :loading="loading"
                type="submit"
              >
                Entrar
              </v-btn>
            </v-form>

            <v-alert v-if="error" type="error" variant="tonal" class="mt-4">
              {{ error }}
            </v-alert>
          </v-card-text>
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

const username = ref("");
const password = ref("");
const loading = ref(false);
const error = ref("");

async function onSubmit() {
  loading.value = true;
  error.value = "";
  try {
    // ajuste se o endpoint for diferente
    const { data } = await axios.post("/token/", {
      username: username.value,
      password: password.value,
    });
    localStorage.setItem("accessToken", data.access);
    localStorage.setItem(
      "userName",
      data.user?.first_name || data.user?.username || username.value
    );

    const redirect = route.query.redirect || "/";
    router.replace(redirect);
  } catch (e) {
    error.value = "Usuário ou senha inválidos.";
  } finally {
    loading.value = false;
  }
}
</script>
