<template>
  <v-layout class="rounded rounded-md">
    <!-- App bar só no mobile -->
    <v-app-bar
      v-if="display.mdAndDown.value"
      title="Gastos a Dois"
      color="blue-darken-3"
      density="compact"
    >
      <template #prepend>
        <v-app-bar-nav-icon @click.stop="drawer = !drawer" />
      </template>
    </v-app-bar>

    <v-navigation-drawer
      v-model="drawer"
      :rail="rail"
      :permanent="display.mdAndUp.value"
      @click="rail = false"
    >
      <v-list-item prepend-avatar="" :title="userName" nav>
        <template #append>
          <v-btn
            v-if="display.mdAndUp.value"
            icon="mdi-chevron-left"
            variant="text"
            @click.stop="rail = !rail"
          />
        </template>
      </v-list-item>

      <v-divider />

      <div class="d-flex flex-column" style="height: calc(100% - 65px)">
        <v-list density="compact" nav class="flex-grow-1">
          <v-list-item
            prepend-icon="mdi-view-dashboard"
            :disabled="$route.meta?.hideChrome"
            title="Dashboard"
            to="/"
          />
          <v-list-item
            prepend-icon="mdi-email-arrow-right-outline"
            :disabled="$route.meta?.hideChrome"
            title="Meu Casal"
            to="/meu-casal"
          />
          <v-list-item
            prepend-icon="mdi-cash-multiple"
            :disabled="$route.meta?.hideChrome"
            title="Lançamentos"
            to="/lancamentos"
          />
          <v-list-item
            prepend-icon="mdi-file-cog"
            :disabled="$route.meta?.hideChrome"
            title="Modelos de Despesa"
            value="despesas-modelo"
            to="/modelos"
          />

          <v-list-item
            prepend-icon="mdi-shape-plus-outline"
            :disabled="$route.meta?.hideChrome"
            title="Categorias"
            to="/categorias"
          />
          <!-- <v-list-item prepend-icon="mdi-cog-outline" title="Configurações" to="/config" /> -->
          <!-- <v-list-item v-if="isStaff" prepend-icon="mdi-account-group" title="Usuários" to="/usuarios" /> -->
          <v-list-item
            prepend-icon="mdi-logout"
            title="Sair"
            style="background-color: brown"
            @click="showLogoutDialog = true"
          />
        </v-list>
      </div>
    </v-navigation-drawer>

    <v-main
      class="d-flex align-center justify-center"
      style="min-height: 300px"
    >
      <div class="pa-4" style="width: 100%; height: 100%; overflow-y: auto">
        <router-view />
      </div>
    </v-main>

    <v-dialog v-model="showLogoutDialog" persistent max-width="400px">
      <v-card>
        <v-card-title class="text-h5">Confirmar Saída</v-card-title>
        <v-card-text
          >Você tem certeza de que deseja sair do sistema?</v-card-text
        >
        <v-card-actions>
          <v-spacer />
          <v-btn text @click="showLogoutDialog = false">Cancelar</v-btn>
          <v-btn color="red-darken-1" @click="handleLogout">Sair</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-layout>
</template>

<script setup>
import { ref, onMounted, computed } from "vue";
import { useRouter } from "vue-router";
import axios from "@/api/axios";
import { useDisplay } from "vuetify";

const display = useDisplay();
const drawer = ref(display.mdAndUp.value);
const rail = ref(false);
const showLogoutDialog = ref(false);
const router = useRouter();

const userName = ref("Usuário");
const isStaff = computed(() => localStorage.getItem("isStaff") === "true");

onMounted(() => {
  const storedName = localStorage.getItem("userName");
  if (storedName) userName.value = storedName;
});

const handleLogout = () => {
  localStorage.removeItem("accessToken");
  localStorage.removeItem("refreshToken");
  localStorage.removeItem("userName");
  delete axios.defaults.headers.common["Authorization"];
  showLogoutDialog.value = false;
  router.push("/login");
};
</script>

<style scoped>
.v-layout {
  height: 100vh;
  width: 100vw;
}
</style>
