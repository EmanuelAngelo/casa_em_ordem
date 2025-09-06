<template>
  <v-container fluid>
    <v-card>
      <v-toolbar color="blue-darken-3">
        <v-toolbar-title>Meu Casal</v-toolbar-title>
        <v-spacer />
        <v-btn icon @click="loadCasal"><v-icon>mdi-refresh</v-icon></v-btn>
      </v-toolbar>

      <v-card-text>
        <v-row>
          <v-col cols="12" md="6">
            <v-list two-line>
              <v-list-subheader>Informações</v-list-subheader>
              <v-list-item>
                <v-list-item-title>Nome</v-list-item-title>
                <v-list-item-subtitle>{{
                  casal?.nome || "-"
                }}</v-list-item-subtitle>
              </v-list-item>
              <v-list-subheader class="mt-4">Membros</v-list-subheader>
              <v-list-item v-for="m in casal?.membros || []" :key="m.id">
                <v-list-item-title>
                  {{ m.usuario.first_name || m.usuario.username }}
                </v-list-item-title>
                <v-list-item-subtitle>
                  {{ m.ativo ? "Ativo" : "Inativo" }}
                </v-list-item-subtitle>
              </v-list-item>
            </v-list>
          </v-col>

          <v-col cols="12" md="6">
            <v-card variant="outlined">
              <v-card-title>Convidar parceiro(a)</v-card-title>
              <v-card-text>
                <v-form @submit.prevent="onInvite" :disabled="loadingInvite">
                  <v-text-field
                    v-model="usernameOrEmail"
                    label="Username ou e-mail"
                    prepend-inner-icon="mdi-account-plus"
                    required
                  />
                  <v-btn
                    color="blue-darken-3"
                    :loading="loadingInvite"
                    type="submit"
                    >Convidar</v-btn
                  >
                </v-form>
                <v-alert
                  v-if="inviteMsg"
                  class="mt-4"
                  :type="inviteType"
                  variant="tonal"
                >
                  {{ inviteMsg }}
                </v-alert>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>
  </v-container>
</template>

<script setup>
import { ref, onMounted } from "vue";
import axios from "@/api/axios";

const casal = ref(null);
const loadingInvite = ref(false);
const usernameOrEmail = ref("");
const inviteMsg = ref("");
const inviteType = ref("info");

onMounted(loadCasal);

async function loadCasal() {
  try {
    const { data } = await axios.get("/casais/meu/");
    casal.value = data;
  } catch (e) {
    // usuário sem casal (incomum neste fluxo)
    casal.value = null;
  }
}

async function onInvite() {
  inviteMsg.value = "";
  inviteType.value = "info";
  loadingInvite.value = true;
  try {
    await axios.post("/casais-extras/convidar/", {
      username_or_email: usernameOrEmail.value.trim(),
    });
    inviteMsg.value = "Convite concluído. Usuário adicionado ao casal.";
    inviteType.value = "success";
    usernameOrEmail.value = "";
    await loadCasal();
  } catch (e) {
    const d = e.response?.data;
    inviteMsg.value = d?.detail || "Não foi possível concluir o convite.";
    inviteType.value =
      e.response?.status === 409 || e.response?.status === 404
        ? "warning"
        : "error";
  } finally {
    loadingInvite.value = false;
  }
}
</script>
