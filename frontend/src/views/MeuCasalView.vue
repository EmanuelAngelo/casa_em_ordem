<template>
  <v-container fluid>
    <v-card>
      <v-toolbar color="blue-darken-3">
        <v-toolbar-title>Meu Casal</v-toolbar-title>
        <v-spacer />
        <v-btn icon @click="loadCasal" :disabled="saving"
          ><v-icon>mdi-refresh</v-icon></v-btn
        >
      </v-toolbar>

      <v-card-text>
        <v-row>
          <!-- Coluna da Esquerda: Informações e Salários -->
          <v-col cols="12" md="6">
            <v-skeleton-loader
              v-if="loading"
              type="list-item-two-line@2"
            ></v-skeleton-loader>
            <div v-else>
              <v-text-field
                v-model="casal.nome"
                label="Nome do Casal"
                variant="outlined"
                density="compact"
                class="mb-4"
              />

              <v-list-subheader>Membros e Salários</v-list-subheader>
              <div
                v-for="membro in casal.membros"
                :key="membro.id"
                class="mb-3"
              >
                <v-text-field
                  v-model.number="membro.salario_mensal"
                  :label="`Salário de ${
                    membro.usuario.first_name || membro.usuario.username
                  }`"
                  type="number"
                  step="0.01"
                  prefix="R$"
                  variant="outlined"
                  density="compact"
                  hide-details
                />
              </div>
              <v-btn
                color="blue-darken-3"
                :loading="saving"
                @click="saveMembros"
                class="mt-2"
              >
                Salvar Alterações
              </v-btn>
            </div>
          </v-col>

          <!-- Coluna da Direita: Convite (sem alterações) -->
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
    <v-snackbar v-model="snackbar.show" :color="snackbar.color" :timeout="3000">
      {{ snackbar.text }}
    </v-snackbar>
  </v-container>
</template>

<script setup>
import { ref, reactive, onMounted } from "vue";
import axios from "@/api/axios";

const casal = ref({ nome: "", membros: [] });
const loading = ref(true);
const saving = ref(false);
const loadingInvite = ref(false);
const usernameOrEmail = ref("");
const inviteMsg = ref("");
const inviteType = ref("info");
const snackbar = reactive({ show: false, text: "", color: "success" });

onMounted(loadCasal);

async function loadCasal() {
  loading.value = true;
  try {
    const { data } = await axios.get("/casais/meu/");
    casal.value = data;
  } catch (e) {
    casal.value = { nome: "Não encontrado", membros: [] };
    snackbar.value = {
      show: true,
      text: "Não foi possível carregar dados do casal.",
      color: "error",
    };
  } finally {
    loading.value = false;
  }
}

async function saveMembros() {
  saving.value = true;
  try {
    // Salva o nome do casal primeiro
    await axios.patch(`/casais/${casal.value.id}/`, { nome: casal.value.nome });

    // Salva o salário de cada membro em paralelo
    const promises = casal.value.membros.map((membro) =>
      axios.patch(`/membros/${membro.id}/`, {
        salario_mensal: membro.salario_mensal || 0,
      })
    );
    await Promise.all(promises);

    snackbar.value = {
      show: true,
      text: "Dados do casal salvos com sucesso!",
      color: "success",
    };
  } catch (e) {
    snackbar.value = {
      show: true,
      text: "Erro ao salvar os dados.",
      color: "error",
    };
  } finally {
    saving.value = false;
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
